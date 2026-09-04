import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { Subject } from 'rxjs';
import { debounceTime, switchMap, takeUntil } from 'rxjs/operators';
import {
  DipAnalysisService,
  OpportunitiesResponse,
  Opportunity,
  RecommendService,
  TickerSuggestion,
  UiHelperService,
  fiScoreBands,
} from '../../../core';
import { EmptyStateComponent } from '../../empty-state/empty-state.component';
import { HelpTooltipComponent } from '../../help-tooltip/help-tooltip.component';
import { ProvenanceComponent } from '../../provenance/provenance.component';
import { ScoreRulerComponent } from '../../score-ruler/score-ruler.component';
import { SkeletonComponent } from '../../skeleton/skeleton.component';

const CACHE_TTL_MS = 5 * 60 * 1000;

@Component({
  selector: 'app-opportunities-list',
  standalone: true,
  imports: [
    CommonModule,
    EmptyStateComponent,
    FormsModule,
    HelpTooltipComponent,
    LucideAngularModule,
    ProvenanceComponent,
    RouterLink,
    ScoreRulerComponent,
    SkeletonComponent,
  ],
  templateUrl: './opportunities-list.component.html',
})
export class OpportunitiesListComponent implements OnInit, OnDestroy {
  readonly scoreBands = fiScoreBands;

  private api = inject(RecommendService);
  readonly helper = inject(UiHelperService);

  private readonly dip = inject(DipAnalysisService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

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

  readonly vereditoDaLista = computed<string | null>(() => {
    const res = this.opportunities();
    if (!res || res.items.length === 0) return null;

    const amplos = res.items.filter(o => (o.margin_of_safety ?? 0) >= 0.25).length;
    const destacados = res.items.filter(o => o.is_interesting).length;

    const base = `${res.total_items} de ${res.universe_size} ativos avaliados passaram pelos seus critérios`;

    if (amplos > 0) {
      const plural = amplos === 1 ? 'está' : 'estão';
      return `${base}; ${amplos} ${plural} pelo menos 25% abaixo do preço justo estimado.`;
    }
    if (destacados > 0) {
      const plural = destacados === 1 ? 'destacado' : 'destacados';
      return `${base}; ${destacados} ${plural} pela leitura do sistema, nenhum com desconto amplo.`;
    }
    return `${base}, e nenhum com desconto amplo hoje.`;
  });

  readonly recorte = computed<string | null>(() => {
    const partes: string[] = [];
    if (this.filterText.trim()) partes.push(`busca "${this.filterText.trim()}"`);
    if (this.filterCategory) partes.push(this.helper.categoryLabel(this.filterCategory));
    if (this.filterMinDy != null) partes.push(`DY ≥ ${this.filterMinDy}%`);
    if (this.filterMinMos != null) partes.push(`margem ≥ ${this.filterMinMos}%`);
    if (this.onlyInteresting) partes.push('só o que o sistema destacou');
    return partes.length ? `Recorte: ${partes.join(' · ')}` : null;
  });

  houveQueda(opp: Opportunity): boolean {
    return (opp.margin_of_safety ?? 0) > 0;
  }

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

  private _syncFilters(): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        q: this.filterText || null,
        dy: this.filterMinDy ?? null,
        mos: this.filterMinMos ?? null,
        cat: this.filterCategory || null,
        destaque: this.onlyInteresting ? '1' : null,
        p: this.currentPage() > 1 ? this.currentPage() : null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  private _restoreFilters(): void {
    const q = this.route.snapshot.queryParamMap;
    this.filterText = q.get('q') ?? '';
    this.filterMinDy = q.get('dy') != null ? Number(q.get('dy')) : null;
    this.filterMinMos = q.get('mos') != null ? Number(q.get('mos')) : null;
    this.filterCategory = q.get('cat') ?? '';
    this.onlyInteresting = q.get('destaque') === '1';
    const page = Number(q.get('p') ?? 1);
    if (Number.isFinite(page) && page > 1) this.currentPage.set(page);
  }

  onFilterChange() {
    this.currentPage.set(1);
    this._syncFilters();
    this.filterDebounce$.next();
  }

  clearFilters(): void {
    this.filterText = '';
    this.filterMinDy = null;
    this.filterMinMos = null;
    this.filterCategory = '';
    this.onlyInteresting = false;
    this.onFilterChange();
    this.loadOpportunities(true);
  }

  reasonFor(opp: Opportunity): string {
    const first = opp.reasons[0];
    if (first) return first;
    if (opp.margin_of_safety != null && opp.margin_of_safety > 0) {
      const pct = Math.round(opp.margin_of_safety * 100);
      return `Negocia ${pct}% abaixo do preço justo estimado, com dados suficientes para avaliar.`;
    }
    return 'Aparece pela leitura combinada de preço, proventos e qualidade.';
  }

  marginPct(opp: Opportunity): number | null {
    return opp.margin_of_safety == null ? null : opp.margin_of_safety * 100;
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
    this._syncFilters();
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
