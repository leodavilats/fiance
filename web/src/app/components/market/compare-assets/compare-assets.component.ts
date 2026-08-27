import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import {
  AssetAnalysis,
  AssetType,
  CompareResponse,
  RecommendService,
  TickerSuggestion,
  UiHelperService,
} from '../../../core';
import {
  ASSET_TYPE_LABEL,
  COMPARE_GROUPS,
  COMPARE_METRICS,
  CompareMetric,
} from './compare-metrics';
import { EmptyStateComponent } from '../../empty-state/empty-state.component';
import { MarginOfSafetyComponent } from '../../margin-of-safety/margin-of-safety.component';

const MAX_TICKERS = 4;

@Component({
  selector: 'app-compare-assets',
  standalone: true,
  imports: [CommonModule, RouterLink, EmptyStateComponent, MarginOfSafetyComponent],
  templateUrl: './compare-assets.component.html',
})
export class CompareAssetsComponent implements OnInit, OnDestroy {
  private api = inject(RecommendService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  readonly ui = inject(UiHelperService);

  private destroy$ = new Subject<void>();
  private tickerSearch$ = new Subject<string>();

  tickerInput = signal('');
  tickers = signal<string[]>([]);
  suggestions = signal<TickerSuggestion[]>([]);
  suggestionsOpen = signal(false);

  loading = signal(false);
  result = signal<CompareResponse | null>(null);
  error = signal('');

  readonly maxTickers = MAX_TICKERS;
  readonly marginReason = 'Nenhum método de valuation se aplica a este ativo.';

  ngOnInit(): void {
    this.tickerSearch$
      .pipe(
        debounceTime(250),
        switchMap(query => {
          if (query.trim().length < 1) return [[] as TickerSuggestion[]];
          return this.api.searchTickers(query).pipe(switchMap(res => [res.items]));
        }),
        takeUntil(this.destroy$)
      )
      .subscribe(items => this.suggestions.set(items));

    const fromQuery = this.route.snapshot.queryParamMap.get('tickers');
    if (fromQuery) {
      const tickers = fromQuery
        .split(',')
        .map(t => t.trim().toUpperCase())
        .filter(Boolean)
        .slice(0, MAX_TICKERS);
      if (tickers.length > 0) {
        this.tickers.set(tickers);
        this.compare();
      }
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onTickerInput(value: string): void {
    this.tickerInput.set(value);
    this.suggestionsOpen.set(true);
    this.tickerSearch$.next(value);
  }

  addTicker(ticker: string): void {
    const t = ticker.trim().toUpperCase();
    if (!t || this.tickers().includes(t) || this.tickers().length >= MAX_TICKERS) return;
    this.tickers.update(list => [...list, t]);
    this.tickerInput.set('');
    this.closeSuggestions();
    this.syncUrl();
  }

  removeTicker(ticker: string): void {
    this.tickers.update(list => list.filter(t => t !== ticker));
    this.syncUrl();
  }

  private syncUrl(): void {
    const tickers = this.tickers();
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tickers: tickers.length > 0 ? tickers.join(',') : null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  closeSuggestions(): void {
    this.suggestionsOpen.set(false);
    this.suggestions.set([]);
  }

  compare(): void {
    if (this.tickers().length < 2) {
      this.error.set('Adicione ao menos 2 ativos para comparar.');
      return;
    }
    this.error.set('');
    this.loading.set(true);
    this.api.compareAssets(this.tickers()).subscribe({
      next: res => {
        this.result.set(res);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Não foi possível comparar os ativos agora.');
        this.loading.set(false);
      },
    });
  }

  readonly groups = COMPARE_GROUPS;

  readonly visibleGroups = computed(() => {
    const items = this.result()?.items ?? [];
    if (items.length === 0) return [] as string[];
    return this.groups.filter(g => this.metricsOf(g).length > 0);
  });

  metricsOf(group: string): readonly CompareMetric[] {
    const items = this.result()?.items ?? [];
    return COMPARE_METRICS.filter(
      m => m.group === group && items.some(i => this.applies(m, i) && m.value(i) !== null)
    );
  }

  applies(metric: CompareMetric, item: AssetAnalysis): boolean {
    return metric.appliesTo.includes(item.asset_type);
  }

  notApplicableLabel(item: AssetAnalysis): string {
    return `não se aplica a ${this.typeLabel(item.asset_type)}`;
  }

  typeLabel(type: AssetType): string {
    return ASSET_TYPE_LABEL[type] ?? type;
  }

  formatted(metric: CompareMetric, item: AssetAnalysis): string {
    const v = metric.value(item);
    if (v === null) return '—';
    switch (metric.format) {
      case 'money':
        return v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      case 'pct':
        return `${v.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
      case 'ratio':
        return v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      default:
        return v.toLocaleString('pt-BR', { maximumFractionDigits: 0 });
    }
  }

  bestSymbol(metric: CompareMetric): string | null {
    if (!metric.direction) return null;
    const candidates = (this.result()?.items ?? [])
      .filter(i => this.applies(metric, i))
      .map(i => ({ symbol: i.symbol, v: metric.value(i) }))
      .filter((c): c is { symbol: string; v: number } => c.v !== null);
    if (candidates.length < 2) return null;
    const best = candidates.reduce((a, b) =>
      metric.direction === 'higher' ? (b.v > a.v ? b : a) : b.v < a.v ? b : a
    );
    if (candidates.filter(c => c.v === best.v).length > 1) return null;
    return best.symbol;
  }

  marginPct(item: AssetAnalysis): number | null {
    const m = item.fair_price.margin_of_safety;
    return m == null ? null : m * 100;
  }
}
