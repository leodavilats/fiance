import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SectionNavComponent, SectionNavItem } from './section-nav.component';

@Component({
  selector: 'app-portfolio-shell',
  standalone: true,
  imports: [RouterOutlet, SectionNavComponent],
  template: `
    <app-section-nav [items]="items" label="Carteira">
      <router-outlet />
    </app-section-nav>
  `,
})
export class PortfolioShellComponent {
  readonly items: readonly SectionNavItem[] = [
    { path: '/carteira', label: 'Resumo', icon: 'wallet' },
    { path: '/carteira/composicao', label: 'Composição', icon: 'chart-pie' },
    { path: '/carteira/desempenho', label: 'Desempenho', icon: 'chart-line' },
    { path: '/carteira/proventos', label: 'Proventos', icon: 'coins' },
    { path: '/carteira/posicoes', label: 'Posições', icon: 'table' },
    { path: '/carteira/encerradas', label: 'Encerradas', icon: 'circle-check' },
  ];
}
