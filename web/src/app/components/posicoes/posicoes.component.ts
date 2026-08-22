import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CarteiraStore,
  FixedIncomePosition,
  MAX_COMPARE,
  PortfolioPosition,
  PositionSortColumn,
  RecommendService,
  RendaFixaTipo,
  SnackbarService,
  UiHelperService,
} from '../../core';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';

@Component({
  selector: 'app-posicoes',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule, RouterLink, HelpTooltipComponent],
  templateUrl: './posicoes.component.html',
  styleUrls: ['./posicoes.component.scss'],
})
export class PosicoesComponent implements OnInit {
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

  readonly showFixedIncomeDetail = signal(true);
  readonly expandedReasonsTicker = signal<string | null>(null);
  readonly sellModal = signal<{
    position: PortfolioPosition;
    quantity: number;
    price: number;
  } | null>(null);
  readonly sellingInProgress = signal(false);

  ngOnInit(): void {
    this.store.ensureLoaded();
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
