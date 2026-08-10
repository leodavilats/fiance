import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Dashboard')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(dashboardProvider),
        child: dashboard.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => _ErrorView(message: '$err'),
          data: (data) => ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _SummaryCard(summary: data.summary),
              const SizedBox(height: 16),
              if (data.allocations.isNotEmpty) ...[
                const _SectionTitle('Alocação por categoria'),
                ...data.allocations.map((a) => _AllocationRow(allocation: a)),
                const SizedBox(height: 16),
              ],
              if (data.alerts.isNotEmpty) ...[
                const _SectionTitle('Alertas'),
                ...data.alerts.map((a) => _AlertTile(alert: a)),
                const SizedBox(height: 16),
              ],
              if (data.positions.isNotEmpty) ...[
                const _SectionTitle('Carteira'),
                ...data.positions.map((p) => _PositionRow(position: p)),
                const SizedBox(height: 16),
              ],
              if (data.topBuys.isNotEmpty) ...[
                const _SectionTitle('Oportunidades em destaque'),
                ...data.topBuys.map((o) => _OpportunityTile(opportunity: o)),
              ],
              if (data.topSells.isNotEmpty) ...[
                const SizedBox(height: 16),
                const _SectionTitle('Atenção (sinal de venda)'),
                ...data.topSells.map((p) => _PositionRow(position: p)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _AlertTile extends StatelessWidget {
  const _AlertTile({required this.alert});

  final PortfolioAlert alert;

  Color _color() {
    switch (alert.severity) {
      case 'critical':
      case 'high':
        return Colors.red.shade700;
      case 'warning':
      case 'medium':
        return Colors.orange.shade700;
      default:
        return Colors.blueGrey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ListTile(
        leading: Icon(Icons.info_outline, color: _color()),
        title: Text(
          alert.title,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(alert.detail),
      ),
    );
  }
}

class _PositionRow extends StatelessWidget {
  const _PositionRow({required this.position});

  final PortfolioPosition position;

  @override
  Widget build(BuildContext context) {
    final positive = (position.pnl ?? 0) >= 0;
    final color = positive ? Colors.green.shade700 : Colors.red.shade700;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ListTile(
        title: Text(
          position.ticker,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(
          '${position.quantity} un. · PM ${formatCurrency(position.avgPrice)}',
        ),
        trailing: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(formatCurrency(position.currentValue)),
            Text(
              formatPercent(position.pnlPct),
              style: TextStyle(color: color, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final positive = summary.totalPnl >= 0;
    final pnlColor = positive ? Colors.green.shade700 : Colors.red.shade700;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              formatCurrency(summary.totalCurrent),
              style: Theme.of(
                context,
              ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            Text(
              '${summary.positionsCount} posições · caixa ${formatCurrency(summary.cashAvailable)}',
              style: TextStyle(color: Colors.grey.shade600),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(
                  positive ? Icons.arrow_upward : Icons.arrow_downward,
                  color: pnlColor,
                  size: 18,
                ),
                const SizedBox(width: 4),
                Text(
                  '${formatCurrency(summary.totalPnl)} (${formatPercent(summary.totalPnlPct)})',
                  style: TextStyle(
                    color: pnlColor,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _MiniStat(
                  label: 'Investido',
                  value: formatCurrency(summary.totalInvested),
                ),
                _MiniStat(
                  label: 'Dividendos/mês',
                  value: formatCurrency(summary.monthlyDividendsEstimate),
                ),
              ],
            ),
            if (summary.passiveIncomeGoal != null) ...[
              const SizedBox(height: 16),
              Text(
                'Meta de renda passiva: ${formatCurrency(summary.passiveIncomeGoal)}/mês',
              ),
              const SizedBox(height: 4),
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

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
        ),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
      ],
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, top: 8),
      child: Text(
        title,
        style: Theme.of(
          context,
        ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
      ),
    );
  }
}

class _AllocationRow extends StatelessWidget {
  const _AllocationRow({required this.allocation});

  final CategoryAllocation allocation;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(allocation.category),
              Text(
                '${formatCurrency(allocation.currentValue)} · ${formatPercent(allocation.currentPct)}',
              ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (allocation.currentPct / 100).clamp(0, 1),
              minHeight: 6,
            ),
          ),
        ],
      ),
    );
  }
}

class _OpportunityTile extends StatelessWidget {
  const _OpportunityTile({required this.opportunity});

  final Opportunity opportunity;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ListTile(
        title: Text(
          opportunity.ticker,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(opportunity.name ?? ''),
        trailing: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(formatCurrency(opportunity.price)),
            Text(
              'DY ${formatPercent(opportunity.dividendYield)}',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text('Erro ao carregar: $message', textAlign: TextAlign.center),
      ),
    );
  }
}
