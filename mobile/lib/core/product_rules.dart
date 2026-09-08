// As bandas de regua e o vocabulario do produto, escritos a mao.
//
// Os limiares de score espelham `backend/app/analysis/score_ruler.py`, que e a fonte: mudar um
// limiar exige mudar o Python primeiro, e depois aqui e no espelho de `web/src/app/core/`.

enum FiState { favorable, attention, adverse, neutral, indeterminate }

const double kScoreStrong = 75;
const double kScoreGood = 60;
const double kScoreNeutral = 40;
const double kMinDataCompleteness = 0.5;
const double kHighlightMinDy = 6;

class FiScoreBand {
  const FiScoreBand({
    required this.id,
    required this.min,
    required this.max,
    required this.label,
    required this.state,
    required this.emphasis,
  });

  final String id;
  final double? min;
  final double? max;
  final String label;
  final FiState state;
  final String emphasis;
}

const List<FiScoreBand> fiScoreBands = [
  FiScoreBand(id: 'strong', min: 75, max: 100, label: 'Forte', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'good', min: 60, max: 74, label: 'Boa', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'neutral', min: 40, max: 59, label: 'Neutra', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'weak', min: 0, max: 39, label: 'Fraca', state: FiState.adverse, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem dado', state: FiState.indeterminate, emphasis: 'muted'),
];

abstract final class FiScoreRulerSize {
  static const inline = 16.0;
  static const list = 24.0;
  static const card = 40.0;
  static const page = 64.0;
}

bool fiScoreIsReliable(double? dataCompleteness) =>
    (dataCompleteness ?? 1) >= kMinDataCompleteness;

FiScoreBand fiScoreBandFor(double score, double? dataCompleteness) {
  if (!fiScoreIsReliable(dataCompleteness)) {
    return fiScoreBands.firstWhere((b) => b.id == 'insufficient');
  }
  return fiScoreBands.firstWhere(
    (b) => b.min != null && score >= b.min!,
    orElse: () => fiScoreBands.firstWhere((b) => b.id == 'weak'),
  );
}

const List<FiScoreBand> fiHealthBands = [
  FiScoreBand(id: 'healthy', min: 75, max: 100, label: 'Saudável', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'ok', min: 60, max: 74, label: 'Em ordem', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'watch', min: 40, max: 59, label: 'Atenção', state: FiState.attention, emphasis: 'muted'),
  FiScoreBand(id: 'fragile', min: 0, max: 39, label: 'Frágil', state: FiState.adverse, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Carteira pequena demais para avaliar', state: FiState.indeterminate, emphasis: 'muted'),
];

const List<FiScoreBand> fiMarginOfSafetyBands = [
  FiScoreBand(id: 'wide', min: 25, max: 50, label: 'Desconto amplo', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'some', min: 10, max: 24, label: 'Algum desconto', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'fair', min: 0, max: 9, label: 'Perto do justo', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'above', min: -50, max: -1, label: 'Acima do justo', state: FiState.attention, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem preço justo', state: FiState.indeterminate, emphasis: 'muted'),
];

const ({double min, double max}) fiMarginOfSafetyDomain = (min: -50, max: 50);

const List<FiScoreBand> fiAllocationGapBands = [
  FiScoreBand(id: 'relevant', min: 5, max: 20, label: 'Desvio relevante', state: FiState.attention, emphasis: 'strong'),
  FiScoreBand(id: 'drift', min: 2, max: 4, label: 'Desvio', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'on-target', min: 0, max: 1, label: 'Na meta', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem meta definida', state: FiState.indeterminate, emphasis: 'muted'),
];

const ({double min, double max}) fiAllocationGapDomain = (min: 0, max: 20);

const List<FiScoreBand> fiGoalProgressBands = [
  FiScoreBand(id: 'reached', min: 100, max: 100, label: 'Meta atingida', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'advancing', min: 50, max: 99, label: 'Mais da metade', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'starting', min: 0, max: 49, label: 'No começo', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem meta definida', state: FiState.indeterminate, emphasis: 'muted'),
];

const ({double min, double max}) fiGoalProgressDomain = (min: 0, max: 100);

const List<FiScoreBand> fiDipScoreBands = [
  FiScoreBand(id: 'opportunity', min: 68, max: 100, label: 'Oportunidade na baixa', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'wait', min: 42, max: 67, label: 'Aguardar', state: FiState.neutral, emphasis: 'muted'),
  FiScoreBand(id: 'trap', min: 0, max: 41, label: 'Armadilha', state: FiState.adverse, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem leitura', state: FiState.indeterminate, emphasis: 'muted'),
];

const List<FiScoreBand> fiMonthPressureBands = [
  FiScoreBand(id: 'tight', min: 80, max: 100, label: 'Mês apertado', state: FiState.adverse, emphasis: 'strong'),
  FiScoreBand(id: 'pressured', min: 60, max: 79, label: 'Mês sob pressão', state: FiState.attention, emphasis: 'strong'),
  FiScoreBand(id: 'steady', min: 30, max: 59, label: 'Mês em ordem', state: FiState.favorable, emphasis: 'muted'),
  FiScoreBand(id: 'loose', min: 0, max: 29, label: 'Mês folgado', state: FiState.favorable, emphasis: 'strong'),
  FiScoreBand(id: 'insufficient', min: null, max: null, label: 'Sem leitura', state: FiState.indeterminate, emphasis: 'muted'),
];

const ({double min, double max}) fiMonthPressureDomain = (min: 0, max: 100);

FiScoreBand fiBandFor(
  double value,
  List<FiScoreBand> bands, [
  double? dataCompleteness,
]) {
  if (!fiScoreIsReliable(dataCompleteness)) {
    return bands.firstWhere((b) => b.min == null, orElse: () => bands.last);
  }
  return bands.firstWhere(
    (b) => b.min != null && value >= b.min!,
    orElse: () => bands.lastWhere((b) => b.min != null, orElse: () => bands.last),
  );
}

abstract final class FiDecision {
  static const interesting = (label: 'Interessante', state: FiState.favorable);
  static const neutral = (label: 'Neutro', state: FiState.neutral);
  static const attention = (label: 'Atenção', state: FiState.attention);
  static const avoid = (label: 'Evitar', state: FiState.adverse);
  static const unknown = (label: 'Sem leitura', state: FiState.indeterminate);
}

abstract final class FiDipDiagnosis {
  static const healthy = (label: 'Queda saudável', criterion: 'preço caiu, fundamentos preservados', state: FiState.favorable);
  static const investigate = (label: 'Queda para investigar', criterion: 'preço caiu e alguma métrica piorou', state: FiState.attention);
  static const structural = (label: 'Queda estrutural', criterion: 'preço caiu junto de deterioração relevante', state: FiState.adverse);
}
