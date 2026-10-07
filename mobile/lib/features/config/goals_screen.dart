import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/sector_translations.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/controls.dart';

class GoalsScreen extends StatelessWidget {
  const GoalsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Metas')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: [
          Text(
            'Diga quanto quer em cada tipo de investimento. A Sobra compara a sua carteira com '
            'essa divisão, e só aponta desvio depois que você salvar uma divisão que some 100%.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const PassiveIncomeSection(),
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

class PassiveIncomeSection extends ConsumerWidget {
  const PassiveIncomeSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferences = ref.watch(preferencesProvider);

    return FiSection(
      title: 'Renda passiva',
      hint: 'Quanto você quer receber por mês. É o alvo da régua de progresso do patrimônio.',
      child: preferences.when(
        loading: () => const FiSkeleton(shape: FiSkeletonShape.row, count: 1),
        error: (err, _) => FiErrorState(
          error: err,
          action: 'carregar sua meta',
          onRetry: () => ref.invalidate(preferencesProvider),
        ),
        data: (prefs) => FiDataRow(
          label: 'Meta por mês',
          value: prefs.passiveIncomeGoal == null
              ? 'sem meta'
              : formatCurrency(prefs.passiveIncomeGoal),
          note: prefs.passiveIncomeGoal == null
              ? 'Sem alvo declarado o produto não inventa um.'
              : null,
          onTap: () => _editar(context, ref, prefs),
        ),
      ),
    );
  }

  Future<void> _editar(
    BuildContext context,
    WidgetRef ref,
    Preferences prefs,
  ) async {
    final controller = TextEditingController(text: formatForInput(prefs.passiveIncomeGoal));

    final salvar = await showDialog<bool>(
      context: context,
      builder: (context) => ValueListenableBuilder<TextEditingValue>(
        valueListenable: controller,
        builder: (context, digitado, _) {
          final texto = digitado.text.trim();
          final valor = parseDecimal(texto);
          final valido = texto.isEmpty || (valor != null && valor > 0);
          return AlertDialog(
            title: const Text('Meta de renda passiva'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Quanto você quer receber de proventos por mês. Deixe vazio para não declarar '
                  'alvo nenhum.',
                  style: FiType.body.copyWith(color: fiInk2(context)),
                ),
                const SizedBox(height: FiSpace.s4),
                TextField(
                  controller: controller,
                  autofocus: true,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Meta por mês',
                    prefixText: r'R$ ',
                    errorText: valido ? null : 'Use um valor em reais maior que zero, como 1.500,00',
                  ),
                ),
              ],
            ),
            actions: [
              FiButton.quiet(
                label: 'Cancelar',
                onPressed: () => Navigator.pop(context, false),
              ),
              FiButton.primary(
                label: texto.isEmpty ? 'Ficar sem meta' : 'Salvar',
                onPressed: valido ? () => Navigator.pop(context, true) : null,
              ),
            ],
          );
        },
      ),
    );
    if (salvar != true || !context.mounted) return;

    final valor = parseDecimal(controller.text.trim());
    final ok = await fiAttempt(
      context,
      () => ref.read(apiRepositoryProvider).savePreferences(
            passiveIncomeGoal: valor,
            clearPassiveIncomeGoal: valor == null,
          ),
      action: 'salvar sua meta',
      success: valor == null ? 'Meta removida' : 'Meta salva',
    );
    if (!ok) return;
    ref.invalidate(preferencesProvider);
    ref.invalidate(dashboardProvider);
  }
}

class _GoalRow extends StatelessWidget {
  const _GoalRow({
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
                formatPercent(value, digits: 0),
                style: FiType.figure.copyWith(color: fiInk1(context)),
              ),
            ],
          ),
          FiSlider(
            label: label,
            value: value,
            min: 0,
            max: 100,
            divisions: 100,
            format: formatPercent,
            flush: true,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}

class _NotYours extends StatelessWidget {
  const _NotYours();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s3),
      child: Text(
        'Este é o ponto de partida do produto, e não a sua escolha. Enquanto for assim, nada '
        'no aplicativo cobra desvio contra ele — salve para que passe a cobrar.',
        style: FiType.body.copyWith(color: fiInk2(context)),
      ),
    );
  }
}


class _Closing extends StatelessWidget {
  const _Closing({
    required this.total,
    required this.requiresFullAllocation,
    required this.onSave,
    this.saving = false,
  });

  final double total;

  final bool requiresFullAllocation;

  final VoidCallback? onSave;

  final bool saving;

  @override
  Widget build(BuildContext context) {
    final fechou = (total - 100).abs() < 0.5;
    final diferenca = 100 - total;
    final estado = !requiresFullAllocation
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
                'Soma ${formatPercent(total, digits: 0)}',
                style: FiType.metricSm.copyWith(
                  color: fiStateColor(estado, Theme.of(context).brightness),
                ),
              ),
            ),
            FiButton.primary(label: 'Salvar metas', busy: saving, onPressed: onSave),
          ],
        ),
        if (requiresFullAllocation && !fechou) ...[
          const SizedBox(height: FiSpace.s2),
          Text(
            diferenca > 0
                ? 'Faltam ${formatDecimal(diferenca, digits: 0)} pontos para fechar 100%.'
                : 'Passou ${formatDecimal(-diferenca, digits: 0)} pontos de 100%. '
                      'Tire de alguma categoria.',
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
  bool _saving = false;

  Future<void> _save(Future<void> Function() write) async {
    setState(() => _saving = true);
    final ok = await fiAttempt(
      context,
      write,
      action: 'salvar suas metas por categoria',
      success: 'Metas por categoria salvas',
    );
    if (!mounted) return;
    if (ok) {
      ref.invalidate(goalsProvider);
      ref.invalidate(onboardingProvider);
      invalidateAllocationReaders(ref);
    }
    setState(() {
      _saving = false;
      if (ok) _editing = null;
    });
  }

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
        final padrao = data.isNotEmpty && data.every((g) => !g.declared);
        final podeSalvar = (_editing != null || padrao) && (total - 100).abs() < 0.5;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (padrao) const _NotYours(),
            for (final g in items)
              _GoalRow(
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
            _Closing(
              total: total,
              requiresFullAllocation: true,
              saving: _saving,
              onSave: podeSalvar && !_saving
                  ? () => _save(() => ref.read(apiRepositoryProvider).saveGoals(_editing ?? data))
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
  bool _saving = false;

  Future<void> _save(Future<void> Function() write) async {
    setState(() => _saving = true);
    final ok = await fiAttempt(
      context,
      write,
      action: 'salvar suas metas por setor',
      success: 'Metas por setor salvas',
    );
    if (!mounted) return;
    if (ok) {
      ref.invalidate(sectorGoalsProvider);
      invalidateAllocationReaders(ref);
    }
    setState(() {
      _saving = false;
      if (ok) _editing = null;
    });
  }

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
        final padrao = items.every((g) => !g.declared);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (padrao) const _NotYours(),
            for (final g in current)
              _GoalRow(
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
            _Closing(
              total: total,
              requiresFullAllocation: false,
              saving: _saving,
              onSave: _saving || (_editing == null && (!padrao || data.isEmpty))
                  ? null
                  : () => _save(
                      () => ref.read(apiRepositoryProvider).saveSectorGoals(_editing ?? data),
                    ),
            ),
          ],
        );
      },
    );
  }
}
