import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import {
  AssetAnalysis,
  AssetFundamentals,
  CompareResponse,
  RecommendService,
  TickerSuggestion,
  UiHelperService,
} from '../../../core';

const MAX_TICKERS = 4;

@Component({
  selector: 'app-compare-assets',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './compare-assets.component.html',
})
export class CompareAssetsComponent implements OnInit, OnDestroy {
  private api = inject(RecommendService);
  private route = inject(ActivatedRoute);
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
  }

  removeTicker(ticker: string): void {
    this.tickers.update(list => list.filter(t => t !== ticker));
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

  fundamental(item: AssetAnalysis, key: keyof AssetFundamentals): number | null {
    return item.fundamentals[key] ?? null;
  }
}
