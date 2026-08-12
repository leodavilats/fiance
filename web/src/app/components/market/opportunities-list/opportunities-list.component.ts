import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import { OpportunitiesResponse, RecommendService, UiHelperService } from '../../../core';
import { HelpTooltipComponent } from '../../help-tooltip/help-tooltip.component';

const FILTER_STORAGE_KEY = 'market_filters';
const CACHE_TTL_MS = 5 * 60 * 1000;

@Component({
  selector: 'app-opportunities-list',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule, HelpTooltipComponent],
  templateUrl: './opportunities-list.component.html',
  styleUrls: ['./opportunities-list.component.scss'],
})
export class OpportunitiesListComponent implements OnInit, OnDestroy {
  private api = inject(RecommendService);
  readonly helper = inject(UiHelperService);

  readonly analyze = output<string>();

  private filterDebounce$ = new Subject<void>();
  private destroy$ = new Subject<void>();
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
          this._cacheTime = Date.now();
          this.loadingOpportunities.set(false);
        },
        error: () => this.loadingOpportunities.set(false),
      });
  }

  showOpportunityDetails(ticker: string) {
    this.analyze.emit(ticker);
  }
}
