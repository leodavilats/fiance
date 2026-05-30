import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  FormArray,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { forkJoin } from 'rxjs';
import {
  AllocationCategory,
  Goal,
  RecommendService,
  SectorGoal,
  UiHelperService,
  WatchlistItem,
} from '../../core';

interface GoalForm {
  category: FormControl<AllocationCategory>;
  target_pct: FormControl<number>;
  target_value: FormControl<number | null>;
  deadline: FormControl<string | null>;
}

interface SectorGoalForm {
  sector: FormControl<string>;
  target_pct: FormControl<number>;
}

interface ConfigFormShape {
  cash_available: FormControl<number>;
  desired_yield: FormControl<number>;
  goals: FormArray<FormGroup<GoalForm>>;
  sector_goals: FormArray<FormGroup<SectorGoalForm>>;
  watchlist: FormControl<string>;
}

const CATEGORIES: { key: AllocationCategory; label: string; icon: string; desc: string }[] = [
  { key: 'renda_fixa', label: 'Renda Fixa', icon: 'landmark', desc: 'CDB, LCI, LCA, Tesouro...' },
  { key: 'acoes_br', label: 'Ações BR', icon: 'trending-up', desc: 'Ações da B3' },
  { key: 'acoes_int', label: 'Ações INT', icon: 'globe', desc: 'Ações internacionais' },
  { key: 'fiis', label: 'FIIs', icon: 'building-2', desc: 'Fundos Imobiliários' },
  { key: 'cripto', label: 'Cripto', icon: 'bitcoin', desc: 'Criptomoedas' },
];

@Component({
  selector: 'app-config',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <form [formGroup]="form" class="flex flex-col gap-5">
      <!-- Caixa e Yield -->
      <div class="p-5 rounded-lg bg-panel border border-border">
        <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
          <lucide-icon name="settings" size="18"></lucide-icon> Configurações Gerais
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Caixa disponível para investir (R$)</label
            >
            <input
              type="number"
              class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              formControlName="cash_available"
              min="0"
              step="100"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5"
              >Yield desejado — Bazin (ex.: 0.06 = 6%)</label
            >
            <input
              type="number"
              class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              formControlName="desired_yield"
              min="0.02"
              max="0.20"
              step="0.005"
            />
          </div>
        </div>
      </div>

      <!-- Metas de Alocação -->
      <div class="p-5 rounded-lg bg-panel border border-border">
        <div class="flex items-start justify-between gap-4 mb-4 flex-wrap">
          <div>
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-1 text-tx">
              <lucide-icon name="pie-chart" size="18"></lucide-icon> Alocação Alvo
            </h2>
            <p class="text-xs text-muted m-0">
              Defina quanto (%) cada categoria deve ter na sua carteira.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="text-sm font-medium"
              [class.text-accent]="goalSum() === 100"
              [class.text-red-400]="goalSum() !== 100"
            >
              Soma: <strong>{{ goalSum() }}%</strong>
            </span>
            @if (goalSum() !== 100) {
              <span class="text-xs text-red-400">(deve ser 100%)</span>
            } @else {
              <lucide-icon name="check-circle" size="16" class="text-accent"></lucide-icon>
            }
          </div>
        </div>

        <!-- Barra visual de composição -->
        <div class="flex h-3 rounded-full overflow-hidden mb-5 gap-0.5">
          @for (cat of categories; track cat.key; let i = $index) {
            @if (goalPct(i) > 0) {
              <div
                class="transition-all"
                [class]="catBarColor(cat.key)"
                [style.width.%]="goalPct(i)"
                [title]="cat.label + ': ' + goalPct(i) + '%'"
              ></div>
            }
          }
        </div>

        <div formArrayName="goals" class="flex flex-col gap-4">
          @for (g of goalItems.controls; track $index; let i = $index) {
            <div class="p-4 rounded-lg bg-panel-2 border border-border" [formGroupName]="i">
              <div class="flex items-center gap-3 mb-3 flex-wrap">
                <div class="flex items-center gap-2 flex-1 min-w-[160px]">
                  <div
                    class="w-8 h-8 grid place-items-center rounded-lg"
                    [class]="catBgColor(categories[i].key)"
                  >
                    <lucide-icon
                      [name]="categories[i].icon"
                      size="16"
                      class="text-white"
                    ></lucide-icon>
                  </div>
                  <div>
                    <div class="font-semibold text-sm text-tx">{{ categories[i].label }}</div>
                    <div class="text-xs text-muted">{{ categories[i].desc }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <input
                    type="number"
                    class="w-20 px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent text-center font-bold"
                    formControlName="target_pct"
                    min="0"
                    max="100"
                    step="1"
                  />
                  <span class="text-muted text-sm font-medium">%</span>
                </div>
              </div>
              <!-- Slider visual -->
              <input
                type="range"
                class="w-full accent-accent h-1.5 rounded-full cursor-pointer"
                [min]="0"
                [max]="100"
                [step]="1"
                [value]="goalPct(i)"
                (input)="updateGoalPct(i, $any($event.target).value)"
              />
              <!-- Metas opcionais -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
                <div>
                  <label class="block text-xs text-muted mb-1">Meta em R$ (opcional)</label>
                  <input
                    type="number"
                    class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-xs focus:outline-none focus:ring-2 focus:ring-accent"
                    formControlName="target_value"
                    min="0"
                    step="100"
                    placeholder="ex.: 50000"
                  />
                </div>
                <div>
                  <label class="block text-xs text-muted mb-1">Prazo (opcional)</label>
                  <input
                    type="date"
                    class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-xs focus:outline-none focus:ring-2 focus:ring-accent"
                    formControlName="deadline"
                  />
                </div>
              </div>
            </div>
          }
        </div>
      </div>

      <!-- Alocação Setorial (NOVO) -->
      <div class="p-5 rounded-lg bg-panel border border-border">
        <div class="flex items-start justify-between gap-4 mb-4 flex-wrap">
          <div>
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-1 text-tx">
              <lucide-icon name="git-compare" size="18"></lucide-icon> Alocação Setorial
            </h2>
            <p class="text-xs text-muted m-0">
              Defina quanto (%) de cada setor você quer dentro do total de ações.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="text-sm font-medium"
              [class.text-accent]="sectorGoalSum() === 100"
              [class.text-warn]="sectorGoalSum() !== 100"
            >
              Soma: <strong>{{ sectorGoalSum() }}%</strong>
            </span>
            @if (sectorGoalSum() !== 100) {
              <span class="text-xs text-warn">(deve ser 100%)</span>
            } @else {
              <lucide-icon name="check-circle" size="16" class="text-accent"></lucide-icon>
            }
          </div>
        </div>

        <div
          formArrayName="sector_goals"
          class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3"
        >
          @for (sg of sectorGoalItems.controls; track $index; let i = $index) {
            <div class="p-3 rounded-lg bg-panel-2 border border-border" [formGroupName]="i">
              <div class="flex items-center justify-between gap-2 mb-2">
                <div class="font-semibold text-sm text-tx">
                  {{ sectorGoalItems.at(i).controls.sector.value }}
                </div>
                <div class="flex items-center gap-2">
                  <input
                    type="number"
                    class="w-16 px-2 py-1 rounded bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent text-center font-bold"
                    formControlName="target_pct"
                    min="0"
                    max="100"
                    step="5"
                  />
                  <span class="text-muted text-xs">%</span>
                </div>
              </div>
              <input
                type="range"
                class="w-full accent-accent h-1.5 rounded-full cursor-pointer"
                [min]="0"
                [max]="100"
                [step]="5"
                [value]="sectorGoalItems.at(i).controls.target_pct.value"
                (input)="updateSectorGoalPct(i, $any($event.target).value)"
              />
            </div>
          }
        </div>
      </div>

      <!-- Watchlist -->
      <div class="p-5 rounded-lg bg-panel border border-border">
        <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-1 text-tx">
          <lucide-icon name="eye" size="18"></lucide-icon> Watchlist
        </h2>
        <p class="text-xs text-muted mb-3">
          Tickers monitorados que entram no ranking de oportunidades. Separe por vírgula.
        </p>
        <input
          type="text"
          class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          formControlName="watchlist"
          placeholder="ex.: BBSE3, ENBR3, ETH"
        />
      </div>

      <!-- Ações -->
      <div class="flex items-center gap-3 flex-wrap">
        <button
          type="button"
          class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          (click)="saveConfig()"
          [disabled]="saving() || goalSum() !== 100"
        >
          <lucide-icon [name]="saving() ? 'loader-circle' : 'check'" size="16"></lucide-icon>
          {{ saving() ? 'Salvando...' : 'Salvar configurações' }}
        </button>
        <span
          class="text-sm"
          [class.text-accent]="message().startsWith('✓')"
          [class.text-red-400]="message().startsWith('✗')"
          *ngIf="message()"
          >{{ message() }}</span
        >
      </div>

      <!-- Cache -->
      <div class="p-5 rounded-lg bg-panel border border-border">
        <h3 class="text-base font-semibold mb-1 text-tx flex items-center gap-2">
          <lucide-icon name="database" size="16"></lucide-icon> Cache de Dados
        </h3>
        <p class="text-xs text-muted mb-3">Limpe o cache para forçar atualização das cotações.</p>
        <div class="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-bg text-tx border border-border hover:bg-border disabled:opacity-50 transition-colors"
            (click)="clearAssetsCache()"
            [disabled]="clearing()"
          >
            <lucide-icon
              [name]="clearing() ? 'loader-circle' : 'refresh-cw'"
              size="16"
            ></lucide-icon>
            {{ clearing() ? 'Limpando...' : 'Limpar cache de ativos' }}
          </button>
          <button
            type="button"
            class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-bg text-tx border border-border hover:bg-border disabled:opacity-50 transition-colors"
            (click)="clearAllCache()"
            [disabled]="clearing()"
          >
            <lucide-icon [name]="clearing() ? 'loader-circle' : 'trash2'" size="16"></lucide-icon>
            {{ clearing() ? 'Limpando...' : 'Limpar todo cache' }}
          </button>
          <span class="text-sm text-muted" *ngIf="cacheMessage()">{{ cacheMessage() }}</span>
        </div>
      </div>
    </form>
  `,
})
export class ConfigComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);

  readonly categories = CATEGORIES;
  saving = signal(false);
  message = signal('');
  clearing = signal(false);
  cacheMessage = signal('');

  form: FormGroup<ConfigFormShape> = this.fb.group({
    cash_available: this.fb.control(0, { nonNullable: true, validators: Validators.min(0) }),
    desired_yield: this.fb.control(0.06, {
      nonNullable: true,
      validators: [Validators.min(0.02), Validators.max(0.2)],
    }),
    goals: this.fb.array<FormGroup<GoalForm>>([]),
    sector_goals: this.fb.array<FormGroup<SectorGoalForm>>([]),
    watchlist: this.fb.control('', { nonNullable: true }),
  });

  get goalItems() {
    return this.form.controls.goals;
  }

  get sectorGoalItems() {
    return this.form.controls.sector_goals;
  }

  goalSum(): number {
    return this.goalItems.controls.reduce((sum, g) => sum + (g.controls.target_pct.value || 0), 0);
  }

  goalPct(i: number): number {
    return this.goalItems.controls[i]?.controls.target_pct.value || 0;
  }

  updateGoalPct(i: number, val: string): void {
    this.goalItems.controls[i]?.controls.target_pct.setValue(Number(val));
  }

  sectorGoalSum(): number {
    return this.sectorGoalItems.controls.reduce(
      (sum, sg) => sum + (sg.controls.target_pct.value || 0),
      0
    );
  }

  updateSectorGoalPct(i: number, val: string): void {
    this.sectorGoalItems.controls[i]?.controls.target_pct.setValue(Number(val));
  }

  catBarColor(cat: AllocationCategory): string {
    const map: Record<AllocationCategory, string> = {
      renda_fixa: 'bg-blue-400',
      acoes_br: 'bg-green-400',
      acoes_int: 'bg-purple-400',
      fiis: 'bg-orange-400',
      cripto: 'bg-yellow-400',
    };
    return map[cat] || 'bg-muted';
  }

  catBgColor(cat: AllocationCategory): string {
    const map: Record<AllocationCategory, string> = {
      renda_fixa: 'bg-blue-500',
      acoes_br: 'bg-green-500',
      acoes_int: 'bg-purple-500',
      fiis: 'bg-orange-500',
      cripto: 'bg-yellow-500',
    };
    return map[cat] || 'bg-muted';
  }

  ngOnInit(): void {
    this._initGoals();
    this._initSectorGoals();
    this.loadConfig();
  }

  private _initGoals(): void {
    CATEGORIES.forEach(cat => {
      this.goalItems.push(this._makeGoalGroup(cat.key, 0));
    });
  }

  private _initSectorGoals(): void {
    const sectors = ['Financeiro', 'Energia', 'Varejo', 'Tecnologia', 'Saúde', 'Outros'];
    sectors.forEach(sector => {
      this.sectorGoalItems.push(this._makeSectorGoalGroup(sector, 0));
    });
  }

  private _makeGoalGroup(
    category: AllocationCategory,
    pct: number,
    targetValue?: number | null,
    deadline?: string | null
  ): FormGroup<GoalForm> {
    return this.fb.group<GoalForm>({
      category: this.fb.control(category, { nonNullable: true }),
      target_pct: this.fb.control(pct, {
        nonNullable: true,
        validators: [Validators.min(0), Validators.max(100)],
      }),
      target_value: this.fb.control(targetValue ?? null),
      deadline: this.fb.control(deadline ?? null),
    });
  }

  private _makeSectorGoalGroup(sector: string, pct: number): FormGroup<SectorGoalForm> {
    return this.fb.group<SectorGoalForm>({
      sector: this.fb.control(sector, { nonNullable: true }),
      target_pct: this.fb.control(pct, {
        nonNullable: true,
        validators: [Validators.min(0), Validators.max(100)],
      }),
    });
  }

  private loadConfig(): void {
    forkJoin({
      prefs: this.svc.getPreferences(),
      goals: this.svc.getGoals(),
      sectorGoals: this.svc.getSectorGoals(),
      watchlist: this.svc.getWatchlist(),
    }).subscribe({
      next: ({ prefs, goals, sectorGoals, watchlist }) => {
        this.form.patchValue({
          cash_available: prefs.cash_available,
          desired_yield: prefs.desired_yield,
          watchlist: watchlist.map(w => w.ticker).join(', '),
        });

        // Mapear goals por categoria
        const goalMap = new Map(goals.map(g => [g.category, g]));
        this.goalItems.controls.forEach((ctrl, i) => {
          const cat = CATEGORIES[i].key;
          const g = goalMap.get(cat);
          if (g) {
            ctrl.patchValue({
              target_pct: g.target_pct,
              target_value: g.target_value ?? null,
              deadline: g.deadline ?? null,
            });
          }
        });

        // Mapear sector goals
        const sectorGoalMap = new Map(sectorGoals.map(sg => [sg.sector, sg]));
        this.sectorGoalItems.controls.forEach(ctrl => {
          const sector = ctrl.controls.sector.value;
          const sg = sectorGoalMap.get(sector);
          if (sg) {
            ctrl.patchValue({
              target_pct: sg.target_pct,
            });
          }
        });
      },
      error: () => {},
    });
  }

  saveConfig(): void {
    const { cash_available, desired_yield, watchlist, sector_goals } = this.form.getRawValue();
    const goalsRaw = this.goalItems.getRawValue();
    const goalsPayload: Goal[] = goalsRaw.map(g => ({
      category: g.category,
      target_pct: g.target_pct,
      target_value: g.target_value,
      deadline: g.deadline,
    }));
    const sectorGoalsPayload: SectorGoal[] = sector_goals.map(sg => ({
      sector: sg.sector,
      target_pct: sg.target_pct,
    }));
    const watchlistItems: WatchlistItem[] = watchlist
      .split(',')
      .map(t => ({ ticker: t.trim(), note: '' }))
      .filter(w => w.ticker);

    this.saving.set(true);
    this.message.set('');

    forkJoin({
      prefs: this.svc.savePreferences(cash_available, desired_yield),
      goals: this.svc.saveGoals(goalsPayload),
      sectorGoals: this.svc.saveSectorGoals(sectorGoalsPayload),
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
    });
  }

  clearAssetsCache(): void {
    this.clearing.set(true);
    this.cacheMessage.set('');
    this.svc.clearCache('uasset:*').subscribe({
      next: res => {
        this.clearing.set(false);
        this.cacheMessage.set(`✓ ${res.deleted} entradas removidas`);
        setTimeout(() => this.cacheMessage.set(''), 3000);
      },
      error: () => {
        this.clearing.set(false);
        this.cacheMessage.set('✗ Erro ao limpar cache');
        setTimeout(() => this.cacheMessage.set(''), 3000);
      },
    });
  }

  clearAllCache(): void {
    this.clearing.set(true);
    this.cacheMessage.set('');
    this.svc.clearCache('*').subscribe({
      next: res => {
        this.clearing.set(false);
        this.cacheMessage.set(`✓ ${res.deleted} entradas removidas`);
        setTimeout(() => this.cacheMessage.set(''), 3000);
      },
      error: () => {
        this.clearing.set(false);
        this.cacheMessage.set('✗ Erro ao limpar cache');
        setTimeout(() => this.cacheMessage.set(''), 3000);
      },
    });
  }
}
