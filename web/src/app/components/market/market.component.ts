import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import {
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import {
  AssetAnalysis,
  DipAnalysisResponse,
  DipScanItem,
  InvestmentStrategy,
  LoadingService,
  OpportunitiesResponse,
  QuickInvestResponse,
  RecommendService,
  RendaFixaAsset,
  RendaFixaCompareResponse,
  ReferenceRates,
  UiHelperService,
} from '../../core';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';
import { SectorsComponent } from '../sectors/sectors.component';

type MarketTab = 'opportunities' | 'investir' | 'ferramentas';
type OppMode = 'todas' | 'setores' | 'queda';
type ToolMode = 'analisar' | 'renda_fixa';

const FILTER_STORAGE_KEY = 'market_filters';
const CACHE_TTL_MS = 5 * 60 * 1000;

interface AnalyzeForm {
  symbol: FormControl<string>;
}

interface RendaFixaForm {
  tipo: FormControl<string>;
  nome: FormControl<string>;
  valor_investido: FormControl<number>;
  taxa: FormControl<number>;
  prazo_meses: FormControl<number>;
  tipo_taxa: FormControl<string>;
  percentual_cdi: FormControl<number | null>;
  liquidez: FormControl<string>;
}

@Component({
  selector: 'app-market',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    LucideAngularModule,
    HelpTooltipComponent,
    SectorsComponent,
  ],
  templateUrl: './market.component.html',
  styleUrls: ['./market.component.scss'],
})
export class MarketComponent implements OnInit, OnDestroy {
  private api = inject(RecommendService);
  readonly helper = inject(UiHelperService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);
  private fb = inject(FormBuilder);

  private filterDebounce$ = new Subject<void>();
  private destroy$ = new Subject<void>();
  private _cacheKey: string | null = null;
  _cacheTime: number | null = null;

  readonly activeTab = signal<MarketTab>('opportunities');
  readonly oppMode = signal<OppMode>('todas');
  readonly toolMode = signal<ToolMode>('analisar');
  readonly opportunities = signal<OpportunitiesResponse | null>(null);
  readonly loadingOpportunities = signal(false);
  readonly dipResults = signal<{ items: DipScanItem[] } | null>(null);
  readonly dipAnalysis = signal<DipAnalysisResponse | null>(null);
  readonly showAnalysis = signal(false);

  strategy = signal<InvestmentStrategy | null>(null);
  analyzeResult = signal<AssetAnalysis | null>(null);
  rfResult = signal<RendaFixaCompareResponse | null>(null);
  referenceRates = signal<ReferenceRates | null>(null);
  quickInvestResult = signal<QuickInvestResponse | null>(null);
  quickInvestLoading = signal(false);
  quickInvestError = signal(false);

  filterText = '';
  filterMinDy: number | null = null;
  filterMinMos: number | null = null;
  filterCategory = '';
  onlyInteresting = false;

  readonly currentPage = signal(1);
  readonly pageSize = 24;
  readonly skeletonItems = [1, 2, 3, 4, 5, 6];

  scanForm = this.fb.nonNullable.group({
    min_score: [40, [Validators.required, Validators.min(0), Validators.max(100)]],
    top: [12, [Validators.required, Validators.min(1), Validators.max(30)]],
    category: [''],
  });

  analyzeForm: FormGroup<AnalyzeForm> = this.fb.group({
    symbol: this.fb.control('VALE3', { nonNullable: true, validators: Validators.required }),
  });

  rfForms!: FormArray<FormGroup<RendaFixaForm>>;

  quickInvestForm = this.fb.nonNullable.group({
    cash_available: [1000, [Validators.required, Validators.min(1)]],
    min_order_value: [50, [Validators.required, Validators.min(1)]],
    use_current_goals: [true],
    prioritize_rebalance: [true],
  });

  ngOnInit() {
    this._restoreFilters();
    this.filterDebounce$
      .pipe(debounceTime(500), takeUntil(this.destroy$))
      .subscribe(() => this.loadOpportunities());

    this.loadOpportunities();
    this.rfForms = this.fb.array<FormGroup<RendaFixaForm>>([this._makeRFGroup()]);
    this.loadStrategy();
    this.api
      .getReferencRates()
      .subscribe({ next: r => this.referenceRates.set(r), error: () => {} });
    this.api.getPreferences().subscribe({
      next: p => {
        if (p.cash_available > 0) {
          this.quickInvestForm.patchValue({ cash_available: p.cash_available });
        }
      },
      error: () => {},
    });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private _filterKey(): string {
    return JSON.stringify({
      t: this.filterText,
      dy: this.filterMinDy,
      mos: this.filterMinMos,
      cat: this.filterCategory,
      int: this.onlyInteresting,
      p: this.currentPage(),
    });
  }

  private _saveFilters(): void {
    try {
      sessionStorage.setItem(FILTER_STORAGE_KEY, this._filterKey());
    } catch {}
  }

  private _restoreFilters(): void {
    try {
      const raw = sessionStorage.getItem(FILTER_STORAGE_KEY);
      if (!raw) return;
      const f = JSON.parse(raw);
      this.filterText = f.t ?? '';
      this.filterMinDy = f.dy ?? null;
      this.filterMinMos = f.mos ?? null;
      this.filterCategory = f.cat ?? '';
      this.onlyInteresting = f.int ?? false;
    } catch {}
  }

  onFilterChange() {
    this._saveFilters();
    this.currentPage.set(1);
    this.filterDebounce$.next();
  }

  goToPage(page: number) {
    this.currentPage.set(page);
    this.loadOpportunities(true);
  }

  loadOpportunities(force = false) {
    const key = this._filterKey();
    const now = Date.now();
    if (
      !force &&
      this._cacheKey === key &&
      this._cacheTime !== null &&
      now - this._cacheTime < CACHE_TTL_MS &&
      this.opportunities() !== null
    ) {
      return;
    }
    this.loadingOpportunities.set(true);
    this._cacheKey = key;
    this.api
      .opportunities(
        false,
        this.currentPage(),
        this.pageSize,
        'score',
        'desc',
        this.filterText,
        this.filterMinDy,
        this.filterMinMos,
        '',
        '',
        this.filterCategory,
        this.onlyInteresting
      )
      .subscribe({
        next: data => {
          this.opportunities.set(data);
          this._cacheTime = Date.now();
          this.loadingOpportunities.set(false);
        },
        error: () => this.loadingOpportunities.set(false),
      });
  }

  runScan() {
    if (this.scanForm.invalid) return;
    const { min_score, top, category } = this.scanForm.getRawValue();
    this.api
      .dipScanner(min_score, top, undefined, category || undefined)
      .subscribe(data => this.dipResults.set(data));
  }

  showOpportunityDetails(ticker: string) {
    this.showDipAnalysis(ticker);
  }

  showDipAnalysis(ticker: string) {
    this.api.dipAnalysis(ticker).subscribe(data => {
      this.dipAnalysis.set(data);
      this.showAnalysis.set(true);
    });
  }

  closeAnalysis() {
    this.showAnalysis.set(false);
    this.dipAnalysis.set(null);
  }

  submitAnalyze(): void {
    if (this.analyzeForm.invalid) return;
    const { symbol } = this.analyzeForm.getRawValue();
    this.api.analyzeAsset(symbol).subscribe({
      next: res => this.analyzeResult.set(res),
      error: () => {},
    });
  }

  loadStrategy(): void {
    this.api.getStrategy().subscribe({
      next: data => this.strategy.set(data),
      error: () => {},
    });
  }

  runQuickInvest(): void {
    if (this.quickInvestForm.invalid) return;
    this.quickInvestLoading.set(true);
    this.quickInvestError.set(false);
    this.quickInvestResult.set(null);
    const v = this.quickInvestForm.getRawValue();
    this.api
      .quickInvest({
        cash_available: v.cash_available,
        use_current_goals: v.use_current_goals,
        prioritize_rebalance: v.prioritize_rebalance,
        min_order_value: v.min_order_value,
      })
      .subscribe({
        next: r => {
          this.quickInvestResult.set(r);
          this.quickInvestLoading.set(false);
        },
        error: () => {
          this.quickInvestError.set(true);
          this.quickInvestLoading.set(false);
        },
      });
  }

  private _makeRFGroup(): FormGroup<RendaFixaForm> {
    return this.fb.group<RendaFixaForm>({
      tipo: this.fb.control('cdb', { nonNullable: true }),
      nome: this.fb.control('', { nonNullable: true }),
      valor_investido: this.fb.control(10000, { nonNullable: true, validators: Validators.min(1) }),
      taxa: this.fb.control(12.0, { nonNullable: true, validators: Validators.min(0.01) }),
      prazo_meses: this.fb.control(12, { nonNullable: true, validators: Validators.min(1) }),
      tipo_taxa: this.fb.control('pre_fixado', { nonNullable: true }),
      percentual_cdi: this.fb.control<number | null>(110),
      liquidez: this.fb.control('no_vencimento', { nonNullable: true }),
    });
  }

  addRFAtivo(): void {
    this.rfForms.push(this._makeRFGroup());
  }

  removeRFAtivo(i: number): void {
    this.rfForms.removeAt(i);
  }

  onTipoChange(i: number): void {
    const ctrl = this.rfForms.controls[i];
    const tipo = ctrl.controls.tipo.value;
    if (['lci', 'lca', 'cri', 'cra'].includes(tipo)) {
      ctrl.controls.tipo_taxa.setValue('pos_fixado');
    } else if (tipo === 'tesouro_selic') {
      ctrl.controls.tipo_taxa.setValue('pos_fixado');
    } else if (tipo === 'tesouro_ipca') {
      ctrl.controls.tipo_taxa.setValue('hibrido');
    } else if (tipo === 'tesouro_pre') {
      ctrl.controls.tipo_taxa.setValue('pre_fixado');
    }
  }

  onTaxaTipoChange(i: number): void {
    const ctrl = this.rfForms.controls[i];
    if (ctrl.controls.tipo_taxa.value !== 'pos_fixado') {
      ctrl.controls.percentual_cdi.setValue(null);
    } else {
      ctrl.controls.percentual_cdi.setValue(110);
    }
  }

  compareRF(): void {
    const ativos: RendaFixaAsset[] = this.rfForms.controls.map(ctrl => {
      const v = ctrl.getRawValue();
      return {
        tipo: v.tipo as any,
        nome: v.nome || null,
        valor_investido: v.valor_investido,
        taxa: v.taxa,
        prazo_meses: v.prazo_meses,
        tipo_taxa: v.tipo_taxa as any,
        percentual_cdi: v.tipo_taxa === 'pos_fixado' ? v.percentual_cdi : null,
        liquidez: v.liquidez as any,
      };
    });
    const cdi = this.referenceRates()?.cdi_anual ?? null;
    const selic = this.referenceRates()?.selic_anual ?? null;
    this.api.compareRendaFixa({ ativos, cdi_anual: cdi, selic_anual: selic }).subscribe({
      next: r => this.rfResult.set(r),
      error: () => {},
    });
  }

  riskClass(risk: string): string {
    return { Baixo: 'tag-success', Médio: 'tag-warning', Alto: 'tag-danger' }[risk] || 'tag-muted';
  }

  totalToInvest(s: InvestmentStrategy): number {
    return s.suggestions.reduce((sum, x) => sum + x.invest_amount, 0);
  }

  verdictClassFromString(v: string): string {
    if (v === 'STRONG_BUY' || v === 'BUY') return 'v-buy';
    if (v === 'STRONG_SELL' || v === 'SELL') return 'v-sell';
    if (v === 'HOLD') return 'v-hold';
    return 'v-unknown';
  }

  assetLabel(type: string): string {
    return this.ui.assetTypeLabel(type as any);
  }

  rfTipoLabel(tipo: string): string {
    return (
      {
        cdb: 'CDB',
        lci: 'LCI',
        lca: 'LCA',
        tesouro_selic: 'Tesouro Selic',
        tesouro_ipca: 'Tesouro IPCA+',
        tesouro_pre: 'Tesouro Pré',
        lc: 'LC',
        cri: 'CRI',
        cra: 'CRA',
      }[tipo] || tipo.toUpperCase()
    );
  }

  getCategoryBarColor(category: string): string {
    return this.ui.categoryBarColor(category);
  }
}
