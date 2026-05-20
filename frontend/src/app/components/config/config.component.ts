import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, FormArray, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { forkJoin } from 'rxjs';
import { Goal, RecommendService, UiHelperService, WatchlistItem } from '../../core';

interface GoalForm {
  category: FormControl<'renda' | 'trade' | 'cripto' | 'caixa'>;
  target_pct: FormControl<number>;
}

interface ConfigFormShape {
  cash_available: FormControl<number>;
  desired_yield: FormControl<number>;
  goals: FormArray<FormGroup<GoalForm>>;
  watchlist: FormControl<string>;
}

@Component({
  selector: 'app-config',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <form class="p-5 rounded-lg bg-panel border border-border" [formGroup]="form">
      <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx"><lucide-icon name="settings" size="18"></lucide-icon> Configurações</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Caixa disponível (R$)</label>
          <input type="number" class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" formControlName="cash_available" min="0" step="100" />
        </div>
        <div>
          <label class="block text-xs font-medium text-muted mb-1.5">Yield desejado (Bazin)</label>
          <input type="number" class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" formControlName="desired_yield" min="0.02" max="0.20" step="0.005" />
        </div>
      </div>

      <h3 class="text-base font-semibold mt-5 mb-2 text-tx">Metas de alocação (%)</h3>
      <p class="text-xs text-muted mb-3">Total ideal: 100%. Soma atual: <strong>{{ goalSum() }}%</strong></p>
      <div formArrayName="goals" class="flex flex-col gap-2">
        @for (g of goalItems.controls; track $index; let i = $index) {
          <div class="flex items-center gap-3" [formGroupName]="i">
            <span class="tag tag-cat" [class]="'cat-' + g.controls.category.value">{{ ui.categoryLabel(g.controls.category.value) }}</span>
            <input type="number" class="w-20 px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" formControlName="target_pct" min="0" max="100" step="1" />
            <span class="text-muted text-sm">%</span>
          </div>
        }
      </div>

      <h3 class="text-base font-semibold mt-5 mb-2 text-tx">Watchlist</h3>
      <p class="text-xs text-muted mb-3">Tickers que entram no ranking de oportunidades. Separe por vírgula.</p>
      <input type="text" class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent" formControlName="watchlist" placeholder="ex.: BBSE3, ENBR3, ETH" />

      <div class="flex items-center gap-3 mt-5 flex-wrap">
        <button type="button" class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity" (click)="saveConfig()" [disabled]="saving()">
          <lucide-icon [name]="saving() ? 'loader-circle' : 'check'" size="16"></lucide-icon>
          {{ saving() ? 'Salvando...' : 'Salvar configurações' }}
        </button>
        <span class="text-sm text-muted" *ngIf="message()">{{ message() }}</span>
      </div>
    </form>
  `,
})
export class ConfigComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);

  saving = signal(false);
  message = signal('');

  form: FormGroup<ConfigFormShape> = this.fb.group({
    cash_available: this.fb.control(0, { nonNullable: true, validators: Validators.min(0) }),
    desired_yield: this.fb.control(0.06, { nonNullable: true, validators: [Validators.min(0.02), Validators.max(0.20)] }),
    goals: this.fb.array<FormGroup<GoalForm>>([]),
    watchlist: this.fb.control('', { nonNullable: true }),
  });

  get goalItems() {
    return this.form.controls.goals;
  }

  goalSum = computed(() => {
    return this.goalItems.controls.reduce((sum, g) => sum + (g.controls.target_pct.value || 0), 0);
  });

  ngOnInit(): void {
    this.loadConfig();
  }

  private loadConfig(): void {
    forkJoin({
      prefs: this.svc.getPreferences(),
      goals: this.svc.getGoals(),
      watchlist: this.svc.getWatchlist(),
    }).subscribe({
      next: ({ prefs, goals, watchlist }) => {
        this.form.patchValue({
          cash_available: prefs.cash_available,
          desired_yield: prefs.desired_yield,
          watchlist: watchlist.map(w => w.ticker).join(', '),
        });

        const defaultGoals: Goal[] = goals.length > 0 ? goals : [
          { category: 'renda', target_pct: 60 },
          { category: 'trade', target_pct: 30 },
          { category: 'caixa', target_pct: 10 },
        ];

        defaultGoals.forEach(g => {
          const group = this.fb.group<GoalForm>({
            category: this.fb.control(g.category, { nonNullable: true }),
            target_pct: this.fb.control(g.target_pct, { nonNullable: true, validators: [Validators.min(0), Validators.max(100)] }),
          });
          this.goalItems.push(group);
        });
      },
      error: () => {},
    });
  }

  saveConfig(): void {
    const { cash_available, desired_yield, watchlist } = this.form.getRawValue();
    const goals = this.goalItems.getRawValue();
    const watchlistItems: WatchlistItem[] = watchlist.split(',').map(t => ({ ticker: t.trim(), note: '' })).filter(w => w.ticker);

    this.saving.set(true);
    this.message.set('');

    forkJoin({
      prefs: this.svc.savePreferences(cash_available, desired_yield),
      goals: this.svc.saveGoals(goals),
      watchlist: this.svc.saveWatchlist(watchlistItems),
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.message.set('✓ Configurações salvas!');
        setTimeout(() => this.message.set(''), 3000);
      },
      error: () => {
        this.saving.set(false);
        this.message.set('✗ Erro ao salvar');
        setTimeout(() => this.message.set(''), 3000);
      },
      complete: () => {},
    });
  }
}
