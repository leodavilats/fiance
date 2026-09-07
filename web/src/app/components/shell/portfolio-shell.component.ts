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
    { path: '/patrimonio', label: 'Resumo', icon: 'wallet' },
    { path: '/patrimonio/composicao', label: 'Composição', icon: 'chart-pie' },
    { path: '/patrimonio/desempenho', label: 'Desempenho', icon: 'chart-line' },
    { path: '/patrimonio/proventos', label: 'Proventos', icon: 'coins' },
    { path: '/patrimonio/posicoes', label: 'Posições', icon: 'table' },
    { path: '/patrimonio/encerradas', label: 'Encerradas', icon: 'circle-check' },
  ];
}
