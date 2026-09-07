import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  CarteiraStore,
  PortfolioHealth,
  RecommendService,
  UiHelperService,
  MIN_POSICOES_PARA_SAUDE,
  allocationScalePct,
  fiHealthBands,
  vereditoDeSaude,
} from '../../core';
import { AllocationGapComponent } from '../allocation-gap/allocation-gap.component';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { ImportTradesComponent } from '../import-trades/import-trades.component';
import { LedgerEntriesComponent } from '../ledger-entries/ledger-entries.component';
import { ScoreRulerComponent } from '../score-ruler/score-ruler.component';
import { PageHeaderComponent } from '../page-header/page-header.component';

interface HealthDimension {
  readonly label: string;
  readonly score: number;
  readonly explains: string;
}

@Component({
  selector: 'app-portfolio-summary',
  standalone: true,
  imports: [
    PageHeaderComponent,
    AllocationGapComponent,
    CommonModule,
    EmptyStateComponent,
    ImportTradesComponent,
    LedgerEntriesComponent,
    LucideAngularModule,
    RouterLink,
    ScoreRulerComponent,
  ],
  template: `
    <app-page-header title="Carteira" question="Como está meu patrimônio?" />

    @if (store.loadFailed()) {
      <div class="notice notice-adverse flex-col mb-6" role="alert">
        <p class="fi-verdict-sm text-ink m-0 mb-1">Não conseguimos carregar toda a sua carteira</p>
        <p class="fi-body text-ink-2 m-0 mb-3">
          Parte dos dados pode estar faltando abaixo. Seus lançamentos estão salvos.
        </p>
        <button type="button" class="btn-secondary" (click)="store.reload()">Tentar de novo</button>
      </div>
    }

    @if (store.isEmpty()) {
      <section class="max-w-reading">
        <p class="fi-verdict text-ink m-0 mb-2">Sua carteira ainda está vazia</p>
        <p class="fi-body text-ink-2 m-0 mb-5">
          Adicione uma posição — ações, FIIs, BDRs, ETFs ou renda fixa — e o fiance passa a marcar
          tudo a mercado, calcular preço justo e avaliar a saúde da carteira.
        </p>
        <a routerLink="/patrimonio/editar" class="btn-primary no-underline"
          >Adicionar primeira posição</a
        >
      </section>
    } @else {
      <div class="flex flex-col gap-8">
        <section>
          <p class="fi-eyebrow text-ink-3 m-0 mb-2">Valor da carteira</p>
          <p class="fi-money-lg text-ink m-0">R$ {{ store.valorAtual() | number: '1.2-2' }}</p>

          <p class="fi-body text-ink m-0 mt-2 flex items-center gap-1.5 flex-wrap">
            <lucide-icon
              [name]="store.rendimentoTotal() >= 0 ? 'arrow-up-right' : 'arrow-down-right'"
              size="15"
              aria-hidden="true"
            ></lucide-icon>
            <span class="fi-num">
              {{ store.rendimentoTotal() >= 0 ? '+' : '−' }}R$ {{ absResult() | number: '1.2-2' }}
            </span>
            <span class="fi-num">({{ store.rendimentoPct() | number: '1.2-2' }}%)</span>
            <span class="text-ink-3"
              >sobre R$ {{ store.totalInvestido() | number: '1.0-0' }} aportados</span
            >
          </p>

          <p class="fi-caption text-ink-3 m-0 mt-3">
            <span class="fi-num">{{ store.negociadosCount() }}</span>
            {{ store.negociadosCount() === 1 ? 'ativo negociado' : 'ativos negociados' }}
            @if (store.rendaFixaCount() > 0) {
              · <span class="fi-num">{{ store.rendaFixaCount() }}</span>
              {{ store.rendaFixaCount() === 1 ? 'aplicação' : 'aplicações' }} de renda fixa
            }
            @if (store.evaluating()) {
              · atualizando…
            } @else if (store.lastEvaluatedLabel()) {
              · avaliada às {{ store.lastEvaluatedLabel() }}
            }
          </p>
        </section>

        <section class="fi-block">
          <div class="flex items-baseline justify-between gap-3 mb-4">
            <p class="fi-eyebrow text-ink-3 m-0">Alocação × meta</p>
            <a routerLink="/sobra/metas" class="fi-caption text-brand no-underline">
              Ajustar metas →
            </a>
          </div>

          @if (hasGoals()) {
            <ul class="list-none m-0 p-0 flex flex-col gap-3">
              @for (gap of gaps(); track gap.label) {
                <li>
                  <app-allocation-gap
                    [label]="gap.label"
                    [currentPct]="gap.currentPct"
                    [targetPct]="gap.targetPct"
                    [barColor]="gap.barColor"
                    [scalePct]="gapScalePct()"
                  />
                </li>
              }
            </ul>
          } @else {
            <app-empty-state
              icon="target"
              title="Nenhuma meta de alocação definida"
              reason="Sem meta, o fiance mostra onde seu dinheiro está, mas não tem contra o que comparar — e desvio de uma meta que não existe seria número inventado."
              nextStep="Defina o peso que cada classe deveria ter na carteira. Leva um minuto e passa a valer para o Mês, a Sobra e o aporte."
              actionLabel="Definir metas"
              actionRoute="/sobra/metas"
            />
          }
        </section>

        @if (health(); as h) {
          <section class="fi-block">
            <div class="flex items-start justify-between gap-6 flex-wrap mb-4">
              <div class="flex-1 min-w-[260px]">
                <p class="fi-eyebrow text-ink-3 m-0 mb-2">Saúde da carteira</p>
                <!-- veredito: a mesma frase que Hoje exibe, vinda da mesma função -->
                <h2 class="fi-verdict text-ink m-0">{{ healthVerdict() }}</h2>
              </div>
              <div class="w-full sm:w-[240px]">
                <app-score-ruler
                  [score]="h.score"
                  [bands]="healthBands"
                  [dataCompleteness]="healthReliable() ? 1 : 0"
                  subject="Saúde da carteira"
                  size="card"
                  [showScale]="true"
                />
              </div>
            </div>

            @if (!healthReliable()) {
              <p class="fi-body text-ink-2 m-0">
                Com {{ store.negociadosCount() }}
                {{ store.negociadosCount() === 1 ? 'ativo' : 'ativos' }}, concentração e
                diversificação ainda não dizem muito — a leitura fica confiável a partir de quatro.
              </p>
            } @else {
              <dl class="grid grid-cols-2 md:grid-cols-4 gap-4 m-0">
                @for (dim of healthDimensions(); track dim.label) {
                  <div>
                    <dt class="fi-caption text-ink-3">{{ dim.label }}</dt>
                    <dd class="m-0 mt-1">
                      <app-score-ruler
                        [score]="dim.score"
                        [bands]="healthBands"
                        [subject]="dim.label"
                        size="list"
                      />
                    </dd>
                  </div>
                }
              </dl>

              <button
                type="button"
                class="btn-link mt-4"
                (click)="toggleHealthDetail()"
                [attr.aria-expanded]="showHealthDetail()"
              >
                <lucide-icon
                  [name]="showHealthDetail() ? 'chevron-down' : 'chevron-right'"
                  size="16"
                ></lucide-icon>
                O que cada dimensão considera
              </button>

              @if (showHealthDetail()) {
                <dl class="flex flex-col gap-3 mt-3 max-w-reading m-0">
                  @for (dim of healthDimensions(); track dim.label) {
                    <div>
                      <dt class="fi-label text-ink">{{ dim.label }}</dt>
                      <dd class="fi-body text-ink-2 m-0">{{ dim.explains }}</dd>
                    </div>
                  }
                </dl>
              }

              @if (h.warnings.length > 0) {
                <ul class="list-none m-0 p-0 mt-4 flex flex-col gap-1.5 max-w-reading">
                  @for (warning of h.warnings; track warning) {
                    <li class="fi-body text-ink-2 pl-3 border-l-2 border-hairline-strong">
                      {{ warning }}
                    </li>
                  }
                </ul>
              }
            }
          </section>
        }

        <nav class="fi-block" aria-label="Detalhe da carteira">
          <p class="fi-eyebrow text-ink-3 m-0 mb-3">Ver em detalhe</p>
          <ul
            class="list-none m-0 p-0 grid grid-cols-1 sm:grid-cols-2 gap-x-6 divide-y divide-hairline sm:divide-y-0"
          >
            <li>
              <a routerLink="/patrimonio/posicoes" class="menu-item no-underline">
                <span class="fi-body flex-1 min-w-0">Todas as posições, linha a linha</span>
                <lucide-icon
                  name="chevron-right"
                  size="14"
                  class="text-ink-3 shrink-0"
                  aria-hidden="true"
                ></lucide-icon>
              </a>
            </li>
            <li>
              <a routerLink="/patrimonio/encerradas" class="menu-item no-underline">
                <span class="fi-body flex-1 min-w-0">O que eu já vendi</span>
                <lucide-icon
                  name="chevron-right"
                  size="14"
                  class="text-ink-3 shrink-0"
                  aria-hidden="true"
                ></lucide-icon>
              </a>
            </li>
          </ul>
        </nav>

        <nav class="fi-block" aria-label="Registro e manutenção">
          <p class="fi-eyebrow text-ink-3 m-0 mb-1">Registro e manutenção</p>
          <p class="fi-caption text-ink-3 m-0 mb-3 max-w-reading">
            Operações sobre o livro-razão, não leituras do patrimônio.
          </p>
          <ul
            class="list-none m-0 p-0 grid grid-cols-1 sm:grid-cols-2 gap-x-6 divide-y divide-hairline sm:divide-y-0"
          >
            <li>
              <button type="button" class="menu-item" (click)="showTransacoes.set(true)">
                <span class="fi-body flex-1 min-w-0 text-left">Lançamentos</span>
                <lucide-icon
                  name="chevron-right"
                  size="14"
                  class="text-ink-3 shrink-0"
                  aria-hidden="true"
                ></lucide-icon>
              </button>
            </li>
            <li>
              <button type="button" class="menu-item" (click)="showImport.set(true)">
                <span class="fi-body flex-1 min-w-0 text-left">Importar operações</span>
                <lucide-icon
                  name="chevron-right"
                  size="14"
                  class="text-ink-3 shrink-0"
                  aria-hidden="true"
                ></lucide-icon>
              </button>
            </li>
            <li>
              <a routerLink="/patrimonio/editar" class="menu-item no-underline">
                <span class="fi-body flex-1 min-w-0">Editar a carteira</span>
                <lucide-icon
                  name="chevron-right"
                  size="14"
                  class="text-ink-3 shrink-0"
                  aria-hidden="true"
                ></lucide-icon>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    }

    @if (showImport()) {
      <app-import-trades (close)="showImport.set(false)" (imported)="onImported()" />
    }
    @if (showTransacoes()) {
      <app-ledger-entries (close)="showTransacoes.set(false)" />
    }
  `,
})
export class PortfolioSummaryComponent implements OnInit {
  readonly store = inject(CarteiraStore);
  private readonly svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);

  readonly health = signal<PortfolioHealth | null>(null);
  readonly healthBands = fiHealthBands;
  readonly showHealthDetail = signal(false);

  readonly showImport = signal(false);
  readonly showTransacoes = signal(false);

  ngOnInit(): void {
    this.store.ensureLoaded();
    this.svc.dashboard().subscribe({
      next: d => this.health.set(d.health),
      error: () => this.health.set(null),
    });
  }

  readonly healthReliable = computed(() => this.store.negociadosCount() >= MIN_POSICOES_PARA_SAUDE);

  readonly healthVerdict = computed(() => {
    const h = this.health();
    return h ? vereditoDeSaude(h.score, this.store.negociadosCount()) : '';
  });

  readonly healthDimensions = computed<HealthDimension[]>(() => {
    const h = this.health();
    if (!h) return [];
    return [
      {
        label: 'Concentração',
        score: h.concentration_score,
        explains: 'O quanto o seu maior ativo pesa no total da carteira.',
      },
      {
        label: 'Setor',
        score: h.sector_concentration_score,
        explains: 'O quanto as suas ações e BDRs dependem de um único setor.',
      },
      {
        label: 'Diversificação',
        score: h.diversification_score,
        explains: 'A variedade entre classes: renda fixa, ações, FIIs, BDRs e ETFs.',
      },
      {
        label: 'Risco',
        score: h.risk_score,
        explains: 'A fatia da carteira em ativos com sinal de venda.',
      },
    ];
  });

  readonly absResult = computed(() => Math.abs(this.store.rendimentoTotal()));

  readonly gaps = computed(() =>
    this.store
      .alocacaoPorTipo()
      .filter(a => a.targetPct != null)
      .map(a => ({
        label: this.ui.categoryLabel(a.tipo),
        currentPct: a.pct,
        targetPct: a.targetPct as number,
        deltaPct: a.pct - (a.targetPct as number),
        barColor: this.ui.categoryBarColor(a.tipo),
      }))
      .sort((a, b) => Math.abs(b.deltaPct) - Math.abs(a.deltaPct))
  );

  readonly gapScalePct = computed(() => allocationScalePct(this.gaps()));

  readonly hasGoals = computed(() => this.gaps().length > 0);

  toggleHealthDetail(): void {
    this.showHealthDetail.update(v => !v);
  }

  onImported(): void {
    this.showImport.set(false);
    this.showTransacoes.set(true);
    this.store.reload();
  }
}
