import { CommonModule } from '@angular/common';
import { ProvenanceComponent } from '../../provenance/provenance.component';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import {
  IncomeCompareResponse,
  IncomeOption,
  RecommendService,
  UiHelperService,
} from '../../../core';

@Component({
  selector: 'app-income-compare',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule, ProvenanceComponent],
  templateUrl: './income-compare.component.html',
})
export class IncomeCompareComponent implements OnInit {
  private readonly svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);

  amount = signal(10000);
  horizonMonths = signal(12);

  result = signal<IncomeCompareResponse | null>(null);
  loading = signal(false);

  ranked = computed<IncomeOption[]>(() => {
    const data = this.result();
    if (!data) return [];
    return [...data.fixed_income, ...data.assets].sort(
      (a, b) => b.net_income_yield_pct - a.net_income_yield_pct
    );
  });

  ngOnInit(): void {
    this.compare();
  }

  compare(): void {
    this.loading.set(true);
    this.svc.incomeCompare(this.amount(), this.horizonMonths()).subscribe({
      next: res => {
        this.result.set(res);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  kindLabel(kind: string): string {
    const map: Record<string, string> = {
      renda_fixa: 'Renda fixa',
      br_stock: 'Ação BR',
      fii: 'FII',
      bdr: 'BDR',
      etf: 'ETF',
    };
    return map[kind] || kind;
  }

  kindIcon(kind: string): string {
    return this.ui.categoryIcon(
      kind === 'renda_fixa'
        ? 'renda_fixa'
        : kind === 'fii'
          ? 'fiis'
          : kind === 'bdr'
            ? 'bdrs'
            : kind === 'etf'
              ? 'etfs'
              : 'acoes_br'
    );
  }

  liquidityLabel(liquidity: string): string {
    const map: Record<string, string> = {
      diaria: 'Resgate diário',
      no_vencimento: 'Só no vencimento',
      bolsa: 'Venda em bolsa (D+2)',
    };
    return map[liquidity] || liquidity;
  }

  isFixedIncome(option: IncomeOption): boolean {
    return option.kind === 'renda_fixa';
  }
}
