import { computed, inject, Injectable, signal } from '@angular/core';
import {
  CategoryAllocation,
  ClosedTradesResponse,
  DividendsReceivedResponse,
  FixedIncomeListResponse,
  Goal,
  PortfolioEvaluationResponse,
  PortfolioPosition,
  SectorGoal,
} from '../models';
import { RecommendService } from './recommend.service';
import { UiHelperService } from './ui-helper.service';

export type PositionSortColumn =
  | 'ticker'
  | 'asset_type'
  | 'quantity'
  | 'avg_price'
  | 'current_price'
  | 'fair_price'
  | 'current_value'
  | 'pnl_pct'
  | 'verdict';

export const MAX_COMPARE = 4;

/**
 * Quantas séries um gráfico pode distinguir por cor.
 *
 * O `tokens.json` declara a regra em comentário — "NO MÁXIMO 6 séries por
 * gráfico, resolvida agregando a cauda em Outros" — e nada a implementava: os
 * onze setores da B3 mapeiam para `series-1..11`, então a composição setorial
 * podia render onze cores, e a sétima cor distinguível não existe.
 */
const MAX_SERIES = 6;

interface Fatia {
  readonly label: string;
  readonly valor: number;
  readonly pct: number;
  readonly targetPct: number | null;
  readonly color: string;
  readonly icon: string;
}

/**
 * Da sétima fatia em diante, tudo vira uma só.
 *
 * A cauda não ganha meta: somar metas de categorias diferentes produziria um
 * alvo que ninguém definiu.
 */
function agregarCauda(fatias: readonly Fatia[]): Fatia[] {
  if (fatias.length <= MAX_SERIES) return [...fatias];

  const cabeca = fatias.slice(0, MAX_SERIES - 1);
  const cauda = fatias.slice(MAX_SERIES - 1);

  return [
    ...cabeca,
    {
      label: `Outros (${cauda.length})`,
      valor: cauda.reduce((soma, f) => soma + f.valor, 0),
      pct: cauda.reduce((soma, f) => soma + f.pct, 0),
      targetPct: null,
      color: 'var(--fi-series-other)',
      icon: 'circle-dot',
    },
  ];
}

@Injectable({ providedIn: 'root' })
export class CarteiraStore {
  private readonly svc = inject(RecommendService);
  private readonly ui = inject(UiHelperService);

  readonly evaluation = signal<PortfolioEvaluationResponse | null>(null);
  readonly fixedIncome = signal<FixedIncomeListResponse | null>(null);
  readonly closedTrades = signal<ClosedTradesResponse | null>(null);
  readonly dividends = signal<DividendsReceivedResponse | null>(null);
  /**
   * A alocação por categoria, **como o backend a calcula**.
   *
   * Antes o cliente somava as posições e dividia pelo total, enquanto o
   * backend fazia a mesma conta para `/hoje` e `/estrategia`: duas verdades
   * sobre o mesmo número, e nada garantia que batessem. Carteira mostrava uma,
   * Estratégia mostrava outra, e a diferença aparecia na mesma visita.
   *
   * A conta agora vem de `/dashboard`, e o cliente só decide como desenhá-la.
   * Setor continua no cliente porque não existe equivalente no servidor — e
   * está declarado assim, não escondido.
   */
  readonly alocacaoOficial = signal<CategoryAllocation[]>([]);

  readonly goals = signal<Goal[]>([]);
  readonly sectorGoals = signal<SectorGoal[]>([]);

  readonly loadFailed = signal(false);
  readonly evaluating = signal(false);
  readonly lastEvaluatedAt = signal<number | null>(null);
  readonly hasStoredAssets = signal(false);

  private loaded = false;

  readonly sortColumn = signal<PositionSortColumn>('current_value');
  readonly sortDirection = signal<'asc' | 'desc'>('desc');
  readonly selectedTickers = signal<string[]>([]);
  readonly composicaoMode = signal<'ativo' | 'setor'>('ativo');

  ensureLoaded(): void {
    if (this.loaded) return;
    this.loaded = true;
    this.reload();
  }

  reload(): void {
    this.loadFailed.set(false);
    this.loadFixedIncome();
    this.loadClosedTrades();
    this.loadDividends();
    this.svc.dashboard().subscribe({
      next: d => this.alocacaoOficial.set(d.allocations ?? []),
      error: () => this.alocacaoOficial.set([]),
    });
    this.svc.getGoals().subscribe({ next: g => this.goals.set(g), error: () => {} });
    this.svc.getSectorGoals().subscribe({ next: sg => this.sectorGoals.set(sg), error: () => {} });
    this.loadAndEvaluate();
  }

  reloadPositions(): void {
    this.loadAndEvaluate();
  }

  private loadAndEvaluate(): void {
    this.svc.getPortfolio().subscribe({
      next: res => {
        this.hasStoredAssets.set(res.items.length > 0);
        if (res.items.length === 0) {
          this.evaluation.set(null);
          return;
        }
        this.evaluate(
          res.items.map(i => ({ ticker: i.ticker, quantity: i.quantity, avg_price: i.avg_price }))
        );
      },
      error: () => this.loadFailed.set(true),
    });
  }

  private evaluate(items: { ticker: string; quantity: number; avg_price: number }[]): void {
    this.evaluating.set(true);
    this.svc.evaluatePortfolio({ items }).subscribe({
      next: res => {
        this.evaluation.set(res);
        this.lastEvaluatedAt.set(Date.now());
        this.evaluating.set(false);
        this.loadDividends();
      },
      error: () => {
        this.evaluating.set(false);
        this.loadFailed.set(true);
      },
    });
  }

  private loadFixedIncome(): void {
    this.svc.getFixedIncome().subscribe({
      next: res => this.fixedIncome.set(res),
      error: () => this.loadFailed.set(true),
    });
  }

  loadClosedTrades(): void {
    this.svc.getClosedTrades().subscribe({
      next: res => this.closedTrades.set(res),
      error: () => {},
    });
  }

  loadDividends(): void {
    const estimate = this.estimatedMonthlyIncome();
    this.svc.getDividendsReceived(estimate ?? undefined).subscribe({
      next: res => this.dividends.set(res),
      error: () => {},
    });
  }

  readonly lastEvaluatedLabel = computed(() => {
    const t = this.lastEvaluatedAt();
    return t ? new Date(t).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '';
  });

  private readonly unsorted = computed(() => this.evaluation()?.positions ?? []);

  readonly tradedPositions = computed(() => {
    const column = this.sortColumn();
    const direction = this.sortDirection() === 'asc' ? 1 : -1;

    const value = (p: PortfolioPosition): number | string => {
      switch (column) {
        case 'ticker':
          return p.ticker;
        case 'asset_type':
          return p.asset_type;
        case 'quantity':
          return p.quantity;
        case 'avg_price':
          return p.avg_price;
        case 'current_price':
          return p.current_price ?? 0;
        case 'fair_price':
          return p.fair_price ?? 0;
        case 'pnl_pct':
          return p.pnl_pct ?? 0;
        case 'verdict':
          return p.verdict;
        default:
          return p.current_value ?? p.invested;
      }
    };

    return [...this.unsorted()].sort((a, b) => {
      const left = value(a);
      const right = value(b);
      if (typeof left === 'string' || typeof right === 'string') {
        return String(left).localeCompare(String(right)) * direction;
      }
      return (left - right) * direction;
    });
  });

  readonly fixedIncomePositions = computed(() =>
    (this.fixedIncome()?.items ?? []).filter(i => !i.oculto)
  );
  readonly hiddenFixedIncome = computed(() =>
    (this.fixedIncome()?.items ?? []).filter(i => i.oculto)
  );

  readonly totalInvestido = computed(
    () => (this.evaluation()?.total_invested ?? 0) + (this.fixedIncome()?.total_investido ?? 0)
  );
  readonly valorAtual = computed(
    () => (this.evaluation()?.total_current ?? 0) + (this.fixedIncome()?.total_atual ?? 0)
  );
  readonly rendimentoTotal = computed(() => this.valorAtual() - this.totalInvestido());
  readonly rendimentoPct = computed(() => {
    const invested = this.totalInvestido();
    return invested === 0 ? 0 : (this.rendimentoTotal() / invested) * 100;
  });

  /**
   * Listas que o backend cortou por paginação.
   *
   * A tela precisa dizer isso em voz alta: uma lista truncada em silêncio é
   * indistinguível de uma lista completa, e a pessoa conclui que operações
   * sumiram. Os totais continuam corretos — quem foi cortado é `items`.
   */
  readonly truncated = computed(() => {
    const cortadas: string[] = [];
    if (this.closedTrades()?.has_more) cortadas.push('operações encerradas');
    if (this.dividends()?.has_more) cortadas.push('proventos');
    if (this.fixedIncome()?.has_more) cortadas.push('renda fixa');
    return cortadas;
  });

  readonly negociadosCount = computed(() => this.tradedPositions().length);
  readonly rendaFixaCount = computed(() => this.fixedIncomePositions().length);
  readonly totalAtivos = computed(() => this.negociadosCount() + this.rendaFixaCount());
  readonly isEmpty = computed(() => !this.hasStoredAssets() && this.rendaFixaCount() === 0);

  readonly goalTargetBySector = computed(() => {
    const map = new Map<string, number>();
    for (const sg of this.sectorGoals()) map.set(sg.sector, sg.target_pct);
    return map;
  });

  readonly alocacaoPorTipo = computed(() =>
    this.alocacaoOficial()
      .map(a => ({
        tipo: a.category,
        valor: a.current_value,
        pct: a.current_pct,
        targetPct: a.target_pct,
      }))
      .sort((a, b) => b.valor - a.valor)
  );

  readonly alocacaoPorSetor = computed(() => {
    const STOCK_TYPES = new Set(['br_stock', 'bdr']);
    const buckets = new Map<string, number>();
    let totalAcoes = 0;

    for (const p of this.tradedPositions()) {
      if (!STOCK_TYPES.has(p.asset_type)) continue;
      const valor = p.current_value ?? p.invested;
      const setor = p.sector ? this.ui.translateSector(p.sector) : 'Outros';
      buckets.set(setor, (buckets.get(setor) || 0) + valor);
      totalAcoes += valor;
    }

    if (totalAcoes <= 0) return [];

    let entries = Array.from(buckets.entries())
      .map(([setor, valor]) => ({ setor, valor }))
      .sort((a, b) => b.valor - a.valor);

    const MAX_SEGMENTOS = 6;
    if (entries.length > MAX_SEGMENTOS) {
      const cauda = entries.slice(MAX_SEGMENTOS - 1);
      const outros = cauda.reduce((sum, e) => sum + e.valor, 0);
      entries = [...entries.slice(0, MAX_SEGMENTOS - 1), { setor: 'Outros', valor: outros }].sort(
        (a, b) => b.valor - a.valor
      );
    }

    const targets = this.goalTargetBySector();
    return entries.map(e => ({
      ...e,
      pct: (e.valor / totalAcoes) * 100,
      targetPct: targets.get(e.setor) ?? null,
    }));
  });

  readonly composicaoSlices = computed(() => {
    const mode = this.composicaoMode();
    const raw =
      mode === 'ativo'
        ? this.alocacaoPorTipo().map(t => ({
            label: this.ui.categoryLabel(t.tipo),
            valor: t.valor,
            pct: t.pct,
            targetPct: t.targetPct,
            color: this.ui.categoryBarColor(t.tipo),
            icon: this.ui.categoryIcon(t.tipo),
          }))
        : this.alocacaoPorSetor().map(s => ({
            label: s.setor,
            valor: s.valor,
            pct: s.pct,
            targetPct: s.targetPct,
            color: this.ui.sectorSeriesColor(s.setor),
            icon: this.ui.sectorIcon(s.setor),
          }));

    const fatias = agregarCauda(raw);

    let acc = 0;
    return fatias.map(r => {
      const start = acc;
      acc += r.pct;
      return { ...r, start, end: acc };
    });
  });

  readonly vencimentosProximos = computed(() =>
    this.fixedIncomePositions()
      .filter(i => i.vencimento_proximo)
      .sort((a, b) => (a.dias_para_vencimento ?? 0) - (b.dias_para_vencimento ?? 0))
  );

  estimatedMonthlyIncome(): number | null {
    const traded = this.tradedPositions().reduce((sum, p) => {
      const value = p.current_value ?? p.invested;
      return sum + (value * (p.dividend_yield ?? 0)) / 100;
    }, 0);

    const fixed = this.fixedIncomePositions().reduce(
      (sum, i) => sum + (i.valor_atual * i.yield_equivalente_pct) / 100,
      0
    );

    const yearly = traded + fixed;
    return yearly > 0 ? Math.round((yearly / 12) * 100) / 100 : null;
  }

  toggleSort(column: PositionSortColumn): void {
    if (this.sortColumn() === column) {
      this.sortDirection.update(d => (d === 'asc' ? 'desc' : 'asc'));
      return;
    }
    this.sortColumn.set(column);
    this.sortDirection.set(column === 'ticker' || column === 'asset_type' ? 'asc' : 'desc');
  }

  sortIcon(column: PositionSortColumn): string {
    if (this.sortColumn() !== column) return 'chevrons-up-down';
    return this.sortDirection() === 'asc' ? 'chevron-up' : 'chevron-down';
  }

  isSelected(ticker: string): boolean {
    return this.selectedTickers().includes(ticker);
  }

  toggleSelection(ticker: string): void {
    const current = this.selectedTickers();
    if (current.includes(ticker)) {
      this.selectedTickers.set(current.filter(t => t !== ticker));
      return;
    }
    if (current.length >= MAX_COMPARE) return;
    this.selectedTickers.set([...current, ticker]);
  }

  clearSelection(): void {
    this.selectedTickers.set([]);
  }
}
