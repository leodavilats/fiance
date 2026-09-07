import { CommonModule } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { RulerZone, zoneBackground } from '../../core/ruler';

@Component({
  selector: 'app-ruler-track',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="fi-ruler" [style.height.px]="height()">
      @if (modo() === 'fill') {
        <div
          class="fi-ruler-fill"
          [style.width.%]="preenchidoPct()"
          [style.background]="corDoValor()"
        ></div>
      } @else {
        @for (z of zones(); track z.id) {
          <div
            class="fi-ruler-zone"
            [style.width.%]="z.widthPct"
            [style.background]="background(z)"
            [attr.data-zone]="z.id"
          ></div>
        }
      }

      @for (d of divisas(); track d) {
        <div class="fi-ruler-tick" [style.left.%]="d"></div>
      }

      @if (markerPct() !== null) {
        <div class="fi-ruler-marker" [style.left]="'calc(' + markerPct() + '% - 1px)'"></div>
      }
    </div>
  `,
  styles: [
    `
      .fi-ruler {
        position: relative;
        display: flex;
        width: 100%;
        border-radius: var(--fi-radius-pill);
        background: var(--fi-track);
        border: 1px solid var(--fi-control-border);
        overflow: hidden;
      }

      .fi-ruler-zone,
      .fi-ruler-fill {
        height: 100%;
      }

      .fi-ruler-fill {
        border-radius: inherit;
        transition: width var(--fi-motion-base) var(--fi-motion-ease-enter);
      }

      .fi-ruler-tick {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 1px;
        background: var(--fi-control-border);
      }

      .fi-ruler-marker {
        position: absolute;
        top: -2px;
        bottom: -2px;
        width: 2px;
        background: var(--fi-ink-1);
      }

      :host(.ruler-insufficient) .fi-ruler {
        background: repeating-linear-gradient(90deg, var(--fi-track) 0 4px, transparent 4px 8px);
      }
    `,
  ],
  host: { '[class.ruler-insufficient]': 'insufficient()' },
})
export class RulerTrackComponent {
  readonly zones = input.required<readonly RulerZone[]>();

  readonly markerPct = input<number | null>(null);
  readonly height = input(8);
  readonly insufficient = input(false);

  readonly modo = input<'marker' | 'fill'>('marker');
  readonly preenchidoPct = input(0);

  readonly divisas = computed(() => {
    const acumulado: number[] = [];
    let soma = 0;
    for (const z of this.zones().slice(0, -1)) {
      soma += z.widthPct;
      acumulado.push(soma);
    }
    return acumulado;
  });

  readonly corDoValor = computed(() => {
    if (this.insufficient()) return 'transparent';
    const ativa = this.zones().find(z => z.active);
    return ativa ? zoneBackground(ativa) : 'var(--fi-brand)';
  });

  background(zone: RulerZone): string {
    return zoneBackground(zone);
  }
}
