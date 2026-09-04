import { CommonModule } from '@angular/common';
import { PendingDividendsComponent } from '../pending-dividends/pending-dividends.component';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { CarteiraStore, DividendPayload, RecommendService, SnackbarService } from '../../core';
import { PageHeaderComponent } from '../page-header/page-header.component';

@Component({
  selector: 'app-dividends',
  standalone: true,
  imports: [
    PageHeaderComponent,
    CommonModule,
    FormsModule,
    LucideAngularModule,
    PendingDividendsComponent,
  ],
  templateUrl: './dividends.component.html',
})
export class DividendsComponent implements OnInit {
  private readonly store = inject(CarteiraStore);
  private readonly svc = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);

  readonly dividends = this.store.dividends;
  readonly showDividends = signal(true);
  readonly savingDividend = signal(false);

  readonly dividendForm = signal<DividendPayload>({
    ticker: '',
    paid_at: new Date().toISOString().slice(0, 10),
    amount: 0,
    kind: 'dividendo',
  });

  ngOnInit(): void {
    this.store.ensureLoaded();
  }

  updateDividendField(patch: Partial<DividendPayload>): void {
    this.dividendForm.update(current => ({ ...current, ...patch }));
  }

  saveDividend(): void {
    const form = this.dividendForm();
    if (!form.ticker.trim() || !form.paid_at || form.amount <= 0) {
      this.snackbar.showError('Informe ticker, data do crédito e valor recebido.');
      return;
    }

    this.savingDividend.set(true);
    this.svc
      .createDividendReceived({ ...form, ticker: form.ticker.trim().toUpperCase() })
      .subscribe({
        next: () => {
          this.savingDividend.set(false);
          this.snackbar.showSuccess('Provento registrado.');
          this.dividendForm.set({
            ticker: '',
            paid_at: new Date().toISOString().slice(0, 10),
            amount: 0,
            kind: 'dividendo',
          });
          this.store.loadDividends();
        },
        error: err => {
          this.savingDividend.set(false);
          this.snackbar.showError(err?.error?.detail || 'Não foi possível registrar o provento.');
        },
      });
  }

  deleteDividend(id: number): void {
    this.svc.deleteDividendReceived(id).subscribe({
      next: () => this.store.loadDividends(),
      error: () => this.snackbar.showError('Não foi possível remover o lançamento.'),
    });
  }

  estimateAccuracyLabel(): string {
    const data = this.dividends();
    if (!data?.estimate_accuracy_pct) return '';

    const pct = data.estimate_accuracy_pct;
    if (pct >= 95 && pct <= 105) return 'a estimativa está batendo com o recebido';
    if (pct > 105) return `você recebeu ${Math.round(pct - 100)}% mais que o estimado`;
    return `você recebeu ${Math.round(100 - pct)}% menos que o estimado`;
  }
}
