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
  PriceAlert,
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

interface ConfigFormShape {
  cash_available: FormControl<number>;
  passive_income_goal: FormControl<number | null>;
  goals: FormArray<FormGroup<GoalForm>>;
  sector_goals: FormArray<FormGroup<SectorGoalForm>>;
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
  templateUrl: './config.component.html',
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
    passive_income_goal: this.fb.control<number | null>(null, { validators: Validators.min(0) }),
    goals: this.fb.array<FormGroup<GoalForm>>([]),
    sector_goals: this.fb.array<FormGroup<SectorGoalForm>>([]),
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
    this.loadAlerts();
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
    }).subscribe({
      next: ({ prefs, goals, sectorGoals }) => {
        this.form.patchValue({
          cash_available: prefs.cash_available,
          passive_income_goal: prefs.passive_income_goal ?? null,
        });

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
    const { cash_available, passive_income_goal, sector_goals } = this.form.getRawValue();
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

    this.saving.set(true);
    this.message.set('');

    forkJoin({
      prefs: this.svc.savePreferences(cash_available, passive_income_goal ?? undefined),
      goals: this.svc.saveGoals(goalsPayload),
      sectorGoals: this.svc.saveSectorGoals(sectorGoalsPayload),
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

  alerts = signal<PriceAlert[]>([]);
  alertMessage = signal('');
  alertForm: FormGroup<{
    ticker: FormControl<string>;
    condition: FormControl<string>;
    target_price: FormControl<number>;
    note: FormControl<string>;
  }> = this.fb.group({
    ticker: this.fb.control('', { nonNullable: true, validators: Validators.required }),
    condition: this.fb.control('below', { nonNullable: true }),
    target_price: this.fb.control(0, { nonNullable: true, validators: Validators.min(0.01) }),
    note: this.fb.control('', { nonNullable: true }),
  });

  loadAlerts(): void {
    this.svc.getAlerts().subscribe({ next: a => this.alerts.set(a), error: () => {} });
  }

  addAlert(): void {
    if (this.alertForm.invalid) return;
    const { ticker, condition, target_price, note } = this.alertForm.getRawValue();
    this.svc.createAlert({ ticker, condition, target_price, note: note || undefined }).subscribe({
      next: () => {
        this.alertForm.patchValue({ ticker: '', target_price: 0, note: '' });
        this.loadAlerts();
      },
      error: () => this.alertMessage.set('✗ Erro ao criar alerta'),
    });
  }

  removeAlert(id: number): void {
    this.svc.deleteAlert(id).subscribe({ next: () => this.loadAlerts(), error: () => {} });
  }
}
