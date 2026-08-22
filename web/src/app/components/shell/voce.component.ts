import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SectionNavComponent, SectionNavItem } from './section-nav.component';

@Component({
  selector: 'app-voce',
  standalone: true,
  imports: [RouterOutlet, SectionNavComponent],
  template: `
    <app-section-nav [items]="items" label="Sua conta" />
    <router-outlet />
  `,
})
export class VoceComponent {
  readonly items: readonly SectionNavItem[] = [
    { path: '/voce/preferencias', label: 'Preferências', icon: 'sliders-horizontal' },
    { path: '/voce/alertas', label: 'Alertas', icon: 'bell' },
    { path: '/voce/conta', label: 'Conta e dados', icon: 'shield-check' },
  ];
}
