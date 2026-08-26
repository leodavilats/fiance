import { inject, Injectable, signal } from '@angular/core';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { RecommendService } from './recommend.service';

/**
 * O índice de navegação da busca global.
 *
 * Os destinos são estáticos de propósito: são as 19 rotas endereçáveis da
 * arquitetura de informação, e cada uma entra pela **pergunta que responde**,
 * não pelo nome técnico da tela. Quem procura "quanto rendeu" precisa achar
 * Desempenho sem saber que a rota se chama assim.
 */
export interface SearchDestination {
  readonly route: string;
  readonly label: string;
  readonly section: string;
  /** Sinônimos e a pergunta da tela — o que o usuário digitaria de verdade. */
  readonly keywords: string;
  readonly icon: string;
}

export const SEARCH_DESTINATIONS: readonly SearchDestination[] = [
  {
    route: '/hoje',
    label: 'Hoje',
    section: 'Hoje',
    keywords: 'o que mudou novidades resumo início dashboard',
    icon: 'sunrise',
  },
  {
    route: '/hoje/atividade',
    label: 'Atividade recente',
    section: 'Hoje',
    keywords: 'histórico eventos o que aconteceu log',
    icon: 'history',
  },
  {
    route: '/carteira',
    label: 'Carteira',
    section: 'Carteira',
    keywords: 'quanto tenho patrimônio saúde total',
    icon: 'wallet',
  },
  {
    route: '/carteira/composicao',
    label: 'Composição',
    section: 'Carteira',
    keywords: 'alocação distribuição setor concentração onde está meu dinheiro',
    icon: 'chart-pie',
  },
  {
    route: '/carteira/desempenho',
    label: 'Desempenho',
    section: 'Carteira',
    keywords: 'rendimento retorno cdi ibovespa benchmark ganhei quanto rendeu',
    icon: 'trending-up',
  },
  {
    route: '/carteira/proventos',
    label: 'Proventos',
    section: 'Carteira',
    keywords: 'dividendos jcp renda passiva recebido',
    icon: 'coins',
  },
  {
    route: '/carteira/posicoes',
    label: 'Posições',
    section: 'Carteira',
    keywords: 'ativos tabela quantidade preço médio o que eu tenho',
    icon: 'table',
  },
  {
    route: '/carteira/encerradas',
    label: 'Operações encerradas',
    section: 'Carteira',
    keywords: 'vendas lucro realizado imposto ir prejuízo a compensar',
    icon: 'receipt',
  },
  {
    route: '/carteira/editar',
    label: 'Editar carteira',
    section: 'Carteira',
    keywords: 'adicionar comprar cadastrar posição importar',
    icon: 'pencil',
  },
  {
    route: '/descobrir/oportunidades',
    label: 'Oportunidades',
    section: 'Descobrir',
    keywords: 'o que comprar barato desconto margem de segurança',
    icon: 'compass',
  },
  {
    route: '/descobrir/quedas',
    label: 'Quedas',
    section: 'Descobrir',
    keywords: 'caiu dip baixa desconto armadilha',
    icon: 'trending-down',
  },
  {
    route: '/descobrir/comparar',
    label: 'Comparar ativos',
    section: 'Descobrir',
    keywords: 'versus x comparação lado a lado',
    icon: 'git-compare',
  },
  {
    route: '/estrategia',
    label: 'Estratégia',
    section: 'Estratégia',
    keywords: 'plano próximo aporte o que fazer rebalancear',
    icon: 'target',
  },
  {
    route: '/estrategia/aporte',
    label: 'Aporte',
    section: 'Estratégia',
    keywords: 'quick invest investir dinheiro distribuir caixa',
    icon: 'wallet',
  },
  {
    route: '/estrategia/metas',
    label: 'Metas',
    section: 'Estratégia',
    keywords: 'objetivo alocação alvo percentual meta de renda',
    icon: 'target',
  },
  {
    route: '/estrategia/renda-fixa',
    label: 'Renda fixa',
    section: 'Estratégia',
    keywords: 'cdb lci lca tesouro cdi selic ipca comparar títulos',
    icon: 'landmark',
  },
  {
    route: '/estrategia/projecao',
    label: 'Projeção',
    section: 'Estratégia',
    keywords: 'futuro simular cenário juros compostos',
    icon: 'chart-line',
  },
  {
    route: '/voce/preferencias',
    label: 'Preferências',
    section: 'Você',
    keywords: 'configurações perfil risco caixa tema',
    icon: 'sliders-horizontal',
  },
  {
    route: '/voce/alertas',
    label: 'Alertas',
    section: 'Você',
    keywords: 'notificação aviso push preço alvo',
    icon: 'bell',
  },
  {
    route: '/voce/conta',
    label: 'Conta',
    section: 'Você',
    keywords: 'sair logout cache dados sessão',
    icon: 'circle-user',
  },
];

/** Remove acento e caixa: "projeção" e "projecao" precisam achar a mesma tela. */
function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .trim();
}

@Injectable({ providedIn: 'root' })
export class GlobalSearchService {
  private readonly api = inject(RecommendService);

  readonly open = signal(false);
  readonly query = signal('');
  readonly tickers = signal<{ ticker: string; name: string }[]>([]);
  readonly searching = signal(false);

  private readonly queries = new Subject<string>();

  constructor() {
    this.queries
      .pipe(
        debounceTime(180),
        distinctUntilChanged(),
        switchMap(q => {
          this.searching.set(true);
          return this.api.searchTickers(q, 6);
        })
      )
      .subscribe({
        next: r => {
          this.tickers.set(r.items);
          this.searching.set(false);
        },
        error: () => {
          this.tickers.set([]);
          this.searching.set(false);
        },
      });
  }

  show(): void {
    this.open.set(true);
  }

  hide(): void {
    this.open.set(false);
    this.query.set('');
    this.tickers.set([]);
  }

  toggle(): void {
    this.open() ? this.hide() : this.show();
  }

  setQuery(value: string): void {
    this.query.set(value);
    const q = value.trim();
    if (q.length >= 2) this.queries.next(q);
    else this.tickers.set([]);
  }

  /** Destinos que casam com o termo — por rótulo, seção ou sinônimo. */
  destinations(): SearchDestination[] {
    const q = normalize(this.query());
    if (!q) return SEARCH_DESTINATIONS.slice(0, 6);
    return SEARCH_DESTINATIONS.filter(d =>
      normalize(`${d.label} ${d.section} ${d.keywords}`).includes(q)
    ).slice(0, 8);
  }
}
