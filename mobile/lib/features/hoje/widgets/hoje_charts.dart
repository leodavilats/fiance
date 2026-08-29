import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import 'hoje_patrimony.dart';

class FiEvolutionChart extends StatefulWidget {
  const FiEvolutionChart({super.key, required this.snapshots});

  final List<PortfolioSnapshot> snapshots;

  @override
  State<FiEvolutionChart> createState() => _FiEvolutionChartState();
}

class _FiEvolutionChartState extends State<FiEvolutionChart> {
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
    final lineColor = fiDirectionColor(positive ? 1 : -1, brightness);
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
                      style: TextStyle(color: fiInk2(context), fontSize: 12),
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
                            fiCompactCurrency(value),
                            style: TextStyle(
                              color: fiInk2(context),
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
                                color: fiInk2(context),
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
                        color: lineColor.withValues(alpha: 0.10),
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

class FiBenchmarkSection extends ConsumerWidget {
  const FiBenchmarkSection({super.key});

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
                    _FiBenchmarkStat(
                      label: 'Carteira',
                      pct: data.portfolioReturnPct,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    _FiBenchmarkStat(
                      label: 'CDI',
                      pct: data.cdiReturnPct,
                      color: fiInk3(context),
                    ),
                    if (data.ibovAvailable)
                      _FiBenchmarkStat(
                        label: 'Ibovespa',
                        pct: data.ibovReturnPct ?? 0,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                  ],
                ),
                if (!data.ibovAvailable) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Ibovespa indisponível no momento.',
                    style: TextStyle(color: fiInk3(context), fontSize: 11),
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

class _FiBenchmarkStat extends StatelessWidget {
  const _FiBenchmarkStat({required this.label, required this.pct, required this.color});

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
        Text(label, style: TextStyle(color: fiInk2(context), fontSize: 11)),
      ],
    );
  }
}
