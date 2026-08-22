import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { InvestmentStrategy, LoadingService, RecommendService, UiHelperService } from '../../core';
import { FollowedSuggestionsComponent } from '../market/followed-suggestions/followed-suggestions.component';
import { RebalanceSuggestionsComponent } from '../market/rebalance-suggestions/rebalance-suggestions.component';

@Component({
  selector: 'app-strategy',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    RouterLink,
    RebalanceSuggestionsComponent,
    FollowedSuggestionsComponent,
  ],
  templateUrl: './strategy.component.html',
})
export class StrategyComponent implements OnInit {
  private readonly svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  readonly strategy = signal<InvestmentStrategy | null>(null);

  ngOnInit(): void {
    this.loadStrategy();
  }

  loadStrategy(): void {
    this.svc.getPreferences().subscribe({
      next: prefs => this.fetch(prefs.cash_available ?? 0),
      error: () => this.fetch(0),
    });
  }

  private fetch(cash: number): void {
    this.svc.getStrategy(cash).subscribe({
      next: data => this.strategy.set(data),
      error: () => {},
    });
  }

  riskClass(risk: string): string {
    return { Baixo: 'tag-success', Médio: 'tag-warning', Alto: 'tag-danger' }[risk] || 'tag-muted';
  }

  totalToInvest(s: InvestmentStrategy): number {
    return s.suggestions.reduce((sum, x) => sum + x.invest_amount, 0);
  }

  verdictClassFromString(v: string): string {
    if (v === 'STRONG_BUY' || v === 'BUY') return 'v-buy';
    if (v === 'STRONG_SELL' || v === 'SELL') return 'v-sell';
    if (v === 'HOLD') return 'v-hold';
    return 'v-unknown';
  }

  assetLabel(type: string): string {
    return { br_stock: 'Ação BR', fii: 'FII', bdr: 'BDR', etf: 'ETF' }[type] || type;
  }

  getCategoryBarColor(category: string): string {
    return this.ui.assetTypeSeriesColor(
      { acoes_br: 'br_stock', bdrs: 'bdr', fiis: 'fii', etfs: 'etf', renda_fixa: 'renda_fixa' }[
        category
      ] ?? category
    );
  }
}
