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
  if (methods == null || methods == 0) return 'sem preço justo';
  if (methods == 1) return 'sem confirmação independente';
  return 'confirmada por outro insumo';
}

String fairBandLabel(double? low, double? high) {
  if (low == null || high == null) return '—';
  if ((high - low).abs() < 0.01) return formatCurrency(low);
  return '${formatCurrency(low)} a ${formatCurrency(high)}';
}

String fairBandSummary(double? low, double? high, int? methods) {
  if (low == null || high == null) return consensusLabel(methods);
  if ((high - low).abs() < 0.01) return 'Preço justo pontual, ${consensusLabel(methods)}';
  return 'Justo entre ${fairBandLabel(low, high)}, ${consensusLabel(methods)}';
}

String fairBandEdgeLabel(double? price, double? low, double? high) {
  if (low == null || high == null || price == null) return '—';
  if (price < low) return formatCurrency(low);
  if (price > high) return formatCurrency(high);
  return 'na faixa';
}

String bandQualityLabel(String? quality, int independentInputs) {
  switch (quality) {
    case 'firme':
      return 'faixa estreita, confirmada por outro insumo';
    case 'ampla':
      return independentInputs <= 1
          ? 'sem confirmação por outro insumo'
          : 'a confirmação fica perto da faixa, ou a faixa é larga pelas premissas';
    case 'fragil':
      return 'evidência frágil: a leitura não passa de abaixo ou acima do preço justo';
    default:
      return 'sem faixa de preço justo';
  }
}

String agreementLabel(String? agreement) {
  switch (agreement) {
    case 'dentro':
      return 'dentro da faixa: confirma';
    case 'fora_ate_30':
      return 'fora da faixa, a até 30% dela';
    case 'fora_mais_30':
      return 'longe da faixa: não confirma';
    default:
      return '';
  }
}

String principalLabel(String? principal) {
  switch (principal) {
    case 'lucros_descontados':
      return 'Pelo lucro que a empresa pode distribuir sem deixar de crescer';
    case 'dividendos':
      return 'Pela distribuição recorrente, no yield que o juro exige';
    default:
      return 'Valor central';
  }
}

String staleRateNote(Map<String, dynamic> premises) {
  if (premises['rate_source'] != 'bcb_cache_vencido') return '';
  final idade = formatAge((premises['rates_as_of'] as num?)?.toDouble());
  if (idade.isEmpty) return 'taxa de uma leitura anterior, com o BCB fora do ar';
  return 'taxa lida $idade, com o BCB fora do ar';
}

String rateBaseLabel(String? base) {
  switch (base) {
    case 'selic_media_10a':
      return 'Selic média de 10 anos';
    case 'selic_atual':
      return 'Selic do dia, sem a série de 10 anos';
    default:
      return '';
  }
}

String methodStatusLabel(String status) {
  switch (status) {
    case 'ok':
      return 'entrou na faixa';
    case 'destoa_dos_demais':
      return 'entrou, e é ele que alarga a faixa';
    case 'inaplicavel':
      return 'não descreve esta classe de ativo';
    case 'sem_dado':
      return 'falta o dado';
    case 'lucro_negativo':
      return 'a empresa não teve lucro';
    case 'fora_da_faixa':
      return 'o dado existe e reprova o método';
    case 'roe_insuficiente':
      return 'o retorno sobre o patrimônio não cobre o crescimento';
    case 'sem_juro':
      return 'falta o juro de referência';
    case 'pouco_distribuido':
      return 'a empresa distribui pouco do lucro';
    case 'taxa_implausivel':
      return 'a taxa de desconto não cabe no modelo';
    default:
      return status;
  }
}

String methodLabel(String method) {
  switch (method) {
    case 'bazin':
      return 'Pelos dividendos';
    case 'graham':
      return 'Critério de Graham';
    case 'dcf':
      return 'Pelo lucro distribuível';
    case 'vpa':
      return 'Pelo valor patrimonial';
    default:
      return method;
  }
}

String basisLabel(String? basis) {
  if (basis == 'trend') return 'leitura de tendência, sem preço justo';
  return '';
}

String confidenceLabel(double? confidence) {
  if (confidence == null) return '';
  if (confidence >= 0.6) return 'confiança alta';
  if (confidence >= 0.4) return 'confiança média';
  return 'confiança baixa';
}
