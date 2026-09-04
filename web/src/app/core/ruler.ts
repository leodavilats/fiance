import { FiScoreBand, FiState } from './design-tokens';

export interface RulerDomain {
  readonly min: number;
  readonly max: number;
}

export interface RulerZone {
  readonly id: string;
  readonly label: string;
  readonly widthPct: number;
  readonly active: boolean;
  readonly state: FiState;
}

const STATE_VAR: Record<FiState, string> = {
  favorable: '--fi-state-favorable',
  attention: '--fi-state-attention',
  adverse: '--fi-state-adverse',
  indeterminate: '--fi-state-indeterminate',
  neutral: '--fi-ink-2',
};

export function zoneBackground(zone: RulerZone): string {
  return zone.active
    ? `var(${STATE_VAR[zone.state]})`
    : 'color-mix(in srgb, var(--fi-ink-3) 70%, transparent)';
}

function cells(domain: RulerDomain): number {
  return domain.max + 1 - domain.min;
}

export function numericBands(bands: readonly FiScoreBand[]): FiScoreBand[] {
  return bands
    .filter(b => b.min !== null && b.max !== null)
    .sort((a, b) => (a.min as number) - (b.min as number));
}

export function rulerZones(
  bands: readonly FiScoreBand[],
  domain: RulerDomain,
  value: number,
  reliable: boolean
): RulerZone[] {
  const total = cells(domain);
  const clamped = clampToDomain(value, domain);
  return numericBands(bands).map(b => ({
    id: b.id,
    label: b.label,
    widthPct: (((b.max as number) + 1 - (b.min as number)) / total) * 100,
    active: reliable && clamped >= (b.min as number) && clamped <= (b.max as number),
    state: b.state,
  }));
}

export function clampToDomain(value: number, domain: RulerDomain): number {
  return Math.max(domain.min, Math.min(domain.max, value));
}

export function markerPct(value: number, domain: RulerDomain): number {
  const clamped = clampToDomain(value, domain);
  return ((clamped - domain.min + 0.5) / cells(domain)) * 100;
}

export function rulerTicks(bands: readonly FiScoreBand[], domain: RulerDomain): number[] {
  return numericBands(bands)
    .map(b => b.min as number)
    .filter(min => min > domain.min);
}

export function allocationScalePct(
  rows: readonly { currentPct: number; targetPct: number | null }[]
): number {
  const maior = rows.reduce((max, r) => Math.max(max, r.currentPct, r.targetPct ?? 0), 0);
  if (maior <= 0) return 100;
  return Math.min(100, Math.max(10, maior * 1.15));
}
