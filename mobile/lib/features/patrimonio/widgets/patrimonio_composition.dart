import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/models.dart';
import '../../../core/providers.dart';
import '../../../core/sector_translations.dart';
import '../../../core/widgets/allocation_gap.dart';
import '../../../core/widgets/empty_state.dart';

enum FiCompositionMode { asset, sector }

const fiStockCategories = {'acoes_br', 'bdrs'};

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
    this.mode = FiCompositionMode.asset,
  });

  final List<CategoryAllocation> allocations;
  final List<PortfolioPosition> positions;
  final FiCompositionMode mode;

  @override
  ConsumerState<FiCompositionBlock> createState() => _FiCompositionBlockState();
}

class _FiCompositionBlockState extends ConsumerState<FiCompositionBlock> {
  List<FiCompositionSlice> _byAsset(Brightness brightness) {
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

  /// As metas por setor, so quando sao da pessoa.
  ///
  /// `GET /sector-goals` devolve o padrao do produto quando nada foi declarado, e desenhar 20%
  /// como alvo de quem nunca declarou nada seria inventar objetivo alheio. O `declared` da
  /// resposta e o que separa os dois casos.
  Map<String, double> _metasPorSetor() {
    final metas = ref.watch(sectorGoalsProvider).valueOrNull ?? const <SectorGoal>[];
    return {
      for (final m in metas.where((m) => m.declared)) translateSector(m.sector): m.targetPct,
    };
  }

  List<FiCompositionSlice> _bySector(Brightness brightness) {
    final metas = _metasPorSetor();
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
    final slices = widget.mode == FiCompositionMode.asset
        ? _byAsset(brightness)
        : _bySector(brightness);

    if (slices.isEmpty) {
      return const FiEmptyLine('Nenhuma ação ou BDR avaliada ainda.');
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
