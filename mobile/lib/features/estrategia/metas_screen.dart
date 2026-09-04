import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/design_tokens.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/sector_translations.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';

class MetasScreen extends StatelessWidget {
  const MetasScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final isDark = brightness == Brightness.dark;
    final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;
    final ink3 = isDark ? FiColors.darkInk3 : FiColors.lightInk3;

    return Scaffold(
      appBar: AppBar(title: const Text('Minhas metas')),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: FiSpace.s4),
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: FiSpace.s4),
            child: Text(
              'A meta é a referência contra a qual a sua carteira é comparada. '
              'Enquanto a soma não fechar 100%, o desvio calculado em Estratégia '
              'não quer dizer nada — por isso o botão de salvar só libera lá.',
              style: FiType.body.copyWith(color: ink2),
            ),
          ),
          const SizedBox(height: FiSpace.s5),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: FiSpace.s4),
            child: Text(
              'POR CATEGORIA',
              style: FiType.eyebrow.copyWith(color: ink3),
            ),
          ),
          const SizedBox(height: FiSpace.s2),
          const GoalsSection(),
          const SizedBox(height: FiSpace.s6),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: FiSpace.s4),
            child: Text(
              'POR SETOR',
              style: FiType.eyebrow.copyWith(color: ink3),
            ),
          ),
          const SizedBox(height: FiSpace.s1),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: FiSpace.s4),
            child: Text(
              'Dentro do total em ações, não do total da carteira.',
              style: FiType.caption.copyWith(color: ink3),
            ),
          ),
          const SizedBox(height: FiSpace.s2),
          const SectorGoalsSection(),
        ],
      ),
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
      loading: () => const Padding(
        padding: EdgeInsets.all(16),
        child: LinearProgressIndicator(),
      ),
      error: (err, _) => Padding(
        padding: const EdgeInsets.all(16),
        child: FiErrorState(error: err, action: 'carregar suas metas'),
      ),
      data: (data) {
        final items = _editing ?? data;
        final total = items.fold<double>(0, (sum, g) => sum + g.targetPct);

        return Column(
          children: [
            ...items.map(
              (g) => Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 4,
                ),
                child: Row(
                  children: [
                    Expanded(child: Text(categoryLabel(g.category))),
                    SizedBox(
                      width: 160,
                      child: Slider(
                        value: g.targetPct.clamp(0, 100),
                        max: 100,
                        divisions: 100,
                        label: '${g.targetPct.toStringAsFixed(0)}%',
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
                    ),
                    SizedBox(
                      width: 44,
                      child: Text('${g.targetPct.toStringAsFixed(0)}%'),
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Total: ${total.toStringAsFixed(0)}%',
                    style: TextStyle(
                      color: (total - 100).abs() < 0.5
                          ? fiStateColor(
                              FiState.favorable,
                              Theme.of(context).brightness,
                            )
                          : fiStateColor(
                              FiState.adverse,
                              Theme.of(context).brightness,
                            ),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  FilledButton(
                    onPressed: _editing == null || (total - 100).abs() >= 0.5
                        ? null
                        : () async {
                            await ref
                                .read(apiRepositoryProvider)
                                .saveGoals(_editing!);
                            ref.invalidate(goalsProvider);
                            setState(() => _editing = null);
                          },
                    child: const Text('Salvar'),
                  ),
                ],
              ),
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
      loading: () => const Padding(
        padding: EdgeInsets.all(16),
        child: LinearProgressIndicator(),
      ),
      error: (err, _) => Padding(
        padding: const EdgeInsets.all(16),
        child: FiErrorState(error: err, action: 'carregar suas metas'),
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
          children: [
            ...current.map(
              (g) => Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 4,
                ),
                child: Row(
                  children: [
                    Expanded(child: Text(translateSector(g.sector))),
                    SizedBox(
                      width: 160,
                      child: Slider(
                        value: g.targetPct.clamp(0, 100),
                        max: 100,
                        divisions: 100,
                        label: '${g.targetPct.toStringAsFixed(0)}%',
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
                    ),
                    SizedBox(
                      width: 44,
                      child: Text('${g.targetPct.toStringAsFixed(0)}%'),
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Total: ${total.toStringAsFixed(0)}%'),
                  FilledButton(
                    onPressed: _editing == null
                        ? null
                        : () async {
                            await ref
                                .read(apiRepositoryProvider)
                                .saveSectorGoals(_editing!);
                            ref.invalidate(sectorGoalsProvider);
                            setState(() => _editing = null);
                          },
                    child: const Text('Salvar'),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
