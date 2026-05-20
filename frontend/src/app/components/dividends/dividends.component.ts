import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { DividendRankingItem, LoadingService, RecommendService, UiHelperService } from '../../core';

interface DividendsForm {
  universe: FormControl<string>;
  top: FormControl<number>;
}

@Component({
  selector: 'app-dividends',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <form class="p-5 rounded-lg bg-panel border border-border" [formGroup]="form" (ngSubmit)="submit()">
      <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx"><lucide-icon name="dollar-sign" size="18"></lucide-icon> Top pagadoras de dividendos</h2>
      <p class="text-sm text-muted mb-4">Ranqueia pelo DY dos últimos 12 meses.</p>
      <div class="grid grid-cols-1 sm:grid-cols-[2fr_1fr] gap-4">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Universo (opcional, separado por vírgula)</label>
          <input type="text" class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" formControlName="universe" placeholder="ex.: TAEE11, BBAS3, ITSA4" />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Top N</label>
          <input type="number" class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" formControlName="top" min="1" max="50" />
        </div>
      </div>
      <div class="flex items-center gap-3 mt-4">
        <button class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity" type="submit" [disabled]="loading.loading()">
          <lucide-icon [name]="loading.loading() ? 'loader-circle' : 'search'" size="16"></lucide-icon>
          {{ loading.loading() ? 'Buscando...' : 'Buscar ranking' }}
        </button>
      </div>
    </form>

    @if (result(); as d) {
      <div class="p-5 rounded-lg bg-panel border border-border">
        <h2 class="text-xl font-bold m-0 mb-4 text-tx">Ranking</h2>
        <div style="overflow-x:auto;">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-border">
                <th class="text-left py-2 px-2 font-medium text-muted">#</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Ativo</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Setor</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Preço</th>
                <th class="text-right py-2 px-2 font-medium text-muted">DY 12m</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Justo (Bazin)</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Bazin diz</th>
              </tr>
            </thead>
            <tbody>
              @for (it of d; track it.ticker; let i = $index) {
                <tr class="border-b border-border hover:bg-bg-2 transition-colors">
                  <td class="py-2 px-2 text-tx">{{ i + 1 }}</td>
                  <td class="py-2 px-2">
                    <div class="font-semibold text-tx">{{ it.ticker }}</div>
                    <div class="text-xs text-muted">{{ it.name }}</div>
                  </td>
                  <td class="py-2 px-2">
                    <span class="tag">{{ ui.translateSector(it.sector) }}</span>
                  </td>
                  <td class="text-right py-2 px-2 text-tx">{{ it.price != null ? (it.price | number: '1.2-2') : '—' }}</td>
                  <td class="text-right py-2 px-2">
                    <span class="score-pill" [class]="ui.dyClass(it.dividend_yield_12m)">{{ it.dividend_yield_12m | number: '1.2-2' }}%</span>
                  </td>
                  <td class="text-right py-2 px-2 text-tx">{{ it.fair_price_bazin != null ? (it.fair_price_bazin | number: '1.2-2') : '—' }}</td>
                  <td class="py-2 px-2">
                    @if (it.verdict) {
                      <span class="verdict-pill" [class]="ui.verdictClass(ui.verdictFromLabel(it.verdict))">{{ it.verdict }}</span>
                    } @else { — }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    }
  `,
})
export class DividendsComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  result = signal<DividendRankingItem[] | null>(null);

  form: FormGroup<DividendsForm> = this.fb.group({
    universe: this.fb.control('TAEE11, ITSA4, BBAS3, VALE3, BBSE3, CPLE6, CMIG4, KLBN11', { nonNullable: true }),
    top: this.fb.control(15, { nonNullable: true, validators: [Validators.min(1), Validators.max(50)] }),
  });

  ngOnInit(): void {}

  submit(): void {
    const { universe, top } = this.form.getRawValue();
    this.svc.dividendsRanking(universe || undefined, top).subscribe({
      next: (res) => {
        this.result.set(res.items);
      },
      error: () => {},
      complete: () => {},
    });
  }
}
