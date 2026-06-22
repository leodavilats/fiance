import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import {
  DipAnalysisResponse,
  DipScanItem,
  OpportunitiesResponse,
  RecommendService,
  UiHelperService,
} from '../../core';
import { HelpTooltipComponent } from '../help-tooltip/help-tooltip.component';

type MarketTab = 'opportunities' | 'dip-scanner';

const FILTER_STORAGE_KEY = 'market_filters';
const CACHE_TTL_MS = 5 * 60 * 1000;

@Component({
  selector: 'app-market',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    LucideAngularModule,
    HelpTooltipComponent,
  ],
  templateUrl: './market.component.html',
  styleUrls: ['./market.component.scss'],
})
export class MarketComponent implements OnInit, OnDestroy {
  private api = inject(RecommendService);
  readonly helper = inject(UiHelperService);
  private fb = inject(FormBuilder);

  private filterDebounce$ = new Subject<void>();
  private destroy$ = new Subject<void>();
  private _cacheKey: string | null = null;
  _cacheTime: number | null = null;

  readonly activeTab = signal<MarketTab>('opportunities');
  readonly opportunities = signal<OpportunitiesResponse | null>(null);
  readonly loadingOpportunities = signal(false);
  readonly dipResults = signal<{ items: DipScanItem[] } | null>(null);
  readonly dipAnalysis = signal<DipAnalysisResponse | null>(null);
  readonly showAnalysis = signal(false);

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

  ngOnInit() {
    this._restoreFilters();
    this.filterDebounce$
      .pipe(debounceTime(500), takeUntil(this.destroy$))
      .subscribe(() => this.loadOpportunities());

    this.loadOpportunities();
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
          this._cacheTime = Date.now(); // public for template
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
}
