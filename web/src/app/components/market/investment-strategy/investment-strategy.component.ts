import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, output, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import {
  InvestmentStrategy,
  LoadingService,
  RecommendService,
  UiHelperService,
} from '../../../core';

@Component({
  selector: 'app-investment-strategy',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './investment-strategy.component.html',
})
export class InvestmentStrategyComponent implements OnInit {
  private api = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  readonly goToRendaFixa = output<void>();

  strategy = signal<InvestmentStrategy | null>(null);

  ngOnInit(): void {
    this.loadStrategy();
  }

  loadStrategy(): void {
    this.api.getStrategy().subscribe({
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
    return this.ui.assetTypeLabel(type as any);
  }

  getCategoryBarColor(category: string): string {
    return this.ui.categoryBarColor(category);
  }
}
