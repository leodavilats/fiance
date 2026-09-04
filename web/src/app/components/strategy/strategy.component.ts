import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  InvestmentStrategy,
  LoadingService,
  RecommendService,
  UiHelperService,
  allocationScalePct,
} from '../../core';
import { AllocationGapComponent } from '../allocation-gap/allocation-gap.component';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { RebalanceSuggestionsComponent } from '../market/rebalance-suggestions/rebalance-suggestions.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';
import { PageHeaderComponent } from '../page-header/page-header.component';

/** Uma linha da comparação atual × projetada, já pareada por categoria. */
interface ProjectionRow {
  readonly category: string;
  readonly currentPct: number;
  readonly projectedPct: number;
}

@Component({
  selector: 'app-strategy',
  standalone: true,
  imports: [
    PageHeaderComponent,
    AllocationGapComponent,
    CommonModule,
    EmptyStateComponent,
    LucideAngularModule,
    RebalanceSuggestionsComponent,
    RouterLink,
    SkeletonComponent,
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

  /**
   * O perfil de risco é uma escolha da pessoa, não um veredito sobre ela.
   *
   * "Alto" vinha em `tag-adverse`, vermelho — o produto pintando a preferência
   * do usuário como problema. `.tag` passa a carregar só fato; julgamento é
   * `verdict-pill`, e nenhum dos dois se aplica a uma configuração.
   */
  riskClass(): string {
    return 'tag-neutral';
  }

  /**
   * Soma dos aportes sugeridos, ou null quando o valor foi retido.
   *
   * `affirmation.apply` anula `invest_amount` fora do modo prescritivo. Somar
   * com null daria NaN na tela, e tratar null como zero seria pior: afirmaria um
   * total menor do que o que está sugerido logo abaixo.
   */
  totalToInvest(s: InvestmentStrategy): number | null {
    if (s.suggestions.some(x => x.invest_amount === null)) return null;
    return s.suggestions.reduce((sum, x) => sum + (x.invest_amount ?? 0), 0);
  }

  cashPct(s: InvestmentStrategy): number {
    return s.total_capital > 0 ? (s.cash_available / s.total_capital) * 100 : 0;
  }

  absValue(v: number): number {
    return Math.abs(v);
  }

  /**
   * Atual e projetada na mesma linha, por categoria.
   *
   * Antes eram duas colunas independentes, o que obrigava o olho a procurar a
   * mesma categoria nos dois lados para responder "mudou quanto?". Categoria
   * que só existe de um lado entra com 0 no outro — é informação, não ausência.
   */
  projection(s: InvestmentStrategy): ProjectionRow[] {
    const current = new Map(s.current_allocation.map(a => [a.category, a.current_pct]));
    const projected = new Map(s.projected_allocation.map(a => [a.category, a.projected_pct]));
    const categories = [...new Set([...current.keys(), ...projected.keys()])];

    return categories
      .map(category => ({
        category,
        currentPct: current.get(category) ?? 0,
        projectedPct: projected.get(category) ?? 0,
      }))
      .sort((a, b) => b.projectedPct - a.projectedPct);
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

  gapScalePct(gaps: { current_pct: number; target_pct: number }[]): number {
    return allocationScalePct(
      gaps.map(g => ({ currentPct: g.current_pct, targetPct: g.target_pct }))
    );
  }

  getCategoryBarColor(category: string): string {
    return this.ui.categoryBarColor(category);
  }
}
