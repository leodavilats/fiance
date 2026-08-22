import 'package:flutter/material.dart';

import '../design_tokens.dart';

enum ScoreRulerSize { inline, list, card, page }

class ScoreRuler extends StatelessWidget {
  const ScoreRuler({
    super.key,
    required this.score,
    this.dataCompleteness,
    this.bands = fiScoreBands,
    this.size = ScoreRulerSize.card,
    this.showScale = false,
    this.showValue = true,
    this.subject = 'Score',
  });

  final double score;
  final double? dataCompleteness;
  final List<FiScoreBand> bands;
  final ScoreRulerSize size;
  final bool showScale;
  final bool showValue;

  final String subject;

  List<FiScoreBand> get _numeric =>
      bands.where((b) => b.min != null && b.max != null).toList()
        ..sort((a, b) => a.min!.compareTo(b.min!));

  double get _clamped => score.clamp(0, 100).toDouble();

  FiScoreBand get _band => fiBandFor(_clamped, bands, dataCompleteness);

  bool get _reliable => _band.state != FiState.indeterminate;

  double get _trackHeight => size == ScoreRulerSize.inline ? 6 : 8;

  String get _semantics => _reliable
      ? '$subject: ${_clamped.round()} de 100 — leitura ${_band.label.toLowerCase()}'
      : '$subject: dado insuficiente para calcular';

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final isDark = brightness == Brightness.dark;
    final ink1 = isDark ? FiColors.darkInk1 : FiColors.lightInk1;
    final ink3 = isDark ? FiColors.darkInk3 : FiColors.lightInk3;
    final inactive = ink3.withValues(alpha: 0.2);
    final activeId = _reliable ? _activeBandId() : null;

    return Semantics(
      label: _semantics,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                LayoutBuilder(
                  builder: (context, constraints) {
                    final width = constraints.maxWidth;
                    return SizedBox(
                      height: _trackHeight,
                      child: Stack(
                        children: [
                          Row(
                            children: [
                              for (final band in _numeric) ...[
                                Expanded(
                                  flex: ((band.max! + 1 - band.min!) * 10).round(),
                                  child: DecoratedBox(
                                    decoration: BoxDecoration(
                                      color: band.id == activeId
                                          ? fiStateColor(band.state, brightness)
                                          : inactive,
                                      borderRadius: BorderRadius.circular(2),
                                    ),
                                  ),
                                ),
                                if (band != _numeric.last) const SizedBox(width: 1),
                              ],
                            ],
                          ),
                          if (_reliable)
                            Positioned(
                              left: (width * _clamped / 100 - 1).clamp(0, width - 2),
                              top: 0,
                              bottom: 0,
                              child: Container(width: 2, color: ink1),
                            ),
                        ],
                      ),
                    );
                  },
                ),
                if (showScale) ...[
                  const SizedBox(height: FiSpace.s1),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      for (final label in _scaleLabels)
                        Text(label, style: FiType.caption.copyWith(color: ink3)),
                    ],
                  ),
                ],
              ],
            ),
          ),
          if (showValue) ...[
            const SizedBox(width: FiSpace.s3),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _reliable ? '${_clamped.round()}' : '—',
                  style: (size == ScoreRulerSize.page ? FiType.metric : FiType.metricSm).copyWith(
                    color: fiStateColor(_band.state, brightness),
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _band.label,
                  style: FiType.caption.copyWith(
                    color: fiStateColor(_band.state, brightness),
                  ),
                  textAlign: TextAlign.end,
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  List<String> get _scaleLabels => [
    '0',
    for (final b in _numeric)
      if (b.min! > 0) '${b.min!.round()}',
    '100',
  ];

  String? _activeBandId() {
    for (final band in _numeric) {
      if (_clamped >= band.min! && _clamped <= band.max!) return band.id;
    }
    return null;
  }
}
