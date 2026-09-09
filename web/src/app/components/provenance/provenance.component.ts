import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-provenance',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    @if (asOf()) {
      <p class="fi-caption text-ink-2 m-0 mt-4">
        <span class="text-ink-3">Dado de</span> <span class="fi-num">{{ asOf() }}</span>
      </p>
    }

    <details class="fi-provenance" [class.mt-1]="asOf()" [class.mt-4]="!asOf()">
      <summary
        class="fi-caption text-ink-3 cursor-pointer list-none inline-flex items-center gap-1.5 fi-focusable rounded-sm"
      >
        <lucide-icon name="info" size="12" aria-hidden="true"></lucide-icon>
        {{ summary() }}
      </summary>

      <div class="mt-2 pl-4 border-l border-hairline flex flex-col gap-1">
        @if (method()) {
          <p class="fi-caption text-ink-2 m-0">
            <span class="text-ink-3">Método:</span> {{ method() }}
          </p>
        }
        @if (source()) {
          <p class="fi-caption text-ink-2 m-0">
            <span class="text-ink-3">Fonte:</span> {{ source() }}
          </p>
        }
        @if (limitation()) {
          <p class="fi-caption text-ink-2 m-0">
            <span class="text-ink-3">Limitação:</span> {{ limitation() }}
          </p>
        }
        <ng-content />
      </div>
    </details>
  `,
  styles: [
    `
      .fi-provenance > summary::-webkit-details-marker {
        display: none;
      }
      .fi-provenance > summary:hover {
        color: var(--fi-ink-2);
      }
    `,
  ],
})
export class ProvenanceComponent {
  readonly summary = input('Como calculamos');
  readonly method = input<string>('');
  readonly source = input<string>('');

  /**
   * Fica **fora** da gaveta: método e fonte são nota de rodapé, momento não é.
   *
   * Um preço de anteontem muda a decisão, e ele estava no quarto item de uma gaveta fechada —
   * que é o mesmo que não estar. Nenhuma tela passava este valor, então a promoção não desloca
   * nada: ela abre o lugar onde ele passa a caber.
   */
  readonly asOf = input<string>('');

  readonly limitation = input<string>('');
}
