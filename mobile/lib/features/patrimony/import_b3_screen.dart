import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/ledger_models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/controls.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/tag.dart';

final b3FileReaderProvider = Provider<Future<List<int>?> Function()>(
  (ref) => () async {
    final escolhido = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['xlsx'],
      withData: true,
    );
    return escolhido?.files.single.bytes;
  },
);

String _plural(int n, String um, String varios) => n == 1 ? '1 $um' : '$n $varios';

class ImportB3Screen extends ConsumerStatefulWidget {
  const ImportB3Screen({super.key});

  @override
  ConsumerState<ImportB3Screen> createState() => _ImportB3ScreenState();
}

class _ImportB3ScreenState extends ConsumerState<ImportB3Screen> {
  List<int>? _file;
  B3ImportPreview? _preview;
  Object? _error;
  bool _reading = false;
  bool _committing = false;
  final Set<int> _include = {};

  Future<void> _choose() async {
    setState(() {
      _reading = true;
      _error = null;
    });
    try {
      final arquivo = await ref.read(b3FileReaderProvider)();
      if (arquivo == null) {
        if (mounted) setState(() => _reading = false);
        return;
      }
      final previa = await ref.read(apiRepositoryProvider).previewB3Import(arquivo);
      if (!mounted) return;
      setState(() {
        _file = arquivo;
        _preview = previa;
        _include.clear();
        _reading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _file = null;
        _preview = null;
        _error = e;
        _reading = false;
      });
    }
  }

  Future<void> _commit() async {
    final arquivo = _file;
    if (arquivo == null) return;
    setState(() => _committing = true);
    B3ImportResult? result;
    final ok = await fiAttempt(
      context,
      () async {
        result = await ref
            .read(apiRepositoryProvider)
            .commitB3Import(arquivo, includeLines: {..._include});
      },
      action: 'importar o extrato da B3',
    );
    if (!mounted) return;
    final r = result;
    if (!ok || r == null) {
      setState(() => _committing = false);
      return;
    }
    invalidateLedgerReaders(ref);
    final partes = [
      if (r.operations > 0) _plural(r.operations, 'operação', 'operações'),
      if (r.dividends > 0) _plural(r.dividends, 'provento', 'proventos'),
    ];
    final gravado = partes.isEmpty ? 'Nada novo importado.' : '${partes.join(' e ')} importados.';
    final ficaram = r.skippedDuplicates == 0
        ? ''
        : ' ${_plural(r.skippedDuplicates, 'repetida ficou', 'repetidas ficaram')} de fora.';
    fiNotify(context, '$gravado$ficaram');
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/patrimonio/razao');
    }
  }

  @override
  Widget build(BuildContext context) {
    final previa = _preview;
    final brightness = Theme.of(context).brightness;

    return Scaffold(
      appBar: AppBar(title: const Text('Extrato da B3')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s3,
          FiLayout.gutter,
          FiSpace.s8,
        ),
        children: [
          Text(
            'Traga o que a B3 registrou',
            style: FiType.title.copyWith(color: fiInk1(context)),
          ),
          const SizedBox(height: FiSpace.s2),
          Text(
            'Na Área do Investidor da B3, abra Extratos › Movimentação, escolha o período e '
            'baixe em Excel. Nada é gravado antes de você conferir, e a importação é tudo ou nada.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const SizedBox(height: FiSpace.s2),
          Text(
            'Compras e vendas entram no dia do pregão, dois pregões antes da liquidação que a B3 '
            'mostra. JCP, dividendos e rendimentos entram nos proventos recebidos, com o valor '
            'líquido.',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
          const SizedBox(height: FiSpace.s4),
          FiButton(
            label: _reading ? 'Lendo o arquivo…' : 'Escolher o arquivo .xlsx',
            icon: Icons.file_open_outlined,
            tone: previa == null ? FiButtonTone.primary : FiButtonTone.secondary,
            busy: _reading,
            onPressed: _reading || _committing ? null : _choose,
          ),
          if (_error != null) ...[
            const SizedBox(height: FiSpace.s3),
            Text(
              fiErrorMessage(_error!, action: 'ler o extrato'),
              style: FiType.caption.copyWith(color: fiStateColor(FiState.adverse, brightness)),
            ),
          ],
          if (previa != null)
            _Review(
              preview: previa,
              include: _include,
              committing: _committing,
              onInclude: (linha, incluir) => setState(() {
                if (incluir) {
                  _include.add(linha);
                } else {
                  _include.remove(linha);
                }
              }),
              onCommit: _commit,
            ),
        ],
      ),
    );
  }
}

class _Review extends StatelessWidget {
  const _Review({
    required this.preview,
    required this.include,
    required this.committing,
    required this.onInclude,
    required this.onCommit,
  });

  final B3ImportPreview preview;
  final Set<int> include;
  final bool committing;
  final void Function(int line, bool include) onInclude;
  final VoidCallback onCommit;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final novas = preview.rows.where((r) => !r.isDuplicate).toList();
    final repetidas = preview.rows.where((r) => r.isDuplicate).length;
    final aGravar = novas.length + include.length;
    final bloqueada = preview.issues.isNotEmpty || aGravar == 0;

    return FiSection(
      title: 'Revisão',
      hint: 'Formato lido: ${preview.format}',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (preview.issues.isNotEmpty) ...[
            Text(
              preview.issues.length == 1
                  ? '1 linha impede a importação — nada será gravado enquanto ela existir.'
                  : '${preview.issues.length} linhas impedem a importação — nada será gravado '
                        'enquanto elas existirem.',
              style: FiType.label.copyWith(color: fiStateColor(FiState.adverse, brightness)),
            ),
            const SizedBox(height: FiSpace.s3),
            for (final issue in preview.issues) _IssueLine(issue: issue),
          ],
          if (preview.rows.isEmpty && preview.issues.isEmpty)
            Text(
              'O extrato não tem compra, venda nem provento de ativo da B3.',
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
          if (preview.rows.isNotEmpty)
            Text(
              _summary(novas, repetidas),
              style: FiType.body.copyWith(color: fiInk1(context)),
            ),
          if (preview.warnings.isNotEmpty) ...[
            const SizedBox(height: FiSpace.s4),
            Text(
              preview.warnings.length == 1
                  ? '1 aviso, que não impede a importação:'
                  : '${preview.warnings.length} avisos, que não impedem a importação:',
              style: FiType.label.copyWith(color: fiStateColor(FiState.attention, brightness)),
            ),
            const SizedBox(height: FiSpace.s2),
            for (final aviso in preview.warnings) _IssueLine(issue: aviso),
          ],
          const SizedBox(height: FiSpace.s4),
          FiButton.primary(
            label: committing
                ? 'Importando…'
                : 'Importar ${_plural(aGravar, 'lançamento', 'lançamentos')}',
            expand: true,
            busy: committing,
            onPressed: bloqueada || committing ? null : onCommit,
          ),
          if (preview.rows.isNotEmpty)
            FiSection(
              title: 'Lido do extrato',
              count: preview.rows.length,
              child: FiRows(
                children: [
                  for (final row in preview.rows)
                    _B3RowLine(
                      row: row,
                      included: include.contains(row.line),
                      onInclude: committing ? null : (v) => onInclude(row.line, v),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  static String _summary(List<B3ImportRow> novas, int repetidas) {
    final proventos = novas.where((r) => r.isDividend).length;
    final operacoes = novas.length - proventos;
    final contadas = [
      if (operacoes > 0) _plural(operacoes, 'operação nova', 'operações novas'),
      if (proventos > 0) _plural(proventos, 'provento novo', 'proventos novos'),
    ];
    final partes = contadas.isEmpty ? 'Nada novo' : contadas.join(' e ');
    if (repetidas == 0) return '$partes — nada foi gravado ainda.';
    final ja = _plural(repetidas, 'linha parece já estar', 'linhas parecem já estar');
    return '$partes. $ja no fiance e fica de fora, a menos que você marque — nada foi gravado '
        'ainda.';
  }
}

class _IssueLine extends StatelessWidget {
  const _IssueLine({required this.issue});

  final ImportIssue issue;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s3),
      child: Text(
        issue.line > 0 ? 'Linha ${issue.line}: ${issue.message}' : issue.message,
        style: FiType.body.copyWith(color: fiInk1(context)),
      ),
    );
  }
}

class _B3RowLine extends StatelessWidget {
  const _B3RowLine({required this.row, required this.included, required this.onInclude});

  final B3ImportRow row;
  final bool included;
  final ValueChanged<bool>? onInclude;

  @override
  Widget build(BuildContext context) {
    final linha = FiDataRow(
      label:
          '${row.symbol} · ${row.isDividend ? dividendKindLabel(row.kind) : ledgerKindLabel(row.kind)}',
      value: formatCurrency(row.amount),
      detail: row.isDividend
          ? [
              'creditado em ${formatDate(row.day)}',
              '${formatQuantity(row.quantity)} × ${formatCurrency(row.price)} bruto',
              'linha ${row.line}',
            ].join(' · ')
          : [
              'pregão de ${formatDate(row.day)}',
              '${formatQuantity(row.quantity)} × ${formatCurrency(row.price)}',
              if (row.settledOn != null) 'liquidada em ${formatDate(row.settledOn!)}',
              'linha ${row.line}',
            ].join(' · '),
    );
    final par = row.duplicate;
    if (par == null) return linha;

    final noFiance = [
      formatDate(par.day),
      if (par.quantity != null && par.price != null)
        '${formatQuantity(par.quantity!)} × ${formatCurrency(par.price!)}',
      if (par.amount != null) formatCurrency(par.amount!),
    ].join(' · ');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        linha,
        const FiTag(label: 'Já no fiance', state: FiState.attention),
        const SizedBox(height: FiSpace.s1),
        Text(
          'No fiance: $noFiance',
          style: FiType.caption.copyWith(color: fiInk3(context)),
        ),
        Row(
          children: [
            Expanded(
              child: Text(
                'Importar também',
                style: FiType.body.copyWith(color: fiInk2(context)),
              ),
            ),
            FiSwitch(
              label: 'Importar também a linha ${row.line}',
              value: included,
              onChanged: onInclude,
            ),
          ],
        ),
        const SizedBox(height: FiSpace.s2),
      ],
    );
  }
}
