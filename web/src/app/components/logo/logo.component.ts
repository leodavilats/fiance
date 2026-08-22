import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-logo',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div
      class="grid place-items-center rounded-md bg-brand flex-shrink-0"
      [style.width.px]="size()"
      [style.height.px]="size()"
      aria-hidden="true"
    >
      <lucide-icon
        name="trending-up"
        [size]="size() * 0.56"
        style="color: var(--fi-ink-on-brand)"
      ></lucide-icon>
    </div>
  `,
})
export class LogoComponent {
  readonly size = input<number>(44);
}
