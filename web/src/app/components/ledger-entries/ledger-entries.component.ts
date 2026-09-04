import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, output, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import {
  DerivationResponse,
  DialogDirective,
  RecommendService,
  ReconciliationResponse,
  Transaction,
  TransactionKind,
} from '../../core';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

const KIND_LABEL: Record<TransactionKind, string> = {
  buy: 'Compra',
  sell: 'Venda',
  split: 'Desdobramento',
  bonus: 'Bonificação',
  transfer_in: 'Transferência de entrada',
  transfer_out: 'Transferência de saída',
  amortization: 'Amortização',
  adjust: 'Estado declarado',
};

@Component({
  selector: 'app-ledger-entries',
  standalone: true,
  imports: [
    DialogDirective,
    CommonModule,
    EmptyStateComponent,
    LucideAngularModule,
    SkeletonComponent,
  ],
  templateUrl: './ledger-entries.component.html',
})
export class LedgerEntriesComponent implements OnInit {
  private readonly svc = inject(RecommendService);

  readonly close = output<void>();

  readonly transactions = signal<Transaction[] | null>(null);
  readonly reconciliation = signal<ReconciliationResponse | null>(null);
  readonly errored = signal(false);

  readonly openSymbol = signal<string | null>(null);
  readonly derivation = signal<DerivationResponse | null>(null);
  readonly derivationLoading = signal(false);

  readonly bySymbol = computed(() => {
    const groups = new Map<string, Transaction[]>();
    for (const item of this.transactions() ?? []) {
      const list = groups.get(item.symbol) ?? [];
      list.push(item);
      groups.set(item.symbol, list);
    }
    return [...groups.entries()]
      .map(([symbol, items]) => ({
        symbol,
        items: [...items].sort((a, b) => b.traded_on.localeCompare(a.traded_on) || b.id - a.id),
      }))
      .sort((a, b) => a.symbol.localeCompare(b.symbol));
  });

  readonly isEmpty = computed(() => (this.transactions() ?? []).length === 0);

  ngOnInit(): void {
    this.svc.getTransactions().subscribe({
      next: res => this.transactions.set(res.items),
      error: () => this.errored.set(true),
    });
    this.svc.getReconciliation().subscribe({
      next: res => this.reconciliation.set(res),
      error: () => {},
    });
  }

  kindLabel(kind: TransactionKind): string {
    return KIND_LABEL[kind] ?? kind;
  }

  kindDirectionClass(kind: TransactionKind): string {
    if (kind === 'buy' || kind === 'transfer_in' || kind === 'bonus') return 'text-ink';
    if (kind === 'sell' || kind === 'transfer_out') return 'text-ink-2';
    return 'text-ink-2';
  }

  toggleDerivation(symbol: string): void {
    if (this.openSymbol() === symbol) {
      this.openSymbol.set(null);
      this.derivation.set(null);
      return;
    }

    this.openSymbol.set(symbol);
    this.derivation.set(null);
    this.derivationLoading.set(true);
    this.svc.getDerivation(symbol).subscribe({
      next: res => {
        this.derivation.set(res);
        this.derivationLoading.set(false);
      },
      error: () => this.derivationLoading.set(false),
    });
  }
}
