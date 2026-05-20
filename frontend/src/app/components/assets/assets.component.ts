import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, FormArray, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { LoadingService, PortfolioItem, PortfolioEvaluationResponse, RecommendService, UiHelperService } from '../../core';

interface PortfolioItemForm {
  ticker: FormControl<string>;
  quantity: FormControl<number>;
  avg_price: FormControl<number>;
  category: FormControl<'auto' | 'renda' | 'trade'>;
}

interface PortfolioFormShape {
  items: FormArray<FormGroup<PortfolioItemForm>>;
  desired_yield: FormControl<number>;
}

@Component({
  selector: 'app-assets',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <div class="p-5 rounded-lg bg-panel border border-border">
      <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx"><lucide-icon name="briefcase" size="18"></lucide-icon> Meus Ativos</h2>
      <p class="text-sm text-muted mb-4">
        Cadastre suas posições. A categoria define se o ativo é foco de <em>renda</em> (dividendos)
        ou <em>trade/crescimento</em> (valorização). Deixe em "auto" para o sistema sugerir.
      </p>

      <form [formGroup]="form">
        <div class="grid grid-cols-[2fr_1fr_1fr_1.5fr_auto] gap-2 mb-2 text-sm font-medium text-muted">
          <div>Ticker</div>
          <div>Quantidade</div>
          <div>Preço médio</div>
          <div>Categoria</div>
          <div></div>
        </div>
        <div class="flex flex-col gap-2" formArrayName="items">
          @for (item of portfolioItems.controls; track $index; let i = $index) {
            <div class="grid grid-cols-[2fr_1fr_1fr_1.5fr_auto] gap-2 items-center" [formGroupName]="i">
              <input type="text" formControlName="ticker" placeholder="ex.: PETR4" class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" />
              <input type="number" formControlName="quantity" placeholder="qtd" step="0.0001" min="0" class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" />
              <input type="number" formControlName="avg_price" placeholder="preço" step="0.01" min="0" class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" />
              <select formControlName="category" class="px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer">
                <option value="auto">Auto</option>
                <option value="renda">Renda</option>
                <option value="trade">Trade</option>
              </select>
              <button type="button" class="w-9 h-9 grid place-items-center rounded-lg cursor-pointer bg-panel-2 border border-border text-danger hover:bg-danger hover:text-white transition-colors" (click)="removeItem(i)" title="Remover">
                <lucide-icon name="x" size="16"></lucide-icon>
              </button>
            </div>
          }
        </div>
        <div class="flex items-center gap-3 mt-4 flex-wrap">
          <button type="button" class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all" (click)="addItem()">
            <lucide-icon name="plus" size="16"></lucide-icon> Adicionar ativo
          </button>
          <button type="button" class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity" (click)="evaluateAssets()" [disabled]="loading.loading() || portfolioItems.length === 0">
            <lucide-icon [name]="loading.loading() ? 'loader-circle' : 'refresh-cw'" size="16"></lucide-icon>
            {{ loading.loading() ? 'Avaliando...' : 'Avaliar agora' }}
          </button>
        </div>
      </form>
    </div>

    @if (result(); as r) {
      <div class="p-5 rounded-lg bg-panel border border-border">
        <h2 class="text-xl font-bold m-0 mb-3 text-tx">Resumo</h2>
        <p class="leading-relaxed text-sm text-tx">{{ ui.portfolioSummary(r.positions, r.total_pnl, r.total_pnl_pct) }}</p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
          <div class="p-4 rounded-lg bg-bg-2 border border-border info">
            <div class="text-xs text-muted mb-1">Investido</div>
            <div class="text-xl font-bold text-tx">R$ {{ r.total_invested | number: '1.2-2' }}</div>
          </div>
          <div class="p-4 rounded-lg bg-bg-2 border border-border" [class.good]="r.total_pnl >= 0" [class.warn]="r.total_pnl < 0">
            <div class="text-xs text-muted mb-1">Valor atual</div>
            <div class="text-xl font-bold text-tx">R$ {{ r.total_current | number: '1.2-2' }}</div>
          </div>
          <div class="p-4 rounded-lg bg-bg-2 border border-border" [class.good]="r.total_pnl >= 0" [class.warn]="r.total_pnl < 0">
            <div class="text-xs text-muted mb-1">Resultado</div>
            <div class="text-xl font-bold text-tx">
              {{ r.total_pnl >= 0 ? '+' : '' }}R$ {{ r.total_pnl | number: '1.2-2' }}
              ({{ r.total_pnl_pct | number: '1.2-2' }}%)
            </div>
          </div>
        </div>
      </div>

      <div class="p-5 rounded-lg bg-panel border border-border">
        <h2 class="text-xl font-bold m-0 mb-4 text-tx">Posições</h2>
        <div style="overflow-x:auto;">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr class="border-b border-border">
                <th class="text-left py-2 px-2 font-medium text-muted">Ativo</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Categoria</th>
                <th class="text-right py-2 px-2 font-medium text-muted">Qtd</th>
                <th class="text-right py-2 px-2 font-medium text-muted">P. médio</th>
                <th class="text-right py-2 px-2 font-medium text-muted">P. atual</th>
                <th class="text-right py-2 px-2 font-medium text-muted">P. justo</th>
                <th class="text-right py-2 px-2 font-medium text-muted">PnL</th>
                <th class="text-left py-2 px-2 font-medium text-muted">Decisão</th>
              </tr>
            </thead>
            <tbody>
              @for (p of r.positions; track p.ticker) {
                <tr class="border-b border-border hover:bg-bg-2 transition-colors">
                  <td class="py-2 px-2">
                    <div class="font-semibold text-tx">{{ p.ticker }}</div>
                    <div class="text-xs text-muted">{{ p.name }}</div>
                  </td>
                  <td class="py-2 px-2">
                    <span class="tag tag-cat" [class]="'cat-' + p.category_resolved">{{ ui.categoryLabel(p.category_resolved) }}</span>
                  </td>
                  <td class="text-right py-2 px-2 text-tx">{{ p.quantity }}</td>
                  <td class="text-right py-2 px-2 text-tx">{{ p.avg_price | number: '1.2-2' }}</td>
                  <td class="text-right py-2 px-2 text-tx">{{ p.current_price != null ? (p.current_price | number: '1.2-2') : '—' }}</td>
                  <td class="text-right py-2 px-2 text-tx">{{ p.fair_price != null ? (p.fair_price | number: '1.2-2') : '—' }}</td>
                  <td class="text-right py-2 px-2" [class.good]="(p.pnl_pct || 0) >= 0" [class.warn]="(p.pnl_pct || 0) < 0">
                    {{ p.pnl_pct != null ? (p.pnl_pct | number: '1.2-2') + '%' : '—' }}
                  </td>
                  <td class="py-2 px-2">
                    <span class="verdict-pill" [class]="ui.verdictClass(p.verdict)">{{ p.label }}</span>
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
export class AssetsComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  result = signal<PortfolioEvaluationResponse | null>(null);
  saveState = signal<'idle' | 'saving' | 'saved' | 'error'>('idle');

  private save$ = new Subject<void>();

  form: FormGroup<PortfolioFormShape> = this.fb.group({
    items: this.fb.array<FormGroup<PortfolioItemForm>>([]),
    desired_yield: this.fb.control(0.06, { nonNullable: true, validators: [Validators.min(0.02), Validators.max(0.20)] }),
  });

  get portfolioItems() {
    return this.form.controls.items;
  }

  ngOnInit(): void {
    this.loadStoredPortfolio();

    this.form.valueChanges.subscribe(() => {
      this.save$.next();
    });

    this.save$.pipe(debounceTime(800)).subscribe(() => {
      this.persistPortfolio();
    });
  }

  addItem(): void {
    const group = this.fb.group<PortfolioItemForm>({
      ticker: this.fb.control('', { nonNullable: true, validators: Validators.required }),
      quantity: this.fb.control(0, { nonNullable: true, validators: [Validators.required, Validators.min(0.0001)] }),
      avg_price: this.fb.control(0, { nonNullable: true, validators: [Validators.required, Validators.min(0.0001)] }),
      category: this.fb.control<'auto' | 'renda' | 'trade'>('auto', { nonNullable: true }),
    });
    this.portfolioItems.push(group);
  }

  removeItem(i: number): void {
    this.portfolioItems.removeAt(i);
  }

  evaluateAssets(): void {
    const items = this.portfolioItems.getRawValue();
    const dy = this.form.controls.desired_yield.getRawValue();
    this.svc.evaluatePortfolio({ items, desired_yield: dy }).subscribe({
      next: (res) => {
        this.result.set(res);
      },
      error: () => {},
      complete: () => {},
    });
  }

  private loadStoredPortfolio(): void {
    this.svc.getPortfolio().subscribe({
      next: (res) => {
        res.items.forEach((item) => {
          const group = this.fb.group<PortfolioItemForm>({
            ticker: this.fb.control(item.ticker, { nonNullable: true, validators: Validators.required }),
            quantity: this.fb.control(item.quantity, { nonNullable: true, validators: [Validators.required, Validators.min(0.0001)] }),
            avg_price: this.fb.control(item.avg_price, { nonNullable: true, validators: [Validators.required, Validators.min(0.0001)] }),
            category: this.fb.control(item.category, { nonNullable: true }),
          });
          this.portfolioItems.push(group);
        });
      },
      error: () => {},
    });
  }

  private persistPortfolio(): void {
    const items = this.portfolioItems.getRawValue();
    if (items.length === 0) return;

    this.saveState.set('saving');
    this.svc.savePortfolio(items).subscribe({
      next: () => {
        this.saveState.set('saved');
        setTimeout(() => this.saveState.set('idle'), 2000);
      },
      error: () => {
        this.saveState.set('error');
        setTimeout(() => this.saveState.set('idle'), 3000);
      },
      complete: () => {},
    });
  }
}
