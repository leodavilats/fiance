import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';

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
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              _SummaryCard(summary: data.summary),
              if (data.allocations.isNotEmpty) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.pie_chart_outline,
                  title: 'Alocação por categoria',
                ),
                _CardGroup(
                  children: data.allocations
                      .map((a) => _AllocationRow(allocation: a))
                      .toList(),
                ),
              ],
              if (data.alerts.isNotEmpty) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.notifications_none,
                  title: 'Alertas',
                ),
                ...data.alerts.map((a) => _AlertTile(alert: a)),
              ],
              if (data.positions.isNotEmpty) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.account_balance_wallet_outlined,
                  title: 'Carteira',
                ),
                ...data.positions.map((p) => _PositionRow(position: p)),
              ],
              if (data.topBuys.isNotEmpty) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.trending_up,
                  title: 'Oportunidades em destaque',
                ),
                ...data.topBuys.map((o) => _OpportunityTile(opportunity: o)),
              ],
              if (data.topSells.isNotEmpty) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.trending_down,
                  title: 'Atenção (sinal de venda)',
                ),
                ...data.topSells.map((p) => _PositionRow(position: p)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Agrupa linhas relacionadas dentro de um único Card, com divisores finos
/// entre elas — evita a repetição visual de "card dentro de card".
class _CardGroup extends StatelessWidget {
  const _CardGroup({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Column(
          children: [
            for (var i = 0; i < children.length; i++) ...[
              if (i > 0) const Divider(height: 1),
              children[i],
            ],
          ],
        ),
      ),
    );
  }
}

class _AlertTile extends StatelessWidget {
  const _AlertTile({required this.alert});

  final PortfolioAlert alert;

  Color _color(Brightness brightness) {
    switch (alert.severity) {
      case 'critical':
      case 'high':
        return lossColor(brightness);
      case 'warning':
      case 'medium':
        return warnColor(brightness);
      default:
        return Colors.blueGrey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _color(Theme.of(context).brightness);
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha: 0.12),
          child: Icon(Icons.info_outline, color: color, size: 20),
        ),
        title: Text(
          alert.title,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(alert.detail),
      ),
    );
  }
}

class _VerdictChip extends StatelessWidget {
  const _VerdictChip({required this.verdict, required this.label});

  final String verdict;
  final String label;

  Color _color(Brightness brightness) {
    if (verdict.contains('BUY')) return gainColor(brightness);
    if (verdict.contains('SELL')) return lossColor(brightness);
    return Colors.blueGrey;
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

class _PositionRow extends StatelessWidget {
  const _PositionRow({required this.position});

  final PortfolioPosition position;

  @override
  Widget build(BuildContext context) {
    final positive = (position.pnl ?? 0) >= 0;
    final brightness = Theme.of(context).brightness;
    final color = positive ? gainColor(brightness) : lossColor(brightness);
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
                      _VerdictChip(
                        verdict: position.verdict,
                        label: position.label,
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${position.quantity} un. · PM ${formatCurrency(position.avgPrice)}',
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
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

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final positive = summary.totalPnl >= 0;
    final brightness = Theme.of(context).brightness;
    final pnlColor = positive ? gainColor(brightness) : lossColor(brightness);
    final scheme = Theme.of(context).colorScheme;

    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              scheme.primaryContainer.withValues(alpha: 0.5),
              scheme.surface,
            ],
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Patrimônio total',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
            ),
            const SizedBox(height: 4),
            Text(
              formatCurrency(summary.totalCurrent),
              style: Theme.of(
                context,
              ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
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
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: _MiniStat(
                    icon: Icons.savings_outlined,
                    label: 'Investido',
                    value: formatCurrency(summary.totalInvested),
                  ),
                ),
                Expanded(
                  child: _MiniStat(
                    icon: Icons.account_balance_wallet_outlined,
                    label: 'Caixa',
                    value: formatCurrency(summary.cashAvailable),
                  ),
                ),
                Expanded(
                  child: _MiniStat(
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
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
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

class _MiniStat extends StatelessWidget {
  const _MiniStat({
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
            Icon(icon, size: 14, color: Colors.grey.shade600),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(color: Colors.grey.shade600, fontSize: 11),
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

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.icon, required this.title});

  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10, left: 4),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Colors.grey.shade700),
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

class _AllocationRow extends StatelessWidget {
  const _AllocationRow({required this.allocation});

  final CategoryAllocation allocation;

  @override
  Widget build(BuildContext context) {
    final color = categoryColor(allocation.category);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: color,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    categoryLabel(allocation.category),
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                ],
              ),
              Text(
                '${formatCurrency(allocation.currentValue)} · ${formatPercent(allocation.currentPct)}',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (allocation.currentPct / 100).clamp(0, 1),
              minHeight: 6,
              backgroundColor: color.withValues(alpha: 0.12),
              valueColor: AlwaysStoppedAnimation(color),
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
      margin: const EdgeInsets.only(bottom: 8),
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
