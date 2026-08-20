import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  FormArray,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { forkJoin, Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import {
  AllocationCategory,
  Goal,
  OpportunitiesFrequency,
  PriceAlert,
  RecommendService,
  RiskProfile,
  SectorGoal,
  TickerSuggestion,
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
  passive_income_goal: FormControl<number | null>;
  yield_stock: FormControl<number>;
  yield_fii: FormControl<number>;
  yield_bdr: FormControl<number>;
  yield_etf: FormControl<number>;
  goals: FormArray<FormGroup<GoalForm>>;
  sector_goals: FormArray<FormGroup<SectorGoalForm>>;
  notify_price_alerts: FormControl<boolean>;
  opportunities_frequency: FormControl<OpportunitiesFrequency>;
  risk_profile: FormControl<RiskProfile>;
  preferred_categories: FormControl<AllocationCategory[]>;
  preferred_sectors: FormControl<string>;
  excluded_tickers: FormControl<string>;
}

const FREQUENCY_OPTIONS: { key: OpportunitiesFrequency; label: string }[] = [
  { key: 'off', label: 'Desativado' },
  { key: 'daily', label: 'Diária' },
  { key: 'weekly', label: 'Semanal' },
  { key: 'monthly', label: 'Mensal' },
];

const RISK_PROFILE_OPTIONS: { key: RiskProfile; label: string }[] = [
  { key: 'conservative', label: 'Conservador' },
  { key: 'moderate', label: 'Moderado' },
  { key: 'aggressive', label: 'Arrojado' },
];

const CATEGORIES: { key: AllocationCategory; label: string; icon: string; desc: string }[] = [
  { key: 'renda_fixa', label: 'Renda Fixa', icon: 'landmark', desc: 'CDB, LCI, LCA, Tesouro...' },
  { key: 'acoes_br', label: 'Ações BR', icon: 'trending-up', desc: 'Ações da B3' },
  { key: 'bdrs', label: 'BDRs', icon: 'globe', desc: 'BDRs (ações internacionais)' },
  { key: 'fiis', label: 'FIIs', icon: 'building-2', desc: 'Fundos Imobiliários' },
  {
    key: 'etfs',
    label: 'ETFs',
    icon: 'layers',
    desc: 'ETFs (fundos de índice negociados na bolsa)',
  },
];

@Component({
  selector: 'app-config',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './config.component.html',
})
export class ConfigComponent implements OnInit, OnDestroy {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  private cdr = inject(ChangeDetectorRef);
  readonly ui = inject(UiHelperService);

  private destroy$ = new Subject<void>();

  readonly categories = CATEGORIES;
  readonly frequencyOptions = FREQUENCY_OPTIONS;
  readonly riskProfileOptions = RISK_PROFILE_OPTIONS;
  saving = signal(false);
  message = signal('');
  clearing = signal(false);
  cacheMessage = signal('');

  private readonly yieldValidators = [Validators.min(0.5), Validators.max(30)];

  form: FormGroup<ConfigFormShape> = this.fb.group({
    passive_income_goal: this.fb.control<number | null>(null, { validators: Validators.min(0) }),
    yield_stock: this.fb.control(6, { nonNullable: true, validators: this.yieldValidators }),
    yield_fii: this.fb.control(10, { nonNullable: true, validators: this.yieldValidators }),
    yield_bdr: this.fb.control(4, { nonNullable: true, validators: this.yieldValidators }),
    yield_etf: this.fb.control(4, { nonNullable: true, validators: this.yieldValidators }),
    goals: this.fb.array<FormGroup<GoalForm>>([]),
    sector_goals: this.fb.array<FormGroup<SectorGoalForm>>([]),
    notify_price_alerts: this.fb.control(true, { nonNullable: true }),
    opportunities_frequency: this.fb.control<OpportunitiesFrequency>('weekly', {
      nonNullable: true,
    }),
    risk_profile: this.fb.control<RiskProfile>('moderate', { nonNullable: true }),
    preferred_categories: this.fb.control<AllocationCategory[]>([], { nonNullable: true }),
    preferred_sectors: this.fb.control('', { nonNullable: true }),
    excluded_tickers: this.fb.control('', { nonNullable: true }),
  });

  isPreferredCategory(cat: AllocationCategory): boolean {
    return this.form.controls.preferred_categories.value.includes(cat);
  }

  togglePreferredCategory(cat: AllocationCategory, checked: boolean): void {
    const current = this.form.controls.preferred_categories.value;
    const next = checked ? [...current, cat] : current.filter(c => c !== cat);
    this.form.controls.preferred_categories.setValue(next);
  }

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
    return this.ui.categoryBarClass(cat);
  }

  catBgColor(cat: AllocationCategory): string {
    return this.ui.categoryBgClass(cat);
  }

  ngOnInit(): void {
    this._initGoals();
    this._initSectorGoals();
    this.loadConfig();
    this.loadAlerts();

    this.alertTickerSearch$
      .pipe(
        debounceTime(1000),
        switchMap(query => {
          if (query.trim().length < 1) return [[] as TickerSuggestion[]];
          return this.svc.searchTickers(query).pipe(switchMap(res => [res.items]));
        }),
        takeUntil(this.destroy$)
      )
      .subscribe(items => {
        this.alertTickerSuggestions.set(items);
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  alertTickerSuggestions = signal<TickerSuggestion[]>([]);
  alertTickerSuggestionsOpen = signal(false);
  private alertTickerSearch$ = new Subject<string>();

  onAlertTickerInput(value: string): void {
    this.alertTickerSuggestionsOpen.set(true);
    this.alertTickerSearch$.next(value);
  }

  selectAlertTickerSuggestion(suggestion: TickerSuggestion): void {
    this.alertForm.controls.ticker.setValue(suggestion.ticker);
    this.closeAlertTickerSuggestions();
  }

  closeAlertTickerSuggestions(): void {
    this.alertTickerSuggestionsOpen.set(false);
    this.alertTickerSuggestions.set([]);
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
          passive_income_goal: prefs.passive_income_goal ?? null,
          yield_stock: Math.round((prefs.desired_yield_stock ?? 0.06) * 1000) / 10,
          yield_fii: Math.round((prefs.desired_yield_fii ?? 0.1) * 1000) / 10,
          yield_bdr: Math.round((prefs.desired_yield_bdr ?? 0.04) * 1000) / 10,
          yield_etf: Math.round((prefs.desired_yield_etf ?? 0.04) * 1000) / 10,
          notify_price_alerts: prefs.notify_price_alerts ?? true,
          opportunities_frequency: prefs.opportunities_frequency ?? 'weekly',
          risk_profile: prefs.risk_profile ?? 'moderate',
          preferred_categories: prefs.preferred_categories ?? [],
          preferred_sectors: (prefs.preferred_sectors ?? []).join(', '),
          excluded_tickers: (prefs.excluded_tickers ?? []).join(', '),
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

        this.cdr.detectChanges();
      },
      error: () => {},
    });
  }

  saveConfig(): void {
    const {
      passive_income_goal,
      sector_goals,
      yield_stock,
      yield_fii,
      yield_bdr,
      yield_etf,
      notify_price_alerts,
      opportunities_frequency,
      risk_profile,
      preferred_categories,
      preferred_sectors,
      excluded_tickers,
    } = this.form.getRawValue();
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
      // Sem `cash_available` no payload: esta tela não edita o caixa, e o PUT
      // parcial preserva o valor salvo em vez de zerá-lo.
      prefs: this.svc.savePreferences({
        passive_income_goal: passive_income_goal ?? null,
        desired_yield_stock: yield_stock / 100,
        desired_yield_fii: yield_fii / 100,
        desired_yield_bdr: yield_bdr / 100,
        desired_yield_etf: yield_etf / 100,
        notify_price_alerts: notify_price_alerts,
        opportunities_frequency: opportunities_frequency,
        risk_profile: risk_profile,
        preferred_categories: preferred_categories,
        preferred_sectors: preferred_sectors
          .split(',')
          .map(s => s.trim())
          .filter(Boolean),
        excluded_tickers: excluded_tickers
          .split(',')
          .map(s => s.trim().toUpperCase())
          .filter(Boolean),
      }),
      goals: this.svc.saveGoals(goalsPayload),
      sectorGoals: this.svc.saveSectorGoals(sectorGoalsPayload),
    }).subscribe({
      next: () => {
        this.saving.set(false);
        setTimeout(() => this.message.set(''), 3000);
      },
      error: () => {
        this.saving.set(false);
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
        this.closeAlertTickerSuggestions();
        this.loadAlerts();
      },
      error: () => this.alertMessage.set('✗ Erro ao criar alerta'),
    });
  }

  removeAlert(id: number): void {
    this.svc.deleteAlert(id).subscribe({ next: () => this.loadAlerts(), error: () => {} });
  }
}
