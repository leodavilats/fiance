import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { FiScoreBand, FiState, fiBandFor, fiScoreBands, stateTextClass } from '../../core';

export type ScoreRulerSize = 'inline' | 'list' | 'card' | 'page';

interface Zone {
  readonly id: string;
  readonly label: string;
  readonly widthPct: number;
  readonly background: string;
}

const STATE_VAR: Record<FiState, string> = {
  favorable: '--fi-state-favorable',
  attention: '--fi-state-attention',
  adverse: '--fi-state-adverse',
  indeterminate: '--fi-state-indeterminate',
  neutral: '--fi-ink-2',
};

@Component({
  selector: 'app-score-ruler',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="flex items-center gap-3"
      role="img"
      [attr.aria-label]="ariaLabel()"
      [title]="ariaLabel()"
    >
      <div class="flex-1 min-w-[72px]">
        <div
          class="relative w-full rounded-sm overflow-hidden flex gap-px"
          [style.height.px]="trackHeight()"
        >
          @for (z of zones(); track z.id) {
            <div
              class="h-full"
              [style.width.%]="z.widthPct"
              [style.background]="z.background"
            ></div>
          }
          @if (reliable()) {
            <!-- A marca do valor: um fio fino e preciso, não uma bolha. -->
            <div
              class="absolute top-0 bottom-0 w-[2px]"
              [style.background]="'var(--fi-ink-1)'"
              [style.left]="'calc(' + clamped() + '% - 1px)'"
            ></div>
          }
        </div>

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
  readonly bands = input<readonly FiScoreBand[]>(fiScoreBands);

  private readonly numeric = computed(() =>
    this.bands().filter(b => b.min !== null && b.max !== null)
  );

  readonly thresholds = computed(() =>
    this.numeric()
      .map(b => b.min as number)
      .filter(min => min > 0)
      .sort((a, b) => a - b)
  );

  readonly band = computed(() => fiBandFor(this.clamped(), this.bands(), this.dataCompleteness()));
  readonly reliable = computed(() => this.band().state !== 'indeterminate');
  readonly clamped = computed(() => Math.max(0, Math.min(100, this.score())));
  readonly trackHeight = computed(() => (this.size() === 'inline' ? 6 : 8));

  readonly zones = computed<Zone[]>(() => {
    const activeId = this.reliable() ? this.activeBandId() : null;
    return [...this.numeric()]
      .sort((a, b) => (a.min as number) - (b.min as number))
      .map(b => ({
        id: b.id,
        label: b.label,
        widthPct: (((b.max as number) + 1 - (b.min as number)) / 101) * 100,
        background:
          b.id === activeId
            ? `var(${STATE_VAR[b.state]})`
            : 'color-mix(in srgb, var(--fi-ink-3) 20%, transparent)',
      }));
  });

  private activeBandId(): string | null {
    const s = this.clamped();
    const hit = this.numeric().find(b => s >= (b.min as number) && s <= (b.max as number));
    return hit?.id ?? null;
  }

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
