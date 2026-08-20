import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import {
  ClosedTradesResponse,
  DividendPayload,
  DividendsReceivedResponse,
  FixedIncomeListResponse,
  FixedIncomePosition,
  Goal,
  LoadingService,
  PortfolioEvaluationResponse,
  PortfolioPosition,
  RecommendService,
  RendaFixaTipo,
  SectorGoal,
  SnackbarService,
  UiHelperService,
} from '../../core';

/** Colunas ordenáveis da tabela de posições. */
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

/**
 * "Meus Ativos" — **análise**.
 *
 * Antes este componente acumulava CRUD de ativos, CRUD de renda fixa,
 * avaliação, composição, metas, vendas e histórico em 781 linhas de TS e 883
 * de HTML, com autosave por debounce sobre um PUT destrutivo. Cadastro é tarefa
 * rara e pontual; análise é o retorno diário — os dois competiam pela mesma
 * tela. O cadastro agora vive em `/assets/cadastro`
 * (PortfolioEditorComponent).
 *
 * O cálculo de rendimento da renda fixa saiu daqui: era uma segunda
 * implementação da regra, divergente do backend (% do CDI, dias por mês,
 * IPCA+). Agora vem marcada a mercado de `GET /fixed-income`.
 */
@Component({
  selector: 'app-assets',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule, HelpTooltipComponent, RouterLink],
  templateUrl: './assets.component.html',
  styleUrls: ['./assets.component.scss'],
})
export class AssetsComponent implements OnInit {
  private readonly svc = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);
  private readonly router = inject(Router);
  readonly loading = inject(LoadingService);
  readonly ui = inject(UiHelperService);

  evaluation = signal<PortfolioEvaluationResponse | null>(null);
  fixedIncome = signal<FixedIncomeListResponse | null>(null);
  closedTrades = signal<ClosedTradesResponse | null>(null);
  dividends = signal<DividendsReceivedResponse | null>(null);
  goals = signal<Goal[]>([]);
  sectorGoals = signal<SectorGoal[]>([]);

  loadFailed = signal(false);
  evaluating = signal(false);
  lastEvaluatedAt = signal<number | null>(null);
  hasStoredAssets = signal(false);

  showClosedTrades = signal(false);
  showFixedIncomeDetail = signal(false);
  showDividends = signal(false);

  /** Formulário de lançamento de provento recebido. */
  dividendForm = signal<DividendPayload>({
    ticker: '',
    paid_at: new Date().toISOString().slice(0, 10),
    amount: 0,
    kind: 'dividendo',
  });
  savingDividend = signal(false);
  expandedReasonsTicker = signal<string | null>(null);
  composicaoMode = signal<'ativo' | 'setor'>('ativo');

  sellModal = signal<{ position: PortfolioPosition; quantity: number; price: number } | null>(null);
  sellingInProgress = signal(false);

  lastEvaluatedLabel = computed(() => {
    const t = this.lastEvaluatedAt();
    return t ? new Date(t).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '';
  });

  /**
   * Ordenação da tabela de posições.
   *
   * Não havia tabela ordenável, seleção múltipla para comparar nem exportação —
   * tudo natural em desktop e ausente, apesar de o `/compare` já aceitar 4
   * tickers.
   */
  sortColumn = signal<PositionSortColumn>('current_value');
  sortDirection = signal<'asc' | 'desc'>('desc');
  selectedTickers = signal<string[]>([]);

  private readonly unsorted = computed(() => this.evaluation()?.positions ?? []);

  /** Posições negociadas (a renda fixa vem da própria tabela), ordenadas. */
  tradedPositions = computed(() => {
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

  /** Até 4 tickers, que é o limite do endpoint /compare. */
  readonly maxCompare = 4;

  toggleSort(column: PositionSortColumn): void {
    if (this.sortColumn() === column) {
      this.sortDirection.update(d => (d === 'asc' ? 'desc' : 'asc'));
      return;
    }
    this.sortColumn.set(column);
    this.sortDirection.set(column === 'ticker' || column === 'verdict' ? 'asc' : 'desc');
  }

  sortIcon(column: PositionSortColumn): string {
    if (this.sortColumn() !== column) return 'chevrons-up-down';
    return this.sortDirection() === 'asc' ? 'chevron-up' : 'chevron-down';
  }

  isSelected(ticker: string): boolean {
    return this.selectedTickers().includes(ticker);
  }

  toggleSelection(ticker: string): void {
    this.selectedTickers.update(current => {
      if (current.includes(ticker)) return current.filter(t => t !== ticker);
      if (current.length >= this.maxCompare) {
        this.snackbar.showError(`A comparação aceita no máximo ${this.maxCompare} ativos.`);
        return current;
      }
      return [...current, ticker];
    });
  }

  clearSelection(): void {
    this.selectedTickers.set([]);
  }

  compareSelected(): void {
    const tickers = this.selectedTickers();
    if (tickers.length < 2) {
      this.snackbar.showError('Selecione ao menos dois ativos para comparar.');
      return;
    }
    this.router.navigate(['/market'], {
      queryParams: { tab: 'ferramentas', tool: 'comparar', tickers: tickers.join(',') },
    });
  }

  /**
   * Exporta a carteira em CSV.
   *
   * Separador `;` e vírgula decimal: é o que o Excel em pt-BR abre sem pedir
   * assistente de importação.
   */
  exportCsv(): void {
    const rows: string[][] = [
      [
        'Ativo',
        'Nome',
        'Tipo',
        'Quantidade',
        'Preco medio',
        'Preco atual',
        'Preco justo',
        'Investido',
        'Valor atual',
        'Rendimento %',
        'Veredito',
        'Setor',
      ],
    ];

    for (const p of this.tradedPositions()) {
      rows.push([
        p.ticker,
        p.name ?? '',
        this.ui.assetTypeLabel(p.asset_type),
        this.num(p.quantity),
        this.num(p.avg_price),
        this.num(p.current_price),
        this.num(p.fair_price),
        this.num(p.invested),
        this.num(p.current_value),
        this.num(p.pnl_pct),
        p.label,
        p.sector ? this.ui.translateSector(p.sector) : '',
      ]);
    }

    for (const item of this.fixedIncomePositions()) {
      rows.push([
        item.nome,
        `${item.tipo} · ${item.taxa_anual_efetiva_pct.toFixed(2)}% a.a.`,
        'Renda Fixa',
        '1',
        this.num(item.valor_investido),
        this.num(item.valor_atual),
        '',
        this.num(item.valor_investido),
        this.num(item.valor_atual),
        this.num(item.rendimento_pct),
        'Manter',
        'Renda Fixa',
      ]);
    }

    const csv = rows
      .map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(';'))
      .join('\r\n');

    // BOM para o Excel reconhecer UTF-8.
    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `carteira-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  private num(value: number | null | undefined): string {
    if (value == null) return '';
    return value.toFixed(2).replace('.', ',');
  }

  fixedIncomePositions = computed(() => (this.fixedIncome()?.items ?? []).filter(i => !i.oculto));

  hiddenFixedIncome = computed(() => (this.fixedIncome()?.items ?? []).filter(i => i.oculto));

  totalInvestido = computed(
    () => (this.evaluation()?.total_invested ?? 0) + (this.fixedIncome()?.total_investido ?? 0)
  );

  valorAtual = computed(
    () => (this.evaluation()?.total_current ?? 0) + (this.fixedIncome()?.total_atual ?? 0)
  );

  rendimentoTotal = computed(() => this.valorAtual() - this.totalInvestido());

  rendimentoPct = computed(() => {
    const invested = this.totalInvestido();
    return invested === 0 ? 0 : (this.rendimentoTotal() / invested) * 100;
  });

  negociadosCount = computed(() => this.tradedPositions().length);
  rendaFixaCount = computed(() => this.fixedIncomePositions().length);
  totalAtivos = computed(() => this.negociadosCount() + this.rendaFixaCount());

  isEmpty = computed(() => !this.hasStoredAssets() && this.rendaFixaCount() === 0);

  goalTargetByCategory = computed(() => {
    const map = new Map<string, number>();
    for (const g of this.goals()) map.set(g.category, g.target_pct);
    return map;
  });

  goalTargetBySector = computed(() => {
    const map = new Map<string, number>();
    for (const sg of this.sectorGoals()) map.set(sg.sector, sg.target_pct);
    return map;
  });

  alocacaoPorTipo = computed(() => {
    const total = this.valorAtual();
    if (total <= 0) return [];

    const buckets = new Map<string, number>();

    const rf = this.fixedIncome()?.total_atual ?? 0;
    if (rf > 0) buckets.set('renda_fixa', rf);

    for (const p of this.tradedPositions()) {
      const valor = p.current_value ?? p.invested;
      buckets.set(p.category_resolved, (buckets.get(p.category_resolved) || 0) + valor);
    }

    const targets = this.goalTargetByCategory();
    return Array.from(buckets.entries())
      .map(([tipo, valor]) => ({
        tipo,
        valor,
        pct: (valor / total) * 100,
        targetPct: targets.get(tipo) ?? null,
      }))
      .sort((a, b) => b.valor - a.valor);
  });

  alocacaoPorSetor = computed(() => {
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

    const MAX_SEGMENTOS = 8;
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

  composicaoSlices = computed(() => {
    const mode = this.composicaoMode();
    const raw =
      mode === 'ativo'
        ? this.alocacaoPorTipo().map(t => ({
            label: this.ui.categoryLabel(t.tipo),
            valor: t.valor,
            pct: t.pct,
            color: this.ui.categoryBarColor(t.tipo),
            icon: this.ui.categoryIcon(t.tipo),
          }))
        : this.alocacaoPorSetor().map(s => ({
            label: s.setor,
            valor: s.valor,
            pct: s.pct,
            color: this.ui.sectorSeriesColor(s.setor),
            icon: this.ui.sectorIcon(s.setor),
          }));

    let acc = 0;
    return raw.map(r => {
      const start = acc;
      acc += r.pct;
      return { ...r, start, end: acc };
    });
  });

  conicGradient = computed(() => {
    const slices = this.composicaoSlices();
    if (slices.length === 0) return 'none';
    return `conic-gradient(${slices.map(s => `${s.color} ${s.start}% ${s.end}%`).join(', ')})`;
  });

  /** Vencimentos dentro de 30 dias — impossível antes: a data não existia no servidor. */
  vencimentosProximos = computed(() =>
    this.fixedIncomePositions()
      .filter(i => i.vencimento_proximo)
      .sort((a, b) => (a.dias_para_vencimento ?? 0) - (b.dias_para_vencimento ?? 0))
  );

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loadFailed.set(false);
    this.loadFixedIncome();
    this.loadClosedTrades();
    this.loadDividends();
    this.svc.getGoals().subscribe({ next: g => this.goals.set(g), error: () => {} });
    this.svc.getSectorGoals().subscribe({ next: sg => this.sectorGoals.set(sg), error: () => {} });
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
          res.items.map(i => ({
            ticker: i.ticker,
            quantity: i.quantity,
            avg_price: i.avg_price,
          }))
        );
      },
      error: () => {
        this.loadFailed.set(true);
      },
    });
  }

  private evaluate(items: { ticker: string; quantity: number; avg_price: number }[]): void {
    this.evaluating.set(true);
    this.svc.evaluatePortfolio({ items }).subscribe({
      next: res => {
        this.evaluation.set(res);
        this.lastEvaluatedAt.set(Date.now());
        this.evaluating.set(false);
        // A estimativa depende da carteira avaliada; recarrega para o
        // comparativo recebido-vs-estimado ficar correto.
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

  /**
   * Proventos efetivamente creditados.
   *
   * Todo número de renda no produto era estimativa derivada de DY; aqui a
   * estimativa mensal do próprio app é passada para o backend confrontar com o
   * recebido de fato.
   */
  loadDividends(): void {
    const estimate = this.estimatedMonthlyIncome();
    this.svc.getDividendsReceived(estimate ?? undefined).subscribe({
      next: res => this.dividends.set(res),
      error: () => {},
    });
  }

  /** Renda mensal estimada pela carteira (DY das posições + renda fixa). */
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

  updateDividendField(patch: Partial<DividendPayload>): void {
    this.dividendForm.update(current => ({ ...current, ...patch }));
  }

  saveDividend(): void {
    const form = this.dividendForm();
    if (!form.ticker.trim() || !form.paid_at || form.amount <= 0) {
      this.snackbar.showError('Informe ticker, data do crédito e valor recebido.');
      return;
    }

    this.savingDividend.set(true);
    this.svc
      .createDividendReceived({ ...form, ticker: form.ticker.trim().toUpperCase() })
      .subscribe({
        next: () => {
          this.savingDividend.set(false);
          this.snackbar.showSuccess('Provento registrado.');
          this.dividendForm.set({
            ticker: '',
            paid_at: new Date().toISOString().slice(0, 10),
            amount: 0,
            kind: 'dividendo',
          });
          this.loadDividends();
        },
        error: err => {
          this.savingDividend.set(false);
          this.snackbar.showError(err?.error?.detail || 'Não foi possível registrar o provento.');
        },
      });
  }

  deleteDividend(id: number): void {
    this.svc.deleteDividendReceived(id).subscribe({
      next: () => this.loadDividends(),
      error: () => this.snackbar.showError('Não foi possível remover o lançamento.'),
    });
  }

  /** Rótulo da comparação entre recebido e estimado. */
  estimateAccuracyLabel(): string {
    const data = this.dividends();
    if (!data?.estimate_accuracy_pct) return '';

    const pct = data.estimate_accuracy_pct;
    if (pct >= 95 && pct <= 105) return 'a estimativa está batendo com o recebido';
    if (pct > 105) return `você recebeu ${Math.round(pct - 100)}% mais que o estimado`;
    return `você recebeu ${Math.round(100 - pct)}% menos que o estimado`;
  }

  categoryLabel(category: string): string {
    return this.ui.categoryLabel(category);
  }

  setComposicaoMode(mode: 'ativo' | 'setor'): void {
    this.composicaoMode.set(mode);
  }

  toggleReasons(ticker: string): void {
    this.expandedReasonsTicker.set(this.expandedReasonsTicker() === ticker ? null : ticker);
  }

  rfTipoLabel(tipo: RendaFixaTipo | string): string {
    const labels: Record<string, string> = {
      cdb: 'CDB',
      lci: 'LCI',
      lca: 'LCA',
      tesouro_selic: 'Tesouro Selic',
      tesouro_ipca: 'Tesouro IPCA+',
      tesouro_pre: 'Tesouro Pré',
      lc: 'LC',
      cri: 'CRI',
      cra: 'CRA',
    };
    return labels[tipo] || tipo;
  }

  liquidezLabel(liquidez: string): string {
    return liquidez === 'diaria' ? 'Liquidez diária' : 'No vencimento';
  }

  trackFixedIncome(_: number, item: FixedIncomePosition): number {
    return item.id;
  }

  // --- venda -------------------------------------------------------------

  openSellModal(p: PortfolioPosition): void {
    this.sellModal.set({
      position: p,
      quantity: p.quantity,
      price: p.current_price ?? p.avg_price,
    });
  }

  closeSellModal(): void {
    if (this.sellingInProgress()) return;
    this.sellModal.set(null);
  }

  updateSellQuantity(quantity: number): void {
    const modal = this.sellModal();
    if (modal) this.sellModal.set({ ...modal, quantity });
  }

  updateSellPrice(price: number): void {
    const modal = this.sellModal();
    if (modal) this.sellModal.set({ ...modal, price });
  }

  confirmSell(): void {
    const modal = this.sellModal();
    if (!modal) return;

    const { position, quantity, price } = modal;
    if (quantity <= 0 || quantity > position.quantity || price <= 0) {
      this.snackbar.showError('Quantidade ou preço de venda inválidos.');
      return;
    }

    this.sellingInProgress.set(true);
    this.svc.sellPosition({ ticker: position.ticker, quantity, sell_price: price }).subscribe({
      next: trade => {
        this.sellingInProgress.set(false);
        this.sellModal.set(null);
        const lucro = trade.net_profit >= 0 ? 'lucro' : 'prejuízo';
        this.snackbar.showSuccess(
          `Venda registrada: ${lucro} líquido de R$ ${Math.abs(trade.net_profit).toFixed(2)}` +
            (trade.ir_amount > 0 ? ` (IR: R$ ${trade.ir_amount.toFixed(2)})` : '')
        );
        this.loadClosedTrades();
        this.loadAndEvaluate();
      },
      error: err => {
        this.sellingInProgress.set(false);
        this.snackbar.showError(err?.error?.detail || 'Erro ao registrar venda.');
      },
    });
  }
}
