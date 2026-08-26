import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { RulerZone, zoneBackground } from '../../core/ruler';

/**
 * O traço da régua — zonas nomeadas e uma marca fina no valor.
 *
 * Não é um componente de domínio: não sabe o que o número significa, só como
 * desenhá-lo. Quem dá sentido é `ScoreRuler`, `MarginOfSafety`, `AllocationGap`
 * e `GoalProgress`. Nunca vira gauge, velocímetro ou donut (§13).
 *
 * Sem leitura confiável a marca some e o traço fica tracejado e cinza: dado
 * insuficiente tem forma própria, não é nota baixa (§11).
 */
@Component({
  selector: 'app-ruler-track',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="relative w-full flex gap-px rounded-sm overflow-hidden"
      [style.height.px]="height()"
    >
      @for (z of zones(); track z.id) {
        <div
          class="h-full"
          [style.width.%]="z.widthPct"
          [style.background]="z.active ? background(z) : 'transparent'"
          [class.ruler-zone-idle]="!z.active"
          [attr.data-zone]="z.id"
        ></div>
      }

      @if (markerPct() !== null) {
        <div
          class="absolute top-0 bottom-0 w-[2px] bg-ink"
          [style.left]="'calc(' + markerPct() + '% - 1px)'"
        ></div>
      }
    </div>
  `,
  styles: [
    `
      /* Zona sem valor: tinta fraca. Tracejada quando não há leitura confiável. */
      .ruler-zone-idle {
        background: color-mix(in srgb, var(--fi-ink-3) 20%, transparent);
      }
      :host(.ruler-insufficient) .ruler-zone-idle {
        background: repeating-linear-gradient(
          90deg,
          color-mix(in srgb, var(--fi-ink-3) 28%, transparent) 0 4px,
          transparent 4px 8px
        );
      }
    `,
  ],
  host: { '[class.ruler-insufficient]': 'insufficient()' },
})
export class RulerTrackComponent {
  readonly zones = input.required<readonly RulerZone[]>();
  /** Posição da marca em %, ou `null` quando não há leitura confiável. */
  readonly markerPct = input<number | null>(null);
  readonly height = input(8);
  readonly insufficient = input(false);

  background(zone: RulerZone): string {
    return zoneBackground(zone);
  }
}
