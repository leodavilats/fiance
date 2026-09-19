import 'package:flutter/material.dart';

import 'design_tokens.dart';
import 'format.dart';

export 'design_tokens.dart'
    show
        FiScoreBand,
        fiBandFor,
        fiHealthBands,
        fiScoreBandFor,
        fiScoreBands,
        fiScoreIsReliable,
        kHighlightMinDy,
        kMinDataCompleteness,
        kScoreGood,
        kScoreNeutral,
        kScoreStrong;

class ScoreBand {
  const ScoreBand(this.text, this.color);

  final String text;
  final Color color;
}

ScoreBand _fromToken(FiScoreBand band, Brightness brightness) =>
    ScoreBand(band.label, fiStateColor(band.state, brightness));

ScoreBand scoreBand(double score, Brightness brightness) =>
    _fromToken(fiScoreBandFor(score, null), brightness);

bool scoreIsReliable(double? dataCompleteness) => fiScoreIsReliable(dataCompleteness);

ScoreBand scoreBandFor(double score, double? dataCompleteness, Brightness brightness) =>
    _fromToken(fiScoreBandFor(score, dataCompleteness), brightness);

String dataCompletenessLabel(double? dataCompleteness) {
  final value = dataCompleteness ?? 1;
  if (value >= 1) return '';
  return '${(value * 100).round()}% dos indicadores disponíveis';
}

final String scoreGlossary =
    'Pontuação 0–100 calculada pelo sistema combinando margem de segurança '
    '(preço justo), dividendos, qualidade e endividamento, ponderados pelo seu '
    'perfil de risco. '
    '${fiScoreBands.where((b) => b.min != null).map((b) => b.max == 100 ? '${b.min!.toInt()} ou mais: leitura ${b.label.toLowerCase()}' : '${b.min!.toInt()}–${b.max!.toInt()}: leitura ${b.label.toLowerCase()}').join('; ')}'
    '. É uma leitura do sistema, não recomendação de compra.';

String trendBasisLabel(String? basis) {
  switch (basis) {
    case 'long':
      return 'médias de 50 e 200 dias';
    case 'short':
      return 'médias de 20 e 50 dias (histórico curto)';
    default:
      return 'sem histórico suficiente';
  }
}

String dataYearsLabel(int? dataYears) {
  if (dataYears == null || dataYears == 0) return 'sem histórico de proventos';
  return '$dataYears ${dataYears == 1 ? 'ano' : 'anos'} de proventos';
}

String consensusLabel(int? methods) {
  if (methods == null || methods == 0) return 'sem método aplicável';
  return '$methods ${methods == 1 ? 'método' : 'métodos'} na faixa';
}

String fairBandLabel(double? low, double? high) {
  if (low == null || high == null) return '—';
  if ((high - low).abs() < 0.01) return formatCurrency(low);
  return '${formatCurrency(low)} a ${formatCurrency(high)}';
}

String fairBandSummary(double? low, double? high, int? methods) {
  if (low == null || high == null) return consensusLabel(methods);
  if ((high - low).abs() < 0.01) return 'Justo de ${consensusLabel(methods)}';
  return 'Justo entre ${fairBandLabel(low, high)}, ${consensusLabel(methods)}';
}

String fairBandEdgeLabel(double? price, double? low, double? high) {
  if (low == null || high == null || price == null) return '—';
  if (price < low) return formatCurrency(low);
  if (price > high) return formatCurrency(high);
  return 'na faixa';
}

String basisLabel(String? basis) {
  if (basis == 'trend') return 'leitura de tendência, sem preço justo';
  return '';
}

String confidenceLabel(double? confidence) {
  if (confidence == null) return '';
  return 'confiança ${(confidence * 100).round()}%';
}
