export const fiColor = {
  dark: {
    'ground-0': '#090C0B',
    'ground-1': '#171E1B',
    'ground-2': '#212927',
    'hairline': '#323B38',
    'hairline-strong': '#45504C',
    'ink-1': '#E9EAE9',
    'ink-2': '#BBC0BE',
    'ink-3': '#A1A6A5',
    'ink-on-brand': '#08131A',
    'brand': '#74ACC9',
    'brand-quiet': '#1D3140',
    'state-favorable': '#58B68C',
    'state-attention': '#D9A23B',
    'state-adverse': '#E29184',
    'state-indeterminate': '#A1A6A5',
    'state-favorable-surface': '#1D3229',
    'state-attention-surface': '#3A321B',
    'state-adverse-surface': '#372C28',
    'state-indeterminate-surface': '#2A2F2D',
    'direction-up': '#89AD9D',
    'direction-down': '#C19D95',
    'series-1': '#74ACC9',
    'series-2': '#58B68C',
    'series-3': '#D9A23B',
    'series-4': '#E29184',
    'series-5': '#A69DD0',
    'series-6': '#5AB0B0',
    'series-7': '#D58CB1',
    'series-8': '#D69361',
    'series-9': '#9AAD56',
    'series-10': '#87A2DD',
    'series-11': '#C198AB',
    'series-other': '#9FA5A2',
  },
  light: {
    'ground-0': '#F0ECE4',
    'ground-1': '#FFFFFF',
    'ground-2': '#F8F5F0',
    'hairline': '#D8D0C3',
    'hairline-strong': '#BBB1A0',
    'ink-1': '#1C1F1E',
    'ink-2': '#3F4744',
    'ink-3': '#515A55',
    'ink-on-brand': '#FFFFFF',
    'brand': '#295D7C',
    'brand-quiet': '#E4EDF2',
    'state-favorable': '#116446',
    'state-attention': '#784F0E',
    'state-adverse': '#973A2D',
    'state-indeterminate': '#515A55',
    'state-favorable-surface': '#D7E5E0',
    'state-attention-surface': '#E8E1D6',
    'state-adverse-surface': '#EFE1E0',
    'state-indeterminate-surface': '#E1E3E2',
    'direction-up': '#33614D',
    'direction-down': '#7A4D41',
    'series-1': '#295D7C',
    'series-2': '#116446',
    'series-3': '#784F0E',
    'series-4': '#973A2D',
    'series-5': '#5C51A0',
    'series-6': '#156766',
    'series-7': '#924168',
    'series-8': '#8B4E1B',
    'series-9': '#56641C',
    'series-10': '#3B5AA8',
    'series-11': '#7A4E62',
    'series-other': '#595F5C',
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
