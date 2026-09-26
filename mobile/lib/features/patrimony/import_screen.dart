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
import '../../core/widgets/section.dart';
import '../../core/widgets/tag.dart';

class ImportScreen extends ConsumerStatefulWidget {
  const ImportScreen({super.key});

  @override
  ConsumerState<ImportScreen> createState() => _ImportScreenState();
}

class _ImportScreenState extends ConsumerState<ImportScreen> {
  final _content = TextEditingController();

  ImportPreview? _preview;
  Object? _previewError;
  bool _checking = false;
  bool _committing = false;
  bool _includeDuplicates = false;

  @override
  void dispose() {
    _content.dispose();
    super.dispose();
  }

  void _contentChanged(String _) {
    if (_preview == null && _previewError == null) return;
    setState(() {
      _preview = null;
      _previewError = null;
      _includeDuplicates = false;
    });
  }

  Future<void> _check() async {
    setState(() {
      _checking = true;
      _previewError = null;
    });
    try {
      final preview = await ref.read(apiRepositoryProvider).previewImport(_content.text);
      if (!mounted) return;
      setState(() {
        _preview = preview;
        _checking = false;
        _includeDuplicates = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _previewError = e;
        _checking = false;
      });
    }
  }

  Future<void> _commit() async {
    setState(() => _committing = true);
    try {
      final result = await ref
          .read(apiRepositoryProvider)
          .commitImport(_content.text, includeDuplicates: _includeDuplicates);
      if (!mounted) return;
      invalidateLedgerReaders(ref);
      final ficaram = result.skippedDuplicates == 0
          ? ''
          : ' ${result.skippedDuplicates} repetida(s) ficaram de fora.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${result.imported} operação(ões) importada(s).$ficaram')),
      );
      if (context.canPop()) {
        context.pop();
      } else {
        context.go('/patrimonio/razao');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _committing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(fiErrorMessage(e, action: 'importar as operações'))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final preview = _preview;
    final temTexto = _content.text.trim().isNotEmpty;

    return Scaffold(
      appBar: AppBar(title: const Text('Importar operações')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s3,
          FiLayout.gutter,
          FiSpace.s6,
        ),
        children: [
          Text(
            'Cole a lista ou o CSV que sua corretora exporta',
            style: FiType.title.copyWith(color: fiInk1(context)),
          ),
          const SizedBox(height: FiSpace.s2),
          Text(
            'Nada é gravado antes de você conferir a revisão, e a importação é tudo ou nada: '
            'com uma linha errada, nenhuma entra.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const SizedBox(height: FiSpace.s4),
          TextField(
            controller: _content,
            minLines: 6,
            maxLines: 14,
            keyboardType: TextInputType.multiline,
            onChanged: (v) {
              _contentChanged(v);
              setState(() {});
            },
            decoration: const InputDecoration(
              labelText: 'Operações',
              alignLabelWithHint: true,
              hintText: 'PETR4 100 30,50\nVALE3 50 62,10 15/03/2024\n\n'
                  'ou\n\nData;Ativo;Tipo;Quantidade;Preço;Taxas',
            ),
          ),
          const SizedBox(height: FiSpace.s2),
          Text(
            'Aceita vírgula ou ponto no decimal, data em DD/MM/AAAA ou AAAA-MM-DD, e cabeçalho '
            'em português ou inglês. Sem data, a operação entra como de hoje; sem tipo, como '
            'compra.',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
          const SizedBox(height: FiSpace.s4),
          FiButton.primary(
            label: _checking ? 'Conferindo…' : 'Conferir',
            icon: Icons.fact_check_outlined,
            busy: _checking,
            onPressed: temTexto && !_checking && !_committing ? _check : null,
          ),
          if (_previewError != null) ...[
            const SizedBox(height: FiSpace.s3),
            Text(
              fiErrorMessage(_previewError!, action: 'conferir as operações'),
              style: FiType.caption.copyWith(
                color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
              ),
            ),
          ],
          if (preview != null)
            _Review(
              preview: preview,
              includeDuplicates: _includeDuplicates,
              committing: _committing,
              onIncludeDuplicates: (v) => setState(() => _includeDuplicates = v),
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
    required this.includeDuplicates,
    required this.committing,
    required this.onIncludeDuplicates,
    required this.onCommit,
  });

  final ImportPreview preview;
  final bool includeDuplicates;
  final bool committing;
  final ValueChanged<bool> onIncludeDuplicates;
  final VoidCallback onCommit;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final novas = preview.fresh.length;
    final repetidas = preview.repeated.length;
    final aGravar = novas + (includeDuplicates ? repetidas : 0);
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
                  ? '1 linha precisa de correção — nada será importado enquanto houver erro.'
                  : '${preview.issues.length} linhas precisam de correção — nada será importado '
                        'enquanto houver erro.',
              style: FiType.label.copyWith(color: fiStateColor(FiState.adverse, brightness)),
            ),
            const SizedBox(height: FiSpace.s3),
            for (final issue in preview.issues)
              Padding(
                padding: const EdgeInsets.only(bottom: FiSpace.s3),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Linha ${issue.line}: ${issue.message}',
                      style: FiType.body.copyWith(color: fiInk1(context)),
                    ),
                    if (issue.raw.isNotEmpty)
                      Text(
                        issue.raw,
                        style: FiType.caption.copyWith(color: fiInk3(context)),
                      ),
                  ],
                ),
              ),
          ],
          if (preview.rows.isEmpty && preview.issues.isEmpty)
            Text(
              'Nenhuma operação encontrada no texto.',
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
          if (preview.rows.isNotEmpty) ...[
            Text(
              _summary(novas, repetidas),
              style: FiType.body.copyWith(color: fiInk1(context)),
            ),
            if (repetidas > 0) ...[
              const SizedBox(height: FiSpace.s3),
              FiSwitch(
                label: 'Importar também as que já existem',
                value: includeDuplicates,
                onChanged: committing ? null : onIncludeDuplicates,
              ),
              Text(
                'Duas compras iguais no mesmo dia acontecem. Ligue só se forem operações de '
                'verdade, e não a mesma linha trazida de novo.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ],
            const SizedBox(height: FiSpace.s4),
            for (final row in preview.rows) _ImportRowObject(row: row),
          ],
          const SizedBox(height: FiSpace.s4),
          FiButton.primary(
            label: committing
                ? 'Importando…'
                : aGravar == 1
                ? 'Importar 1 operação'
                : 'Importar $aGravar operações',
            expand: true,
            busy: committing,
            onPressed: bloqueada || committing ? null : onCommit,
          ),
        ],
      ),
    );
  }

  static String _summary(int novas, int repetidas) {
    final partes = novas == 1 ? '1 operação nova' : '$novas operações novas';
    if (repetidas == 0) return '$partes — nada foi gravado ainda.';
    final ja = repetidas == 1 ? '1 que já existe' : '$repetidas que já existem';
    return '$partes e $ja no razão — nada foi gravado ainda.';
  }
}

class _ImportRowObject extends StatelessWidget {
  const _ImportRowObject({required this.row});

  final ImportRow row;

  @override
  Widget build(BuildContext context) {
    final e = row.entry;
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(e.symbol, style: FiType.title.copyWith(color: fiInk1(context))),
                ),
                if (row.isDuplicate) ...[
                  const FiTag(label: 'Já no razão', state: FiState.attention),
                  const SizedBox(width: FiSpace.s2),
                ],
                FiTag.series(label: ledgerKindLabel(e.kind), color: fiInk2(context)),
              ],
            ),
            FiRows(
              children: [
                FiDataRow(label: 'Linha', value: '${row.line}'),
                FiDataRow(label: 'Data', value: formatDate(e.tradedOn)),
                if (e.hasQuantity)
                  FiDataRow(label: 'Quantidade', value: formatQuantity(e.quantity)),
                if (e.hasPrice) FiDataRow(label: 'Preço', value: formatCurrency(e.price)),
                if (e.fees > 0) FiDataRow(label: 'Custos', value: formatCurrency(e.fees)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
