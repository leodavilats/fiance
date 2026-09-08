import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SectionNavComponent, SectionNavItem } from './section-nav.component';

@Component({
  selector: 'app-strategy-shell',
  standalone: true,
  imports: [RouterOutlet, SectionNavComponent],
  template: `
    <app-section-nav [items]="items" label="Sobra">
      <router-outlet />
    </app-section-nav>
  `,
})
export class StrategyShellComponent {
  readonly items: readonly SectionNavItem[] = [
    { path: '/sobra', label: 'A ordem', icon: 'hand-coins' },
    { path: '/sobra/aporte', label: 'Aporte', icon: 'lightbulb' },
    { path: '/sobra/desvio', label: 'Alocação × meta', icon: 'target' },
  ];
}
