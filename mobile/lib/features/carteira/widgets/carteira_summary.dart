import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/theme.dart';
import 'package:go_router/go_router.dart';

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

class FiCarteiraSummary extends StatelessWidget {
  const FiCarteiraSummary({super.key, required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final positive = summary.totalPnl >= 0;
    final brightness = Theme.of(context).brightness;
    final pnlColor = fiDirectionColor(positive ? 1 : -1, brightness);

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Resumo geral',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: _FiStatBlock(
                    label: 'Investido',
                    value: formatCurrency(summary.totalInvested),
                  ),
                ),
                Expanded(
                  child: _FiStatBlock(
                    label: 'Valor atual',
                    value: formatCurrency(summary.totalCurrent),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: _FiStatBlock(
                    label: 'Rendimento',
                    value:
                        '${positive ? '+' : ''}${formatCurrency(summary.totalPnl)}',
                    valueColor: pnlColor,
                    caption: formatPercent(summary.totalPnlPct),
                  ),
                ),
                Expanded(
                  child: _FiStatBlock(
                    label: 'Ativos',
                    value: '${summary.positionsCount}',
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

class _FiStatBlock extends StatelessWidget {
  const _FiStatBlock({
    required this.label,
    required this.value,
    this.valueColor,
    this.caption,
  });

  final String label;
  final String value;
  final Color? valueColor;
  final String? caption;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            color: fiInk2(context),
            fontSize: 11,
            letterSpacing: 0.2,
          ),
        ),
        const SizedBox(height: 2),
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            Text(
              value,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
                color: valueColor,
              ),
            ),
            if (caption != null) ...[
              const SizedBox(width: 6),
              Text(caption!, style: TextStyle(color: valueColor, fontSize: 12)),
            ],
          ],
        ),
      ],
    );
  }
}

class FiFixedIncomeSummary extends StatelessWidget {
  const FiFixedIncomeSummary({super.key, required this.data});

  final FixedIncomeList data;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final vencendo = data.visiveis.where((i) => i.vencimentoProximo).length;

    return Card(
      child: InkWell(
        onTap: () => context.go('/assets/renda-fixa'),
        borderRadius: BorderRadius.circular(appRadius),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.account_balance_outlined, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Renda fixa (${data.visiveis.length})',
                      style: theme.textTheme.titleMedium,
                    ),
                  ),
                  const Icon(Icons.chevron_right),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '${formatCurrency(data.totalAtual)} hoje · rendimento de '
                '${formatCurrency(data.totalRendimento)} '
                '(${data.rendimentoPct.toStringAsFixed(2)}%)',
              ),
              if (vencendo > 0)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    '$vencendo ${vencendo == 1 ? 'aplicação vence' : 'aplicações vencem'} '
                    'nos próximos 30 dias',
                    style: theme.textTheme.bodySmall,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
