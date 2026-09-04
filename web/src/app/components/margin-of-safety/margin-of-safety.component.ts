import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import {
  fiBandFor,
  fiMarginOfSafetyBands,
  fiMarginOfSafetyDomain,
  stateTextClass,
} from '../../core';
import { clampToDomain, markerPct, rulerZones } from '../../core/ruler';
import { RulerTrackComponent } from '../ruler-track/ruler-track.component';

@Component({
  selector: 'app-margin-of-safety',
  standalone: true,
  imports: [CommonModule, RulerTrackComponent],
  template: `
    <div class="flex items-center gap-3" role="img" [attr.aria-label]="ariaLabel()">
      <div class="flex-1 min-w-[72px]">
        <app-ruler-track
          [zones]="zones()"
          [markerPct]="known() ? marker() : null"
          [height]="6"
          [insufficient]="!known()"
        />
        @if (showScale()) {
          <div class="flex justify-between mt-1 fi-caption text-ink-3">
            <span>acima do justo</span>
            <span>abaixo do justo</span>
          </div>
        }
      </div>

      <div class="shrink-0 text-right leading-none">
        <div class="fi-metric-sm" [class]="stateClass()">
          {{ known() ? signed() : '—' }}
        </div>
        <div class="fi-caption mt-1" [class]="stateClass()">{{ band().label }}</div>
      </div>
    </div>

    @if (!known() && reason()) {
      <p class="fi-caption text-ink-3 m-0 mt-1">{{ reason() }}</p>
    }
  `,
})
export class MarginOfSafetyComponent {
  readonly marginPct = input.required<number | null>();

  readonly reason = input<string>('');
  readonly showScale = input(false);

  readonly known = computed(() => this.marginPct() !== null);

  readonly band = computed(() =>
    fiBandFor(
      clampToDomain(this.marginPct() ?? 0, fiMarginOfSafetyDomain),
      fiMarginOfSafetyBands,
      this.known() ? 1 : 0
    )
  );

  readonly marker = computed(() => markerPct(this.marginPct() ?? 0, fiMarginOfSafetyDomain));

  readonly zones = computed(() =>
    rulerZones(fiMarginOfSafetyBands, fiMarginOfSafetyDomain, this.marginPct() ?? 0, this.known())
  );

  signed(): string {
    const v = this.marginPct() as number;
    return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`;
  }

  stateClass(): string {
    return stateTextClass(this.band().state);
  }

  ariaLabel(): string {
    if (!this.known()) return `Margem de segurança: ${this.reason() || 'não calculável'}`;
    return `Margem de segurança de ${this.signed()} — ${this.band().label.toLowerCase()}`;
  }
}
