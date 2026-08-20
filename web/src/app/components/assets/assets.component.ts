import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import {
  ClosedTradesResponse,
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
  readonly loading = inject(LoadingService);
  readonly ui = inject(UiHelperService);

  evaluation = signal<PortfolioEvaluationResponse | null>(null);
  fixedIncome = signal<FixedIncomeListResponse | null>(null);
  closedTrades = signal<ClosedTradesResponse | null>(null);
  goals = signal<Goal[]>([]);
  sectorGoals = signal<SectorGoal[]>([]);

  loadFailed = signal(false);
  evaluating = signal(false);
  lastEvaluatedAt = signal<number | null>(null);
  hasStoredAssets = signal(false);

  showClosedTrades = signal(false);
  showFixedIncomeDetail = signal(false);
  expandedReasonsTicker = signal<string | null>(null);
  composicaoMode = signal<'ativo' | 'setor'>('ativo');

  sellModal = signal<{ position: PortfolioPosition; quantity: number; price: number } | null>(null);
  sellingInProgress = signal(false);

  lastEvaluatedLabel = computed(() => {
    const t = this.lastEvaluatedAt();
    return t ? new Date(t).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '';
  });

  /** Posições negociadas (a renda fixa vem da própria tabela). */
  tradedPositions = computed(() => this.evaluation()?.positions ?? []);

  fixedIncomePositions = computed(() =>
    (this.fixedIncome()?.items ?? []).filter(i => !i.oculto)
  );

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
