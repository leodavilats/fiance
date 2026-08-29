import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/models.dart';
import '../../../core/sector_translations.dart';
import '../../../core/theme.dart';
import '../../../core/providers.dart';

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

  Widget _cardsFor(
    BuildContext context,
    WidgetRef ref,
    List<PortfolioPosition> items,
  ) {
    return Column(
      children: _sortedByValue(items)
          .map(
            (p) => _FiAssetCard(
              position: p,
              onDelete: () => onDelete(p.ticker),
              onSell: () => onSell(p),
            ),
          )
          .toList(),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (mode == FiAssetGroupMode.value) {
      return _cardsFor(context, ref, positions);
    }

    final totalValue = positions.fold<double>(
      0,
      (sum, p) => sum + (p.currentValue ?? 0),
    );

    if (mode == FiAssetGroupMode.category) {
      final goals = ref.watch(goalsProvider).valueOrNull ?? [];
      final groups = <String, List<PortfolioPosition>>{};
      for (final p in positions) {
        groups.putIfAbsent(p.categoryResolved, () => []).add(p);
      }
      final entries = groups.entries.toList()
        ..sort(
          (a, b) => b.value
              .fold<double>(0, (s, p) => s + (p.currentValue ?? 0))
              .compareTo(
                a.value.fold<double>(0, (s, p) => s + (p.currentValue ?? 0)),
              ),
        );

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: entries.expand((e) {
          final groupValue = e.value.fold<double>(
            0,
            (s, p) => s + (p.currentValue ?? 0),
          );
          final atualPct = totalValue > 0 ? groupValue / totalValue * 100 : 0.0;
          final goal = goals.where((g) => g.category == e.key).firstOrNull;
          return [
            _FiGroupHeader(
              label: categoryLabel(e.key),
              atualPct: atualPct,
              metaPct: goal?.targetPct,
            ),
            _cardsFor(context, ref, e.value),
            const SizedBox(height: 12),
          ];
        }).toList(),
      );
    }

    final sectorGoals = ref.watch(sectorGoalsProvider).valueOrNull ?? [];
    final groups = <String, List<PortfolioPosition>>{};
    for (final p in positions) {
      final sector = p.sector ?? '—';
      groups.putIfAbsent(sector, () => []).add(p);
    }
    final entries = groups.entries.toList()
      ..sort(
        (a, b) => b.value
            .fold<double>(0, (s, p) => s + (p.currentValue ?? 0))
            .compareTo(
              a.value.fold<double>(0, (s, p) => s + (p.currentValue ?? 0)),
            ),
      );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: entries.expand((e) {
        final groupValue = e.value.fold<double>(
          0,
          (s, p) => s + (p.currentValue ?? 0),
        );
        final atualPct = totalValue > 0 ? groupValue / totalValue * 100 : 0.0;
        final goal = sectorGoals
            .where((g) => g.sector == e.key)
            .firstOrNull;
        return [
          _FiGroupHeader(
            label: translateSector(e.key == '—' ? null : e.key),
            atualPct: atualPct,
            metaPct: goal?.targetPct,
          ),
          _cardsFor(context, ref, e.value),
          const SizedBox(height: 12),
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
      padding: const EdgeInsets.only(bottom: 8, top: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
          Text(
            metaPct != null
                ? 'atual ${formatPercent(atualPct)} · meta ${formatPercent(metaPct)}'
                : 'atual ${formatPercent(atualPct)}',
            style: TextStyle(color: fiInk2(context), fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _FiAssetCard extends StatelessWidget {
  const _FiAssetCard({
    required this.position,
    required this.onDelete,
    required this.onSell,
  });

  final PortfolioPosition position;
  final VoidCallback onDelete;
  final VoidCallback onSell;

  void _showReasons(BuildContext context, PortfolioPosition p) {
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${p.ticker} — ${p.label}',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 12),
            ...p.reasons.map(
              (r) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text('•  $r', style: const TextStyle(height: 1.4)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final p = position;
    final positive = (p.pnl ?? 0) >= 0;
    final brightness = Theme.of(context).brightness;
    final pnlColor = fiDirectionColor(positive ? 1 : -1, brightness);

    return Dismissible(
      key: ValueKey(p.ticker),
      direction: DismissDirection.endToStart,
      confirmDismiss: (_) => showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Remover ativo'),
          content: Text('Remover ${p.ticker} da carteira?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar'),
            ),
            FilledButton.tonal(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Remover'),
            ),
          ],
        ),
      ).then((v) => v ?? false),
      onDismissed: (_) => onDelete(),
      background: Container(
        margin: const EdgeInsets.only(bottom: 10),
        decoration: BoxDecoration(
          color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
          borderRadius: BorderRadius.circular(12),
        ),
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        child: Icon(Icons.delete, color: Theme.of(context).colorScheme.onError),
      ),
      child: Card(
        margin: const EdgeInsets.only(bottom: 10),
        child: Padding(
          padding: const EdgeInsets.all(14),
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
                            Text(
                              p.ticker,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 6,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: categoryColor(
                                  p.categoryResolved,
                                  brightness,
                                ).withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(5),
                              ),
                              child: Text(
                                categoryLabel(p.categoryResolved),
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                  color: categoryColor(p.categoryResolved, brightness),
                                ),
                              ),
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
                              style: TextStyle(
                                color: fiInk2(context),
                                fontSize: 12,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        formatCurrency(p.currentValue),
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      Text(
                        '${positive ? '+' : ''}${formatPercent(p.pnlPct)}',
                        style: TextStyle(
                          color: pnlColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const Divider(height: 18),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _FiMiniInfo(label: 'Qtd.', value: '${p.quantity}'),
                  _FiMiniInfo(label: 'PM', value: formatCurrency(p.avgPrice)),
                  _FiMiniInfo(
                    label: 'Atual',
                    value: formatCurrency(p.currentPrice),
                  ),
                  _FiMiniInfo(label: 'DY', value: formatPercent(p.dividendYield)),
                ],
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (p.reasons.isNotEmpty)
                    TextButton.icon(
                      onPressed: () => _showReasons(context, p),
                      icon: const Icon(Icons.info_outline, size: 16),
                      label: const Text('Por quê?'),
                      style: TextButton.styleFrom(
                        padding: EdgeInsets.zero,
                        minimumSize: const Size(0, 32),
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ),
                  const SizedBox(width: 12),
                  TextButton.icon(
                    onPressed: onSell,
                    icon: const Icon(Icons.sell_outlined, size: 16),
                    label: const Text('Vender'),
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(0, 32),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FiMiniInfo extends StatelessWidget {
  const _FiMiniInfo({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(color: fiInk3(context), fontSize: 10),
        ),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 12),
        ),
      ],
    );
  }
}
