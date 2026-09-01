import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/theme.dart';
import '../hoje_actions.dart';
import '../../../core/score_ruler.dart';

/// Uma linha do feed de "O que mudou": o que aconteceu, por que importa, o que
/// fazer — na ordem do padrão Insight, que é o mesmo do web.
///
/// A ação fica **abaixo** do texto, e não em `ListTile.trailing`. No trailing a
/// largura vinha do rótulo: "Ver sugestões de ajuste" tomava metade da linha,
/// quebrava em três e sobrava uma coluna estreita para o título — de modo que
/// cada tile do feed ganhava uma largura de texto diferente, conforme o botão
/// que tivesse. Abaixo, o alinhamento é o mesmo em todas as linhas e o rótulo
/// pode ter o tamanho que precisar.
class FiInsightTile extends StatelessWidget {
  const FiInsightTile({
    super.key,
    required this.icon,
    required this.color,
    required this.title,
    required this.detail,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final Color color;
  final String title;
  final String detail;
  final String? actionLabel;
  final VoidCallback? onAction;

  /// Diâmetro do avatar mais o vão — o que alinha a ação à coluna de texto.
  static const double _textColumnInset = 44;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 16,
                  backgroundColor: color.withValues(alpha: 0.12),
                  child: Icon(icon, color: color, size: 18),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 2),
                      Text(detail, style: TextStyle(color: fiInk2(context))),
                    ],
                  ),
                ),
              ],
            ),
            if (actionLabel != null) ...[
              const SizedBox(height: 12),
              Padding(
                padding: const EdgeInsets.only(left: _textColumnInset),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton(
                    onPressed: onAction,
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(0, 32),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: Text('$actionLabel →'),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class FiAlertTile extends StatelessWidget {
  const FiAlertTile({super.key, required this.alert});

  final PortfolioAlert alert;

  Color _color(Brightness brightness) {
    switch (alert.severity) {
      case 'critical':
      case 'high':
        return fiStateColor(FiState.adverse, brightness);
      case 'warning':
      case 'medium':
        return fiStateColor(FiState.attention, brightness);
      default:
        return fiStateColor(FiState.indeterminate, brightness);
    }
  }

  IconData _icon() {
    switch (alert.kind) {
      case 'sell_target':
        return Icons.trending_down;
      case 'opportunity':
        return Icons.trending_up;
      case 'concentration':
        return Icons.donut_small_outlined;
      case 'rebalance':
        return Icons.balance_outlined;
      default:
        return Icons.info_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return FiInsightTile(
      icon: _icon(),
      color: _color(Theme.of(context).brightness),
      title: alert.count > 1 ? '${alert.title} (${alert.count})' : alert.title,
      detail: alert.detail,
      actionLabel: alert.actionLabel,
      onAction: () => runHojeAction(context, alert.action, alert.ticker),
    );
  }
}

class FiWhatsNewTile extends StatelessWidget {
  const FiWhatsNewTile({super.key, required this.item});

  final WhatsNewItem item;

  IconData _icon() {
    switch (item.kind) {
      case 'patrimony':
        return Icons.show_chart;
      case 'verdict_change':
        return Icons.trending_down;
      case 'allocation':
        return Icons.balance_outlined;
      case 'maturity':
        return Icons.event_available_outlined;
      case 'new_opportunity':
        return Icons.auto_awesome_outlined;
      case 'tax':
        return Icons.receipt_long_outlined;
      default:
        return Icons.check_circle_outline;
    }
  }

  Color _color(Brightness brightness) {
    switch (item.severity) {
      case 'critical':
        return fiStateColor(FiState.adverse, brightness);
      case 'warning':
        return fiStateColor(FiState.attention, brightness);
      case 'positive':
        return fiStateColor(FiState.favorable, brightness);
      default:
        return fiStateColor(FiState.indeterminate, brightness);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FiInsightTile(
      icon: _icon(),
      color: _color(Theme.of(context).brightness),
      title: item.title,
      detail: item.detail,
      actionLabel: item.actionLabel,
      onAction: () => runHojeAction(context, item.action, item.ticker),
    );
  }
}

class FiVerdictChip extends StatelessWidget {
  const FiVerdictChip({super.key, required this.verdict, required this.label});

  final String verdict;
  final String label;

  Color _color(Brightness brightness) {
    if (verdict.contains('BUY')) return fiStateColor(FiState.favorable, brightness);
    if (verdict.contains('SELL')) return fiStateColor(FiState.adverse, brightness);
    return fiStateColor(FiState.indeterminate, brightness);
  }

  @override
  Widget build(BuildContext context) {
    final c = _color(Theme.of(context).brightness);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: c.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(color: c, fontWeight: FontWeight.w600, fontSize: 11),
      ),
    );
  }
}

class FiPositionRow extends StatelessWidget {
  const FiPositionRow({super.key, required this.position});

  final PortfolioPosition position;

  @override
  Widget build(BuildContext context) {
    final positive = (position.pnl ?? 0) >= 0;
    final brightness = Theme.of(context).brightness;
    final color = fiDirectionColor(positive ? 1 : -1, brightness);
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        position.ticker,
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(width: 6),
                      FiVerdictChip(
                        verdict: position.verdict,
                        label: position.label,
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${position.quantity} un. · PM ${formatCurrency(position.avgPrice)}',
                    style: FiType.caption.copyWith(color: fiInk2(context)),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  formatCurrency(position.currentValue),
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                Text(
                  formatPercent(position.pnlPct),
                  style: TextStyle(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class FiOpportunityTile extends StatelessWidget {
  const FiOpportunityTile({super.key, required this.opportunity});

  final Opportunity opportunity;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(
          opportunity.ticker,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(opportunity.name ?? ''),
            Text(
              '${dataYearsLabel(opportunity.dataYears)} · '
              '${consensusLabel(opportunity.consensusMethods)}',
              style: TextStyle(color: fiInk2(context), fontSize: 11),
            ),
          ],
        ),
        trailing: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(formatCurrency(opportunity.price)),
            Text(
              'DY ${formatPercent(opportunity.dividendYield)}',
              style: FiType.caption.copyWith(color: fiInk2(context)),
            ),
            Builder(
              builder: (context) {
                final band = scoreBandFor(
                  opportunity.score,
                  opportunity.dataCompleteness,
                  Theme.of(context).brightness,
                );
                return Text(
                  band.text,
                  style: TextStyle(color: band.color, fontSize: 11),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class FiSectionTitle extends StatelessWidget {
  const FiSectionTitle({super.key, required this.icon, required this.title});

  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10, left: 4),
      child: Row(
        children: [
          Icon(icon, size: 18, color: fiInk2(context)),
          const SizedBox(width: 6),
          Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
