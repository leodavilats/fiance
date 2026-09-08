import { inject, Injectable, signal } from '@angular/core';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { GlobalSearchGroup } from '../models';
import { RecommendService } from './recommend.service';

export interface SearchDestination {
  readonly route: string;
  readonly label: string;
  readonly section: string;

  readonly keywords: string;
  readonly icon: string;
}

export const SEARCH_DESTINATIONS: readonly SearchDestination[] = [
  {
    route: '/mes',
    label: 'Mês',
    section: 'Mês',
    keywords: 'o que mudou novidades resumo início dashboard',
    icon: 'calendar-clock',
  },
  {
    route: '/mes/atividade',
    label: 'Atividade recente',
    section: 'Mês',
    keywords: 'histórico eventos o que aconteceu log',
    icon: 'history',
  },
  {
    route: '/patrimonio',
    label: 'Patrimônio',
    section: 'Patrimônio',
    keywords: 'quanto tenho patrimônio saúde total',
    icon: 'wallet',
  },
  {
    route: '/patrimonio/composicao',
    label: 'Composição',
    section: 'Patrimônio',
    keywords: 'alocação distribuição setor concentração onde está meu dinheiro',
    icon: 'chart-pie',
  },
  {
    route: '/patrimonio/desempenho',
    label: 'Desempenho',
    section: 'Patrimônio',
    keywords: 'rendimento retorno cdi ibovespa benchmark ganhei quanto rendeu',
    icon: 'trending-up',
  },
  {
    route: '/patrimonio/proventos',
    label: 'Proventos',
    section: 'Patrimônio',
    keywords: 'dividendos jcp renda passiva recebido',
    icon: 'coins',
  },
  {
    route: '/patrimonio/posicoes',
    label: 'Posições',
    section: 'Patrimônio',
    keywords: 'ativos tabela quantidade preço médio o que eu tenho',
    icon: 'table',
  },
  {
    route: '/patrimonio/encerradas',
    label: 'Operações encerradas',
    section: 'Patrimônio',
    keywords: 'vendas lucro realizado imposto ir prejuízo a compensar',
    icon: 'receipt',
  },
  {
    route: '/patrimonio/editar',
    label: 'Editar carteira',
    section: 'Patrimônio',
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
    route: '/patrimonio',
    label: 'Sobra',
    section: 'Sobra',
    keywords: 'plano próximo aporte o que fazer rebalancear',
    icon: 'target',
  },
  {
    route: '/sobra/aporte',
    label: 'Aporte',
    section: 'Sobra',
    keywords: 'quick invest investir dinheiro distribuir caixa',
    icon: 'wallet',
  },
  {
    route: '/voce/objetivos',
    label: 'Objetivos',
    section: 'Você',
    keywords: 'meta metas objetivo alocação alvo percentual renda reserva',
    icon: 'target',
  },
  {
    route: '/descobrir/renda-fixa',
    label: 'Renda fixa',
    section: 'Descobrir',
    keywords: 'cdb lci lca tesouro cdi selic ipca comparar títulos',
    icon: 'landmark',
  },
  {
    route: '/patrimonio/projecao',
    label: 'Projeção',
    section: 'Patrimônio',
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

  readonly mine = signal<GlobalSearchGroup[]>([]);
  readonly searching = signal(false);

  private readonly queries = new Subject<string>();

  constructor() {
    this.queries
      .pipe(
        debounceTime(180),
        distinctUntilChanged(),
        switchMap(q => {
          this.searching.set(true);
          return this.api.searchEverything(q);
        })
      )
      .subscribe({
        next: r => {
          const ativos = r.groups.find(g => g.label === 'Ativos');
          this.tickers.set((ativos?.items ?? []).map(i => ({ ticker: i.title, name: i.subtitle })));
          this.mine.set(r.groups.filter(g => g.label !== 'Ativos'));
          this.searching.set(false);
        },
        error: () => {
          this.tickers.set([]);
          this.mine.set([]);
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
    this.mine.set([]);
  }

  toggle(): void {
    this.open() ? this.hide() : this.show();
  }

  setQuery(value: string): void {
    this.query.set(value);
    const q = value.trim();
    if (q.length >= 2) {
      this.queries.next(q);
    } else {
      this.tickers.set([]);
      this.mine.set([]);
    }
  }

  destinations(): SearchDestination[] {
    const q = normalize(this.query());
    if (!q) return SEARCH_DESTINATIONS.slice(0, 6);
    return SEARCH_DESTINATIONS.filter(d =>
      normalize(`${d.label} ${d.section} ${d.keywords}`).includes(q)
    ).slice(0, 8);
  }
}
