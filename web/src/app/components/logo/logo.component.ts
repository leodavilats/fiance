import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

/** Selo da marca: gradiente verde→ciano com o ícone de tendência de alta.
 * Usado no header, na tela de login e como base do favicon — mantém a
 * identidade visual consistente entre web e mobile. */
@Component({
  selector: 'app-logo',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div
      class="grid place-items-center rounded-xl bg-gradient-to-br from-accent to-accent-2 flex-shrink-0"
      [style.width.px]="size()"
      [style.height.px]="size()"
    >
      <lucide-icon
        name="trending-up"
        [size]="size() * 0.56"
        style="color: #0b0e14"
      ></lucide-icon>
    </div>
  `,
})
export class LogoComponent {
  readonly size = input<number>(44);
}
