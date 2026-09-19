import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/models.dart';
import '../../../core/sector_translations.dart';
import '../../../core/theme.dart';
import '../../../core/providers.dart';
import '../../../core/widgets/data_row.dart';
import '../../../core/widgets/disclosure.dart';
import '../../../core/widgets/tag.dart';

enum FiAssetGroupMode {
  value('valor'),
  category('classe'),
  sector('setor');

  const FiAssetGroupMode(this.slug);

  final String slug;

  static FiAssetGroupMode fromSlug(String? slug) => values.firstWhere(
    (m) => m.slug == slug,
    orElse: () => FiAssetGroupMode.value,
  );
}

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

  Widget _objects(List<PortfolioPosition> items) {
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

  double _valueOf(List<PortfolioPosition> items) =>
      items.fold<double>(0, (s, p) => s + (p.currentValue ?? 0));

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (mode == FiAssetGroupMode.value) {
      return _objects(positions);
    }

    final totalValue = _valueOf(positions);

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
      ..sort((a, b) => _valueOf(b.value).compareTo(_valueOf(a.value)));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: entries.expand((e) {
        final atualPct = totalValue > 0 ? _valueOf(e.value) / totalValue * 100 : 0.0;
        final targetPct = porCategoria
            ? goals.where((g) => g.category == e.key).firstOrNull?.targetPct
            : sectorGoals.where((g) => g.sector == e.key).firstOrNull?.targetPct;

        return [
          FiGroupDisclosure(
            label: porCategoria
                ? categoryLabel(e.key)
                : translateSector(e.key == '—' ? null : e.key),
            count: e.value.length,
            trailing: targetPct != null
                ? '${formatPercent(atualPct)} de ${formatPercent(targetPct)}'
                : formatPercent(atualPct),
            initiallyOpen: entries.length <= 3,
            child: _objects(e.value),
          ),
        ];
      }).toList(),
    );
  }
}

class _SwipeBackground extends StatelessWidget {
  const _SwipeBackground({
    required this.label,
    required this.state,
    required this.alignment,
    required this.padding,
  });

  final String label;
  final FiState state;
  final Alignment alignment;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;

    return Container(
      decoration: BoxDecoration(
        color: fiStateSurface(state, brightness),
        borderRadius: BorderRadius.circular(FiRadius.md),
      ),
      alignment: alignment,
      padding: padding,
      child: Text(
        label,
        style: FiType.action.copyWith(color: fiStateColor(state, brightness)),
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

  @override
  Widget build(BuildContext context) {
    final p = position;
    final brightness = Theme.of(context).brightness;
    final positive = (p.pnl ?? 0) >= 0;
    final pnlColor = fiDirectionColor(positive ? 1 : -1, brightness);

    return Dismissible(
      key: ValueKey(p.ticker),
      confirmDismiss: (direcao) async {
        if (direcao == DismissDirection.startToEnd) {
          onSell();
          return false;
        }
        final confirmado = await showDialog<bool>(
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
        );
        return confirmado ?? false;
      },
      onDismissed: (_) => onDelete(),
      background: _SwipeBackground(
        label: 'Vender',
        state: FiState.attention,
        alignment: Alignment.centerLeft,
        padding: const EdgeInsets.only(left: FiSpace.s5),
      ),
      secondaryBackground: _SwipeBackground(
        label: 'Remover',
        state: FiState.adverse,
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: FiSpace.s5),
      ),
      child: FiObject(
        onTap: () => context.push('/ativo/${p.ticker}'),
        semanticsLabel:
            '${p.ticker}, ${p.label}. ${formatCurrency(p.currentValue)}, '
            '${formatPercent(p.pnlPct)}. Abrir a análise.',
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
                          FiTag.series(
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
          ],
        ),
      ),
    );
  }
}
