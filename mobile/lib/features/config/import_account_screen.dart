import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/section.dart';

final accountFileReaderProvider = Provider<Future<Map<String, dynamic>?> Function()>(
  (ref) => () async {
    final escolhido = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['json'],
      withData: true,
    );
    final bytes = escolhido?.files.single.bytes;
    if (bytes == null) return null;
    final conteudo = jsonDecode(utf8.decode(bytes));
    if (conteudo is! Map<String, dynamic>) {
      throw const FormatException('O arquivo não é uma exportação do fiance.');
    }
    return conteudo;
  },
);

String _day(double epochSeconds) => formatDate(
  DateTime.fromMillisecondsSinceEpoch((epochSeconds * 1000).round()).toIso8601String(),
);

const _issuesShown = 10;

class ImportAccountScreen extends ConsumerStatefulWidget {
  const ImportAccountScreen({super.key});

  @override
  ConsumerState<ImportAccountScreen> createState() => _ImportAccountScreenState();
}

class _ImportAccountScreenState extends ConsumerState<ImportAccountScreen> {
  Map<String, dynamic>? _file;
  AccountImportPreview? _preview;
  Object? _error;
  bool _reading = false;
  bool _importing = false;

  Future<void> _choose() async {
    setState(() {
      _reading = true;
      _error = null;
    });
    try {
      final arquivo = await ref.read(accountFileReaderProvider)();
      if (arquivo == null) {
        if (mounted) setState(() => _reading = false);
        return;
      }
      final previa = await ref.read(apiRepositoryProvider).previewAccountImport(arquivo);
      if (!mounted) return;
      setState(() {
        _file = arquivo;
        _preview = previa;
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

  void _refreshReaders() {
    invalidateLedgerReaders(ref);
    ref.invalidate(fixedIncomeProvider);
    ref.invalidate(dividendsProvider);
    ref.invalidate(goalsProvider);
    ref.invalidate(sectorGoalsProvider);
    ref.invalidate(preferencesProvider);
    ref.invalidate(alertsProvider);
    ref.invalidate(cashMonthProvider);
    ref.invalidate(cashEntriesProvider);
    ref.invalidate(debtsProvider);
    ref.invalidate(surplusProvider);
  }

  Future<void> _import() async {
    final arquivo = _file;
    if (arquivo == null) return;
    setState(() => _importing = true);
    try {
      await ref.read(apiRepositoryProvider).importAccount(arquivo);
      if (!mounted) return;
      _refreshReaders();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Seus dados voltaram para esta conta.')),
      );
      context.go('/patrimonio');
    } catch (e) {
      if (!mounted) return;
      setState(() => _importing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(fiErrorMessage(e, action: 'importar seus dados'))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final previa = _preview;
    final brightness = Theme.of(context).brightness;

    return Scaffold(
      appBar: AppBar(title: const Text('Importar meus dados')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s3,
          FiLayout.gutter,
          FiSpace.s8,
        ),
        children: [
          Text(
            'Traga de volta o que você exportou',
            style: FiType.title.copyWith(color: fiInk1(context)),
          ),
          const SizedBox(height: FiSpace.s2),
          Text(
            'Escolha o arquivo que o fiance gerou em "Baixar meus dados". Nada é gravado antes de '
            'você conferir o que ele traz, e a importação é tudo ou nada.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const SizedBox(height: FiSpace.s4),
          FiButton(
            label: _reading ? 'Lendo o arquivo…' : 'Escolher o arquivo',
            icon: Icons.file_open_outlined,
            tone: previa == null ? FiButtonTone.primary : FiButtonTone.secondary,
            busy: _reading,
            onPressed: _reading || _importing ? null : _choose,
          ),
          if (_error != null) ...[
            const SizedBox(height: FiSpace.s3),
            Text(
              _error is FormatException
                  ? 'Este arquivo não é uma exportação do fiance.'
                  : fiErrorMessage(_error!, action: 'ler o arquivo'),
              style: FiType.caption.copyWith(color: fiStateColor(FiState.adverse, brightness)),
            ),
          ],
          if (previa != null) ...[
            FiSection(
              title: 'O que o arquivo traz',
              hint: [
                if (previa.exportedAt != null) 'Exportado em ${_day(previa.exportedAt!)}',
                if (previa.sourceEmail != null) 'da conta ${previa.sourceEmail}',
              ].join(' '),
              child: FiRows(
                children: [
                  for (final s in previa.sections)
                    FiDataRow(label: s.label, value: '${s.count}'),
                ],
              ),
            ),
            if (previa.leftOut.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s2),
              Text(
                'Fica de fora, porque é da conta e não seu: ${previa.leftOut.join(', ')}.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ],
            if (previa.issues.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s4),
              Text(
                previa.issues.length == 1
                    ? '1 item do arquivo tem problema, e nada será gravado enquanto ele existir.'
                    : '${previa.issues.length} itens do arquivo têm problema, e nada será '
                          'gravado enquanto eles existirem.',
                style: FiType.label.copyWith(color: fiStateColor(FiState.adverse, brightness)),
              ),
              const SizedBox(height: FiSpace.s2),
              for (final i in previa.issues.take(_issuesShown))
                Padding(
                  padding: const EdgeInsets.only(bottom: FiSpace.s2),
                  child: Text(
                    '${i.label}, item ${i.index}: ${i.message}',
                    style: FiType.body.copyWith(color: fiInk1(context)),
                  ),
                ),
              if (previa.issues.length > _issuesShown)
                Text(
                  'e mais ${previa.issues.length - _issuesShown} '
                  '${previa.issues.length - _issuesShown == 1 ? 'item' : 'itens'} com problema. '
                  'Corrija estes e confira de novo.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
            ],
            if (previa.blockers.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s4),
              Text(
                'Esta conta já tem ${previa.blockers.join(', ')}. A importação só entra em conta '
                'sem dados financeiros, para não somar o arquivo ao que já existe e duplicar a '
                'carteira.',
                style: FiType.body.copyWith(
                  color: fiStateColor(FiState.attention, brightness),
                ),
              ),
            ],
            if (previa.ok) ...[
              const SizedBox(height: FiSpace.s2),
              Text(
                'Preferências e metas do arquivo substituem as desta conta. A carteira é refeita '
                'a partir dos lançamentos do razão.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ],
            const SizedBox(height: FiSpace.s5),
            FiButton.primary(
              label: _importing ? 'Importando…' : 'Importar',
              expand: true,
              busy: _importing,
              onPressed: previa.ok && !_importing ? _import : null,
            ),
          ],
        ],
      ),
    );
  }
}
