import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormControl,
  FormArray,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import {
  AssetAnalysis,
  InvestmentStrategy,
  LoadingService,
  RecommendService,
  RendaFixaAsset,
  RendaFixaCompareResponse,
  ReferenceRates,
  UiHelperService,
} from '../../core';

type StrategyTab = 'analisar' | 'ajuste' | 'renda_fixa';

interface AnalyzeForm {
  symbol: FormControl<string>;
  desired_yield: FormControl<number>;
}

interface RendaFixaForm {
  tipo: FormControl<string>;
  nome: FormControl<string>;
  valor_investido: FormControl<number>;
  taxa: FormControl<number>;
  prazo_meses: FormControl<number>;
  tipo_taxa: FormControl<string>;
  percentual_cdi: FormControl<number | null>;
  liquidez: FormControl<string>;
}

@Component({
  selector: 'app-strategy',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  template: `
    <div class="space-y-5">
      <div class="flex gap-2 border-b border-border pb-2">
        <button
          type="button"
          (click)="activeTab.set('analisar')"
          [class.active]="activeTab() === 'analisar'"
          class="tab-btn"
        >
          <lucide-icon name="search" size="18"></lucide-icon>
          Analisar Ativo
        </button>
        <button
          type="button"
          (click)="activeTab.set('ajuste')"
          [class.active]="activeTab() === 'ajuste'"
          class="tab-btn"
        >
          <lucide-icon name="wand-sparkles" size="18"></lucide-icon>
          Ajuste de Carteira
        </button>
        <button
          type="button"
          (click)="activeTab.set('renda_fixa')"
          [class.active]="activeTab() === 'renda_fixa'"
          class="tab-btn"
        >
          <lucide-icon name="landmark" size="18"></lucide-icon>
          Renda Fixa
        </button>
      </div>

      <!-- ===== ABA: ANALISAR ===== -->
      @if (activeTab() === 'analisar') {
        <form
          class="p-5 rounded-lg bg-panel border border-border mb-4"
          [formGroup]="analyzeForm"
          (ngSubmit)="submitAnalyze()"
        >
          <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx">
            <lucide-icon name="search" size="18"></lucide-icon> Análise Detalhada
          </h2>
          <p class="text-sm text-muted mb-4">
            Ação BR (PETR4), FII (HGLG11), EUA (AAPL) ou cripto (BTC, ETH).
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-[2fr_1fr] gap-4">
            <div>
              <label class="block text-xs font-medium text-muted mb-1.5">Ticker</label>
              <input
                type="text"
                class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                formControlName="symbol"
                placeholder="ex.: VALE3"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-muted mb-1.5"
                >Yield desejado (Bazin)</label
              >
              <input
                type="number"
                class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                formControlName="desired_yield"
                min="0.02"
                max="0.20"
                step="0.005"
              />
            </div>
          </div>
          <div class="flex items-center gap-3 mt-4">
            <button
              class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
              type="submit"
              [disabled]="analyzeForm.invalid || loading.loading()"
            >
              <lucide-icon
                [name]="loading.loading() ? 'loader-circle' : 'search'"
                size="16"
              ></lucide-icon>
              {{ loading.loading() ? 'Analisando...' : 'Analisar' }}
            </button>
          </div>
        </form>

        @if (analyzeResult(); as a) {
          <div class="p-5 rounded-lg bg-panel border border-border">
            <div style="display:flex; gap:14px; align-items:baseline; flex-wrap:wrap;">
              <h2 class="text-xl font-bold m-0 text-tx">
                {{ a.symbol }}
                @if (a.name && a.name !== a.symbol) {
                  — {{ a.name }}
                }
              </h2>
              <span class="tag">{{ ui.assetTypeLabel(a.asset_type) }}</span>
              <span class="tag" *ngIf="a.sector">{{ ui.translateSector(a.sector) }}</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
              <div class="p-4 rounded-lg bg-bg-2 border border-border">
                <div class="text-xs text-muted mb-1">Preço atual</div>
                <div class="text-xl font-bold text-tx">
                  {{ a.price | number: '1.2-2' }} {{ a.currency }}
                </div>
              </div>
              <div class="p-4 rounded-lg bg-bg-2 border border-border good">
                <div class="text-xs text-muted mb-1">Preço justo</div>
                <div class="text-xl font-bold text-tx">
                  {{
                    a.fair_price.consensus != null
                      ? (a.fair_price.consensus | number: '1.2-2')
                      : '—'
                  }}
                </div>
              </div>
              <div
                class="p-4 rounded-lg bg-bg-2 border border-border"
                [class.good]="(a.fair_price.margin_of_safety ?? 0) >= 0"
                [class.warn]="(a.fair_price.margin_of_safety ?? 0) < 0"
              >
                <div class="text-xs text-muted mb-1">Margem de segurança</div>
                <div class="text-xl font-bold text-tx">
                  {{
                    a.fair_price.margin_of_safety != null
                      ? (a.fair_price.margin_of_safety * 100 | number: '1.1-1') + '%'
                      : '—'
                  }}
                </div>
              </div>
              <div class="p-4 rounded-lg bg-bg-2 border border-border info">
                <div class="text-xs text-muted mb-1">Decisão</div>
                <div class="text-xl font-bold text-tx">
                  <span class="verdict-pill" [class]="ui.verdictClass(a.decision.verdict)">{{
                    a.decision.label
                  }}</span>
                </div>
              </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5">
              <div>
                <h3 class="text-base font-semibold mb-3 text-tx">Preço justo</h3>
                <ul class="flex flex-col gap-2 list-none p-0 m-0">
                  <li class="flex justify-between items-center py-1.5 border-b border-border">
                    <span class="text-muted">Bazin</span
                    ><strong class="text-tx">{{ ui.fmtNum(a.fair_price.bazin) }}</strong>
                  </li>
                  <li class="flex justify-between items-center py-1.5 border-b border-border">
                    <span class="text-muted">Graham</span
                    ><strong class="text-tx">{{ ui.fmtNum(a.fair_price.graham) }}</strong>
                  </li>
                  <li class="flex justify-between items-center py-1.5 border-b border-border">
                    <span class="text-muted">Dividendo médio 5a</span
                    ><strong class="text-tx">{{ ui.fmtNum(a.fair_price.avg_dividend_5y) }}</strong>
                  </li>
                </ul>
              </div>
              <div>
                <h3 class="text-base font-semibold mb-3 text-tx">Indicadores técnicos</h3>
                <ul class="flex flex-col gap-2 list-none p-0 m-0">
                  <li class="flex justify-between items-center py-1.5 border-b border-border">
                    <span class="text-muted">Tendência</span
                    ><strong class="text-tx">{{ ui.trendLabel(a.technical.trend) }}</strong>
                  </li>
                  <li class="flex justify-between items-center py-1.5 border-b border-border">
                    <span class="text-muted">SMA 50 / 200</span
                    ><strong class="text-tx"
                      >{{ ui.fmtNum(a.technical.sma_50) }} /
                      {{ ui.fmtNum(a.technical.sma_200) }}</strong
                    >
                  </li>
                  <li class="flex justify-between items-center py-1.5 border-b border-border">
                    <span class="text-muted">RSI(14)</span
                    ><strong class="text-tx"
                      >{{ ui.fmtNum(a.technical.rsi_14) }}
                      {{ ui.rsiLabel(a.technical.rsi_14) }}</strong
                    >
                  </li>
                </ul>
              </div>
              <div class="sm:col-span-2">
                <h3 class="text-base font-semibold mb-3 text-tx">Por que essa decisão?</h3>
                <ul class="list-disc pl-5 m-0 space-y-1">
                  @for (r of a.decision.reasons; track r) {
                    <li class="text-sm text-tx">{{ r }}</li>
                  }
                </ul>
              </div>
            </div>
          </div>
        }
      }

      <!-- ===== ABA: AJUSTE DE CARTEIRA ===== -->
      @if (activeTab() === 'ajuste') {
        <div class="flex items-center gap-3 mb-5 flex-wrap">
          <button
            class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 transition-opacity"
            (click)="loadStrategy()"
            [disabled]="loading.loading()"
          >
            <lucide-icon
              [name]="loading.loading() ? 'loader-circle' : 'target'"
              size="16"
            ></lucide-icon>
            {{ loading.loading() ? 'Gerando estratégia...' : 'Gerar nova estratégia' }}
          </button>
          <p class="text-sm text-muted m-0">
            Análise baseada nas suas metas de alocação e carteira atual.
          </p>
        </div>

        @if (strategy(); as s) {
          <!-- Perfil -->
          <div class="p-5 rounded-lg bg-panel border border-border mb-5">
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx">
              <lucide-icon name="circle-user" size="18"></lucide-icon> Perfil de Investidor
            </h2>
            <div class="flex items-start gap-4 flex-wrap">
              <div class="flex-1 min-w-[250px]">
                <div class="text-2xl font-bold text-accent mb-2">{{ s.profile.type }}</div>
                <p class="text-sm text-muted mb-3">{{ s.profile.description }}</p>
                <div class="flex items-center gap-2 text-sm">
                  <span class="text-muted">Risco:</span>
                  <span class="tag" [class]="riskClass(s.profile.risk_tolerance)">{{
                    s.profile.risk_tolerance
                  }}</span>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div class="p-3 rounded-lg bg-bg-2 border border-border">
                  <div class="text-xs text-muted mb-1">Capital total</div>
                  <div class="text-lg font-bold text-tx">
                    R$ {{ s.total_capital | number: '1.2-2' }}
                  </div>
                </div>
                <div class="p-3 rounded-lg bg-bg-2 border border-border">
                  <div class="text-xs text-muted mb-1">Caixa disponível</div>
                  <div class="text-lg font-bold text-accent">
                    R$ {{ s.cash_available | number: '1.2-2' }}
                  </div>
                </div>
                <div class="p-3 rounded-lg bg-bg-2 border border-border">
                  <div class="text-xs text-muted mb-1">Investido</div>
                  <div class="text-lg font-bold text-tx">
                    R$ {{ s.total_invested | number: '1.2-2' }}
                  </div>
                </div>
                <div class="p-3 rounded-lg bg-bg-2 border border-border">
                  <div class="text-xs text-muted mb-1">% em caixa</div>
                  <div class="text-lg font-bold text-tx">
                    {{ (s.cash_available / s.total_capital) * 100 | number: '1.1-1' }}%
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Resumo -->
          <div
            class="p-5 rounded-lg bg-gradient-to-br from-accent/10 to-accent-2/10 border-2 border-accent/30 mb-5"
          >
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx">
              <lucide-icon name="lightbulb" size="18"></lucide-icon> Estratégia Recomendada
            </h2>
            <p class="text-base leading-relaxed text-tx m-0">{{ s.summary }}</p>
          </div>

          <!-- Gaps -->
          @if (s.allocation_gaps.length > 0) {
            <div class="p-5 rounded-lg bg-panel border border-border mb-5">
              <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
                <lucide-icon name="circle-alert" size="18"></lucide-icon> Ajustes Necessários
              </h2>
              <div class="flex flex-col gap-3">
                @for (gap of s.allocation_gaps; track gap.category) {
                  <div class="p-4 rounded-lg bg-panel-2 border border-border">
                    <div class="flex items-start justify-between gap-4 mb-3">
                      <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                          <span class="tag tag-cat" [class]="'cat-' + gap.category">{{
                            ui.categoryLabel(gap.category)
                          }}</span>
                          <span
                            class="tag"
                            [class]="gap.gap_value > 0 ? 'tag-warning' : 'tag-accent'"
                            >{{ gap.action }}</span
                          >
                        </div>
                        <div class="flex items-center gap-4 text-sm flex-wrap">
                          <div>
                            <span class="text-muted">Atual:</span>
                            <strong class="text-tx ml-1"
                              >{{ gap.current_pct | number: '1.1-1' }}%</strong
                            >
                          </div>
                          <lucide-icon
                            name="arrow-right"
                            size="14"
                            class="text-muted"
                          ></lucide-icon>
                          <div>
                            <span class="text-muted">Meta:</span>
                            <strong class="text-accent ml-1"
                              >{{ gap.target_pct | number: '1.1-1' }}%</strong
                            >
                          </div>
                          <div
                            class="ml-auto"
                            [class.warn]="gap.gap_value > 0"
                            [class.good]="gap.gap_value < 0"
                          >
                            Gap:
                            <strong
                              >{{ gap.gap_pct > 0 ? '+' : ''
                              }}{{ gap.gap_pct | number: '1.1-1' }}%</strong
                            >
                            (R$ {{ gap.gap_value | number: '1.2-2' }})
                          </div>
                        </div>
                      </div>
                    </div>
                    <!-- Barra de alocação visual -->
                    <div
                      class="relative h-6 rounded-lg border border-border"
                      style="background: rgba(var(--muted) / 0.08)"
                    >
                      <!-- Preenchimento atual (cor da categoria) -->
                      <div
                        class="absolute inset-y-0 left-0 transition-all duration-300 rounded-l-lg"
                        [style.width.%]="gap.current_pct"
                        [style.background]="getCategoryBarColor(gap.category)"
                        [title]="'Atual: ' + gap.current_pct.toFixed(1) + '%'"
                      ></div>

                      <!-- Marcador IDEAL (meta) - Pin destacado -->
                      <div
                        class="absolute top-0 bottom-0 flex items-center z-20 transition-all duration-300"
                        [style.left.%]="gap.target_pct"
                        style="transform: translateX(-50%)"
                      >
                        <!-- Pin/Marcador do ideal -->
                        <div class="relative flex flex-col items-center">
                          <!-- Círculo no topo -->
                          <div
                            class="w-3 h-3 rounded-full border-2 -mb-1.5 z-10"
                            style="background: rgb(var(--accent)); border-color: white; box-shadow: 0 2px 8px rgba(var(--accent) / 0.5)"
                            [title]="'Meta: ' + gap.target_pct.toFixed(1) + '%'"
                          ></div>
                          <!-- Linha vertical do pin -->
                          <div
                            class="w-0.5 h-6"
                            style="background: rgb(var(--accent)); box-shadow: 0 0 4px rgba(var(--accent) / 0.4)"
                          ></div>
                          <!-- Label IDEAL abaixo da barra -->
                          <div
                            class="absolute -bottom-5 whitespace-nowrap text-[10px] font-semibold px-1.5 py-0.5 rounded dark:text-white"
                            style="background: rgb(var(--accent)); color: black"
                          >
                            IDEAL
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Legenda da barra -->
                    <div class="flex items-center justify-between text-xs text-muted mt-6">
                      <span class="flex items-center gap-1.5">
                        <span
                          class="inline-block w-3 h-3 rounded"
                          [style.background]="getCategoryBarColor(gap.category)"
                        ></span>
                        <span
                          >Atual:
                          <strong class="text-tx"
                            >{{ gap.current_pct | number: '1.1-1' }}%</strong
                          ></span
                        >
                      </span>
                      <span class="flex items-center gap-1.5">
                        <span
                          >Meta:
                          <strong class="text-accent"
                            >{{ gap.target_pct | number: '1.1-1' }}%</strong
                          ></span
                        >
                        <span
                          class="inline-block w-2.5 h-2.5 rounded-full"
                          style="background: rgb(var(--accent))"
                        ></span>
                      </span>
                    </div>
                  </div>
                }
              </div>
            </div>
          }

          <!-- Sugestões -->
          @if (s.suggestions.length > 0) {
            <div class="p-5 rounded-lg bg-panel border border-border mb-5">
              <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
                <lucide-icon name="trending-up" size="18"></lucide-icon> Sugestões de Investimento
              </h2>
              <p class="text-sm text-muted mb-4">
                {{ s.suggestions.length }}
                {{ s.suggestions.length === 1 ? 'ativo sugerido' : 'ativos sugeridos' }} — Total a
                investir: <strong>R$ {{ totalToInvest(s) | number: '1.2-2' }}</strong>
              </p>
              <div class="flex flex-col gap-4">
                @for (sug of s.suggestions; track sug.ticker) {
                  @if (sug.ticker === 'RENDA_FIXA') {
                    <!-- Sugestão especial de Renda Fixa -->
                    <div class="p-4 rounded-lg bg-blue-500/10 border-2 border-blue-500/40">
                      <div class="flex items-start justify-between gap-4">
                        <div class="flex-1">
                          <div class="flex items-center gap-2 flex-wrap mb-2">
                            <lucide-icon
                              name="landmark"
                              size="18"
                              class="text-blue-400"
                            ></lucide-icon>
                            <div class="font-bold text-lg text-tx">Renda Fixa</div>
                            <span class="tag bg-blue-500/20 text-blue-400 border-blue-500/30"
                              >Alocação necessária</span
                            >
                          </div>
                          @for (reason of sug.reasons; track reason) {
                            <div class="flex items-start gap-2 text-sm text-tx mb-1">
                              <lucide-icon
                                name="arrow-right"
                                size="12"
                                class="text-blue-400 flex-shrink-0 mt-0.5"
                              ></lucide-icon>
                              <span>{{ reason }}</span>
                            </div>
                          }
                        </div>
                        <div class="text-right flex-shrink-0">
                          <div class="text-xs text-muted mb-1">Alocar</div>
                          <div class="text-2xl font-bold text-blue-400">
                            R$ {{ sug.invest_amount | number: '1.2-2' }}
                          </div>
                          <button
                            class="flex items-center gap-1 px-3 py-1.5 mt-2 rounded-lg text-xs font-medium cursor-pointer bg-blue-500 text-white border-0 hover:opacity-90 transition-opacity"
                            type="button"
                            (click)="activeTab.set('renda_fixa')"
                          >
                            <lucide-icon name="calculator" size="12"></lucide-icon> Simular RF
                          </button>
                        </div>
                      </div>
                    </div>
                  } @else {
                    <div
                      class="p-4 rounded-lg bg-panel-2 border-2"
                      [class.border-accent-50]="sug.already_held"
                      [class.border-border]="!sug.already_held"
                    >
                      <div class="flex justify-between items-start gap-4 mb-3">
                        <div class="flex-1 min-w-0">
                          <div class="flex items-center gap-2 flex-wrap mb-2">
                            <div class="font-bold text-lg text-tx">{{ sug.ticker }}</div>
                            <span class="tag">{{ assetLabel(sug.asset_type) }}</span>
                            <span class="tag tag-cat" [class]="'cat-' + sug.category">{{
                              ui.categoryLabel(sug.category)
                            }}</span>
                            @if (sug.already_held) {
                              <span class="tag tag-accent"
                                ><lucide-icon name="circle-check" size="11"></lucide-icon> Na
                                carteira</span
                              >
                            }
                          </div>
                          <div class="text-sm text-muted mb-2">{{ sug.name }}</div>
                          <div class="flex items-center gap-2 text-xs flex-wrap">
                            <span
                              class="verdict-pill"
                              [class]="verdictClassFromString(sug.verdict)"
                              >{{ sug.verdict }}</span
                            >
                            <span class="text-muted"
                              >Score: <strong>{{ sug.score | number: '1.0-0' }}</strong></span
                            >
                            @if (sug.margin_of_safety != null) {
                              <span class="text-muted"
                                >MS:
                                <strong
                                  >{{ sug.margin_of_safety * 100 | number: '1.0-0' }}%</strong
                                ></span
                              >
                            }
                            @if (sug.dividend_yield) {
                              <span class="text-muted"
                                >DY:
                                <strong>{{ sug.dividend_yield | number: '1.1-1' }}%</strong></span
                              >
                            }
                          </div>
                        </div>
                        <div class="text-right flex-shrink-0">
                          <div class="text-xs text-muted mb-1">Investir</div>
                          <div class="text-2xl font-bold text-accent">
                            R$ {{ sug.invest_amount | number: '1.2-2' }}
                          </div>
                          <div class="text-sm text-muted mt-1">
                            {{ sug.quantity }} × R$ {{ sug.price | number: '1.2-2' }}
                          </div>
                        </div>
                      </div>
                      <div class="p-3 rounded-lg bg-bg-2 border border-border mb-3">
                        <div class="flex items-start gap-2">
                          <lucide-icon
                            name="target"
                            size="14"
                            class="text-accent flex-shrink-0 mt-0.5"
                          ></lucide-icon>
                          <div class="flex-1">
                            <div class="text-xs font-medium text-muted mb-1">Objetivo:</div>
                            <div class="text-sm text-tx">{{ sug.objective }}</div>
                          </div>
                        </div>
                      </div>
                      <!-- Custo de transação se houver -->
                      @if (sug.transaction_cost) {
                        <div
                          class="p-3 rounded-lg bg-orange-500/10 border border-orange-500/30 mb-3 text-xs"
                        >
                          <div class="flex items-center gap-1.5 text-orange-400 font-medium mb-1">
                            <lucide-icon name="receipt" size="13"></lucide-icon> IR estimado na
                            venda
                          </div>
                          <span class="text-muted">{{ sug.transaction_cost.observation }}</span>
                          @if (sug.transaction_cost.ir_amount > 0) {
                            <span class="ml-2 text-orange-400 font-medium"
                              >R$ {{ sug.transaction_cost.ir_amount | number: '1.2-2' }}</span
                            >
                          }
                        </div>
                      }
                      <div class="flex flex-col gap-1.5">
                        <div class="text-xs font-medium text-muted mb-1">Por que investir?</div>
                        @for (reason of sug.reasons; track reason) {
                          <div class="flex items-start gap-2 text-xs">
                            <lucide-icon
                              name="check"
                              size="12"
                              class="text-accent flex-shrink-0 mt-0.5"
                            ></lucide-icon>
                            <span class="text-tx">{{ reason }}</span>
                          </div>
                        }
                      </div>
                    </div>
                  }
                }
              </div>
            </div>
          } @else if (s.cash_available < 100) {
            <div
              class="empty flex items-center gap-2 p-6 rounded-lg bg-panel border border-border text-muted"
            >
              <lucide-icon name="wallet" size="18"></lucide-icon>
              Caixa insuficiente. Configure em Configurações.
            </div>
          } @else {
            <div
              class="empty flex items-center gap-2 p-6 rounded-lg bg-panel border border-border text-muted"
            >
              <lucide-icon name="circle-check" size="18"></lucide-icon>
              Carteira bem balanceada! Nenhum ajuste crítico.
            </div>
          }

          <!-- Alocação Projetada -->
          @if (s.suggestions.length > 0 && s.projected_allocation.length > 0) {
            <div class="p-5 rounded-lg bg-panel border border-border">
              <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
                <lucide-icon name="git-compare" size="18"></lucide-icon> Alocação Projetada
              </h2>
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <div>
                  <h3 class="text-sm font-semibold mb-3 text-muted">Atual</h3>
                  <div class="flex flex-col gap-2">
                    @for (item of s.current_allocation; track item.category) {
                      <div
                        class="flex items-center justify-between gap-3 p-2 rounded bg-bg-2 border border-border"
                      >
                        <span class="tag tag-cat" [class]="'cat-' + item.category">{{
                          ui.categoryLabel(item.category)
                        }}</span>
                        <div class="flex-1 h-3 rounded-full bg-bg overflow-hidden">
                          <div
                            class="h-full rounded-full bg-muted transition-all"
                            [style.width.%]="item.current_pct"
                          ></div>
                        </div>
                        <span class="text-xs text-tx font-medium w-14 text-right"
                          >{{ item.current_pct | number: '1.1-1' }}%</span
                        >
                      </div>
                    }
                  </div>
                </div>
                <div>
                  <h3 class="text-sm font-semibold mb-3 text-accent">Projetada</h3>
                  <div class="flex flex-col gap-2">
                    @for (item of s.projected_allocation; track item.category) {
                      <div
                        class="flex items-center justify-between gap-3 p-2 rounded bg-bg-2 border border-accent/30"
                      >
                        <span class="tag tag-cat" [class]="'cat-' + item.category">{{
                          ui.categoryLabel(item.category)
                        }}</span>
                        <div class="flex-1 h-3 rounded-full bg-bg overflow-hidden">
                          <div
                            class="h-full rounded-full bg-accent transition-all"
                            [style.width.%]="item.projected_pct"
                          ></div>
                        </div>
                        <span class="text-xs text-tx font-medium w-14 text-right"
                          >{{ item.projected_pct | number: '1.1-1' }}%</span
                        >
                      </div>
                    }
                  </div>
                </div>
              </div>
            </div>
          }
        } @else if (!loading.loading()) {
          <div class="empty p-6 rounded-lg bg-panel border border-border text-center">
            <lucide-icon
              name="wand-sparkles"
              size="32"
              class="text-muted mx-auto mb-3"
            ></lucide-icon>
            <h3 class="text-lg font-semibold m-0 mb-2 text-tx">
              Gere sua estratégia personalizada
            </h3>
            <p class="text-sm text-muted m-0">
              Clique em "Gerar nova estratégia" para sugestões baseadas no seu perfil.
            </p>
          </div>
        }
      }

      <!-- ===== ABA: RENDA FIXA ===== -->
      @if (activeTab() === 'renda_fixa') {
        <!-- Taxas de referência -->
        @if (referenceRates()) {
          <div
            class="flex items-center gap-4 p-4 rounded-lg bg-panel border border-border mb-5 flex-wrap text-sm"
          >
            <lucide-icon name="info" size="16" class="text-muted"></lucide-icon>
            <span class="text-muted">Taxas de referência:</span>
            <span class="font-medium text-tx"
              >CDI:
              <strong class="text-accent">{{ referenceRates()!.cdi_anual }}% a.a.</strong></span
            >
            <span class="font-medium text-tx"
              >Selic:
              <strong class="text-accent">{{ referenceRates()!.selic_anual }}% a.a.</strong></span
            >
            <span class="font-medium text-tx"
              >IPCA:
              <strong class="text-accent">{{ referenceRates()!.ipca_anual }}% a.a.</strong></span
            >
          </div>
        }

        <!-- Lista de ativos para comparar -->
        <div class="p-5 rounded-lg bg-panel border border-border mb-5">
          <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 text-tx">
              <lucide-icon name="landmark" size="18"></lucide-icon> Simulador de Renda Fixa
            </h2>
            <button
              type="button"
              class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer bg-panel-2 border border-border text-tx hover:bg-panel transition-all"
              (click)="addRFAtivo()"
            >
              <lucide-icon name="plus" size="15"></lucide-icon> Adicionar opção
            </button>
          </div>
          <p class="text-sm text-muted mb-4">
            Insira uma ou mais opções para comparar. Identifica a melhor taxa líquida.
          </p>

          <div class="flex flex-col gap-4">
            @for (ctrl of rfForms.controls; track $index; let i = $index) {
              <div class="p-4 rounded-lg bg-panel-2 border border-border" [formGroup]="ctrl">
                <div class="flex items-center justify-between mb-3">
                  <div class="font-medium text-sm text-tx">Opção {{ i + 1 }}</div>
                  @if (rfForms.length > 1) {
                    <button
                      type="button"
                      class="w-7 h-7 grid place-items-center rounded-lg text-muted hover:text-red-400 hover:bg-red-400/10 transition-all cursor-pointer"
                      (click)="removeRFAtivo(i)"
                    >
                      <lucide-icon name="x" size="14"></lucide-icon>
                    </button>
                  }
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  <div>
                    <label class="block text-xs text-muted mb-1">Nome / Banco (opcional)</label>
                    <input
                      type="text"
                      class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                      formControlName="nome"
                      placeholder="ex.: Nubank"
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-muted mb-1">Tipo</label>
                    <select
                      class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
                      formControlName="tipo"
                      (change)="onTipoChange(i)"
                    >
                      <option value="cdb">CDB</option>
                      <option value="lci">LCI</option>
                      <option value="lca">LCA</option>
                      <option value="tesouro_selic">Tesouro Selic</option>
                      <option value="tesouro_ipca">Tesouro IPCA+</option>
                      <option value="tesouro_pre">Tesouro Pré-fixado</option>
                      <option value="lc">LC</option>
                      <option value="cri">CRI</option>
                      <option value="cra">CRA</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs text-muted mb-1">Tipo de taxa</label>
                    <select
                      class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
                      formControlName="tipo_taxa"
                      (change)="onTaxaTipoChange(i)"
                    >
                      <option value="pre_fixado">Pré-fixado</option>
                      <option value="pos_fixado">Pós-fixado (CDI)</option>
                      <option value="hibrido">Híbrido (IPCA+)</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs text-muted mb-1">Valor investido (R$)</label>
                    <input
                      type="number"
                      class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                      formControlName="valor_investido"
                      min="100"
                      step="100"
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-muted mb-1">
                      @if (ctrl.controls['tipo_taxa'].value === 'pos_fixado') {
                        % do CDI
                      } @else {
                        Taxa a.a. (%)
                      }
                    </label>
                    <input
                      type="number"
                      class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                      [formControlName]="
                        ctrl.controls['tipo_taxa'].value === 'pos_fixado'
                          ? 'percentual_cdi'
                          : 'taxa'
                      "
                      min="0.1"
                      step="0.1"
                      [placeholder]="
                        ctrl.controls['tipo_taxa'].value === 'pos_fixado' ? 'ex.: 110' : 'ex.: 12.5'
                      "
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-muted mb-1">Prazo (meses)</label>
                    <input
                      type="number"
                      class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                      formControlName="prazo_meses"
                      min="1"
                      step="1"
                    />
                  </div>
                  <div>
                    <label class="block text-xs text-muted mb-1">Liquidez</label>
                    <select
                      class="w-full px-3 py-2 rounded-lg bg-bg border border-border text-tx text-sm focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer"
                      formControlName="liquidez"
                    >
                      <option value="no_vencimento">No vencimento</option>
                      <option value="diaria">Diária (D+1)</option>
                    </select>
                  </div>
                </div>
              </div>
            }
          </div>

          <div class="flex items-center gap-3 mt-4">
            <button
              type="button"
              class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 transition-opacity"
              (click)="compareRF()"
              [disabled]="loading.loading()"
            >
              <lucide-icon
                [name]="loading.loading() ? 'loader-circle' : 'calculator'"
                size="16"
              ></lucide-icon>
              {{
                loading.loading()
                  ? 'Calculando...'
                  : rfForms.length > 1
                    ? 'Comparar opções'
                    : 'Calcular rendimento'
              }}
            </button>
          </div>
        </div>

        <!-- Resultados RF -->
        @if (rfResult(); as result) {
          <div class="p-5 rounded-lg bg-panel border border-border">
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-2 text-tx">
              <lucide-icon name="chart-bar" size="18"></lucide-icon> Resultado da Análise
            </h2>
            <div class="flex items-center gap-3 mb-4 text-sm text-muted">
              <lucide-icon name="info" size="14"></lucide-icon>
              <span
                >CDI usado: <strong>{{ result.cdi_referencia }}%</strong> — Selic:
                <strong>{{ result.selic_referencia }}%</strong></span
              >
            </div>
            <div class="flex flex-col gap-4">
              @for (r of result.resultados; track $index; let i = $index) {
                <div
                  class="p-4 rounded-lg border-2 transition-all"
                  [class.border-accent]="r.melhor_opcao"
                  [class.bg-accent-5]="r.melhor_opcao"
                  [class.border-border]="!r.melhor_opcao"
                  [class.bg-panel-2]="!r.melhor_opcao"
                >
                  <div class="flex items-start justify-between gap-4 flex-wrap">
                    <div class="flex items-center gap-2 flex-wrap mb-2">
                      <span class="font-bold text-base text-tx">{{
                        r.nome || rfTipoLabel(r.tipo)
                      }}</span>
                      <span class="tag">{{ rfTipoLabel(r.tipo) }}</span>
                      @if (r.isento_ir) {
                        <span class="tag bg-green-500/20 text-green-400 border-green-500/30"
                          >Isento IR</span
                        >
                      }
                      @if (r.liquidez === 'diaria') {
                        <span class="tag bg-blue-500/20 text-blue-400 border-blue-500/30"
                          >Liquidez D+1</span
                        >
                      }
                      @if (r.melhor_opcao) {
                        <span class="tag bg-accent/20 text-accent border-accent/30">
                          <lucide-icon name="trophy" size="11"></lucide-icon> Melhor opção
                        </span>
                      }
                    </div>
                    <div class="text-right">
                      <div class="text-xs text-muted">Taxa líquida a.a.</div>
                      <div
                        class="text-2xl font-bold"
                        [class.text-accent]="r.melhor_opcao"
                        [class.text-tx]="!r.melhor_opcao"
                      >
                        {{ r.taxa_liquida_aa | number: '1.2-2' }}%
                      </div>
                      @if (r.taxa_equivalente_cdi_pct) {
                        <div class="text-xs text-muted">
                          ≈ {{ r.taxa_equivalente_cdi_pct | number: '1.1-1' }}% do CDI líquido
                        </div>
                      }
                    </div>
                  </div>
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
                    <div class="p-3 rounded-lg bg-bg border border-border text-center">
                      <div class="text-xs text-muted mb-0.5">Investido</div>
                      <div class="font-semibold text-sm text-tx">
                        R$ {{ r.valor_investido | number: '1.2-2' }}
                      </div>
                    </div>
                    <div class="p-3 rounded-lg bg-bg border border-border text-center">
                      <div class="text-xs text-muted mb-0.5">Rendimento bruto</div>
                      <div class="font-semibold text-sm text-tx good">
                        +R$ {{ r.rendimento_bruto | number: '1.2-2' }}
                      </div>
                    </div>
                    @if (!r.isento_ir) {
                      <div class="p-3 rounded-lg bg-bg border border-border text-center">
                        <div class="text-xs text-muted mb-0.5">IR ({{ r.ir.aliquota_pct }}%)</div>
                        <div class="font-semibold text-sm warn">
                          -R$ {{ r.ir.valor_ir | number: '1.2-2' }}
                        </div>
                      </div>
                    }
                    <div
                      class="p-3 rounded-lg bg-bg border border-border text-center"
                      [class.col-span-1]="!r.isento_ir"
                      [class.col-span-2]="r.isento_ir"
                    >
                      <div class="text-xs text-muted mb-0.5">
                        Valor líquido em {{ r.prazo_meses }}m
                      </div>
                      <div
                        class="font-bold text-base"
                        [class.text-accent]="r.melhor_opcao"
                        [class.text-tx]="!r.melhor_opcao"
                      >
                        R$ {{ r.valor_liquido | number: '1.2-2' }}
                      </div>
                    </div>
                  </div>
                </div>
              }
            </div>
          </div>
        }
      }
    </div>
  `,
})
export class StrategyComponent implements OnInit {
  private fb = inject(FormBuilder);
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  activeTab = signal<StrategyTab>('ajuste');
  strategy = signal<InvestmentStrategy | null>(null);
  analyzeResult = signal<AssetAnalysis | null>(null);
  rfResult = signal<RendaFixaCompareResponse | null>(null);
  referenceRates = signal<ReferenceRates | null>(null);

  // Form de análise de ativo
  analyzeForm: FormGroup<AnalyzeForm> = this.fb.group({
    symbol: this.fb.control('VALE3', { nonNullable: true, validators: Validators.required }),
    desired_yield: this.fb.control(0.06, {
      nonNullable: true,
      validators: [Validators.min(0.02), Validators.max(0.2)],
    }),
  });

  // FormArray para renda fixa
  rfForms!: FormArray<FormGroup<RendaFixaForm>>;

  ngOnInit(): void {
    this.rfForms = this.fb.array<FormGroup<RendaFixaForm>>([this._makeRFGroup()]);
    this.loadStrategy();
    this.svc
      .getReferencRates()
      .subscribe({ next: r => this.referenceRates.set(r), error: () => {} });
  }

  private _makeRFGroup(): FormGroup<RendaFixaForm> {
    return this.fb.group<RendaFixaForm>({
      tipo: this.fb.control('cdb', { nonNullable: true }),
      nome: this.fb.control('', { nonNullable: true }),
      valor_investido: this.fb.control(10000, { nonNullable: true, validators: Validators.min(1) }),
      taxa: this.fb.control(12.0, { nonNullable: true, validators: Validators.min(0.01) }),
      prazo_meses: this.fb.control(12, { nonNullable: true, validators: Validators.min(1) }),
      tipo_taxa: this.fb.control('pre_fixado', { nonNullable: true }),
      percentual_cdi: this.fb.control<number | null>(110),
      liquidez: this.fb.control('no_vencimento', { nonNullable: true }),
    });
  }

  addRFAtivo(): void {
    this.rfForms.push(this._makeRFGroup());
  }
  removeRFAtivo(i: number): void {
    this.rfForms.removeAt(i);
  }

  onTipoChange(i: number): void {
    const ctrl = this.rfForms.controls[i];
    const tipo = ctrl.controls.tipo.value;
    // LCI, LCA, CRI, CRA geralmente pós-fixados
    if (['lci', 'lca', 'cri', 'cra'].includes(tipo)) {
      ctrl.controls.tipo_taxa.setValue('pos_fixado');
    } else if (tipo === 'tesouro_selic') {
      ctrl.controls.tipo_taxa.setValue('pos_fixado');
    } else if (tipo === 'tesouro_ipca') {
      ctrl.controls.tipo_taxa.setValue('hibrido');
    } else if (tipo === 'tesouro_pre') {
      ctrl.controls.tipo_taxa.setValue('pre_fixado');
    }
  }

  onTaxaTipoChange(i: number): void {
    const ctrl = this.rfForms.controls[i];
    if (ctrl.controls.tipo_taxa.value !== 'pos_fixado') {
      ctrl.controls.percentual_cdi.setValue(null);
    } else {
      ctrl.controls.percentual_cdi.setValue(110);
    }
  }

  compareRF(): void {
    const ativos: RendaFixaAsset[] = this.rfForms.controls.map(ctrl => {
      const v = ctrl.getRawValue();
      return {
        tipo: v.tipo as any,
        nome: v.nome || null,
        valor_investido: v.valor_investido,
        taxa: v.taxa,
        prazo_meses: v.prazo_meses,
        tipo_taxa: v.tipo_taxa as any,
        percentual_cdi: v.tipo_taxa === 'pos_fixado' ? v.percentual_cdi : null,
        liquidez: v.liquidez as any,
      };
    });

    const cdi = this.referenceRates()?.cdi_anual ?? null;
    const selic = this.referenceRates()?.selic_anual ?? null;

    this.svc.compareRendaFixa({ ativos, cdi_anual: cdi, selic_anual: selic }).subscribe({
      next: r => this.rfResult.set(r),
      error: () => {},
    });
  }

  loadStrategy(): void {
    this.svc.getStrategy().subscribe({
      next: data => this.strategy.set(data),
      error: () => {},
    });
  }

  submitAnalyze(): void {
    if (this.analyzeForm.invalid) return;
    const { symbol, desired_yield } = this.analyzeForm.getRawValue();
    this.svc.analyzeAsset(symbol, desired_yield).subscribe({
      next: res => this.analyzeResult.set(res),
      error: () => {},
    });
  }

  riskClass(risk: string): string {
    return { Baixo: 'tag-success', Médio: 'tag-warning', Alto: 'tag-danger' }[risk] || 'tag-muted';
  }

  totalToInvest(s: InvestmentStrategy): number {
    return s.suggestions.reduce((sum, x) => sum + x.invest_amount, 0);
  }

  verdictClassFromString(v: string): string {
    if (v === 'STRONG_BUY' || v === 'BUY') return 'v-buy';
    if (v === 'STRONG_SELL' || v === 'SELL') return 'v-sell';
    if (v === 'HOLD') return 'v-hold';
    return 'v-unknown';
  }

  assetLabel(type: string): string {
    return (
      { br_stock: 'Ação BR', fii: 'FII', us_stock: 'Ação EUA', crypto: 'Cripto' }[type] || type
    );
  }

  rfTipoLabel(tipo: string): string {
    return (
      {
        cdb: 'CDB',
        lci: 'LCI',
        lca: 'LCA',
        tesouro_selic: 'Tesouro Selic',
        tesouro_ipca: 'Tesouro IPCA+',
        tesouro_pre: 'Tesouro Pré',
        lc: 'LC',
        cri: 'CRI',
        cra: 'CRA',
      }[tipo] || tipo.toUpperCase()
    );
  }

  getCategoryBarColor(category: string): string {
    const colorMap: Record<string, string> = {
      renda_fixa: 'rgba(59, 130, 246, 0.6)', // Azul
      acoes_br: 'rgba(34, 197, 94, 0.6)', // Verde
      acoes_int: 'rgba(168, 85, 247, 0.6)', // Roxo
      fiis: 'rgba(251, 191, 36, 0.6)', // Amarelo
      cripto: 'rgba(249, 115, 22, 0.6)', // Laranja
    };
    return colorMap[category] || 'rgba(var(--accent) / 0.5)';
  }
}
