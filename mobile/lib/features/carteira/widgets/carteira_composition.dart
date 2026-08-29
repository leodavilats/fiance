import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/models.dart';
import '../../../core/sector_translations.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/allocation_gap.dart';

enum FiCompositionMode { asset, sector }

const fiStockCategories = {'acoes_br', 'bdrs'};

class FiCompositionSlice {
  const FiCompositionSlice({
    required this.label,
    required this.value,
    required this.pct,
    required this.color,
    required this.icon,
    this.targetPct,
  });

  final String label;
  final double value;
  final double pct;
  final Color color;
  final IconData? icon;

  /// Meta declarada pelo usuário, quando existe. Sem ela a fatia não é julgada.
  final double? targetPct;
}

class FiCompositionBlock extends StatefulWidget {
  const FiCompositionBlock({super.key, required this.allocations, required this.positions});

  final List<CategoryAllocation> allocations;
  final List<PortfolioPosition> positions;

  @override
  State<FiCompositionBlock> createState() => _FiCompositionBlockState();
}

class _FiCompositionBlockState extends State<FiCompositionBlock> {
  FiCompositionMode _mode = FiCompositionMode.asset;

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
            icon: categoryIcon(a.category),
            targetPct: a.targetPct,
          ),
        )
        .toList();
  }

  List<FiCompositionSlice> _bySector(Brightness brightness) {
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
            icon: null,
          ),
        )
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final slices = _mode == FiCompositionMode.asset
        ? _byAsset(brightness)
        : _bySector(brightness);

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            SegmentedButton<FiCompositionMode>(
              segments: const [
                ButtonSegment(
                  value: FiCompositionMode.asset,
                  label: Text('Por ativo'),
                ),
                ButtonSegment(
                  value: FiCompositionMode.sector,
                  label: Text('Por setor (ações)'),
                ),
              ],
              selected: {_mode},
              onSelectionChanged: (s) => setState(() => _mode = s.first),
            ),
            const SizedBox(height: 16),
            if (slices.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Text(
                  'Nenhuma ação ou BDR avaliada ainda.',
                  style: TextStyle(color: fiInk2(context)),
                ),
              )
            else ...[
              for (var i = 0; i < slices.length; i++) ...[
                if (i > 0) const Divider(height: 1),
                FiAllocationGap(
                  label: slices[i].label,
                  currentPct: slices[i].pct,
                  targetPct: slices[i].targetPct,
                  barColor: slices[i].color,
                  trailing: formatCurrency(slices[i].value),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}
