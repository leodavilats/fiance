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
  template: `
    <div class="max-w-reading">
      <section>
        <h1 class="fi-title text-ink m-0">O que eu poderia comprar</h1>
        <p class="fi-body text-ink-2 m-0 mt-1">
          Ativos da B3 que o sistema conseguiu avaliar e que aparecem por um motivo declarado — não
          é a lista do mercado inteiro.
        </p>

        <!-- veredito: a leitura do sistema sobre a lista inteira, antes de qualquer linha -->
        @if (vereditoDaLista(); as frase) {
          <p class="fi-verdict text-ink m-0 mt-4 max-w-reading">{{ frase }}</p>
        }
        @if (recorte(); as r) {
          <p class="fi-caption text-ink-3 m-0 mt-1">{{ r }}</p>
        }

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
          <div class="relative">
            <label for="opp-search" class="fi-caption text-ink-3 block mb-1">Ticker ou nome</label>
            <input
              id="opp-search"
              type="text"
              placeholder="PETR4, Vale…"
              class="input"
              autocomplete="off"
              [(ngModel)]="filterText"
              (ngModelChange)="onFilterTextInput(filterText)"
              (focus)="onFilterTextInput(filterText)"
              (focusout)="closeTickerSuggestions()"
            />
            @if (tickerSuggestionsOpen() && tickerSuggestions().length > 0) {
              <ul
                class="absolute top-full left-0 right-0 mt-1 z-popover list-none m-0 p-0 rounded-lg border border-hairline bg-ground-1 shadow-popover max-h-56 overflow-y-auto"
              >
                @for (s of tickerSuggestions(); track s.ticker) {
                  <li>
                    <button
                      type="button"
                      class="menu-item justify-between"
                      (mousedown)="$event.preventDefault(); selectTickerSuggestion(s)"
                    >
                      <span class="fi-ticker text-ink">{{ s.ticker }}</span>
                      <span class="fi-caption text-ink-3 truncate">{{ s.name }}</span>
                    </button>
                  </li>
                }
              </ul>
            }
          </div>

          <div>
            <label for="opp-dy" class="fi-caption text-ink-3 block mb-1">DY mínimo (%)</label>
            <input
              id="opp-dy"
              type="number"
              class="input"
              [(ngModel)]="filterMinDy"
              (ngModelChange)="onFilterChange()"
            />
          </div>

          <div>
            <label for="opp-mos" class="fi-caption text-ink-3 block mb-1">Margem mínima (%)</label>
            <input
              id="opp-mos"
              type="number"
              class="input"
              [(ngModel)]="filterMinMos"
              (ngModelChange)="onFilterChange()"
            />
          </div>

          <div>
            <label for="opp-cat" class="fi-caption text-ink-3 block mb-1">Categoria</label>
            <select
              id="opp-cat"
              class="input"
              [(ngModel)]="filterCategory"
              (ngModelChange)="onFilterChange()"
            >
              <option value="">Todas</option>
              <option value="acoes_br">Ações BR</option>
              <option value="bdrs">BDRs</option>
              <option value="fiis">FIIs</option>
              <option value="etfs">ETFs</option>
            </select>
          </div>
        </div>

        <div class="flex items-center gap-4 mt-3 flex-wrap">
          <label class="flex items-center gap-2 cursor-pointer fi-label text-ink">
            <input
              type="checkbox"
              class="accent-brand cursor-pointer"
              [(ngModel)]="onlyInteresting"
              (ngModelChange)="onFilterChange()"
            />
            Só o que o sistema destacou
          </label>
          <button type="button" class="btn-secondary compact-btn" (click)="loadOpportunities(true)">
            <lucide-icon name="refresh-cw" size="14"></lucide-icon> Atualizar
          </button>
        </div>
      </section>

      @if (loadingOpportunities()) {
        <div class="mt-8 flex flex-col gap-6">
          <app-skeleton shape="title" />
          <app-skeleton shape="row" [count]="6" />
        </div>
      } @else if (opportunities(); as opps) {
        @if (opps.items.length === 0) {
          <div class="mt-6">
            <app-empty-state
              icon="search-x"
              title="Nenhum ativo passou por estes filtros"
              reason="Os critérios atuais não deixaram passar nenhum ativo do universo varrido. Filtro estreito não é ausência de oportunidade — é ausência de resultado para essa combinação."
              nextStep="Limpar os filtros mostra a lista completa, ordenada pela leitura do sistema."
              actionLabel="Limpar filtros"
              (action)="clearFilters()"
              secondaryLabel="Ver quedas recentes"
              secondaryRoute="/descobrir/quedas"
            />
          </div>
        } @else {
          <section class="mt-8">
            <div class="flex items-baseline justify-between gap-3 mb-2">
              <p class="fi-eyebrow text-ink-3 m-0">
                <span class="fi-num">{{ opps.items.length }}</span> de
                <span class="fi-num">{{ opps.total_items }}</span> ativos avaliados
              </p>
              @if (_cacheTime) {
                <p class="fi-caption text-ink-3 m-0">
                  Atualizado {{ helper.formatTimestamp(_cacheTime / 1000) }}
                </p>
              }
            </div>

            <ul class="list-none m-0 p-0">
              @for (opp of opps.items; track opp.ticker) {
                <li class="py-5 border-t border-hairline">
                  <div class="flex items-start justify-between gap-4 flex-wrap sm:flex-nowrap">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap">
                        <a
                          [routerLink]="['/ativo', opp.ticker]"
                          class="fi-ticker text-ink no-underline hover:text-brand"
                        >
                          {{ opp.ticker }}
                        </a>
                        <span class="verdict-pill" [class]="helper.verdictClass(opp.verdict)">
                          {{ opp.label }}
                        </span>
                        @if (opp.in_portfolio) {
                          <span class="tag tag-brand">Já na carteira</span>
                        }
                      </div>

                      @if (opp.name) {
                        <p class="fi-caption text-ink-3 m-0 mt-0.5">
                          {{ opp.name }}
                          @if (opp.sector) {
                            · {{ helper.translateSector(opp.sector) }}
                          }
                        </p>
                      }

                      <p class="fi-verdict-sm text-ink m-0 mt-2">{{ reasonFor(opp) }}</p>

                      @if (opp.reasons.length > 0) {
                        <details class="mt-2">
                          <summary
                            class="fi-caption text-ink-3 cursor-pointer fi-focusable rounded-sm"
                          >
                            O que sustenta ({{ opp.reasons.length }})
                          </summary>
                          <ul class="list-none m-0 mt-1 p-0 flex flex-col gap-1">
                            @for (reason of opp.reasons; track reason) {
                              <li class="fi-caption text-ink-2">{{ reason }}</li>
                            }
                          </ul>
                        </details>
                      }

                      <dl class="grid grid-cols-2 sm:grid-cols-5 gap-x-5 gap-y-2 m-0 mt-3">
                        <div>
                          <dt class="fi-caption text-ink-3">Preço</dt>
                          <dd class="fi-metric-sm text-ink m-0 fi-num">
                            {{ opp.price != null ? (opp.price | currency: 'BRL') : '—' }}
                          </dd>
                        </div>
                        <div>
                          <dt class="fi-caption text-ink-3">Bazin</dt>
                          @if (opp.bazin) {
                            <dd class="fi-metric-sm text-ink m-0 fi-num">
                              {{ opp.bazin | currency: 'BRL' }}
                            </dd>
                          } @else {
                            <dd class="fi-caption text-indeterminate m-0">sem histórico</dd>
                          }
                        </div>
                        <div>
                          <dt class="fi-caption text-ink-3">
                            {{ !opp.graham && opp.pvp ? 'P/VP' : 'Graham' }}
                          </dt>
                          @if (opp.graham) {
                            <dd class="fi-metric-sm text-ink m-0 fi-num">
                              {{ opp.graham | currency: 'BRL' }}
                            </dd>
                          } @else if (opp.pvp) {
                            <dd class="fi-metric-sm text-ink m-0 fi-num">
                              {{ opp.pvp | number: '1.2-2' }}
                            </dd>
                          } @else {
                            <dd class="fi-caption text-indeterminate m-0">não se aplica</dd>
                          }
                        </div>
                        <div>
                          <dt class="fi-caption text-ink-3">
                            Margem
                            <app-help-tooltip
                              term="margem de segurança"
                              [text]="helper.glossary['ms']"
                            />
                          </dt>
                          @if (marginPct(opp) != null) {
                            <dd class="fi-metric-sm text-ink m-0 fi-num">
                              {{ marginPct(opp)! > 0 ? '+' : ''
                              }}{{ marginPct(opp) | number: '1.0-0' }}%
                            </dd>
                          } @else {
                            <dd class="fi-caption text-indeterminate m-0">sem preço justo</dd>
                          }
                        </div>
                        <div>
                          <dt class="fi-caption text-ink-3">
                            DY
                            <app-help-tooltip
                              term="dividend yield"
                              [text]="helper.glossary['dy']"
                            />
                          </dt>
                          @if (opp.dividend_yield) {
                            <dd class="fi-metric-sm text-ink m-0 fi-num">
                              {{ opp.dividend_yield | number: '1.1-1' }}%
                            </dd>
                          } @else {
                            <dd class="fi-caption text-indeterminate m-0">sem proventos</dd>
                          }
                        </div>
                      </dl>
                    </div>

                    <div class="shrink-0 w-[150px]">
                      <app-score-ruler
                        [score]="opp.score"
                        [bands]="scoreBands"
                        [dataCompleteness]="opp.data_completeness"
                        size="list"
                        subject="Leitura de {{ opp.ticker }}"
                      />
                      <p class="fi-caption text-ink-3 m-0 mt-1">
                        {{ helper.dataYearsLabel(opp.data_years) }} ·
                        {{ helper.consensusLabel(opp.consensus_methods) }}
                      </p>

                      <div class="flex flex-col gap-2 mt-3">
                        <a
                          [routerLink]="['/ativo', opp.ticker]"
                          class="btn-secondary compact-btn no-underline"
                        >
                          Ver ativo
                        </a>
                        @if (houveQueda(opp)) {
                          <button
                            type="button"
                            class="btn-secondary compact-btn"
                            (click)="showOpportunityDetails(opp.ticker)"
                          >
                            Por que caiu?
                          </button>
                        }
                      </div>
                    </div>
                  </div>
                </li>
              }
            </ul>
          </section>

          @if (opps.total_pages > 1) {
            <nav class="flex items-center justify-center gap-2 mt-6" aria-label="Paginação">
              <button
                type="button"
                class="btn-secondary compact-btn"
                [disabled]="opps.current_page <= 1"
                [title]="opps.current_page <= 1 ? 'Você já está na primeira página' : ''"
                (click)="goToPage(opps.current_page - 1)"
              >
                <lucide-icon name="chevron-left" size="14"></lucide-icon> Anterior
              </button>
              <span class="fi-caption text-ink-2">
                Página <span class="fi-num">{{ opps.current_page }}</span> de
                <span class="fi-num">{{ opps.total_pages }}</span>
              </span>
              <button
                type="button"
                class="btn-secondary compact-btn"
                [disabled]="opps.current_page >= opps.total_pages"
                [title]="
                  opps.current_page >= opps.total_pages ? 'Você já está na última página' : ''
                "
                (click)="goToPage(opps.current_page + 1)"
              >
                Próxima <lucide-icon name="chevron-right" size="14"></lucide-icon>
              </button>
            </nav>
          }

          <app-provenance
            method="Score 0–100 combinando margem de segurança, proventos, qualidade e endividamento, ponderados pelo seu perfil (backend/app/analysis/scoring.py). Bazin, Graham e P/VP são calculados separadamente e nunca somados num número único."
            source="Cotações e fundamentos via BRAPI."
            limitation="Leitura do sistema sobre dados públicos, não recomendação de compra. Universo limitado à B3."
          />
        }
      }
    </div>
  `,
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
