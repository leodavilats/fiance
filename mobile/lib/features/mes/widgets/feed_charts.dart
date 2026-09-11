import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/format.dart';
import '../../../core/widgets/measure.dart';
import '../../../core/widgets/provenance.dart';
import '../../../core/widgets/section.dart';
import '../../../core/widgets/skeleton.dart';
import '../../../core/models.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import 'feed_patrimony.dart';

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
    final gridColor = Theme.of(context).dividerColor;
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
    final tocado = _touchedIndex;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Lugar fixo: sem isso o gráfico salta 24dp no primeiro toque, e a linha foge do dedo.
        SizedBox(
          height: 24,
          child: tocado == null
              ? Text(
                  'De ${_dateFormat.format(_dateAt(0))} a '
                  '${_dateFormat.format(_dateAt(lastIndex))}',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                )
              : Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      formatCurrency(snapshots[tocado].totalCurrent),
                      style: FiType.metricSm.copyWith(color: lineColor),
                    ),
                    const SizedBox(width: FiSpace.s2),
                    Text(
                      _dateFormat.format(_dateAt(tocado)),
                      style: FiType.caption.copyWith(color: fiInk2(context)),
                    ),
                  ],
                ),
        ),
        const SizedBox(height: FiSpace.s2),
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
                      padding: const EdgeInsets.only(right: FiSpace.s1),
                      child: Text(
                        fiCompactCurrency(value),
                        style: FiType.axis.copyWith(color: fiInk3(context)),
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
                        padding: const EdgeInsets.only(top: FiSpace.s2),
                        child: Text(
                          _dateFormat.format(_dateAt(index)),
                          style: FiType.axis.copyWith(color: fiInk3(context)),
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
                          FiType.caption.copyWith(
                            color: lineColor,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      )
                      .toList(),
                ),
                getTouchedSpotIndicator: (barData, indicators) => indicators
                    .map(
                      (i) => TouchedSpotIndicatorData(
                        FlLine(
                          color: lineColor.withValues(alpha: 0.4),
                          strokeWidth: 1.5,
                        ),
                        FlDotData(
                          getDotPainter: (spot, percent, bar, index) =>
                              FlDotCirclePainter(
                                radius: 5,
                                color: lineColor,
                                strokeWidth: 2,
                                strokeColor: fiGround0(brightness),
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
                    () => _touchedIndex = response.lineBarSpots!.first.x.round(),
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
    );
  }
}

/// A carteira contra a referência, com o CDI como marca da régua.
class FiBenchmarkSection extends ConsumerWidget {
  const FiBenchmarkSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final benchmark = ref.watch(benchmarkProvider);

    return benchmark.when(
      loading: () => const FiSection(
        title: 'Contra a referência',
        child: FiSkeleton(shape: FiSkeletonShape.row, count: 3),
      ),
      error: (_, _) => const SizedBox.shrink(),
      data: (data) {
        if (data.points.length < 2) return const SizedBox.shrink();

        final delta = data.portfolioReturnPct - data.cdiReturnPct;
        final acima = delta >= 0;
        final estado = acima ? FiState.favorable : FiState.attention;

        // O domínio cobre os três números com folga: sem isso uma carteira negativa contra um
        // CDI positivo sai encostada na borda esquerda, sem escala.
        final numeros = <double>[
          0,
          data.portfolioReturnPct,
          data.cdiReturnPct,
          if (data.ibovAvailable) data.ibovReturnPct ?? 0,
        ];
        final piso = numeros.reduce((a, b) => a < b ? a : b);
        final teto = numeros.reduce((a, b) => a > b ? a : b);
        final folga = (teto - piso).abs() * 0.1 + 0.5;

        return FiSection(
          title: 'Contra a referência',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                acima
                    ? 'Sua carteira rendeu ${delta.abs().toStringAsFixed(1)} pontos '
                          'percentuais acima do CDI no período.'
                    : 'Sua carteira rendeu ${delta.abs().toStringAsFixed(1)} pontos '
                          'percentuais abaixo do CDI no período.',
                style: fiSerif(FiType.verdictSm).copyWith(
                  color: fiStateColor(estado, Theme.of(context).brightness),
                ),
              ),
              const SizedBox(height: FiSpace.s4),
              FiMeasure(
                label: 'Sua carteira',
                value: data.portfolioReturnPct,
                min: piso - folga,
                max: teto + folga,
                reference: data.cdiReturnPct,
                readout: _pct(data.portfolioReturnPct),
                note: 'a marca é o CDI, em ${_pct(data.cdiReturnPct)}',
                state: estado,
              ),
              if (data.ibovAvailable)
                FiMeasure(
                  label: 'Ibovespa',
                  value: data.ibovReturnPct ?? 0,
                  min: piso - folga,
                  max: teto + folga,
                  reference: data.cdiReturnPct,
                  readout: _pct(data.ibovReturnPct ?? 0),
                  fillColor: fiInk3(context),
                )
              else
                Padding(
                  padding: const EdgeInsets.only(top: FiSpace.s2),
                  child: Text(
                    'Ibovespa indisponível no momento.',
                    style: FiType.caption.copyWith(color: fiInk3(context)),
                  ),
                ),
              FiProvenance(
                summary: 'Como comparamos com a referência',
                method:
                    'O retorno da sua carteira no período, contra o CDI acumulado no mesmo '
                    'intervalo.',
                source: 'Suas posições com preços da BRAPI; CDI do BCB.',
                limitation:
                    'A curva de CDI é extrapolada da taxa de hoje, então é referência e não o '
                    'acumulado histórico.',
              ),
            ],
          ),
        );
      },
    );
  }

  String _pct(double v) => '${v >= 0 ? '+' : ''}${v.toStringAsFixed(1)}%';
}
