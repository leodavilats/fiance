import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SectionNavComponent, SectionNavItem } from './section-nav.component';

@Component({
  selector: 'app-carteira',
  standalone: true,
  imports: [RouterOutlet, SectionNavComponent],
  template: `
    <app-section-nav [items]="items" label="Carteira">
      <router-outlet />
    </app-section-nav>
  `,
})
export class CarteiraComponent {
  /**
   * Quatro leituras do patrimônio, não nove destinos.
   *
   * Eram nove abas de mesmo peso, e cinco delas não respondiam a uma pergunta
   * sobre o patrimônio — Posições é o detalhe da tabela, e Lançamentos,
   * Encerradas, Importar e Editar são operações sobre o livro-razão. Todas
   * mantêm a rota; passam a ser alcançadas pelo fim do Resumo, onde estão
   * agrupadas pelo que são. Nove chips numa faixa rolável no celular também
   * significavam três itens que ninguém via.
   */
  readonly items: readonly SectionNavItem[] = [
    { path: '/carteira', label: 'Resumo', icon: 'wallet' },
    { path: '/carteira/composicao', label: 'Composição', icon: 'chart-pie' },
    { path: '/carteira/desempenho', label: 'Desempenho', icon: 'chart-line' },
    { path: '/carteira/proventos', label: 'Proventos', icon: 'coins' },
  ];
}
