import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SectionNavComponent, SectionNavItem } from './section-nav.component';

@Component({
  selector: 'app-estrategia',
  standalone: true,
  imports: [RouterOutlet, SectionNavComponent],
  template: `
    <app-section-nav [items]="items" label="Estratégia">
      <router-outlet />
    </app-section-nav>
  `,
})
export class EstrategiaComponent {
  readonly items: readonly SectionNavItem[] = [
    { path: '/estrategia', label: 'Plano', icon: 'target' },
    { path: '/estrategia/aporte', label: 'Aporte', icon: 'lightbulb' },
    { path: '/estrategia/metas', label: 'Metas', icon: 'flag' },
    { path: '/estrategia/renda-fixa', label: 'Renda fixa', icon: 'landmark' },
    { path: '/estrategia/projecao', label: 'Projeção', icon: 'calendar-clock' },
  ];
}
