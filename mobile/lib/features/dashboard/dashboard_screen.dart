import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/format.dart';
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
              if (data.alerts.isNotEmpty) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.notifications_none,
                  title: 'Alertas',
                ),
                ...data.alerts.map((a) => _AlertTile(alert: a)),
              ],
              if (data.health != null) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.health_and_safety_outlined,
                  title: 'Saúde da carteira',
                ),
                _HealthCard(health: data.health!),
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
              const SizedBox(height: 20),
              const _SectionTitle(
                icon: Icons.bar_chart_outlined,
                title: 'Carteira vs benchmarks',
              ),
              const _BenchmarkSection(),
              if (data.snapshots.length > 1) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.show_chart,
                  title: 'Evolução do patrimônio',
                ),
                _EvolutionChart(snapshots: data.snapshots),
              ],
              if (data.positions.isNotEmpty) ...[
                const SizedBox(height: 20),
                const _SectionTitle(
                  icon: Icons.account_balance_wallet_outlined,
                  title: 'Carteira',
                ),
                ...data.positions.map((p) => _PositionRow(position: p)),
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
    final mutedColor = brightness == Brightness.dark
        ? AppColors.darkMuted
        : AppColors.lightMuted;

    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              scheme.primary.withValues(alpha: brightness == Brightness.dark ? 0.16 : 0.10),
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
                  child: _MiniStat(
                    icon: Icons.savings_outlined,
                    label: 'Investido',
                    value: formatCurrency(summary.totalInvested),
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

String _compactCurrency(double value) {
  final abs = value.abs();
  if (abs >= 1000000) return 'R\$ ${(value / 1000000).toStringAsFixed(1)}M';
  if (abs >= 1000) return 'R\$ ${(value / 1000).toStringAsFixed(0)}k';
  return formatCurrency(value);
}

class _EvolutionChart extends StatefulWidget {
  const _EvolutionChart({required this.snapshots});

  final List<PortfolioSnapshot> snapshots;

  @override
  State<_EvolutionChart> createState() => _EvolutionChartState();
}

class _EvolutionChartState extends State<_EvolutionChart> {
  int? _touchedIndex;

  static final _dateFormat = DateFormat('dd/MM');

  DateTime _dateAt(int index) => DateTime.fromMillisecondsSinceEpoch(
    (widget.snapshots[index].capturedAt * 1000).round(),
  );

  @override
  Widget build(BuildContext context) {
    final snapshots = widget.snapshots;
    final brightness = Theme.of(context).brightness;
    final positive = snapshots.last.totalCurrent >= snapshots.first.totalCurrent;
    final lineColor = positive ? gainColor(brightness) : lossColor(brightness);
    final gridColor = Theme.of(context).dividerColor.withValues(alpha: 0.3);
    final lastIndex = snapshots.length - 1;

    final spots = <FlSpot>[
      for (var i = 0; i < snapshots.length; i++)
        FlSpot(i.toDouble(), snapshots[i].totalCurrent),
    ];

    final values = snapshots.map((s) => s.totalCurrent).toList();
    final minY = values.reduce((a, b) => a < b ? a : b);
    final maxY = values.reduce((a, b) => a > b ? a : b);
    final padding = (maxY - minY).abs() * 0.15 + 1;

    final labelIndices = <int>{0, lastIndex, (lastIndex / 2).round()};

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(8, 16, 16, 4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_touchedIndex != null)
              Padding(
                padding: const EdgeInsets.only(left: 8, bottom: 8),
                child: Row(
                  children: [
                    Text(
                      formatCurrency(snapshots[_touchedIndex!].totalCurrent),
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: lineColor,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _dateFormat.format(_dateAt(_touchedIndex!)),
                      style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                    ),
                  ],
                ),
              ),
            SizedBox(
              height: 200,
              child: LineChart(
                LineChartData(
                  minY: minY - padding,
                  maxY: maxY + padding,
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: (maxY - minY + padding * 2) / 3,
                    getDrawingHorizontalLine: (_) =>
                        FlLine(color: gridColor, strokeWidth: 1),
                  ),
                  borderData: FlBorderData(show: false),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 48,
                        interval: (maxY - minY + padding * 2) / 3,
                        getTitlesWidget: (value, meta) => Padding(
                          padding: const EdgeInsets.only(right: 4),
                          child: Text(
                            _compactCurrency(value),
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 10,
                            ),
                          ),
                        ),
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 24,
                        interval: 1,
                        getTitlesWidget: (value, meta) {
                          final index = value.round();
                          if (!labelIndices.contains(index) ||
                              index < 0 ||
                              index > lastIndex) {
                            return const SizedBox.shrink();
                          }
                          return Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              _dateFormat.format(_dateAt(index)),
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontSize: 10,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (touchedSpots) => touchedSpots
                          .map(
                            (s) => LineTooltipItem(
                              '${formatCurrency(s.y)}\n${_dateFormat.format(_dateAt(s.x.round()))}',
                              TextStyle(
                                color: lineColor,
                                fontWeight: FontWeight.w600,
                                fontSize: 12,
                              ),
                            ),
                          )
                          .toList(),
                    ),
                    getTouchedSpotIndicator: (barData, indicators) =>
                        indicators
                            .map(
                              (i) => TouchedSpotIndicatorData(
                                FlLine(color: lineColor.withValues(alpha: 0.4), strokeWidth: 1.5),
                                FlDotData(
                                  getDotPainter: (spot, percent, bar, index) =>
                                      FlDotCirclePainter(
                                        radius: 5,
                                        color: lineColor,
                                        strokeWidth: 2,
                                        strokeColor: Theme.of(context).cardColor,
                                      ),
                                ),
                              ),
                            )
                            .toList(),
                    touchCallback: (event, response) {
                      if (!event.isInterestedForInteractions ||
                          response?.lineBarSpots == null ||
                          response!.lineBarSpots!.isEmpty) {
                        if (event is FlPanEndEvent || event is FlTapUpEvent) {
                          setState(() => _touchedIndex = null);
                        }
                        return;
                      }
                      setState(
                        () => _touchedIndex =
                            response.lineBarSpots!.first.x.round(),
                      );
                    },
                  ),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      color: lineColor,
                      barWidth: 2.5,
                      dotData: FlDotData(
                        show: snapshots.length <= 14,
                        getDotPainter: (spot, percent, bar, index) =>
                            FlDotCirclePainter(
                              radius: 2.5,
                              color: lineColor,
                              strokeWidth: 0,
                            ),
                      ),
                      belowBarData: BarAreaData(
                        show: true,
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            lineColor.withValues(alpha: 0.22),
                            lineColor.withValues(alpha: 0.0),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

const _healthMetricExplanations = {
  'Concentração':
      'O quanto seu maior ativo pesa na carteira. Nota boa = nenhum ativo domina muito o total; nota ruim = um único papel concentra boa parte do patrimônio.',
  'Setor':
      'O quanto suas ações/BDRs dependem de um único setor da economia. Nota boa = exposição espalhada entre setores; nota ruim = carteira muito presa a um setor só.',
  'Diversificação':
      'A variedade entre categorias (renda fixa, ações BR, BDRs, FIIs, ETFs) e o número de ativos. Nota boa = carteira cobrindo várias categorias; nota ruim = tudo concentrado em 1-2 categorias.',
  'Risco':
      'A fatia da carteira em ativos com sinal de venda hoje. Nota boa = pouca ou nenhuma exposição a esses ativos; nota ruim = parte relevante da carteira pede atenção.',
};

String _healthBandLabel(double score) {
  if (score >= 70) return 'Bom';
  if (score >= 40) return 'Atenção';
  return 'Ruim';
}

class _HealthCard extends StatefulWidget {
  const _HealthCard({required this.health});

  final PortfolioHealth health;

  @override
  State<_HealthCard> createState() => _HealthCardState();
}

class _HealthCardState extends State<_HealthCard> {
  bool _showInfo = false;

  Color _scoreColor(Brightness brightness) {
    if (widget.health.score >= 70) return gainColor(brightness);
    if (widget.health.score >= 40) return warnColor(brightness);
    return lossColor(brightness);
  }

  @override
  Widget build(BuildContext context) {
    final health = widget.health;
    final brightness = Theme.of(context).brightness;
    final color = _scoreColor(brightness);

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Score geral',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                Row(
                  children: [
                    Text(
                      '${health.score.round()}/100',
                      style: TextStyle(
                        color: color,
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Text(
                        _healthBandLabel(health.score),
                        style: TextStyle(
                          color: color,
                          fontWeight: FontWeight.w700,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: () => setState(() => _showInfo = !_showInfo),
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Expanded(
                      child: _HealthMetric(
                        label: 'Concentração',
                        value: health.concentrationScore,
                      ),
                    ),
                    Expanded(
                      child: _HealthMetric(
                        label: 'Setor',
                        value: health.sectorConcentrationScore,
                      ),
                    ),
                    Expanded(
                      child: _HealthMetric(
                        label: 'Diversif.',
                        value: health.diversificationScore,
                      ),
                    ),
                    Expanded(
                      child: _HealthMetric(label: 'Risco', value: health.riskScore),
                    ),
                  ],
                ),
              ),
            ),
            if (_showInfo) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.grey.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Wrap(
                        spacing: 12,
                        runSpacing: 4,
                        children: [
                          _LegendDot(color: gainColor(brightness), label: '≥70 bom'),
                          _LegendDot(color: warnColor(brightness), label: '40–69 atenção'),
                          _LegendDot(color: lossColor(brightness), label: '<40 ruim'),
                        ],
                      ),
                    ),
                    for (final entry in _healthMetricExplanations.entries)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: RichText(
                          text: TextSpan(
                            style: TextStyle(color: Colors.grey.shade700, fontSize: 12),
                            children: [
                              TextSpan(
                                text: '${entry.key}: ',
                                style: const TextStyle(fontWeight: FontWeight.w600),
                              ),
                              TextSpan(text: entry.value),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ],
            if (health.warnings.isNotEmpty) ...[
              const SizedBox(height: 12),
              for (final w in health.warnings)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.info_outline, size: 14, color: Colors.grey.shade600),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          w,
                          style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  const _LegendDot({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: TextStyle(color: Colors.grey.shade600, fontSize: 11)),
      ],
    );
  }
}

class _HealthMetric extends StatelessWidget {
  const _HealthMetric({required this.label, required this.value});

  final String label;
  final double value;

  Color _color(Brightness brightness) {
    if (value >= 70) return gainColor(brightness);
    if (value >= 40) return warnColor(brightness);
    return lossColor(brightness);
  }

  @override
  Widget build(BuildContext context) {
    final color = _color(Theme.of(context).brightness);
    return Column(
      children: [
        Text(
          value.round().toString(),
          style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 15),
        ),
        Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey.shade600, fontSize: 10),
        ),
        Text(
          _healthBandLabel(value),
          textAlign: TextAlign.center,
          style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 9),
        ),
      ],
    );
  }
}

class _BenchmarkSection extends ConsumerWidget {
  const _BenchmarkSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final benchmark = ref.watch(benchmarkProvider);

    return benchmark.when(
      loading: () => const Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Center(child: CircularProgressIndicator()),
        ),
      ),
      error: (_, _) => const SizedBox.shrink(),
      data: (data) {
        if (data.points.length < 2) return const SizedBox.shrink();
        return Card(
          margin: EdgeInsets.zero,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _BenchmarkStat(
                      label: 'Carteira',
                      pct: data.portfolioReturnPct,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    _BenchmarkStat(
                      label: 'CDI',
                      pct: data.cdiReturnPct,
                      color: Colors.grey.shade500,
                    ),
                    if (data.ibovAvailable)
                      _BenchmarkStat(
                        label: 'Ibovespa',
                        pct: data.ibovReturnPct ?? 0,
                        color: warnColor(Theme.of(context).brightness),
                      ),
                  ],
                ),
                if (!data.ibovAvailable) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Ibovespa indisponível no momento.',
                    style: TextStyle(color: Colors.grey.shade500, fontSize: 11),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}

class _BenchmarkStat extends StatelessWidget {
  const _BenchmarkStat({required this.label, required this.pct, required this.color});

  final String label;
  final double pct;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          '${pct >= 0 ? '+' : ''}${pct.toStringAsFixed(1)}%',
          style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 16),
        ),
        Text(label, style: TextStyle(color: Colors.grey.shade600, fontSize: 11)),
      ],
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
