import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/models.dart';
import '../../../core/providers.dart';
import '../../../core/sector_translations.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/allocation_gap.dart';
import '../../../core/widgets/empty_state.dart';
import 'patrimony_positions.dart';

enum FiCompositionMode { position, category, sector }

const fiStockCategories = {'acoes_br', 'bdrs'};

const _visiblePositions = 6;

class FiCompositionSlice {
  const FiCompositionSlice({
    required this.label,
    required this.value,
    required this.pct,
    required this.color,
    this.targetPct,
  });

  final String label;
  final double value;
  final double pct;
  final Color color;

  final double? targetPct;
}

class FiCompositionBlock extends ConsumerStatefulWidget {
  const FiCompositionBlock({
    super.key,
    required this.allocations,
    required this.positions,
    this.mode = FiCompositionMode.position,
  });

  final List<CategoryAllocation> allocations;
  final List<PortfolioPosition> positions;
  final FiCompositionMode mode;

  @override
  ConsumerState<FiCompositionBlock> createState() => _FiCompositionBlockState();
}

class _FiCompositionBlockState extends ConsumerState<FiCompositionBlock> {
  List<FiCompositionSlice> _byPosition(Brightness brightness) {
    final sorted = [
      for (final p in widget.positions) (p, p.currentValue ?? p.invested),
    ]..sort((a, b) => b.$2.compareTo(a.$2));
    final total = sorted.fold<double>(0, (s, e) => s + e.$2);
    if (total <= 0) return [];

    final visiveis = sorted.length > _visiblePositions + 1
        ? sorted.take(_visiblePositions).toList()
        : sorted;
    final resto = sorted.skip(visiveis.length).toList();
    final valorResto = resto.fold<double>(0, (s, e) => s + e.$2);

    return [
      for (final (p, valor) in visiveis.where((e) => e.$2 > 0))
        FiCompositionSlice(
          label: fiIsFixedIncomePosition(p) ? (p.name ?? 'Aplicação de renda fixa') : p.ticker,
          value: valor,
          pct: valor / total * 100,
          color: categoryColor(p.categoryResolved, brightness),
        ),
      if (valorResto > 0)
        FiCompositionSlice(
          label: 'Outros ${resto.length} ativos',
          value: valorResto,
          pct: valorResto / total * 100,
          color: fiInk3Of(brightness),
        ),
    ];
  }

  List<FiCompositionSlice> _byCategory(Brightness brightness) {
    final sorted = [...widget.allocations]
      ..sort((a, b) => b.currentValue.compareTo(a.currentValue));
    return sorted
        .where((a) => a.currentPct > 0)
        .map(
          (a) => FiCompositionSlice(
            label: categoryLabel(a.category),
            value: a.currentValue,
            pct: a.currentPct,
            color: categoryColor(a.category, brightness),
            targetPct: a.targetPct,
          ),
        )
        .toList();
  }

  Map<String, double> _sectorTargets() {
    final metas = ref.watch(sectorGoalsProvider).valueOrNull ?? const <SectorGoal>[];
    return {
      for (final m in metas.where((m) => m.declared)) translateSector(m.sector): m.targetPct,
    };
  }

  List<FiCompositionSlice> _bySector(Brightness brightness) {
    final metas = _sectorTargets();
    final buckets = <String, double>{};
    var totalAcoes = 0.0;
    for (final p in widget.positions) {
      if (!fiStockCategories.contains(p.categoryResolved)) continue;
      final valor = p.currentValue ?? p.invested;
      final setor = translateSector(p.sector);
      buckets[setor] = (buckets[setor] ?? 0) + valor;
      totalAcoes += valor;
    }
    if (totalAcoes <= 0) return [];

    final entries = buckets.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return entries
        .map(
          (e) => FiCompositionSlice(
            label: e.key,
            value: e.value,
            pct: e.value / totalAcoes * 100,
            color: sectorColor(e.key, brightness),
            targetPct: metas[e.key],
          ),
        )
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final slices = switch (widget.mode) {
      FiCompositionMode.position => _byPosition(brightness),
      FiCompositionMode.category => _byCategory(brightness),
      FiCompositionMode.sector => _bySector(brightness),
    };

    if (slices.isEmpty) {
      return FiEmptyLine(switch (widget.mode) {
        FiCompositionMode.position => 'Nenhuma posição com valor na carteira ainda.',
        FiCompositionMode.category => 'Nenhuma classe com valor na carteira ainda.',
        FiCompositionMode.sector =>
          'Nenhuma ação ou BDR na carteira — o setor só se lê nelas.',
      });
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final slice in slices)
          FiAllocationGap(
            label: slice.label,
            currentPct: slice.pct,
            targetPct: slice.targetPct,
            barColor: slice.color,
            trailing: formatCurrency(slice.value),
          ),
      ],
    );
  }
}
