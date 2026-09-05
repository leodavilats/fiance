import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';

@Component({
  selector: 'app-logo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="grid place-items-center rounded-md bg-brand flex-shrink-0"
      [style.width.px]="size()"
      [style.height.px]="size()"
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 100 100"
        [attr.width]="size() * 0.58"
        [attr.height]="size() * 0.58"
        focusable="false"
      >
        <path class="eixo" d="M6 6L76 6L76 19L19 19L19 41L56 41L56 54L19 54L19 79L6 79Z" />
        <rect class="eixo" x="83" y="6" width="13" height="13" rx="3" />
        <rect class="chao" x="0" y="87" width="100" height="8" rx="4" />
      </svg>
    </div>
  `,
  styles: [
    `
      .eixo {
        fill: var(--fi-ink-on-brand);
      }

      .chao {
        fill: color-mix(in srgb, var(--fi-ink-on-brand) 65%, var(--fi-brand));
      }
    `,
  ],
})
export class LogoComponent {
  readonly size = input<number>(44);
}
