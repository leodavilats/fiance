import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import {
  DipAnalysisService,
  OpportunitiesResponse,
  RecommendService,
  TickerSuggestion,
  UiHelperService,
} from '../../../core';
import { HelpTooltipComponent } from '../../help-tooltip/help-tooltip.component';

const FILTER_STORAGE_KEY = 'market_filters';
const CACHE_TTL_MS = 5 * 60 * 1000;

@Component({
  selector: 'app-opportunities-list',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule, RouterLink, HelpTooltipComponent],
  templateUrl: './opportunities-list.component.html',
  styleUrls: ['./opportunities-list.component.scss'],
})
export class OpportunitiesListComponent implements OnInit, OnDestroy {
  private api = inject(RecommendService);
  readonly helper = inject(UiHelperService);

  private readonly dip = inject(DipAnalysisService);
  private readonly router = inject(Router);

  private filterDebounce$ = new Subject<void>();
  private tickerSearch$ = new Subject<string>();
  private destroy$ = new Subject<void>();

  readonly tickerSuggestions = signal<TickerSuggestion[]>([]);
  readonly tickerSuggestionsOpen = signal(false);
  private _cacheKey: string | null = null;
  _cacheTime: number | null = null;

  readonly opportunities = signal<OpportunitiesResponse | null>(null);
  readonly loadingOpportunities = signal(false);

  filterText = '';
  filterMinDy: number | null = null;
  filterMinMos: number | null = null;
  filterCategory = '';
  onlyInteresting = false;

  readonly currentPage = signal(1);
  readonly pageSize = 24;
  readonly skeletonItems = [1, 2, 3, 4, 5, 6];

  ngOnInit() {
    this._restoreFilters();
    this.filterDebounce$
      .pipe(debounceTime(500), takeUntil(this.destroy$))
      .subscribe(() => this.loadOpportunities());

    this.tickerSearch$
      .pipe(
        debounceTime(1000),
        switchMap(query => {
          if (query.trim().length < 1) return [[] as TickerSuggestion[]];
          return this.api.searchTickers(query).pipe(switchMap(res => [res.items]));
        }),
        takeUntil(this.destroy$)
      )
      .subscribe(items => this.tickerSuggestions.set(items));

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

  onFilterTextInput(value: string): void {
    this.filterText = value;
    this.tickerSuggestionsOpen.set(true);
    this.tickerSearch$.next(value);
    this.onFilterChange();
  }

  selectTickerSuggestion(suggestion: TickerSuggestion): void {
    this.filterText = suggestion.ticker;
    this.closeTickerSuggestions();
    this.onFilterChange();
  }

  closeTickerSuggestions(): void {
    this.tickerSuggestionsOpen.set(false);
    this.tickerSuggestions.set([]);
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

  openAsset(ticker: string): void {
    this.router.navigate(['/ativo', ticker]);
  }

  showOpportunityDetails(ticker: string) {
    this.dip.show(ticker);
  }
}
