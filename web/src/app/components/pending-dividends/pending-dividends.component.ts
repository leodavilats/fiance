import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { PendingDividend, RecommendService, SnackbarService } from '../../core';
import { ProvenanceComponent } from '../provenance/provenance.component';

@Component({
  selector: 'app-pending-dividends',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, ProvenanceComponent],
  templateUrl: './pending-dividends.component.html',
})
export class PendingDividendsComponent implements OnInit {
  private readonly api = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);

  readonly pending = signal<PendingDividend[]>([]);
  readonly note = signal('');
  readonly loading = signal(true);
  readonly confirming = signal(false);

  readonly selected = signal<Set<string>>(new Set());

  readonly hasPending = computed(() => this.pending().length > 0);
  readonly selectedCount = computed(() => this.selected().size);

  readonly selectedTotal = computed(() =>
    this.pending()
      .filter(p => this.selected().has(this.keyOf(p)))
      .reduce((soma, p) => soma + p.amount, 0)
  );

  ngOnInit(): void {
    this.load();
  }

  keyOf(item: PendingDividend): string {
    return `${item.ticker}:${item.paid_at}`;
  }

  isSelected(item: PendingDividend): boolean {
    return this.selected().has(this.keyOf(item));
  }

  toggle(item: PendingDividend): void {
    const atual = new Set(this.selected());
    const chave = this.keyOf(item);
    if (atual.has(chave)) atual.delete(chave);
    else atual.add(chave);
    this.selected.set(atual);
  }

  private load(): void {
    this.loading.set(true);
    this.api.getPendingDividends().subscribe({
      next: res => {
        this.pending.set(res.items);
        this.note.set(res.note);
        this.selected.set(new Set());
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  confirm(): void {
    const escolhidos = this.pending().filter(p => this.isSelected(p));
    if (escolhidos.length === 0 || this.confirming()) return;

    this.confirming.set(true);
    this.api
      .confirmPendingDividends(
        escolhidos.map(p => ({
          ticker: p.ticker,
          paid_at: p.paid_at,
          amount: p.amount,
          kind: p.kind,
        }))
      )
      .subscribe({
        next: res => {
          this.confirming.set(false);
          this.snackbar.showSuccess(`${res.created} provento(s) lançados.`);
          this.load();
        },
        error: () => this.confirming.set(false),
      });
  }
}
