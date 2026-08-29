import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CarteiraStore,
  DensityService,
  FiDensity,
  FixedIncomePosition,
  MAX_COMPARE,
  POSITION_COLUMNS,
  PortfolioPosition,
  PositionSortColumn,
  RecommendService,
  RendaFixaTipo,
  SnackbarService,
  UiHelperService,
  parseColumns,
} from '../../core';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';

@Component({
  selector: 'app-posicoes',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule, RouterLink, HelpTooltipComponent],
  templateUrl: './posicoes.component.html',
})
export class PosicoesComponent implements OnInit {
  private readonly densidade = inject(DensityService);
  private readonly store = inject(CarteiraStore);
  private readonly svc = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);
  private readonly router = inject(Router);
  readonly ui = inject(UiHelperService);

  readonly tradedPositions = this.store.tradedPositions;
  readonly fixedIncome = this.store.fixedIncome;
  readonly fixedIncomePositions = this.store.fixedIncomePositions;
  readonly hiddenFixedIncome = this.store.hiddenFixedIncome;
  readonly vencimentosProximos = this.store.vencimentosProximos;
  readonly negociadosCount = this.store.negociadosCount;
  readonly selectedTickers = this.store.selectedTickers;

  readonly maxCompare = MAX_COMPARE;

  /**
   * Colunas e densidade moram na URL junto com a ordenação: a tabela de maior
   * densidade do produto é justamente a que se compartilha por link, e um
   * recorte que não sobrevive ao recarregar não é um recorte (§45).
   */
  readonly allColumns = POSITION_COLUMNS;
  readonly visibleColumns = signal<string[]>([]);
  readonly density = signal<FiDensity>('comfortable');

  readonly columns = computed(() =>
    POSITION_COLUMNS.filter(c => this.visibleColumns().includes(c.id as string))
  );

  readonly showFixedIncomeDetail = signal(true);
  readonly expandedReasonsTicker = signal<string | null>(null);
  readonly sellModal = signal<{
    position: PortfolioPosition;
    quantity: number;
    price: number;
  } | null>(null);
  readonly sellingInProgress = signal(false);

  private readonly route = inject(ActivatedRoute);

  ngOnInit(): void {
    this.store.ensureLoaded();

    const q = this.route.snapshot.queryParamMap;
    this.visibleColumns.set(parseColumns(q.get('cols')));

    const daUrl = q.get('d');
    this.density.set(
      daUrl === 'compact' || daUrl === 'comfortable' ? daUrl : this.densidade.density()
    );
  }

  private syncUrl(): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        cols: this.visibleColumns().join(','),
        d: this.density() === 'compact' ? 'compact' : null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  setDensity(density: FiDensity): void {
    this.density.set(density);
    this.syncUrl();
  }

  isColumnVisible(id: string): boolean {
    return this.visibleColumns().includes(id);
  }

  toggleColumn(id: string): void {
    const column = POSITION_COLUMNS.find(c => c.id === id);
    if (!column || column.essential) return;
    const next = this.isColumnVisible(id)
      ? this.visibleColumns().filter(c => c !== id)
      : [...this.visibleColumns(), id];
    this.visibleColumns.set(parseColumns(next.join(',')));
    this.syncUrl();
  }

  /**
   * `weight` e `margin` são derivadas e não têm coluna correspondente na
   * ordenação do store; caem no eixo mais próximo em vez de virar um `if` no
   * template.
   */
  sortableId(id: string): PositionSortColumn {
    if (id === 'weight') return 'current_value';
    if (id === 'margin') return 'fair_price';
    return id as PositionSortColumn;
  }

  ariaSort(id: string): 'ascending' | 'descending' | 'none' {
    if (this.store.sortColumn() !== this.sortableId(id)) return 'none';
    return this.store.sortDirection() === 'asc' ? 'ascending' : 'descending';
  }

  dash(value: number | null | undefined): string {
    return value == null
      ? '—'
      : value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  /** Peso da posição no total negociado. Sem total, não há peso — não há zero. */
  weightLabel(p: PortfolioPosition): string {
    const total = this.tradedPositions().reduce((sum, x) => sum + (x.current_value ?? 0), 0);
    if (total <= 0 || p.current_value == null) return '—';
    return `${((p.current_value / total) * 100).toFixed(1)}%`;
  }

  /**
   * Quanto o papel rende, comparado ao CDI quando o backend souber dizer.
   * Taxa nua não é resposta (§16).
   */
  rendeLabel(item: FixedIncomePosition): string {
    const pct = item.pct_cdi_equivalente;
    if (pct != null) return `~${pct.toFixed(0)}% do CDI`;
    return `${item.taxa_anual_efetiva_pct.toFixed(2)}% a.a.`;
  }

  toggleSort(column: PositionSortColumn): void {
    this.store.toggleSort(column);
  }

  sortIcon(column: PositionSortColumn): string {
    return this.store.sortIcon(column);
  }

  isSelected(ticker: string): boolean {
    return this.store.isSelected(ticker);
  }

  toggleSelection(ticker: string): void {
    this.store.toggleSelection(ticker);
  }

  clearSelection(): void {
    this.store.clearSelection();
  }

  compareSelected(): void {
    const tickers = this.selectedTickers();
    if (tickers.length < 2) {
      this.snackbar.showError('Selecione ao menos dois ativos para comparar.');
      return;
    }
    this.router.navigate(['/descobrir/comparar'], {
      queryParams: { tickers: tickers.join(',') },
    });
  }

  toggleReasons(ticker: string): void {
    this.expandedReasonsTicker.set(this.expandedReasonsTicker() === ticker ? null : ticker);
  }

  rfTipoLabel(tipo: RendaFixaTipo | string): string {
    return this.ui.fixedIncomeTypeLabel(tipo);
  }

  liquidezLabel(liquidez: string): string {
    return this.ui.liquidityLabel(liquidez);
  }

  trackFixedIncome(_: number, item: FixedIncomePosition): number {
    return item.id;
  }

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
        item.tipo + ' · ' + item.taxa_anual_efetiva_pct.toFixed(2) + '% a.a.',
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
      .map(row => row.map(cell => '"' + cell.replace(/"/g, '""') + '"').join(';'))
      .join('\r\n');

    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'carteira-' + new Date().toISOString().slice(0, 10) + '.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  private num(value: number | null | undefined): string {
    if (value == null) return '';
    return value.toFixed(2).replace('.', ',');
  }

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
        const ir = trade.ir_amount > 0 ? ' (IR: R$ ' + trade.ir_amount.toFixed(2) + ')' : '';
        this.snackbar.showSuccess(
          'Venda registrada: ' +
            lucro +
            ' líquido de R$ ' +
            Math.abs(trade.net_profit).toFixed(2) +
            ir
        );
        this.store.loadClosedTrades();
        this.store.reloadPositions();
      },
      error: err => {
        this.sellingInProgress.set(false);
        this.snackbar.showError(err?.error?.detail || 'Erro ao registrar venda.');
      },
    });
  }
}
