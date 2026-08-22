import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import {
  FollowedSuggestionPayload,
  FollowedSuggestionsResponse,
  RecommendService,
  SnackbarService,
} from '../../../core';

@Component({
  selector: 'app-followed-suggestions',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './followed-suggestions.component.html',
})
export class FollowedSuggestionsComponent implements OnInit {
  private readonly svc = inject(RecommendService);
  private readonly snackbar = inject(SnackbarService);

  data = signal<FollowedSuggestionsResponse | null>(null);
  showForm = signal(false);
  saving = signal(false);

  form = signal<FollowedSuggestionPayload>({
    ticker: '',
    source: 'opportunities',
    action: 'comprar',
    quantity: 0,
    price: 0,
    followed_on: new Date().toISOString().slice(0, 10),
  });

  readonly sources = [
    { value: 'opportunities', label: 'Oportunidades' },
    { value: 'rebalance', label: 'Sugestões de ajuste' },
    { value: 'quick_invest', label: 'Quick Invest' },
    { value: 'strategy', label: 'Estratégia' },
    { value: 'dip_scanner', label: 'Scanner de quedas' },
    { value: 'whats_new', label: 'O que mudou' },
  ];

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.svc.getFollowedSuggestions().subscribe({
      next: res => this.data.set(res),
      error: () => {},
    });
  }

  updateField(patch: Partial<FollowedSuggestionPayload>): void {
    this.form.update(current => ({ ...current, ...patch }));
  }

  save(): void {
    const form = this.form();
    if (!form.ticker.trim() || form.quantity <= 0 || form.price <= 0) {
      this.snackbar.showError('Informe ticker, quantidade e preço executado.');
      return;
    }

    this.saving.set(true);
    this.svc
      .registerFollowedSuggestion({ ...form, ticker: form.ticker.trim().toUpperCase() })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.snackbar.showSuccess('Registrado. O resultado aparece aqui a partir de agora.');
          this.form.set({
            ticker: '',
            source: 'opportunities',
            action: 'comprar',
            quantity: 0,
            price: 0,
            followed_on: new Date().toISOString().slice(0, 10),
          });
          this.showForm.set(false);
          this.load();
        },
        error: err => {
          this.saving.set(false);
          this.snackbar.showError(err?.error?.detail || 'Não foi possível registrar.');
        },
      });
  }

  remove(id: number): void {
    this.svc.deleteFollowedSuggestion(id).subscribe({
      next: () => this.load(),
      error: () => this.snackbar.showError('Não foi possível remover o registro.'),
    });
  }

  sourceLabel(source: string): string {
    return this.sources.find(s => s.value === source)?.label ?? source;
  }
}
