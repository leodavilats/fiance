import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, computed, inject, OnInit, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { forkJoin, map, startWith } from 'rxjs';
import {
  ALLOCATION_CATEGORIES,
  AllocationCategory,
  Goal,
  RecommendService,
  SectorGoal,
  UiHelperService,
} from '../../core';
import { GoalProgressComponent } from '../goal-progress/goal-progress.component';
import { PageHeaderComponent } from '../page-header/page-header.component';

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

const DEFAULT_SECTORS = ['Financeiro', 'Energia', 'Varejo', 'Tecnologia', 'Saúde', 'Outros'];

@Component({
  selector: 'app-goals',
  standalone: true,
  imports: [
    PageHeaderComponent,
    CommonModule,
    GoalProgressComponent,
    LucideAngularModule,
    ReactiveFormsModule,
  ],
  template: `
    <app-page-header
      title="Metas"
      question="Quanto eu quero de renda, e como a carteira deveria estar dividida?"
    />

    <form [formGroup]="form" class="flex flex-col gap-8">
      <div class="fi-block">
        <h2 class="fi-title m-0 mb-4 text-ink">Meta de renda</h2>
        <div class="grid grid-cols-1 gap-5">
          <div>
            <label for="meta-renda" class="fi-caption text-ink-3 block mb-1.5">
              Meta de renda passiva mensal (R$)
            </label>
            <input
              id="meta-renda"
              type="number"
              class="input max-w-[240px]"
              formControlName="passive_income_goal"
              min="0"
              step="100"
              placeholder="Ex: 5000"
            />
          </div>

          <app-goal-progress
            label="Renda passiva estimada"
            [current]="currentMonthlyIncome()"
            [target]="passiveIncomeTarget()"
          />
        </div>
      </div>
      <div class="fi-block">
        <div class="flex items-start justify-between gap-4 mb-4 flex-wrap">
          <div>
            <h2 class="fi-title m-0 mb-1 text-ink">Alocação alvo</h2>
            <p class="fi-caption text-ink-2 m-0">
              Defina quanto (%) cada categoria deve ter na sua carteira.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="fi-label"
              [class.text-brand]="goalSum() === 100"
              [class.text-adverse]="goalSum() !== 100"
            >
              Soma <span class="fi-num">{{ goalSum() }}</span
              >%
            </span>
            @if (goalSum() !== 100) {
              <span class="fi-caption text-adverse">(deve ser 100%)</span>
            } @else {
              <lucide-icon name="circle-check" size="16" class="text-brand"></lucide-icon>
            }
          </div>
        </div>

        <div class="flex h-3 rounded-pill overflow-hidden mb-5 gap-0.5">
          @for (cat of categories; track cat.key; let i = $index) {
            @if (goalPct(i) > 0) {
              <div
                class="transition-[width] duration-base ease-enter"
                [class]="catBarColor(cat.key)"
                [style.width.%]="goalPct(i)"
                [title]="cat.label + ': ' + goalPct(i) + '%'"
              ></div>
            }
          }
        </div>

        <div formArrayName="goals" class="flex flex-col gap-4">
          @for (g of goalItems.controls; track $index; let i = $index) {
            <div class="card" [formGroupName]="i">
              <div class="flex items-center gap-3 mb-3 flex-wrap">
                <div class="flex items-center gap-2 flex-1 min-w-[160px]">
                  <div
                    class="w-8 h-8 grid place-items-center rounded-md"
                    [class]="catBgColor(categories[i].key)"
                  >
                    <lucide-icon
                      [name]="categories[i].icon"
                      size="16"
                      [class]="catColor(categories[i].key)"
                    ></lucide-icon>
                  </div>
                  <div>
                    <div class="fi-label text-ink">{{ categories[i].label }}</div>
                    <div class="fi-caption text-ink-2">{{ categories[i].desc }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <input
                    type="number"
                    class="input text-center"
                    formControlName="target_pct"
                    min="0"
                    max="100"
                    step="1"
                  />
                  <span class="fi-label text-ink-2">%</span>
                </div>
              </div>

              <input
                type="range"
                class="range-slider w-full accent-brand h-1.5 rounded-pill cursor-pointer"
                [min]="0"
                [max]="100"
                [step]="1"
                [value]="goalPct(i)"
                [style]="{ '--range-pct': goalPct(i) + '%' }"
                (input)="updateGoalPct(i, $any($event.target).value)"
              />

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
                <div>
                  <label class="field-label block mb-1">Meta em R$ (opcional)</label>
                  <input
                    type="number"
                    class="input"
                    formControlName="target_value"
                    min="0"
                    step="100"
                    placeholder="ex.: 50000"
                  />
                </div>
                <div>
                  <label class="field-label block mb-1">Prazo (opcional)</label>
                  <input type="date" class="input" formControlName="deadline" />
                </div>
              </div>
            </div>
          }
        </div>
      </div>
      <div class="fi-block">
        <div class="flex items-start justify-between gap-4 mb-4 flex-wrap">
          <div>
            <h2 class="fi-title m-0 mb-1 text-ink">Alocação setorial</h2>
            <p class="fi-caption text-ink-2 m-0">
              Defina quanto (%) de cada setor você quer dentro do total de ações.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="fi-label"
              [class.text-brand]="sectorGoalSum() === 100"
              [class.text-attention]="sectorGoalSum() !== 100"
            >
              Soma: <strong>{{ sectorGoalSum() }}%</strong>
            </span>
            @if (sectorGoalSum() !== 100) {
              <span class="fi-caption text-attention">(deve ser 100%)</span>
            } @else {
              <lucide-icon name="circle-check" size="16" class="text-brand"></lucide-icon>
            }
          </div>
        </div>

        <div
          formArrayName="sector_goals"
          class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3"
        >
          @for (sg of sectorGoalItems.controls; track $index; let i = $index) {
            <div class="card p-3" [formGroupName]="i">
              <div class="flex items-center justify-between gap-2 mb-2">
                <div class="fi-label text-ink">
                  {{ sectorGoalItems.at(i).controls.sector.value }}
                </div>
                <div class="flex items-center gap-2">
                  <input
                    type="number"
                    class="input text-center"
                    formControlName="target_pct"
                    min="0"
                    max="100"
                    step="5"
                  />
                  <span class="fi-caption text-ink-2">%</span>
                </div>
              </div>
              <input
                type="range"
                class="range-slider w-full accent-brand h-1.5 rounded-pill cursor-pointer"
                [min]="0"
                [max]="100"
                [step]="5"
                [value]="sectorGoalItems.at(i).controls.target_pct.value"
                [style]="{ '--range-pct': sectorGoalItems.at(i).controls.target_pct.value + '%' }"
                (input)="updateSectorGoalPct(i, $any($event.target).value)"
              />
            </div>
          }
        </div>
      </div>
      <div class="flex items-center justify-end gap-3 mt-1">
        @if (resultado() === 'ok') {
          <p class="fi-body text-favorable m-0" role="status">Metas salvas</p>
        } @else if (resultado() === 'erro') {
          <p class="fi-body text-adverse m-0" role="alert">
            Não conseguimos salvar. As metas anteriores continuam valendo.
          </p>
        }
        <button
          type="button"
          class="btn-primary"
          (click)="saveMetas()"
          [disabled]="saving() || goalSum() !== 100"
        >
          <lucide-icon [name]="saving() ? 'loader-circle' : 'check'" size="16"></lucide-icon>
          {{ saving() ? 'Salvando...' : 'Salvar' }}
        </button>
      </div>
    </form>
  `,
})
export class GoalsComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly ui = inject(UiHelperService);

  readonly categories = ALLOCATION_CATEGORIES;
  readonly saving = signal(false);
  readonly resultado = signal<'ok' | 'erro' | null>(null);

  readonly currentIncome = signal<number | null>(null);

  readonly currentMonthlyIncome = computed(() => this.currentIncome() ?? 0);

  readonly form = this.fb.group({
    passive_income_goal: this.fb.control<number | null>(null, { validators: Validators.min(0) }),
    goals: this.fb.array<FormGroup<GoalForm>>([]),
    sector_goals: this.fb.array<FormGroup<SectorGoalForm>>([]),
  });

  /*
   * O alvo vem do campo, e por isso precisa de um signal alimentado por `valueChanges`.
   *
   * Era um `computed()` lendo `this.form.controls.passive_income_goal.value` direto. Signal nao
   * rastreia FormControl: o valor era avaliado uma vez e ficava cacheado para sempre, e a regua
   * de progresso nunca reagia ao que a pessoa digitava — ela dizia "nenhum alvo definido" com a
   * meta preenchida na tela ao lado.
   */
  readonly passiveIncomeTarget = toSignal(
    this.form.controls.passive_income_goal.valueChanges.pipe(
      startWith(this.form.controls.passive_income_goal.value),
      map(valor => (valor === null ? null : Number(valor)))
    ),
    { initialValue: null }
  );

  get goalItems(): FormArray<FormGroup<GoalForm>> {
    return this.form.controls.goals;
  }

  get sectorGoalItems(): FormArray<FormGroup<SectorGoalForm>> {
    return this.form.controls.sector_goals;
  }

  ngOnInit(): void {
    ALLOCATION_CATEGORIES.forEach(cat => this.goalItems.push(this.makeGoal(cat.key, 0)));
    DEFAULT_SECTORS.forEach(sector => this.sectorGoalItems.push(this.makeSectorGoal(sector, 0)));
    this.load();
  }

  private makeGoal(category: AllocationCategory, pct: number): FormGroup<GoalForm> {
    return this.fb.group<GoalForm>({
      category: this.fb.control(category, { nonNullable: true }),
      target_pct: this.fb.control(pct, {
        nonNullable: true,
        validators: [Validators.min(0), Validators.max(100)],
      }),
      target_value: this.fb.control<number | null>(null),
      deadline: this.fb.control<string | null>(null),
    });
  }

  private makeSectorGoal(sector: string, pct: number): FormGroup<SectorGoalForm> {
    return this.fb.group<SectorGoalForm>({
      sector: this.fb.control(sector, { nonNullable: true }),
      target_pct: this.fb.control(pct, {
        nonNullable: true,
        validators: [Validators.min(0), Validators.max(100)],
      }),
    });
  }

  private load(): void {
    this.svc.dashboard().subscribe({
      next: d => this.currentIncome.set(d.summary.monthly_dividends_estimate ?? 0),
      error: () => this.currentIncome.set(null),
    });

    forkJoin({
      prefs: this.svc.getPreferences(),
      goals: this.svc.getGoals(),
      sectorGoals: this.svc.getSectorGoals(),
    }).subscribe({
      next: ({ prefs, goals, sectorGoals }) => {
        this.form.patchValue({ passive_income_goal: prefs.passive_income_goal ?? null });

        const goalMap = new Map(goals.map(g => [g.category, g]));
        this.goalItems.controls.forEach((ctrl, i) => {
          const g = goalMap.get(ALLOCATION_CATEGORIES[i].key);
          if (g) {
            ctrl.patchValue({
              target_pct: g.target_pct,
              target_value: g.target_value ?? null,
              deadline: g.deadline ?? null,
            });
          }
        });

        const sectorMap = new Map(sectorGoals.map(sg => [sg.sector, sg]));
        this.sectorGoalItems.controls.forEach(ctrl => {
          const sg = sectorMap.get(ctrl.controls.sector.value);
          if (sg) ctrl.patchValue({ target_pct: sg.target_pct });
        });

        this.cdr.detectChanges();
      },
      error: () => {},
    });
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
    return this.ui.categoryBarClass(cat);
  }

  catBgColor(cat: AllocationCategory): string {
    return this.ui.categoryBgClass(cat);
  }

  catColor(cat: AllocationCategory): string {
    return this.ui.categoryColor(cat);
  }

  saveMetas(): void {
    const { passive_income_goal, sector_goals } = this.form.getRawValue();
    const goalsPayload: Goal[] = this.goalItems.getRawValue().map(g => ({
      category: g.category,
      target_pct: g.target_pct,
      target_value: g.target_value,
      deadline: g.deadline,
    }));
    const sectorGoalsPayload: SectorGoal[] = sector_goals.map(sg => ({
      sector: sg.sector,
      target_pct: sg.target_pct,
    }));

    this.saving.set(true);
    this.resultado.set(null);

    forkJoin({
      prefs: this.svc.savePreferences({ passive_income_goal: passive_income_goal ?? null }),
      goals: this.svc.saveGoals(goalsPayload),
      sectorGoals: this.svc.saveSectorGoals(sectorGoalsPayload),
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.resultado.set('ok');
        setTimeout(() => this.resultado.set(null), 3000);
      },
      error: () => {
        this.saving.set(false);
        this.resultado.set('erro');
        setTimeout(() => this.resultado.set(null), 6000);
      },
    });
  }
}
