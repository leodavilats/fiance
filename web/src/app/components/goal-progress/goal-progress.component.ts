import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { fiBandFor, fiGoalProgressBands, fiGoalProgressDomain, stateTextClass } from '../../core';
import { markerPct, rulerZones } from '../../core/ruler';
import { RulerTrackComponent } from '../ruler-track/ruler-track.component';

/**
 * Quarta leitura da régua: **quanto da meta já foi percorrido**.
 *
 * Deliberadamente não existe "no ritmo": o produto conhece o alvo e o prazo,
 * mas não a data em que a meta começou, então qualquer julgamento de ritmo
 * seria inventado (§57). O prazo aparece como contexto — "faltam 8 meses" —,
 * nunca como nota.
 */
@Component({
  selector: 'app-goal-progress',
  standalone: true,
  imports: [CommonModule, RulerTrackComponent],
  template: `
    <div role="group" [attr.aria-label]="ariaLabel()">
      <div class="flex items-baseline justify-between gap-3 mb-2">
        <span class="fi-label text-ink">{{ label() }}</span>
        <span class="fi-caption" [class]="stateClass()">{{ band().label }}</span>
      </div>

      <app-ruler-track
        [zones]="zones()"
        [markerPct]="hasTarget() ? marker() : null"
        [height]="8"
        [insufficient]="!hasTarget()"
      />

      <div class="flex items-baseline justify-between gap-3 mt-2">
        @if (hasTarget()) {
          <span class="fi-body text-ink-2">
            <span class="fi-num text-ink">{{ current() | currency: 'BRL' }}</span>
            de <span class="fi-num">{{ target() | currency: 'BRL' }}</span>
          </span>
          <span class="fi-metric-sm" [class]="stateClass()"> {{ pct() | number: '1.0-0' }}% </span>
        } @else {
          <span class="fi-body text-ink-2">Nenhum alvo definido para esta meta.</span>
        }
      </div>

      @if (hasTarget() && remaining() > 0) {
        <p class="fi-caption text-ink-3 m-0 mt-1">
          Faltam <span class="fi-num">{{ remaining() | currency: 'BRL' }}</span
          >{{ deadlineNote() }}.
        </p>
      }
    </div>
  `,
})
export class GoalProgressComponent {
  readonly label = input.required<string>();
  readonly current = input.required<number>();
  /** Alvo em reais. `null` quando a meta existe em % mas não em valor. */
  readonly target = input<number | null>(null);
  /** Prazo declarado pelo usuário, em ISO. Vira contexto, não julgamento. */
  readonly deadline = input<string | null>(null);

  readonly hasTarget = computed(() => {
    const t = this.target();
    return t !== null && t > 0;
  });

  readonly pct = computed(() =>
    this.hasTarget() ? Math.min(100, (this.current() / (this.target() as number)) * 100) : 0
  );

  readonly remaining = computed(() =>
    this.hasTarget() ? Math.max(0, (this.target() as number) - this.current()) : 0
  );

  readonly band = computed(() =>
    fiBandFor(this.pct(), fiGoalProgressBands, this.hasTarget() ? 1 : 0)
  );

  readonly marker = computed(() => markerPct(this.pct(), fiGoalProgressDomain));

  readonly zones = computed(() =>
    rulerZones(fiGoalProgressBands, fiGoalProgressDomain, this.pct(), this.hasTarget())
  );

  deadlineNote(): string {
    const raw = this.deadline();
    if (!raw) return '';
    const target = new Date(raw);
    if (Number.isNaN(target.getTime())) return '';
    const months = Math.round((target.getTime() - Date.now()) / (1000 * 60 * 60 * 24 * 30.44));
    if (months > 1) return `, com ${months} meses até o prazo`;
    if (months === 1) return ', com 1 mês até o prazo';
    if (months === 0) return ', com o prazo terminando este mês';
    return ', e o prazo já passou';
  }

  stateClass(): string {
    return stateTextClass(this.band().state);
  }

  ariaLabel(): string {
    if (!this.hasTarget()) return `${this.label()}: sem alvo definido`;
    return `${this.label()}: ${this.pct().toFixed(0)}% da meta — ${this.band().label.toLowerCase()}`;
  }
}
