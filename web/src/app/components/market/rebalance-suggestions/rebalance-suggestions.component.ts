import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import {
  RebalanceAction,
  RebalanceSuggestionsResponse,
  RecommendService,
  UiHelperService,
} from '../../../core';

@Component({
  selector: 'app-rebalance-suggestions',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './rebalance-suggestions.component.html',
})
export class RebalanceSuggestionsComponent implements OnInit {
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);

  readonly rebalance = signal<RebalanceSuggestionsResponse | null>(null);
  readonly loading = signal(false);
  readonly error = signal(false);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(false);
    this.svc.getRebalanceSuggestions().subscribe({
      next: data => {
        this.rebalance.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  verdictClass(v: string): string {
    if (v === 'STRONG_BUY' || v === 'BUY') return 'v-buy';
    if (v === 'STRONG_SELL' || v === 'SELL') return 'v-sell';
    if (v === 'HOLD') return 'v-hold';
    return 'v-unknown';
  }

  actionLabel(action: RebalanceAction): string {
    return (
      {
        comprar_mais: 'Comprar mais',
        vender: 'Vender',
        realocar: 'Realocar',
        manter: 'Não fazer nada',
      }[action] || action
    );
  }

  actionClass(action: RebalanceAction): string {
    return (
      {
        comprar_mais: 'bg-brand/20 text-brand border-brand/30',
        vender: 'bg-adverse/20 text-adverse border-adverse/30',
        realocar: 'bg-attention/20 text-attention border-attention/30',
        manter: 'bg-ground-2 text-ink-2 border-hairline',
      }[action] || 'bg-ground-2 text-ink-2 border-hairline'
    );
  }
}
