// As bandas de régua e o vocabulário do produto, escritos à mão.
//
// Os limiares de score espelham `backend/app/analysis/score_ruler.py`, que é a fonte: mudar um
// limiar exige mudar o Python primeiro, e depois aqui e no espelho de `mobile/lib/core/`.

export type FiState = 'favorable' | 'attention' | 'adverse' | 'neutral' | 'indeterminate';

export const SCORE_STRONG = 75;
export const SCORE_GOOD = 60;
export const SCORE_NEUTRAL = 40;
export const MIN_DATA_COMPLETENESS = 0.5;
export const HIGHLIGHT_MIN_DY = 6;

export interface FiScoreBand {
  readonly id: string;
  readonly min: number | null;
  readonly max: number | null;
  readonly label: string;
  readonly state: FiState;
  readonly emphasis: 'strong' | 'muted';
}

export const fiScoreBands: readonly FiScoreBand[] = [
  { id: 'strong', min: 75, max: 100, label: 'Forte', state: 'favorable', emphasis: 'strong' },
  { id: 'good', min: 60, max: 74, label: 'Boa', state: 'favorable', emphasis: 'muted' },
  { id: 'neutral', min: 40, max: 59, label: 'Neutra', state: 'neutral', emphasis: 'muted' },
  { id: 'weak', min: 0, max: 39, label: 'Fraca', state: 'adverse', emphasis: 'strong' },
  { id: 'insufficient', min: null, max: null, label: 'Sem dado', state: 'indeterminate', emphasis: 'muted' },
] as const;

export const fiScoreRulerSizes = {
  inline: 16,
  list: 24,
  card: 40,
  page: 64,
} as const;

export function fiScoreIsReliable(dataCompleteness?: number | null): boolean {
  return (dataCompleteness ?? 1) >= MIN_DATA_COMPLETENESS;
}

export function fiScoreBandFor(
  score: number,
  dataCompleteness?: number | null
): FiScoreBand {
  if (!fiScoreIsReliable(dataCompleteness)) {
    return fiScoreBands.find(b => b.id === 'insufficient')!;
  }
  return (
    fiScoreBands.find(b => b.min !== null && score >= b.min) ??
    fiScoreBands.find(b => b.id === 'weak')!
  );
}

export const fiHealthBands: readonly FiScoreBand[] = [
  { id: 'healthy', min: 75, max: 100, label: 'Saudável', state: 'favorable', emphasis: 'strong' },
  { id: 'ok', min: 60, max: 74, label: 'Em ordem', state: 'favorable', emphasis: 'muted' },
  { id: 'watch', min: 40, max: 59, label: 'Atenção', state: 'attention', emphasis: 'muted' },
  { id: 'fragile', min: 0, max: 39, label: 'Frágil', state: 'adverse', emphasis: 'strong' },
  { id: 'insufficient', min: null, max: null, label: 'Carteira pequena demais para avaliar', state: 'indeterminate', emphasis: 'muted' },
] as const;

export const fiMarginOfSafetyBands: readonly FiScoreBand[] = [
  { id: 'wide', min: 25, max: 50, label: 'Desconto amplo', state: 'favorable', emphasis: 'strong' },
  { id: 'some', min: 10, max: 24, label: 'Algum desconto', state: 'favorable', emphasis: 'muted' },
  { id: 'fair', min: 0, max: 9, label: 'Perto do justo', state: 'neutral', emphasis: 'muted' },
  { id: 'above', min: -50, max: -1, label: 'Acima do justo', state: 'attention', emphasis: 'strong' },
  { id: 'insufficient', min: null, max: null, label: 'Sem preço justo', state: 'indeterminate', emphasis: 'muted' },
] as const;

export const fiMarginOfSafetyDomain = { min: -50, max: 50 } as const;

export const fiAllocationGapBands: readonly FiScoreBand[] = [
  { id: 'relevant', min: 5, max: 20, label: 'Desvio relevante', state: 'attention', emphasis: 'strong' },
  { id: 'drift', min: 2, max: 4, label: 'Desvio', state: 'neutral', emphasis: 'muted' },
  { id: 'on-target', min: 0, max: 1, label: 'Na meta', state: 'favorable', emphasis: 'muted' },
  { id: 'insufficient', min: null, max: null, label: 'Sem meta definida', state: 'indeterminate', emphasis: 'muted' },
] as const;

export const fiAllocationGapDomain = { min: 0, max: 20 } as const;

export const fiGoalProgressBands: readonly FiScoreBand[] = [
  { id: 'reached', min: 100, max: 100, label: 'Meta atingida', state: 'favorable', emphasis: 'strong' },
  { id: 'advancing', min: 50, max: 99, label: 'Mais da metade', state: 'favorable', emphasis: 'muted' },
  { id: 'starting', min: 0, max: 49, label: 'No começo', state: 'neutral', emphasis: 'muted' },
  { id: 'insufficient', min: null, max: null, label: 'Sem meta definida', state: 'indeterminate', emphasis: 'muted' },
] as const;

export const fiGoalProgressDomain = { min: 0, max: 100 } as const;

export const fiDipScoreBands: readonly FiScoreBand[] = [
  { id: 'opportunity', min: 68, max: 100, label: 'Oportunidade na baixa', state: 'favorable', emphasis: 'strong' },
  { id: 'wait', min: 42, max: 67, label: 'Aguardar', state: 'neutral', emphasis: 'muted' },
  { id: 'trap', min: 0, max: 41, label: 'Armadilha', state: 'adverse', emphasis: 'strong' },
  { id: 'insufficient', min: null, max: null, label: 'Sem leitura', state: 'indeterminate', emphasis: 'muted' },
] as const;

export const fiMonthPressureBands: readonly FiScoreBand[] = [
  { id: 'tight', min: 80, max: 100, label: 'Mês apertado', state: 'adverse', emphasis: 'strong' },
  { id: 'pressured', min: 60, max: 79, label: 'Mês sob pressão', state: 'attention', emphasis: 'strong' },
  { id: 'steady', min: 30, max: 59, label: 'Mês em ordem', state: 'favorable', emphasis: 'muted' },
  { id: 'loose', min: 0, max: 29, label: 'Mês folgado', state: 'favorable', emphasis: 'strong' },
  { id: 'insufficient', min: null, max: null, label: 'Sem leitura', state: 'indeterminate', emphasis: 'muted' },
] as const;

export const fiMonthPressureDomain = { min: 0, max: 100 } as const;

export function fiBandFor(
  value: number,
  bands: readonly FiScoreBand[],
  dataCompleteness?: number | null
): FiScoreBand {
  if (!fiScoreIsReliable(dataCompleteness)) {
    return bands.find(b => b.min === null) ?? bands[bands.length - 1];
  }
  return (
    bands.find(b => b.min !== null && value >= b.min) ??
    bands.filter(b => b.min !== null).slice(-1)[0] ??
    bands[bands.length - 1]
  );
}

export const fiDecision = {
  interesting: { label: 'Interessante', state: 'favorable' as FiState },
  neutral: { label: 'Neutro', state: 'neutral' as FiState },
  attention: { label: 'Atenção', state: 'attention' as FiState },
  avoid: { label: 'Evitar', state: 'adverse' as FiState },
  unknown: { label: 'Sem leitura', state: 'indeterminate' as FiState },
} as const;

export const fiDipDiagnosis = {
  healthy: { label: 'Queda saudável', criterion: 'preço caiu, fundamentos preservados', state: 'favorable' as FiState },
  investigate: { label: 'Queda para investigar', criterion: 'preço caiu e alguma métrica piorou', state: 'attention' as FiState },
  structural: { label: 'Queda estrutural', criterion: 'preço caiu junto de deterioração relevante', state: 'adverse' as FiState },
} as const;
