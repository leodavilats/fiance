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
    final lastIndex = snapshots.length - 1;

    final currentColor = fiDirectionColor(
      snapshots.last.totalPnl >= 0 ? 1 : -1,
      brightness,
    );
    final investedColor = fiInk3(context);
    final gridColor = Theme.of(context).dividerColor;

    final valor = <FlSpot>[
      for (var i = 0; i < snapshots.length; i++)
        FlSpot(i.toDouble(), snapshots[i].totalCurrent),
    ];
    final aplicado = <FlSpot>[
      for (var i = 0; i < snapshots.length; i++)
        FlSpot(i.toDouble(), snapshots[i].totalInvested),
    ];

    final numeros = [
      for (final s in snapshots) ...[s.totalCurrent, s.totalInvested],
    ];
    final minY = numeros.reduce((a, b) => a < b ? a : b);
    final maxY = numeros.reduce((a, b) => a > b ? a : b);
    final padding = (maxY - minY).abs() * 0.15 + 1;

    final labelIndices = <int>{0, lastIndex, (lastIndex / 2).round()};
    final tocado = _touchedIndex;
    final foco = snapshots[tocado ?? lastIndex];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // A altura e fixa: o texto muda ao arrastar sobre a linha, e sem ela o grafico
        // sobe e desce debaixo do dedo.
        SizedBox(
          height: 46,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Expanded(
                    child: Text(
                      tocado == null
                          ? 'HOJE'
                          : _dateFormat.format(_dateAt(tocado)).toUpperCase(),
                      style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                    ),
                  ),
                  const SizedBox(width: FiSpace.s3),
                  Text(
                    '${foco.totalPnl >= 0 ? '+' : ''}${formatCurrency(foco.totalPnl)}',
                    style: FiType.figure.copyWith(
                      color: fiDirectionColor(
                        foco.totalPnl >= 0 ? 1 : -1,
                        brightness,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: FiSpace.s1),
              Text(
                '${formatCurrency(foco.totalCurrent)} sobre '
                '${formatCurrency(foco.totalInvested)} aplicados',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: FiType.caption.copyWith(color: fiInk2(context)),
              ),
            ],
          ),
        ),
        const SizedBox(height: FiSpace.s3),
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
                  getTooltipItems: (touchedSpots) => [
                    for (final s in touchedSpots)
                      LineTooltipItem(
                        '${s.barIndex == 0 ? 'aplicado' : 'hoje'} '
                        '${formatCurrency(s.y)}',
                        FiType.caption.copyWith(
                          color: s.barIndex == 0 ? investedColor : currentColor,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                  ],
                ),
                getTouchedSpotIndicator: (barData, indicators) => indicators
                    .map(
                      (i) => TouchedSpotIndicatorData(
                        FlLine(
                          color: currentColor.withValues(alpha: 0.4),
                          strokeWidth: 1.5,
                        ),
                        FlDotData(
                          getDotPainter: (spot, percent, bar, index) =>
                              FlDotCirclePainter(
                                radius: 4,
                                color: bar.color ?? currentColor,
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
                  spots: aplicado,
                  isCurved: false,
                  color: investedColor,
                  barWidth: 1.5,
                  dashArray: const [4, 3],
                  dotData: const FlDotData(show: false),
                ),
                LineChartBarData(
                  spots: valor,
                  isCurved: false,
                  color: currentColor,
                  barWidth: 2.5,
                  dotData: FlDotData(
                    show: snapshots.length <= 14,
                    getDotPainter: (spot, percent, bar, index) =>
                        FlDotCirclePainter(
                          radius: 2.5,
                          color: currentColor,
                          strokeWidth: 0,
                        ),
                  ),
                  belowBarData: BarAreaData(
                    show: true,
                    color: currentColor.withValues(alpha: 0.10),
                    cutOffY: 0,
                    applyCutOffY: false,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: FiSpace.s3),
        Row(
          children: [
            _Legend(color: currentColor, label: 'valor de hoje'),
            const SizedBox(width: FiSpace.s5),
            _Legend(color: investedColor, label: 'aplicado', dashed: true),
          ],
        ),
      ],
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend({
    required this.color,
    required this.label,
    this.dashed = false,
  });

  final Color color;
  final String label;
  final bool dashed;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 16,
          height: 2,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: color.withValues(alpha: dashed ? 0.7 : 1),
            ),
          ),
        ),
        const SizedBox(width: FiSpace.s2),
        Text(
          label,
          style: FiType.axis.copyWith(color: fiInk3(context)),
        ),
      ],
    );
  }
}

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

        final numeros = <double>[
          0,
          data.portfolioReturnPct,
          data.cdiReturnPct,
          if (data.ibovAvailable) data.ibovReturnPct ?? 0,
        ];
        final piso = numeros.reduce((a, b) => a < b ? a : b);
        final cap = numeros.reduce((a, b) => a > b ? a : b);
        final folga = (cap - piso).abs() * 0.1 + 0.5;

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
                max: cap + folga,
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
                  max: cap + folga,
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
