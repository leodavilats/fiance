import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-provenance',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <details class="fi-provenance mt-4">
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
        @if (asOf()) {
          <p class="fi-caption text-ink-2 m-0">
            <span class="text-ink-3">Momento:</span> <span class="fi-num">{{ asOf() }}</span>
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

  readonly asOf = input<string>('');
  readonly limitation = input<string>('');
}
