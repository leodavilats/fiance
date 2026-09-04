import {
  FiDensity,
  FiScoreBand,
  FiState,
  MIN_DATA_COMPLETENESS as GENERATED_MIN_DATA_COMPLETENESS,
  HIGHLIGHT_MIN_DY as GENERATED_HIGHLIGHT_MIN_DY,
  SCORE_GOOD as GENERATED_SCORE_GOOD,
  SCORE_NEUTRAL as GENERATED_SCORE_NEUTRAL,
  SCORE_STRONG as GENERATED_SCORE_STRONG,
  fiBandFor,
  fiDecision,
  fiDipDiagnosis,
  fiDipScoreBands,
  fiHealthBands,
  fiAllocationGapBands,
  fiAllocationGapDomain,
  fiGoalProgressBands,
  fiGoalProgressDomain,
  fiMarginOfSafetyBands,
  fiMarginOfSafetyDomain,
  fiScoreBandFor,
  fiScoreBands,
  fiScoreIsReliable,
} from './design-tokens';

export const SCORE_STRONG = GENERATED_SCORE_STRONG;
export const SCORE_GOOD = GENERATED_SCORE_GOOD;
export const SCORE_NEUTRAL = GENERATED_SCORE_NEUTRAL;
export const MIN_DATA_COMPLETENESS = GENERATED_MIN_DATA_COMPLETENESS;
export const HIGHLIGHT_MIN_DY = GENERATED_HIGHLIGHT_MIN_DY;

export {
  fiBandFor,
  fiDecision,
  fiDipDiagnosis,
  fiDipScoreBands,
  fiHealthBands,
  fiAllocationGapBands,
  fiAllocationGapDomain,
  fiGoalProgressBands,
  fiGoalProgressDomain,
  fiMarginOfSafetyBands,
  fiMarginOfSafetyDomain,
  fiScoreBandFor,
  fiScoreBands,
  fiScoreIsReliable,
};
export { fiDensity } from './design-tokens';
export type { FiDensity, FiScoreBand, FiState };

export function stateTextClass(state: FiState): string {
  switch (state) {
    case 'favorable':
      return 'text-favorable';
    case 'attention':
      return 'text-attention';
    case 'adverse':
      return 'text-adverse';
    case 'indeterminate':
      return 'text-indeterminate';
    case 'neutral':
      return 'text-ink-2';
  }
}

export interface ScoreBand {
  text: string;
  cls: string;
  state: FiState;
  emphasis: 'strong' | 'muted';
}

function toScoreBand(band: FiScoreBand): ScoreBand {
  return {
    text: band.label,
    cls: stateTextClass(band.state),
    state: band.state,
    emphasis: band.emphasis,
  };
}

export function scoreBand(score: number): ScoreBand {
  return toScoreBand(fiScoreBandFor(score));
}

export function scoreBandFor(score: number, dataCompleteness?: number | null): ScoreBand {
  return toScoreBand(fiScoreBandFor(score, dataCompleteness));
}

export function dataCompletenessLabel(dataCompleteness?: number | null): string {
  const value = dataCompleteness ?? 1;
  if (value >= 1) return '';
  return `${Math.round(value * 100)}% dos indicadores disponíveis`;
}

export const SCORE_GLOSSARY =
  `Pontuação 0–100 calculada pelo sistema combinando margem de segurança (preço justo), ` +
  `dividendos, qualidade e endividamento, ponderados pelo seu perfil de risco. ` +
  fiScoreBands
    .filter(b => b.min !== null)
    .map(b =>
      b.max === 100
        ? `${b.min} ou mais: leitura ${b.label.toLowerCase()}`
        : `${b.min}–${b.max}: leitura ${b.label.toLowerCase()}`
    )
    .join('; ') +
  `. É uma leitura do sistema, não recomendação de compra.`;
