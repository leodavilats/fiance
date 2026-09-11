import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/models.dart';
import '../../../core/sector_translations.dart';
import '../../../core/theme.dart';
import '../../../core/providers.dart';
import '../../../core/widgets/button.dart';
import '../../../core/widgets/data_row.dart';
import '../../../core/widgets/tag.dart';

enum FiAssetGroupMode { value, category, sector }

final fiAssetGroupModeProvider = StateProvider.autoDispose<FiAssetGroupMode>(
  (ref) => FiAssetGroupMode.value,
);

class FiGroupedPositionsList extends ConsumerWidget {
  const FiGroupedPositionsList({
    super.key,
    required this.positions,
    required this.mode,
    required this.onDelete,
    required this.onSell,
  });

  final List<PortfolioPosition> positions;
  final FiAssetGroupMode mode;
  final void Function(String ticker) onDelete;
  final void Function(PortfolioPosition position) onSell;

  List<PortfolioPosition> _sortedByValue(List<PortfolioPosition> items) {
    final sorted = [...items];
    sorted.sort(
      (a, b) => (b.currentValue ?? 0).compareTo(a.currentValue ?? 0),
    );
    return sorted;
  }

  Widget _objetos(List<PortfolioPosition> items) {
    return Column(
      children: _sortedByValue(items)
          .map(
            (p) => Padding(
              padding: const EdgeInsets.only(bottom: FiSpace.s2),
              child: _FiAssetObject(
                position: p,
                onDelete: () => onDelete(p.ticker),
                onSell: () => onSell(p),
              ),
            ),
          )
          .toList(),
    );
  }

  double _valorDe(List<PortfolioPosition> items) =>
      items.fold<double>(0, (s, p) => s + (p.currentValue ?? 0));

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (mode == FiAssetGroupMode.value) {
      return _objetos(positions);
    }

    final totalValue = _valorDe(positions);

    final porCategoria = mode == FiAssetGroupMode.category;
    final goals = porCategoria
        ? (ref.watch(goalsProvider).valueOrNull ?? const <Goal>[])
        : const <Goal>[];
    final sectorGoals = porCategoria
        ? const <SectorGoal>[]
        : (ref.watch(sectorGoalsProvider).valueOrNull ?? const <SectorGoal>[]);

    final groups = <String, List<PortfolioPosition>>{};
    for (final p in positions) {
      final chave = porCategoria ? p.categoryResolved : (p.sector ?? '—');
      groups.putIfAbsent(chave, () => []).add(p);
    }

    final entries = groups.entries.toList()
      ..sort((a, b) => _valorDe(b.value).compareTo(_valorDe(a.value)));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: entries.expand((e) {
        final atualPct = totalValue > 0 ? _valorDe(e.value) / totalValue * 100 : 0.0;
        final metaPct = porCategoria
            ? goals.where((g) => g.category == e.key).firstOrNull?.targetPct
            : sectorGoals.where((g) => g.sector == e.key).firstOrNull?.targetPct;

        return [
          _FiGroupHeader(
            label: porCategoria
                ? categoryLabel(e.key)
                : translateSector(e.key == '—' ? null : e.key),
            atualPct: atualPct,
            metaPct: metaPct,
          ),
          _objetos(e.value),
          const SizedBox(height: FiSpace.s5),
        ];
      }).toList(),
    );
  }
}

class _FiGroupHeader extends StatelessWidget {
  const _FiGroupHeader({
    required this.label,
    required this.atualPct,
    this.metaPct,
  });

  final String label;
  final double atualPct;
  final double? metaPct;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
          const SizedBox(height: FiSpace.s3),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Expanded(
                child: Text(
                  label.toUpperCase(),
                  style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                ),
              ),
              Text(
                metaPct != null
                    ? '${formatPercent(atualPct)} de ${formatPercent(metaPct)}'
                    : formatPercent(atualPct),
                style: FiType.caption.copyWith(color: fiInk2(context)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _FiAssetObject extends StatelessWidget {
  const _FiAssetObject({
    required this.position,
    required this.onDelete,
    required this.onSell,
  });

  final PortfolioPosition position;
  final VoidCallback onDelete;
  final VoidCallback onSell;

  void _showReasons(BuildContext context, PortfolioPosition p) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(FiSpace.s5, 0, FiSpace.s5, FiSpace.s6),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${p.ticker} — ${p.label}', style: FiType.title),
              const SizedBox(height: FiSpace.s4),
              ...p.reasons.map(
                (r) => Padding(
                  padding: const EdgeInsets.only(bottom: FiSpace.s3),
                  child: Text(
                    r,
                    style: FiType.body.copyWith(color: fiInk2(context)),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final p = position;
    final brightness = Theme.of(context).brightness;
    final positive = (p.pnl ?? 0) >= 0;
    final pnlColor = fiDirectionColor(positive ? 1 : -1, brightness);

    return Dismissible(
      key: ValueKey(p.ticker),
      direction: DismissDirection.endToStart,
      confirmDismiss: (_) => showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Remover ativo'),
          content: Text(
            'Remover ${p.ticker} da carteira? A posição sai do patrimônio e das análises.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Remover'),
            ),
          ],
        ),
      ).then((v) => v ?? false),
      onDismissed: (_) => onDelete(),
      background: Container(
        decoration: BoxDecoration(
          color: fiStateSurface(FiState.adverse, brightness),
          borderRadius: BorderRadius.circular(FiRadius.md),
        ),
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: FiSpace.s5),
        child: Text(
          'Remover',
          style: FiType.action.copyWith(
            color: fiStateColor(FiState.adverse, brightness),
          ),
        ),
      ),
      child: FiObject(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              p.ticker,
                              style: FiType.title.copyWith(color: fiInk1(context)),
                            ),
                          ),
                          const SizedBox(width: FiSpace.s2),
                          FiTag.serie(
                            label: categoryLabel(p.categoryResolved),
                            color: categoryColor(p.categoryResolved, brightness),
                          ),
                        ],
                      ),
                      if (p.name != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: Text(
                            p.name!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: FiType.caption.copyWith(color: fiInk2(context)),
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(width: FiSpace.s3),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      formatCurrency(p.currentValue),
                      style: FiType.metricSm.copyWith(color: fiInk1(context)),
                    ),
                    Text(
                      '${positive ? '+' : ''}${formatPercent(p.pnlPct)}',
                      style: FiType.caption.copyWith(color: pnlColor),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: FiSpace.s3),
            Text(
              '${p.quantity} un. · PM ${formatCurrency(p.avgPrice)} · '
              'hoje ${formatCurrency(p.currentPrice)} · DY ${formatPercent(p.dividendYield)}',
              style: FiType.caption.copyWith(color: fiInk2(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
            Row(
              children: [
                if (p.reasons.isNotEmpty) ...[
                  Flexible(
                    child: FiButton.quiet(
                      label: 'Por que ${p.label}?',
                      onPressed: () => _showReasons(context, p),
                    ),
                  ),
                  const SizedBox(width: FiSpace.s5),
                ],
                Flexible(
                  child: FiButton.quiet(label: 'Vender', onPressed: onSell),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
