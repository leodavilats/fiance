import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { FiScoreBand, fiBandFor, stateTextClass } from '../../core';
import { markerPct, rulerTicks, rulerZones } from '../../core/ruler';
import { RulerTrackComponent } from '../ruler-track/ruler-track.component';

export type ScoreRulerSize = 'inline' | 'list' | 'card' | 'page';

const SCORE_DOMAIN = { min: 0, max: 100 } as const;

@Component({
  selector: 'app-score-ruler',
  standalone: true,
  imports: [CommonModule, RulerTrackComponent],
  template: `
    <div
      class="flex items-center gap-3"
      role="img"
      [attr.aria-label]="ariaLabel()"
      [title]="ariaLabel()"
    >
      <div class="flex-1 min-w-[72px]">
        <app-ruler-track
          [zones]="zones()"
          [markerPct]="reliable() ? marker() : null"
          [height]="trackHeight()"
          [insufficient]="!reliable()"
        />

        @if (showScale()) {
          <div class="flex justify-between mt-1 fi-caption text-ink-3">
            <span>0</span>
            @for (t of thresholds(); track t) {
              <span>{{ t }}</span>
            }
            <span>100</span>
          </div>
        }
      </div>

      @if (showValue()) {
        <div class="shrink-0 text-right leading-none">
          <div [class]="valueClass()">{{ reliable() ? (score() | number: '1.0-0') : '—' }}</div>
          <div class="fi-caption mt-1" [class]="bandClass()">{{ band().label }}</div>
        </div>
      }
    </div>
  `,
})
export class ScoreRulerComponent {
  readonly score = input.required<number>();
  readonly dataCompleteness = input<number | null>(null);
  readonly size = input<ScoreRulerSize>('card');
  readonly showScale = input(false);
  readonly showValue = input(true);
  readonly subject = input('Score');

  readonly bands = input.required<readonly FiScoreBand[]>();

  readonly thresholds = computed(() => rulerTicks(this.bands(), SCORE_DOMAIN));
  readonly band = computed(() => fiBandFor(this.clamped(), this.bands(), this.dataCompleteness()));
  readonly reliable = computed(() => this.band().state !== 'indeterminate');
  readonly clamped = computed(() => Math.max(0, Math.min(100, this.score())));
  readonly trackHeight = computed(() => (this.size() === 'inline' ? 6 : 8));
  readonly marker = computed(() => markerPct(this.clamped(), SCORE_DOMAIN));

  readonly zones = computed(() =>
    rulerZones(this.bands(), SCORE_DOMAIN, this.clamped(), this.reliable())
  );

  bandClass(): string {
    return stateTextClass(this.band().state);
  }

  valueClass(): string {
    const base = this.size() === 'page' ? 'fi-metric' : 'fi-metric-sm';
    return `${base} ${this.bandClass()}`;
  }

  ariaLabel(): string {
    if (!this.reliable()) {
      return `${this.subject()}: dado insuficiente para calcular`;
    }
    return `${this.subject()}: ${Math.round(this.score())} de 100 — leitura ${this.band().label.toLowerCase()}`;
  }
}
