import { FiScoreBand, FiState } from './design-tokens';

/**
 * A mecânica compartilhada das quatro réguas do produto.
 *
 * `ScoreRuler`, `MarginOfSafety`, `AllocationGap` e `GoalProgress` são leituras
 * diferentes do **mesmo instrumento**: um valor marcado numa escala de zonas
 * nomeadas. Escala e rótulos saem de `design-tokens/tokens.json`; o que vive
 * aqui é só a aritmética de transformar banda em largura e valor em posição —
 * nenhuma regra de negócio, nenhum limiar.
 */

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

/** A cor de uma zona: tinta cheia só onde o valor caiu, cinza no resto (§13). */
export function zoneBackground(zone: RulerZone): string {
  return zone.active
    ? `var(${STATE_VAR[zone.state]})`
    : 'color-mix(in srgb, var(--fi-ink-3) 20%, transparent)';
}

/**
 * As bandas cobrem o domínio em passos de 1 unidade (0–39, 40–59, …), então o
 * denominador é `max + 1 − min` — 101 células para uma escala de 0 a 100.
 */
function cells(domain: RulerDomain): number {
  return domain.max + 1 - domain.min;
}

/** Bandas numéricas, da menor para a maior. As nulas (dado insuficiente) saem. */
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

/** Posição da marca, no centro da célula do valor — alinha com as zonas. */
export function markerPct(value: number, domain: RulerDomain): number {
  const clamped = clampToDomain(value, domain);
  return ((clamped - domain.min + 0.5) / cells(domain)) * 100;
}

/** Os limiares visíveis abaixo da régua: o início de cada banda, sem as pontas. */
export function rulerTicks(bands: readonly FiScoreBand[], domain: RulerDomain): number[] {
  return numericBands(bands)
    .map(b => b.min as number)
    .filter(min => min > domain.min);
}
