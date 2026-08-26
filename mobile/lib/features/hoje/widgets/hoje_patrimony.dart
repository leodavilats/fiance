import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/theme.dart';


class FiPatrimonyBlock extends StatelessWidget {
  const FiPatrimonyBlock({super.key, required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final positive = summary.totalPnl >= 0;
    final brightness = Theme.of(context).brightness;
    final pnlColor = fiDirectionColor(positive ? 1 : -1, brightness);
    final scheme = Theme.of(context).colorScheme;
    final mutedColor = brightness == Brightness.dark
        ? AppColors.darkMuted
        : AppColors.lightMuted;

    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Patrimônio total',
              style: TextStyle(color: mutedColor, fontSize: 13),
            ),
            const SizedBox(height: 4),
            Text(
              formatCurrency(summary.totalCurrent),
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: scheme.onSurface,
              ),
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Icon(
                  positive ? Icons.arrow_upward : Icons.arrow_downward,
                  color: pnlColor,
                  size: 16,
                ),
                const SizedBox(width: 4),
                Text(
                  '${formatCurrency(summary.totalPnl)} (${formatPercent(summary.totalPnlPct)})',
                  style: TextStyle(
                    color: pnlColor,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '· ${summary.positionsCount} posições',
                  style: TextStyle(color: mutedColor, fontSize: 13),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: FiMiniStat(
                    icon: Icons.savings_outlined,
                    label: 'Investido',
                    value: formatCurrency(summary.totalInvested),
                  ),
                ),
                Expanded(
                  child: FiMiniStat(
                    icon: Icons.payments_outlined,
                    label: 'Div./mês',
                    value: formatCurrency(summary.monthlyDividendsEstimate),
                  ),
                ),
              ],
            ),
            if (summary.passiveIncomeGoal != null) ...[
              const SizedBox(height: 18),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Meta de renda passiva',
                    style: TextStyle(color: fiInk2(context), fontSize: 12),
                  ),
                  Text(
                    '${formatCurrency(summary.passiveIncomeGoal)}/mês',
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: (summary.passiveIncomeProgress ?? 0).clamp(0, 1),
                  minHeight: 6,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class FiMiniStat extends StatelessWidget {
  const FiMiniStat({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 14, color: fiInk2(context)),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(color: fiInk2(context), fontSize: 11),
            ),
          ],
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
      ],
    );
  }
}

String fiCompactCurrency(double value) {
  final abs = value.abs();
  if (abs >= 1000000) return 'R\$ ${(value / 1000000).toStringAsFixed(1)}M';
  if (abs >= 1000) return 'R\$ ${(value / 1000).toStringAsFixed(0)}k';
  return formatCurrency(value);
}

class FiFreshnessLine extends StatelessWidget {
  const FiFreshnessLine({super.key, required this.freshness});

  final DataFreshness freshness;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = freshness.marketDataStale
        ? fiStateColor(FiState.attention, theme.brightness)
        : theme.textTheme.bodySmall?.color;

    return Row(
      children: [
        Icon(
          freshness.marketDataStale
              ? Icons.schedule_outlined
              : Icons.check_circle_outline,
          size: 14,
          color: color,
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            '${freshness.label} - ${freshness.ratesLabel}',
            style: theme.textTheme.bodySmall?.copyWith(color: color),
          ),
        ),
      ],
    );
  }
}
