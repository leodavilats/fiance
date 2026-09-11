import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/sector_translations.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';

/// A alocação-alvo: a referência contra a qual a carteira é comparada.
class ObjetivosScreen extends StatelessWidget {
  const ObjetivosScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Objetivos')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: [
          Text(
            'A meta é a referência contra a qual a sua carteira é comparada. Enquanto a soma '
            'não fechar 100%, o desvio calculado na Sobra não quer dizer nada — por isso '
            'salvar só libera lá.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const FiSection(title: 'Por categoria', child: GoalsSection()),
          const FiSection(
            title: 'Por setor',
            hint: 'Dentro do total em ações, não do total da carteira.',
            child: SectorGoalsSection(),
          ),
        ],
      ),
    );
  }
}

class _LinhaDeMeta extends StatelessWidget {
  const _LinhaDeMeta({
    required this.label,
    required this.value,
    required this.onChanged,
  });

  final String label;
  final double value;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  label,
                  style: FiType.body.copyWith(color: fiInk1(context)),
                ),
              ),
              Text(
                '${value.toStringAsFixed(0)}%',
                style: FiType.figure.copyWith(color: fiInk1(context)),
              ),
            ],
          ),
          Slider(
            value: value.clamp(0, 100),
            max: 100,
            divisions: 100,
            label: '${value.toStringAsFixed(0)}%',
            semanticFormatterCallback: (v) => '$label: ${v.round()} por cento',
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}

class _Fechamento extends StatelessWidget {
  const _Fechamento({
    required this.total,
    required this.exigeCemPorCento,
    required this.onSalvar,
  });

  final double total;

  /// A meta por categoria só faz sentido somando 100%; a por setor aceita parcial.
  final bool exigeCemPorCento;

  final VoidCallback? onSalvar;

  @override
  Widget build(BuildContext context) {
    final fechou = (total - 100).abs() < 0.5;
    final estado = !exigeCemPorCento
        ? FiState.neutral
        : (fechou ? FiState.favorable : FiState.attention);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: FiSpace.s2),
        Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
        const SizedBox(height: FiSpace.s3),
        Row(
          children: [
            Expanded(
              child: Text(
                'Soma ${total.toStringAsFixed(0)}%',
                style: FiType.metricSm.copyWith(
                  color: fiStateColor(estado, Theme.of(context).brightness),
                ),
              ),
            ),
            FiButton.primary(label: 'Salvar metas', onPressed: onSalvar),
          ],
        ),
        if (exigeCemPorCento && !fechou) ...[
          const SizedBox(height: FiSpace.s2),
          Text(
            'Faltam ${(100 - total).abs().toStringAsFixed(0)} pontos para fechar 100%.',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
        ],
      ],
    );
  }
}

class GoalsSection extends ConsumerStatefulWidget {
  const GoalsSection({super.key});

  @override
  ConsumerState<GoalsSection> createState() => GoalsSectionState();
}

class GoalsSectionState extends ConsumerState<GoalsSection> {
  List<Goal>? _editing;

  @override
  Widget build(BuildContext context) {
    final goals = ref.watch(goalsProvider);

    return goals.when(
      loading: () => const FiSkeleton(shape: FiSkeletonShape.row, count: 4),
      error: (err, _) => FiErrorState(
        error: err,
        action: 'carregar suas metas',
        onRetry: () => ref.invalidate(goalsProvider),
      ),
      data: (data) {
        final items = _editing ?? data;
        final total = items.fold<double>(0, (sum, g) => sum + g.targetPct);
        final podeSalvar = _editing != null && (total - 100).abs() < 0.5;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final g in items)
              _LinhaDeMeta(
                label: categoryLabel(g.category),
                value: g.targetPct,
                onChanged: (v) => setState(() {
                  _editing = items
                      .map(
                        (it) => it.category == g.category
                            ? it.copyWith(targetPct: v)
                            : it,
                      )
                      .toList();
                }),
              ),
            _Fechamento(
              total: total,
              exigeCemPorCento: true,
              onSalvar: podeSalvar
                  ? () async {
                      await ref.read(apiRepositoryProvider).saveGoals(_editing!);
                      ref.invalidate(goalsProvider);
                      setState(() => _editing = null);
                    }
                  : null,
            ),
          ],
        );
      },
    );
  }
}

const _sectorFallbackList = [
  'Financeiro',
  'Energia',
  'Varejo',
  'Tecnologia',
  'Saúde',
  'Outros',
];

class SectorGoalsSection extends ConsumerStatefulWidget {
  const SectorGoalsSection({super.key});

  @override
  ConsumerState<SectorGoalsSection> createState() => SectorGoalsSectionState();
}

class SectorGoalsSectionState extends ConsumerState<SectorGoalsSection> {
  List<SectorGoal>? _editing;

  @override
  Widget build(BuildContext context) {
    final goals = ref.watch(sectorGoalsProvider);

    return goals.when(
      loading: () => const FiSkeleton(shape: FiSkeletonShape.row, count: 4),
      error: (err, _) => FiErrorState(
        error: err,
        action: 'carregar suas metas por setor',
        onRetry: () => ref.invalidate(sectorGoalsProvider),
      ),
      data: (data) {
        final items = data.isNotEmpty
            ? data
            : _sectorFallbackList
                  .map(
                    (s) => SectorGoal(
                      sector: s,
                      targetPct: 100 / _sectorFallbackList.length,
                    ),
                  )
                  .toList();
        final current = _editing ?? items;
        final total = current.fold<double>(0, (sum, g) => sum + g.targetPct);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final g in current)
              _LinhaDeMeta(
                label: translateSector(g.sector),
                value: g.targetPct,
                onChanged: (v) => setState(() {
                  _editing = current
                      .map(
                        (it) => it.sector == g.sector
                            ? it.copyWith(targetPct: v)
                            : it,
                      )
                      .toList();
                }),
              ),
            _Fechamento(
              total: total,
              exigeCemPorCento: false,
              onSalvar: _editing == null
                  ? null
                  : () async {
                      await ref
                          .read(apiRepositoryProvider)
                          .saveSectorGoals(_editing!);
                      ref.invalidate(sectorGoalsProvider);
                      setState(() => _editing = null);
                    },
            ),
          ],
        );
      },
    );
  }
}
