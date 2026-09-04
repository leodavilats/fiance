import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SectionNavComponent, SectionNavItem } from './section-nav.component';

@Component({
  selector: 'app-you-shell',
  standalone: true,
  imports: [RouterOutlet, SectionNavComponent],
  template: `
    <app-section-nav [items]="items" label="Sua conta">
      <router-outlet />
    </app-section-nav>
  `,
})
export class YouShellComponent {
  readonly items: readonly SectionNavItem[] = [
    { path: '/voce/preferencias', label: 'Preferências', icon: 'sliders-horizontal' },
    { path: '/voce/alertas', label: 'Alertas', icon: 'bell' },
    { path: '/voce/indicacao', label: 'Indicação', icon: 'gift' },
    { path: '/voce/conta', label: 'Conta e dados', icon: 'shield-check' },
  ];
}
