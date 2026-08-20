import 'package:flutter/material.dart';

/// Régua única do score de oportunidade (0–100).
///
/// Espelha `backend/app/analysis/score_ruler.py` e
/// `web/src/app/core/score-ruler.ts`. O mesmo número tinha três réguas
/// diferentes; ao mudar um limiar, mudar os três.
const double kScoreStrong = 75;
const double kScoreGood = 60;
const double kScoreNeutral = 40;

/// DY mínimo (%) para um score alto contar como destaque de renda.
const double kHighlightMinDy = 6;

class ScoreBand {
  const ScoreBand(this.text, this.color);

  final String text;
  final Color color;
}

ScoreBand scoreBand(double score) {
  if (score >= kScoreStrong) {
    return const ScoreBand('Excelente entrada', Color(0xFF4ADE80));
  }
  if (score >= kScoreGood) {
    return const ScoreBand('Boa oportunidade', Color(0xFF38BDF8));
  }
  if (score >= kScoreNeutral) {
    return const ScoreBand('Neutro', Color(0xFFFACC15));
  }
  return const ScoreBand('Evitar agora', Color(0xFFF87171));
}

/// Texto do glossário derivado dos próprios limiares — não pode divergir.
final String scoreGlossary =
    'Pontuação 0–100 calculada pelo sistema combinando margem de segurança '
    '(preço justo), dividendos, qualidade e endividamento, ponderados pelo seu '
    'perfil de risco. A partir de ${kScoreStrong.toInt()} = excelente entrada; '
    '${kScoreGood.toInt()}–${kScoreStrong.toInt() - 1} = boa oportunidade; '
    '${kScoreNeutral.toInt()}–${kScoreGood.toInt() - 1} = neutro; abaixo de '
    '${kScoreNeutral.toInt()} = evitar agora.';

/// Base da tendência: com histórico curto a SMA200 não existe.
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
  return '$methods ${methods == 1 ? 'método' : 'métodos'} no consenso';
}

String confidenceLabel(double? confidence) {
  if (confidence == null) return '';
  return 'confiança ${(confidence * 100).round()}%';
}
