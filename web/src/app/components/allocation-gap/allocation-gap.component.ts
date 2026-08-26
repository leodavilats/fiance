import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { fiAllocationGapBands, fiAllocationGapDomain, fiBandFor, stateTextClass } from '../../core';
import { rulerZones } from '../../core/ruler';
import { RulerTrackComponent } from '../ruler-track/ruler-track.component';

/**
 * Terceira leitura da régua: **onde estou diferente do que planejei**.
 *
 * A barra é a alocação atual; o fio vertical é a meta. A distância entre as
 * duas é o número que decide, e é ele que ganha estado — não o tamanho da
 * barra. Desvio não é perda: o pior estado possível aqui é "atenção" (§10).
 *
 * Sem meta definida a linha não julga nada. Comparar contra uma meta que não
 * existe seria inventar o número (§57).
 */
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
        <div
          class="absolute inset-y-0 left-0 rounded-sm"
          [style.width.%]="barPct()"
          [style.background]="barColor() || 'var(--fi-ink-3)'"
        ></div>
        @if (hasTarget()) {
          <div
            class="absolute inset-y-[-3px] w-[2px] bg-brand"
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
  /** Meta em %, ou `null` quando o usuário não definiu meta para a categoria. */
  readonly targetPct = input<number | null>(null);
  /** Identidade de série da categoria, quando a lista mistura categorias. */
  readonly barColor = input<string>('');
  /** Mostra a régua de desvio embaixo — só na leitura de página, não em lista. */
  readonly showRuler = input(false);

  readonly hasTarget = computed(() => this.targetPct() !== null);
  readonly delta = computed(() => this.currentPct() - (this.targetPct() ?? 0));
  readonly absDelta = computed(() => Math.abs(this.delta()));
  readonly barPct = computed(() => Math.min(100, Math.max(0, this.currentPct())));
  readonly tickPct = computed(() => Math.min(100, Math.max(0, this.targetPct() ?? 0)));

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
