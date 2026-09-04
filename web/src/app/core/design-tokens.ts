export const fiColor = {
  dark: {
    'ground-0': '#090C0B',
    'ground-1': '#171E1B',
    'ground-2': '#212927',
    'hairline': '#323B38',
    'hairline-strong': '#45504C',
    'ink-1': '#E9EAE9',
    'ink-2': '#A5ACA9',
    'ink-3': '#89908E',
    'ink-on-brand': '#08131A',
    'brand': '#5B9DC0',
    'brand-quiet': '#1D3140',
    'state-favorable': '#4FB286',
    'state-attention': '#D9A23B',
    'state-adverse': '#D9705F',
    'state-indeterminate': '#89908E',
    'direction-up': '#6B9984',
    'direction-down': '#B2847B',
    'series-1': '#5B9DC0',
    'series-2': '#4FB286',
    'series-3': '#D9A23B',
    'series-4': '#D9705F',
    'series-5': '#9084C4',
    'series-6': '#3FA3A3',
    'series-7': '#D07FA8',
    'series-8': '#D2874F',
    'series-9': '#96A94F',
    'series-10': '#6E8FD6',
    'series-11': '#B5849B',
    'series-other': '#6B7470',
  },
  light: {
    'ground-0': '#F0ECE4',
    'ground-1': '#FFFFFF',
    'ground-2': '#F8F5F0',
    'hairline': '#D8D0C3',
    'hairline-strong': '#BBB1A0',
    'ink-1': '#1C1F1E',
    'ink-2': '#55605C',
    'ink-3': '#626C67',
    'ink-on-brand': '#FFFFFF',
    'brand': '#2C6485',
    'brand-quiet': '#E4EDF2',
    'state-favorable': '#147954',
    'state-attention': '#8C5C10',
    'state-adverse': '#B04434',
    'state-indeterminate': '#626C67',
    'direction-up': '#3D755D',
    'direction-down': '#8E5A4C',
    'series-1': '#2C6485',
    'series-2': '#157F58',
    'series-3': '#8C5C10',
    'series-4': '#B04434',
    'series-5': '#5C51A0',
    'series-6': '#17706F',
    'series-7': '#96436B',
    'series-8': '#A05A1F',
    'series-9': '#5C6B1E',
    'series-10': '#3B5AA8',
    'series-11': '#7A4E62',
    'series-other': '#7F8883',
  },
} as const;

export type FiTheme = keyof typeof fiColor;
export type FiColorToken = keyof typeof fiColor.dark;

export type FiState = 'favorable' | 'attention' | 'adverse' | 'neutral' | 'indeterminate';

export const fiSpace = {
  '0': 0,
  '1': 4,
  '2': 8,
  '3': 12,
  '4': 16,
  '5': 20,
  '6': 24,
  '8': 32,
  '10': 40,
  '12': 48,
  '16': 64,
} as const;

export const fiRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  pill: 999,
} as const;

export const fiMotion = {
  fast: 120,
  base: 180,
  slow: 240,
  easeEnter: 'cubic-bezier(0.2, 0, 0, 1)',
  easeExit: 'cubic-bezier(0.4, 0, 1, 1)',
} as const;

export const fiBreakpoint = {
  'mobile-sm': 0,
  'mobile-lg': 420,
  'tablet': 768,
  'desktop-sm': 1024,
  'desktop': 1280,
  'desktop-lg': 1440,
} as const;

export const fiLayout = {
  readingMaxWidth: 1120,
  denseMaxWidth: 1600,
  drawerWidth: 600,
  subnavWidth: 200,
  navHeight: 56,
  minTouchTarget: 44,
} as const;

export const fiDensity = {
  comfortable: { rowHeight: 48, sectionGap: 32, blockPadding: 20 },
  compact: { rowHeight: 36, sectionGap: 24, blockPadding: 14 },
} as const;

export type FiDensity = keyof typeof fiDensity;

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
  { id: 'insufficient', min: null, max: null, label: 'Dado insuficiente', state: 'indeterminate', emphasis: 'muted' },
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
