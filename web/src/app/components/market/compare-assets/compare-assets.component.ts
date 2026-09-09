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
import { PageHeaderComponent } from '../../page-header/page-header.component';
import { AsyncStateComponent } from '../../async-state/async-state.component';
import { SkeletonComponent } from '../../skeleton/skeleton.component';
import { SectionComponent } from '../../section/section.component';

const MAX_TICKERS = 4;

@Component({
  selector: 'app-compare-assets',
  standalone: true,
  imports: [
    PageHeaderComponent,
    CommonModule,
    RouterLink,
    EmptyStateComponent,
    MarginOfSafetyComponent,
    SkeletonComponent,
    AsyncStateComponent,
    SectionComponent,
  ],
  template: `
    <div class="flex flex-col gap-8">
      <section>
        <app-page-header title="Comparar ativos" />
        <p class="fi-body text-ink-2 m-0 mb-4 max-w-reading">
          Até {{ maxTickers }} ativos lado a lado. A decisão de cada um vem primeiro; os indicadores
          que a sustentam vêm depois, agrupados pela pergunta que respondem.
        </p>

        <div class="flex flex-wrap items-center gap-2 mb-3">
          @for (t of tickers(); track t) {
            <span class="tag tag-neutral flex items-center gap-1.5">
              {{ t }}
              <button
                type="button"
                (click)="removeTicker(t)"
                class="btn-quiet"
                [attr.aria-label]="'Remover ' + t + ' da comparação'"
              >
                ×
              </button>
            </span>
          }
        </div>

        <div class="flex flex-wrap items-start gap-2">
          @if (tickers().length < maxTickers) {
            <div class="relative w-full sm:w-[280px]">
              <label class="sr-only" for="compare-ticker">Adicionar ticker à comparação</label>
              <input
                id="compare-ticker"
                type="text"
                class="input uppercase"
                [value]="tickerInput()"
                (input)="onTickerInput($any($event.target).value)"
                (focus)="onTickerInput(tickerInput())"
                (focusout)="closeSuggestions()"
                (keydown.enter)="addTicker(tickerInput())"
                placeholder="Adicionar ticker (ex.: PETR4)"
                autocomplete="off"
              />
              @if (suggestionsOpen() && suggestions().length > 0) {
                <ul
                  class="absolute top-full left-0 right-0 mt-1 rounded-lg border border-hairline bg-ground-1 shadow-popover max-h-56 overflow-y-auto list-none m-0 p-0"
                  style="z-index: var(--fi-z-popover)"
                >
                  @for (s of suggestions(); track s.ticker) {
                    <li>
                      <button
                        type="button"
                        class="menu-item justify-between"
                        (mousedown)="$event.preventDefault(); addTicker(s.ticker)"
                      >
                        <span class="fi-ticker text-ink">{{ s.ticker }}</span>
                        <span class="fi-caption text-ink-3 truncate">{{ s.name }}</span>
                      </button>
                    </li>
                  }
                </ul>
              }
            </div>
          }

          <button
            type="button"
            class="btn-primary"
            (click)="compare()"
            [disabled]="loading() || tickers().length < 2"
          >
            {{ loading() ? 'Comparando…' : 'Comparar' }}
          </button>
        </div>

        @if (error()) {
          <p class="fi-caption text-attention m-0 mt-2">{{ error() }}</p>
        }
      </section>

      @if (erroDeRede()) {
        <app-async-state
          [error]="erroDeRede()"
          errorTitle="A comparação não foi montada"
          errorAction="comparar estes ativos"
          (retry)="compare()"
        />
      } @else if (loading()) {
        <div class="flex flex-col gap-5">
          <app-skeleton shape="title" />
          <app-skeleton shape="verdict" />
          <app-skeleton shape="row" [count]="5" />
        </div>
      } @else if (result(); as r) {
        @if (r.errors.length > 0) {
          <p class="fi-caption text-attention m-0">
            Não foi possível buscar: {{ r.errors.join(', ') }}
          </p>
        }

        @if (r.items.length > 0) {
          <app-section title="Decisão">
            <div
              class="grid gap-x-6 gap-y-6 grid-cols-1 sm:grid-cols-2"
              [class.lg:grid-cols-3]="r.items.length === 3"
              [class.lg:grid-cols-4]="r.items.length >= 4"
            >
              @for (item of r.items; track item.symbol) {
                <div class="flex flex-col gap-2 min-w-0">
                  <div class="flex items-baseline gap-2 flex-wrap">
                    <a
                      [routerLink]="['/ativo', item.symbol]"
                      class="fi-ticker text-ink no-underline hover:text-brand transition-colors"
                    >
                      {{ item.symbol }}
                    </a>
                    <span class="fi-caption text-ink-3">{{ typeLabel(item.asset_type) }}</span>
                  </div>

                  @if (item.name) {
                    <p class="fi-caption text-ink-3 m-0 truncate">{{ item.name }}</p>
                  }

                  <span
                    class="verdict-pill self-start"
                    [class]="ui.verdictClass(item.decision.verdict)"
                  >
                    {{ item.decision.label }}
                  </span>

                  <app-margin-of-safety [marginPct]="marginPct(item)" [reason]="marginReason" />

                  @if (item.decision.reasons.length > 0) {
                    <p class="fi-caption text-ink-2 m-0">{{ item.decision.reasons[0] }}</p>
                  }
                </div>
              }
            </div>
          </app-section>

          <app-section title="Evidência">
            <span sectionActions class="fi-caption text-ink-3">
              <span class="text-brand">•</span> marca o melhor da linha
            </span>

            <div class="overflow-x-auto">
              <table class="w-full border-collapse">
                <caption class="sr-only">
                  Indicadores comparados entre
                  {{
                    tickers().join(', ')
                  }}
                </caption>
                <thead>
                  <tr>
                    <th scope="col" class="text-left fi-caption text-ink-3 py-2 pr-3">Indicador</th>
                    @for (item of r.items; track item.symbol) {
                      <th
                        scope="col"
                        class="text-right fi-ticker text-ink py-2 pl-3 whitespace-nowrap"
                      >
                        {{ item.symbol }}
                      </th>
                    }
                  </tr>
                </thead>
                @for (group of visibleGroups(); track group) {
                  <tbody>
                    <tr>
                      <th
                        [attr.colspan]="r.items.length + 1"
                        scope="colgroup"
                        class="text-left fi-eyebrow text-ink-3 pt-5 pb-2 border-b border-hairline"
                      >
                        {{ group }}
                      </th>
                    </tr>
                    @for (metric of metricsOf(group); track metric.id) {
                      <tr class="border-b border-hairline">
                        <th scope="row" class="text-left fi-body text-ink-2 py-2 pr-3">
                          {{ metric.label }}
                        </th>
                        @for (item of r.items; track item.symbol) {
                          @if (applies(metric, item)) {
                            <td class="text-right fi-num text-ink py-2 pl-3 whitespace-nowrap">
                              @if (bestSymbol(metric) === item.symbol) {
                                <span class="text-brand" aria-hidden="true">•</span>
                                <span class="sr-only">melhor valor:</span>
                              }
                              {{ formatted(metric, item) }}
                            </td>
                          } @else {
                            <td class="text-right fi-caption text-ink-3 py-2 pl-3">
                              {{ notApplicableLabel(item) }}
                            </td>
                          }
                        }
                      </tr>
                    }
                  </tbody>
                }
              </table>
            </div>

            <p class="fi-caption text-ink-3 m-0 mt-4">
              Indicador ausente na fonte aparece como “—”. Indicador que não existe para a classe do
              ativo aparece dito por extenso — não é dado faltando, é pergunta que não se faz.
            </p>
          </app-section>
        }
      } @else {
        <app-empty-state
          icon="git-compare"
          title="Nenhuma comparação ainda"
          reason="A comparação precisa de ao menos dois ativos para existir: ela é sobre a diferença entre eles, não sobre cada um."
          nextStep="Adicione dois ou mais tickers acima. O recorte fica na URL, então o link pode ser salvo."
          actionLabel="Ver oportunidades"
          actionRoute="/descobrir/oportunidades"
        />
      }
    </div>
  `,
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
  /** Validação do formulário. A falha de rede é outra coisa, e mora em `erroDeRede`. */
  error = signal('');
  readonly erroDeRede = signal<unknown>(null);

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
    this.erroDeRede.set(null);
    this.loading.set(true);
    this.api.compareAssets(this.tickers()).subscribe({
      next: res => {
        this.result.set(res);
        this.loading.set(false);
      },
      error: err => {
        this.erroDeRede.set(err);
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
