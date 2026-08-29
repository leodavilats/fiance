import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { fiAllocationGapBands, fiAllocationGapDomain, fiBandFor, stateTextClass } from '../../core';
import { rulerZones } from '../../core/ruler';
import { RulerTrackComponent } from '../ruler-track/ruler-track.component';

@Component({
  selector: 'app-allocation-gap',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RulerTrackComponent],
  template: `
    <div class="flex items-center gap-3 sm:gap-4" [attr.aria-label]="ariaLabel()" role="group">
      <span class="fi-label text-ink w-[92px] sm:w-[100px] shrink-0 truncate" [title]="label()">
        {{ label() }}
      </span>

      <div class="relative flex-1 h-2 rounded-sm bg-ground-2 min-w-[80px]">
        @if (hasTarget()) {
          <div
            class="absolute inset-y-0 rounded-sm"
            [style.left.%]="deviationStartPct()"
            [style.width.%]="deviationWidthPct()"
            [style.background]="deviationColor()"
          ></div>
        }
        <div
          class="absolute inset-y-0 left-0 rounded-sm"
          [style.width.%]="barPct()"
          [style.background]="barColor() || 'var(--fi-ink-3)'"
        ></div>
        @if (hasTarget()) {
          <div
            class="absolute inset-y-[-3px] w-[2px] bg-ink"
            [style.left]="'calc(' + tickPct() + '% - 1px)'"
            [title]="'Meta: ' + targetPct() + '%'"
          ></div>
        }
      </div>

      <span class="fi-metric-sm text-ink w-[52px] text-right shrink-0">
        {{ currentPct() | number: '1.0-0' }}%
      </span>

      @if (hasTarget()) {
        <span class="fi-caption text-ink-3 w-[60px] text-right shrink-0 hidden sm:inline">
          meta {{ targetPct() | number: '1.0-0' }}%
        </span>
        <span class="flex items-center gap-1 w-[84px] justify-end shrink-0" [class]="stateClass()">
          <lucide-icon [name]="icon()" size="12" aria-hidden="true"></lucide-icon>
          <span class="fi-metric-sm">
            {{ delta() > 0 ? '+' : '' }}{{ delta() | number: '1.1-1' }} p.p.
          </span>
        </span>
      } @else {
        <span class="fi-caption text-indeterminate w-[84px] text-right shrink-0">sem meta</span>
      }
    </div>

    @if (showRuler() && hasTarget()) {
      <div class="mt-2 ml-[104px] sm:ml-[116px]">
        <app-ruler-track [zones]="zones()" [markerPct]="null" [height]="4" />
        <p class="fi-caption m-0 mt-1" [class]="stateClass()">{{ band().label }}</p>
      </div>
    }
  `,
})
export class AllocationGapComponent {
  readonly label = input.required<string>();
  readonly currentPct = input.required<number>();
  readonly targetPct = input<number | null>(null);
  readonly barColor = input<string>('');
  readonly showRuler = input(false);
  readonly scalePct = input(100);
  readonly hasTarget = computed(() => this.targetPct() !== null);
  readonly delta = computed(() => this.currentPct() - (this.targetPct() ?? 0));
  readonly absDelta = computed(() => Math.abs(this.delta()));

  private readonly scale = computed(() => Math.min(100, Math.max(10, this.scalePct())));
  private readonly onScale = (value: number) =>
    Math.min(100, Math.max(0, (value / this.scale()) * 100));

  readonly barPct = computed(() => this.onScale(this.currentPct()));
  readonly tickPct = computed(() => this.onScale(this.targetPct() ?? 0));

  readonly deviationStartPct = computed(() => Math.min(this.barPct(), this.tickPct()));
  readonly deviationWidthPct = computed(() => Math.abs(this.barPct() - this.tickPct()));
  readonly deviationColor = computed(() =>
    this.absDelta() < 2
      ? 'color-mix(in srgb, var(--fi-ink-3) 25%, transparent)'
      : 'color-mix(in srgb, var(--fi-state-attention) 30%, transparent)'
  );

  readonly band = computed(() =>
    fiBandFor(this.absDelta(), fiAllocationGapBands, this.hasTarget() ? 1 : 0)
  );

  readonly zones = computed(() =>
    rulerZones(fiAllocationGapBands, fiAllocationGapDomain, this.absDelta(), this.hasTarget())
  );

  icon(): string {
    if (this.absDelta() < 1) return 'equal';
    return this.delta() > 0 ? 'arrow-up' : 'arrow-down';
  }

  stateClass(): string {
    return stateTextClass(this.band().state);
  }

  ariaLabel(): string {
    if (!this.hasTarget()) {
      return `${this.label()}: ${this.currentPct().toFixed(1)}% da carteira, sem meta definida`;
    }
    const side = this.delta() > 0 ? 'acima' : 'abaixo';
    return (
      `${this.label()}: ${this.currentPct().toFixed(1)}% da carteira contra meta de ` +
      `${(this.targetPct() as number).toFixed(1)}% — ${this.absDelta().toFixed(1)} pontos ` +
      `percentuais ${side}, ${this.band().label.toLowerCase()}`
    );
  }
}
