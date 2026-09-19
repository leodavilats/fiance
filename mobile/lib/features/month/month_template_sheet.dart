import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/cash_models.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/month.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';

Future<void> openMonthTemplateSheet(BuildContext context, WidgetRef ref) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) => const _TemplateSheet(),
  );
}

class _TemplateSheet extends ConsumerStatefulWidget {
  const _TemplateSheet();

  @override
  ConsumerState<_TemplateSheet> createState() => _TemplateSheetState();
}

class _TemplateSheetState extends ConsumerState<_TemplateSheet> {
  CashMonthTemplate? _template;
  Set<int> _chosen = {};
  Object? _error;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final alvo = ref.read(selectedMonthProvider);
    try {
      final m = await ref
          .read(apiRepositoryProvider)
          .getMonthTemplate(target: alvo, source: previousMonth(alvo));
      if (!mounted) return;
      setState(() {
        _template = m;
        _chosen = {
          for (var i = 0; i < m.candidates.length; i++)
            if (m.candidates[i].repeats && !m.candidates[i].alreadyThere) i,
        };
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e);
    }
  }

  Future<void> _store() async {
    final m = _template;
    if (m == null || _chosen.isEmpty) return;

    setState(() => _saving = true);
    try {
      final lote = [for (final i in _chosen) m.candidates[i]];
      await ref.read(apiRepositoryProvider).createCashEntriesBatch(lote);

      ref.invalidate(cashMonthProvider);
      ref.invalidate(cashEntriesProvider);
      ref.invalidate(surplusProvider);

      if (!mounted) return;
      final quantos = lote.length;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '$quantos ${quantos == 1 ? 'lançamento copiado' : 'lançamentos copiados'} '
            'para ${monthName(m.target)}',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = e;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final erro = _error;
    if (erro != null) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(FiSpace.s5),
          child: FiErrorState(
            error: erro,
            action: 'montar o molde do mês',
            onRetry: () {
              setState(() => _error = null);
              _load();
            },
          ),
        ),
      );
    }

    final m = _template;
    if (m == null) {
      return const SafeArea(
        child: Padding(
          padding: EdgeInsets.all(FiSpace.s6),
          child: FiSkeleton(shape: FiSkeletonShape.row, count: 5),
        ),
      );
    }

    final disponiveis = [
      for (var i = 0; i < m.candidates.length; i++)
        if (!m.candidates[i].alreadyThere) i,
    ];

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          FiSpace.s5,
          0,
          FiSpace.s5,
          FiSpace.s6,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Repetir ${monthName(m.source)}',
              style: FiType.pageTitle.copyWith(color: fiInk1(context)),
            ),
            const SizedBox(height: FiSpace.s2),
            Text(
              disponiveis.isEmpty
                  ? 'Tudo que ${monthName(m.source)} tinha já está em ${monthName(m.target)}.'
                  : 'Vem marcado o que repete todo mês. O gasto variável fica desmarcado: o '
                        'valor do mês que passou é fato daquele mês.',
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
            const SizedBox(height: FiSpace.s3),

            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: [
                  FiRows(
                    children: [
                      for (final i in disponiveis)
                        FiDataRow(
                          label: m.candidates[i].description,
                          detail:
                              '${formatCurrency(m.candidates[i].amount)} · '
                              '${cashCategoryLabel(m.candidates[i].kind, m.candidates[i].category)}'
                              '${m.candidates[i].repeats ? '' : ' · variável'}',
                          trailing: Checkbox(
                            value: _chosen.contains(i),
                            onChanged: (v) => setState(() {
                              if (v ?? false) {
                                _chosen.add(i);
                              } else {
                                _chosen.remove(i);
                              }
                            }),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: FiSpace.s5),
            FiButton.primary(
              label: _chosen.isEmpty
                  ? 'Escolha o que copiar'
                  : 'Copiar ${_chosen.length} para ${monthName(m.target)}',
              expand: true,
              busy: _saving,
              onPressed: _chosen.isEmpty ? null : _store,
            ),
            if (_chosen.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: FiSpace.s2),
                child: Text(
                  'Tudo de uma vez, ou nada. O copiado nasce a vencer.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
