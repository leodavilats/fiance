import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, inject, OnInit, signal } from '@angular/core';
import {
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { forkJoin } from 'rxjs';
import {
  ALLOCATION_CATEGORIES,
  AllocationCategory,
  Goal,
  RecommendService,
  SectorGoal,
  UiHelperService,
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

const DEFAULT_SECTORS = ['Financeiro', 'Energia', 'Varejo', 'Tecnologia', 'Saúde', 'Outros'];

@Component({
  selector: 'app-metas',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './metas.component.html',
})
export class MetasComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(RecommendService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly ui = inject(UiHelperService);

  readonly categories = ALLOCATION_CATEGORIES;
  readonly saving = signal(false);
  readonly message = signal('');

  readonly form = this.fb.group({
    passive_income_goal: this.fb.control<number | null>(null, { validators: Validators.min(0) }),
    goals: this.fb.array<FormGroup<GoalForm>>([]),
    sector_goals: this.fb.array<FormGroup<SectorGoalForm>>([]),
  });

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
    this.message.set('');

    forkJoin({
      prefs: this.svc.savePreferences({ passive_income_goal: passive_income_goal ?? null }),
      goals: this.svc.saveGoals(goalsPayload),
      sectorGoals: this.svc.saveSectorGoals(sectorGoalsPayload),
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.message.set('✓ Metas salvas');
        setTimeout(() => this.message.set(''), 3000);
      },
      error: () => {
        this.saving.set(false);
        this.message.set('✗ Não conseguimos salvar suas metas');
        setTimeout(() => this.message.set(''), 4000);
      },
    });
  }
}
