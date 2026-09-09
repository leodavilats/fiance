import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CashflowService,
  InvestmentStrategy,
  LoadingService,
  RecommendService,
  UiHelperService,
  allocationScalePct,
  nomeDoMes,
} from '../../core';
import { AllocationGapComponent } from '../allocation-gap/allocation-gap.component';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { RebalanceSuggestionsComponent } from '../market/rebalance-suggestions/rebalance-suggestions.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';
import { PageHeaderComponent } from '../page-header/page-header.component';

interface ProjectionRow {
  readonly category: string;
  readonly currentPct: number;
  readonly projectedPct: number;
}

@Component({
  selector: 'app-strategy',
  standalone: true,
  imports: [
    PageHeaderComponent,
    AllocationGapComponent,
    CommonModule,
    EmptyStateComponent,
    LucideAngularModule,
    RebalanceSuggestionsComponent,
    RouterLink,
    SkeletonComponent,
  ],
  template: `
    <div class="max-w-column">
      <app-page-header
        title="Alocação × meta"
        question="Onde minha carteira está longe do que eu declarei?"
      />

      @if (strategy(); as s) {
        <section>
          <p class="fi-eyebrow text-ink-3 m-0 mb-2">O plano de hoje</p>
          <p class="fi-verdict text-ink m-0">{{ s.summary }}</p>

          <p class="fi-body text-ink-2 m-0 mt-3">
            Perfil <strong class="text-ink">{{ s.profile.type }}</strong
            >, risco
            <span class="tag" [class]="riskClass()">{{ s.profile.risk_tolerance }}</span>
            · patrimônio de
            <span class="fi-num text-ink">{{ s.total_capital | currency: 'BRL' }}</span> · caixa de
            <span class="fi-num text-ink">{{ s.cash_available | currency: 'BRL' }}</span> (<span
              class="fi-num"
              >{{ cashPct(s) | number: '1.1-1' }}</span
            >%)
          </p>

          <p class="fi-caption text-ink-3 m-0 mt-1">
            @if (origemDoCaixa(); as o) {
              {{ o }}
            }
            @if (mesDoCaixa()) {
              <a routerLink="/sobra" class="btn-link">ver a ordem</a>
            } @else {
              <a routerLink="/mes/lancar" class="btn-link">lançar o mês</a>
            }
          </p>

          @if (s.affirmation && !s.affirmation.prescriptive) {
            <p class="notice notice-indeterminate fi-caption text-ink-2 m-0 mt-4 max-w-reading">
              {{ s.affirmation.disclaimer }} Por isso o quanto aportar em cada destino aparece como
              &mdash;.
            </p>
          }

          <div class="flex flex-wrap items-center gap-3 mt-4">
            @if (s.cash_available >= 100) {
              <a routerLink="/sobra/aporte" class="btn-primary no-underline">
                Distribuir este caixa
              </a>
            } @else if (mesDoCaixa()) {
              <a routerLink="/sobra" class="btn-primary no-underline"> Ver a ordem do mês </a>
            } @else {
              <a routerLink="/mes/lancar" class="btn-primary no-underline">
                Lançar o mês para saber quanto sobra
              </a>
            }
            <button
              type="button"
              class="btn-secondary"
              (click)="loadStrategy()"
              [disabled]="loading.loading()"
            >
              <lucide-icon
                [name]="loading.loading() ? 'loader-circle' : 'refresh-cw'"
                size="14"
                [class.spin]="loading.loading()"
              ></lucide-icon>
              {{ loading.loading() ? 'Recalculando…' : 'Recalcular' }}
            </button>
          </div>
        </section>

        @if (s.allocation_gaps.length > 0) {
          <section class="fi-block">
            <div class="flex items-baseline justify-between gap-3 mb-1">
              <h2 class="fi-title text-ink m-0">Onde você está fora da meta</h2>
              <a routerLink="/voce/objetivos" class="fi-caption text-brand no-underline">
                Ajustar metas →
              </a>
            </div>
            <p class="fi-caption text-ink-3 m-0 mb-4">
              A barra é a alocação atual; o fio, a meta. O desvio é o que decide o aporte.
            </p>

            <ul class="list-none m-0 p-0 flex flex-col gap-3">
              @for (gap of s.allocation_gaps; track gap.category) {
                <li>
                  <app-allocation-gap
                    [label]="ui.categoryLabel(gap.category)"
                    [currentPct]="gap.current_pct"
                    [targetPct]="gap.target_pct"
                    [barColor]="getCategoryBarColor(gap.category)"
                    [scalePct]="gapScalePct(s.allocation_gaps)"
                  />
                  <p class="fi-caption text-ink-3 m-0 mt-1 ml-[104px] sm:ml-[116px]">
                    {{ gap.action }} ·
                    <span class="fi-num">{{ absValue(gap.gap_value) | currency: 'BRL' }}</span>
                  </p>
                </li>
              }
            </ul>
          </section>
        }

        @if (s.suggestions.length > 0) {
          <section class="fi-block">
            <h2 class="fi-title text-ink m-0 mb-1">Para onde levar o próximo aporte</h2>
            <p class="fi-caption text-ink-3 m-0 mb-4">
              <span class="fi-num">{{ s.suggestions.length }}</span>
              {{ s.suggestions.length === 1 ? 'destino' : 'destinos' }}
              @if (totalToInvest(s); as total) {
                , somando <span class="fi-num text-ink">{{ total | currency: 'BRL' }}</span>
              }
              — uma leitura do sistema, não uma ordem.
            </p>

            <ul class="list-none m-0 p-0">
              @for (sug of s.suggestions; track sug.ticker) {
                <li class="py-4 border-t border-hairline first:border-t-0">
                  <div class="flex items-start justify-between gap-4">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap">
                        @if (sug.ticker === 'RENDA_FIXA') {
                          <span class="fi-ticker text-ink">Renda fixa</span>
                        } @else {
                          <a
                            [routerLink]="['/ativo', sug.ticker]"
                            class="fi-ticker text-ink no-underline hover:text-brand"
                          >
                            {{ sug.ticker }}
                          </a>
                        }
                        <span class="tag" [class]="ui.categoryChipClass(sug.category)">{{
                          ui.categoryLabel(sug.category)
                        }}</span>
                        @if (sug.already_held) {
                          <span class="tag tag-brand">Já na carteira</span>
                        }
                      </div>

                      @if (sug.name) {
                        <p class="fi-caption text-ink-3 m-0 mt-0.5">{{ sug.name }}</p>
                      }

                      <p class="fi-body text-ink m-0 mt-2">{{ sug.objective }}</p>

                      @if (sug.reasons.length > 0) {
                        <details class="mt-2">
                          <summary
                            class="fi-caption text-ink-3 cursor-pointer fi-focusable rounded-sm"
                          >
                            O que sustenta ({{ sug.reasons.length }})
                          </summary>
                          <ul class="list-none m-0 mt-1 p-0 flex flex-col gap-1">
                            @for (reason of sug.reasons; track reason) {
                              <li class="fi-caption text-ink-2">{{ reason }}</li>
                            }
                          </ul>
                        </details>
                      }

                      @if (sug.ticker !== 'RENDA_FIXA') {
                        <div class="flex items-center gap-4 mt-2 flex-wrap fi-caption text-ink-3">
                          <span>
                            Score
                            <strong class="fi-num text-ink">{{
                              sug.score | number: '1.0-0'
                            }}</strong>
                          </span>
                          @if (sug.margin_of_safety != null) {
                            <span>
                              Margem
                              <strong class="fi-num text-ink"
                                >{{ sug.margin_of_safety * 100 | number: '1.0-0' }}%</strong
                              >
                            </span>
                          }
                          @if (sug.dividend_yield) {
                            <span>
                              DY
                              <strong class="fi-num text-ink"
                                >{{ sug.dividend_yield | number: '1.1-1' }}%</strong
                              >
                            </span>
                          }
                        </div>
                      }

                      @if (sug.transaction_cost) {
                        <p class="fi-caption text-attention m-0 mt-2">
                          <lucide-icon name="receipt" size="12" aria-hidden="true"></lucide-icon>
                          {{ sug.transaction_cost.observation }}
                          @if (sug.transaction_cost.ir_amount > 0) {
                            · IR estimado
                            <span class="fi-num">{{
                              sug.transaction_cost.ir_amount | currency: 'BRL'
                            }}</span>
                          }
                        </p>
                      }
                    </div>

                    <div class="shrink-0 text-right">
                      <p class="fi-eyebrow text-ink-3 m-0">Aportar</p>
                      <p class="fi-metric text-ink m-0">
                        @if (sug.invest_amount !== null) {
                          {{ sug.invest_amount | currency: 'BRL' }}
                        } @else {
                          &mdash;
                        }
                      </p>
                      @if (sug.ticker === 'RENDA_FIXA') {
                        <a
                          routerLink="/descobrir/renda-fixa"
                          class="fi-caption text-brand no-underline"
                        >
                          Comparar títulos →
                        </a>
                      } @else {
                        <p class="fi-caption text-ink-3 m-0 mt-1">
                          @if (sug.quantity !== null) {
                            <span class="fi-num">{{ sug.quantity }}</span> ×
                          }
                          <span class="fi-num">{{ sug.price | currency: 'BRL' }}</span>
                        </p>
                      }
                    </div>
                  </div>
                </li>
              }
            </ul>
          </section>
        } @else if (s.cash_available < 100) {
          <section class="fi-block">
            @if (mesDoCaixa()) {
              <app-empty-state
                icon="wallet"
                title="A ordem do mês não deixou nada para aportar"
                [reason]="
                  'Em ' +
                  nome(mesDoCaixa()) +
                  ' a sobra foi inteira para o que vem antes do aporte — e isso é resposta, não falha.'
                "
                nextStep="Enquanto a dívida custar mais do que a carteira rende, quitar é o melhor uso do dinheiro."
                actionLabel="Ver a ordem"
                actionRoute="/sobra"
              />
            } @else {
              <app-empty-state
                icon="wallet"
                title="Sem caixa para distribuir"
                reason="O plano de aporte precisa saber quanto sobra do seu mês, e hoje esse valor está zerado."
                nextStep="Lance o que entrou e o que saiu. A sobra sai daí, já descontada a dívida cara e a reserva."
                actionLabel="Lançar o mês"
                actionRoute="/mes/lancar"
              />
            }
          </section>
        } @else {
          <section class="fi-block">
            <div class="notice notice-favorable flex-col max-w-reading">
              <p class="fi-verdict-sm text-ink m-0">
                A carteira está dentro das metas que você definiu.
              </p>
              <p class="fi-body text-ink-2 m-0 mt-1">
                Nenhum desvio relevante o bastante para redirecionar o próximo aporte.
              </p>
            </div>
          </section>
        }

        @if (s.reduce_suggestions.length > 0) {
          <section class="fi-block">
            <h2 class="fi-title text-ink m-0 mb-1">Posições para revisar</h2>
            <p class="fi-caption text-ink-3 m-0 mb-4">
              Ativos já na carteira com sinal de venda. Vale reavaliar — não é ordem automática.
            </p>

            <ul class="list-none m-0 p-0">
              @for (r of s.reduce_suggestions; track r.ticker) {
                <li class="py-3 border-t border-hairline first:border-t-0">
                  <div class="flex items-start justify-between gap-4">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap">
                        <a
                          [routerLink]="['/ativo', r.ticker]"
                          class="fi-ticker text-ink no-underline hover:text-brand"
                        >
                          {{ r.ticker }}
                        </a>
                        <span class="verdict-pill" [class]="verdictClassFromString(r.verdict)">{{
                          r.label || r.verdict
                        }}</span>
                        @if (r.overweight_category) {
                          <span class="tag tag-neutral">Categoria acima da meta</span>
                        }
                      </div>
                      <ul class="list-none m-0 mt-2 p-0 flex flex-col gap-1">
                        @for (reason of r.reasons; track reason) {
                          <li class="fi-caption text-ink-2">{{ reason }}</li>
                        }
                      </ul>
                    </div>
                    <div class="shrink-0 text-right">
                      <p class="fi-eyebrow text-ink-3 m-0">Posição</p>
                      <p class="fi-metric-sm text-ink m-0">
                        {{ r.current_value | currency: 'BRL' }}
                      </p>
                      @if (r.pnl_pct != null) {
                        <p class="fi-caption text-ink-2 m-0 mt-0.5 fi-num">
                          {{ r.pnl_pct >= 0 ? '+' : '' }}{{ r.pnl_pct | number: '1.1-1' }}%
                        </p>
                      }
                    </div>
                  </div>
                </li>
              }
            </ul>
          </section>
        }

        @if (s.suggestions.length > 0 && s.projected_allocation.length > 0) {
          <section class="fi-block">
            <h2 class="fi-title text-ink m-0 mb-1">Como a carteira ficaria</h2>
            <p class="fi-caption text-ink-3 m-0 mb-4">
              Atual em tinta neutra, projetada na cor da marca — a mesma barra, dois momentos.
            </p>

            <ul class="list-none m-0 p-0 flex flex-col gap-4">
              @for (row of projection(s); track row.category) {
                <li class="flex items-center gap-4">
                  <span class="fi-label text-ink w-[92px] sm:w-[100px] shrink-0 truncate">
                    {{ ui.categoryLabel(row.category) }}
                  </span>
                  <div class="relative flex-1 min-w-[80px] flex flex-col gap-1">
                    <div class="h-2 rounded-sm bg-hairline-strong overflow-hidden">
                      <div class="h-full bg-ink-3" [style.width.%]="row.currentPct"></div>
                    </div>
                    <div class="h-2 rounded-sm bg-hairline-strong overflow-hidden">
                      <div class="h-full bg-brand" [style.width.%]="row.projectedPct"></div>
                    </div>
                  </div>
                  <span class="fi-caption text-ink-3 w-[52px] text-right shrink-0 fi-num">
                    {{ row.currentPct | number: '1.1-1' }}%
                  </span>
                  <span class="fi-metric-sm text-brand w-[56px] text-right shrink-0">
                    {{ row.projectedPct | number: '1.1-1' }}%
                  </span>
                </li>
              }
            </ul>
          </section>
        }
      } @else if (!loading.loading()) {
        <app-empty-state
          icon="target"
          title="Nenhuma estratégia calculada ainda"
          reason="O plano nasce das suas metas de alocação cruzadas com a carteira e o caixa atuais — e ainda não houve um cálculo nesta sessão."
          nextStep="O cálculo usa o que já está cadastrado; nada é enviado para fora."
          actionLabel="Calcular estratégia"
          (action)="loadStrategy()"
        />
      } @else {
        <div class="flex flex-col gap-6">
          <app-skeleton shape="verdict" />
          <app-skeleton shape="body" />
          <app-skeleton shape="row" [count]="4" />
        </div>
      }

      <div class="fi-block">
        <app-rebalance-suggestions />
      </div>
    </div>
  `,
})
export class StrategyComponent implements OnInit {
  readonly nome = nomeDoMes;

  private readonly svc = inject(RecommendService);
  private readonly caixa = inject(CashflowService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  readonly strategy = signal<InvestmentStrategy | null>(null);

  /** O mês de onde o caixa saiu, ou vazio quando o número foi informado à mão. */
  readonly mesDoCaixa = signal('');
  readonly origemDoCaixa = signal('');

  ngOnInit(): void {
    this.loadStrategy();
  }

  /*
   * O caixa a distribuir é o que sobra do mês depois da dívida cara e da reserva — derivado,
   * não digitado. O valor informado à mão fica como último recurso, para quem ainda não lançou
   * nenhum mês: um número guardado numa preferência envelhece sem avisar, e distribuir dinheiro
   * que já foi gasto é pior que não responder.
   */
  loadStrategy(): void {
    this.caixa.surplus().subscribe({
      next: sobra => {
        if (sobra.has_cash) {
          this.mesDoCaixa.set(sobra.month.month);
          this.origemDoCaixa.set(
            `É o que sobra de ${nomeDoMes(sobra.month.month)} depois do que a ordem já destinou.`
          );
          this.fetch(sobra.cascade.available_to_invest);
          return;
        }
        this.caixaInformado();
      },
      error: () => this.caixaInformado(),
    });
  }

  private caixaInformado(): void {
    this.mesDoCaixa.set('');
    this.svc.getPreferences().subscribe({
      next: prefs => {
        const valor = prefs.cash_available ?? 0;
        this.origemDoCaixa.set(
          valor > 0
            ? 'Este é o último valor que você informou — nenhum mês lançado para derivá-lo.'
            : 'Sem mês lançado, não há sobra para derivar.'
        );
        this.fetch(valor);
      },
      error: () => this.fetch(0),
    });
  }

  private fetch(cash: number): void {
    this.svc.getStrategy(cash).subscribe({
      next: data => this.strategy.set(data),
      error: () => {},
    });
  }

  riskClass(): string {
    return 'tag-neutral';
  }

  totalToInvest(s: InvestmentStrategy): number | null {
    if (s.suggestions.some(x => x.invest_amount === null)) return null;
    return s.suggestions.reduce((sum, x) => sum + (x.invest_amount ?? 0), 0);
  }

  cashPct(s: InvestmentStrategy): number {
    return s.total_capital > 0 ? (s.cash_available / s.total_capital) * 100 : 0;
  }

  absValue(v: number): number {
    return Math.abs(v);
  }

  projection(s: InvestmentStrategy): ProjectionRow[] {
    const current = new Map(s.current_allocation.map(a => [a.category, a.current_pct]));
    const projected = new Map(s.projected_allocation.map(a => [a.category, a.projected_pct]));
    const categories = [...new Set([...current.keys(), ...projected.keys()])];

    return categories
      .map(category => ({
        category,
        currentPct: current.get(category) ?? 0,
        projectedPct: projected.get(category) ?? 0,
      }))
      .sort((a, b) => b.projectedPct - a.projectedPct);
  }

  verdictClassFromString(v: string): string {
    if (v === 'STRONG_BUY' || v === 'BUY') return 'v-buy';
    if (v === 'STRONG_SELL' || v === 'SELL') return 'v-sell';
    if (v === 'HOLD') return 'v-hold';
    return 'v-unknown';
  }

  assetLabel(type: string): string {
    return { br_stock: 'Ação BR', fii: 'FII', bdr: 'BDR', etf: 'ETF' }[type] || type;
  }

  gapScalePct(gaps: { current_pct: number; target_pct: number }[]): number {
    return allocationScalePct(
      gaps.map(g => ({ currentPct: g.current_pct, targetPct: g.target_pct }))
    );
  }

  getCategoryBarColor(category: string): string {
    return this.ui.categoryBarColor(category);
  }
}
