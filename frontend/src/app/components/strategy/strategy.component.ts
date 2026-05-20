import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { InvestmentStrategy, LoadingService, RecommendService, UiHelperService } from '../../core';

@Component({
  selector: 'app-strategy',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="flex items-center gap-3 mb-5 flex-wrap">
      <button class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity" (click)="loadStrategy()" [disabled]="loading.loading()">
        <lucide-icon [name]="loading.loading() ? 'loader-circle' : 'target'" size="16"></lucide-icon>
        {{ loading.loading() ? 'Gerando estratégia...' : 'Gerar nova estratégia' }}
      </button>
      <p class="text-sm text-muted m-0">
        Análise personalizada com base no seu perfil, carteira e metas de alocação.
      </p>
    </div>

    @if (strategy(); as s) {
      <!-- Perfil do Investidor -->
      <div class="p-5 rounded-lg bg-panel border border-border mb-5">
        <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx">
          <lucide-icon name="circle-user" size="18"></lucide-icon> Seu Perfil de Investidor
        </h2>
        <div class="flex items-start gap-4 flex-wrap">
          <div class="flex-1 min-w-[250px]">
            <div class="text-2xl font-bold text-accent mb-2">{{ s.profile.type }}</div>
            <p class="text-sm text-muted mb-3">{{ s.profile.description }}</p>
            <div class="flex items-center gap-2 text-sm">
              <span class="text-muted">Tolerância ao risco:</span>
              <span class="tag" [class]="riskClass(s.profile.risk_tolerance)">{{ s.profile.risk_tolerance }}</span>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div class="p-3 rounded-lg bg-bg-2 border border-border">
              <div class="text-xs text-muted mb-1">Capital total</div>
              <div class="text-lg font-bold text-tx">R$ {{ s.total_capital | number: '1.2-2' }}</div>
            </div>
            <div class="p-3 rounded-lg bg-bg-2 border border-border">
              <div class="text-xs text-muted mb-1">Caixa disponível</div>
              <div class="text-lg font-bold text-accent">R$ {{ s.cash_available | number: '1.2-2' }}</div>
            </div>
            <div class="p-3 rounded-lg bg-bg-2 border border-border">
              <div class="text-xs text-muted mb-1">Investido</div>
              <div class="text-lg font-bold text-tx">R$ {{ s.total_invested | number: '1.2-2' }}</div>
            </div>
            <div class="p-3 rounded-lg bg-bg-2 border border-border">
              <div class="text-xs text-muted mb-1">% em caixa</div>
              <div class="text-lg font-bold text-tx">{{ (s.cash_available / s.total_capital * 100) | number: '1.1-1' }}%</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Resumo da Estratégia -->
      <div class="p-5 rounded-lg bg-gradient-to-br from-accent/10 to-accent-2/10 border-2 border-accent/30 mb-5">
        <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-3 text-tx">
          <lucide-icon name="lightbulb" size="18"></lucide-icon> Estratégia Recomendada
        </h2>
        <p class="text-base leading-relaxed text-tx m-0">{{ s.summary }}</p>
      </div>

      <!-- Gaps de Alocação -->
      @if (s.allocation_gaps.length > 0) {
        <div class="p-5 rounded-lg bg-panel border border-border mb-5">
          <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
            <lucide-icon name="circle-alert" size="18"></lucide-icon> Ajustes Necessários
          </h2>
          <p class="text-sm text-muted mb-4">Diferenças entre sua alocação atual e suas metas:</p>
          <div class="flex flex-col gap-3">
            @for (gap of s.allocation_gaps; track gap.category) {
              <div class="p-4 rounded-lg bg-panel-2 border border-border">
                <div class="flex items-start justify-between gap-4 mb-3">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="tag tag-cat" [class]="'cat-' + gap.category">{{ ui.categoryLabel(gap.category) }}</span>
                      <span class="tag" [class]="gap.gap_value > 0 ? 'tag-success' : 'tag-warning'">
                        {{ gap.action }}
                      </span>
                    </div>
                    <div class="flex items-center gap-4 text-sm flex-wrap">
                      <div>
                        <span class="text-muted">Atual:</span>
                        <strong class="text-tx ml-1">{{ gap.current_pct | number: '1.1-1' }}%</strong>
                      </div>
                      <lucide-icon name="arrow-right" size="14" class="text-muted"></lucide-icon>
                      <div>
                        <span class="text-muted">Meta:</span>
                        <strong class="text-accent ml-1">{{ gap.target_pct | number: '1.1-1' }}%</strong>
                      </div>
                      <div class="ml-auto" [class.good]="gap.gap_value > 0" [class.warn]="gap.gap_value < 0">
                        Gap: <strong>{{ gap.gap_pct > 0 ? '+' : '' }}{{ gap.gap_pct | number: '1.1-1' }}%</strong>
                        (R$ {{ gap.gap_value | number: '1.2-2' }})
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Progress bar -->
                <div class="relative h-4 rounded-full bg-bg-2 overflow-hidden">
                  <div class="absolute inset-y-0 left-0 rounded-full bg-accent/30 transition-all" [style.width.%]="gap.current_pct"></div>
                  <div class="absolute top-0 bottom-0 w-0.5 bg-accent" [style.left.%]="gap.target_pct"></div>
                </div>
              </div>
            }
          </div>
        </div>
      }

      <!-- Sugestões de Investimento -->
      @if (s.suggestions.length > 0) {
        <div class="p-5 rounded-lg bg-panel border border-border mb-5">
          <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
            <lucide-icon name="trending-up" size="18"></lucide-icon> Sugestões de Investimento
          </h2>
          <p class="text-sm text-muted mb-4">
            {{ s.suggestions.length }} {{ s.suggestions.length === 1 ? 'ativo sugerido' : 'ativos sugeridos' }}
            — Total a investir: <strong>R$ {{ totalToInvest(s) | number: '1.2-2' }}</strong>
          </p>
          <div class="flex flex-col gap-4">
            @for (sug of s.suggestions; track sug.ticker) {
              <div class="p-4 rounded-lg bg-panel-2 border-2" [class.border-accent-50]="sug.already_held" [class.border-border]="!sug.already_held" [class.bg-accent-5]="sug.already_held">
                <div class="flex justify-between items-start gap-4 mb-3">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap mb-2">
                      <div class="font-bold text-lg text-tx">{{ sug.ticker }}</div>
                      <span class="tag">{{ assetLabel(sug.asset_type) }}</span>
                      <span class="tag tag-cat" [class]="'cat-' + sug.category">{{ ui.categoryLabel(sug.category) }}</span>
                      @if (sug.already_held) {
                        <span class="tag tag-accent">
                          <lucide-icon name="circle-check" size="11"></lucide-icon> Na carteira
                        </span>
                      }
                    </div>
                    <div class="text-sm text-muted mb-2">{{ sug.name }}</div>
                    <div class="flex items-center gap-2 text-xs flex-wrap">
                      <span class="verdict-pill" [class]="verdictClassFromString(sug.verdict)">{{ sug.verdict }}</span>
                      <span class="text-muted">Score: <strong>{{ sug.score | number: '1.0-0' }}</strong></span>
                      @if (sug.margin_of_safety != null) {
                        <span class="text-muted">MS: <strong>{{ (sug.margin_of_safety * 100) | number: '1.0-0' }}%</strong></span>
                      }
                      @if (sug.dividend_yield) {
                        <span class="text-muted">DY: <strong>{{ sug.dividend_yield | number: '1.1-1' }}%</strong></span>
                      }
                    </div>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <div class="text-xs text-muted mb-1">Investir</div>
                    <div class="text-2xl font-bold text-accent">R$ {{ sug.invest_amount | number: '1.2-2' }}</div>
                    <div class="text-sm text-muted mt-1">
                      {{ sug.quantity }} × R$ {{ sug.price | number: '1.2-2' }}
                    </div>
                  </div>
                </div>

                <!-- Objetivo -->
                <div class="p-3 rounded-lg bg-bg-2 border border-border mb-3">
                  <div class="flex items-start gap-2">
                    <lucide-icon name="target" size="14" class="text-accent flex-shrink-0 mt-0.5"></lucide-icon>
                    <div class="flex-1">
                      <div class="text-xs font-medium text-muted mb-1">Objetivo do investimento:</div>
                      <div class="text-sm text-tx">{{ sug.objective }}</div>
                    </div>
                  </div>
                </div>

                <!-- Razões -->
                <div class="flex flex-col gap-1.5">
                  <div class="text-xs font-medium text-muted mb-1">Por que investir?</div>
                  @for (reason of sug.reasons; track reason) {
                    <div class="flex items-start gap-2 text-xs">
                      <lucide-icon name="check" size="12" class="text-accent flex-shrink-0 mt-0.5"></lucide-icon>
                      <span class="text-tx">{{ reason }}</span>
                    </div>
                  }
                </div>
              </div>
            }
          </div>
        </div>
      } @else if (s.cash_available < 100) {
        <div class="empty flex items-center gap-2 p-6 rounded-lg bg-panel border border-border text-muted">
          <lucide-icon name="wallet" size="18"></lucide-icon>
          Caixa insuficiente para gerar sugestões. Configure um valor maior em Configurações.
        </div>
      } @else {
        <div class="empty flex items-center gap-2 p-6 rounded-lg bg-panel border border-border text-muted">
          <lucide-icon name="circle-check" size="18"></lucide-icon>
          Sua carteira está bem balanceada! Não há ajustes críticos no momento.
        </div>
      }

      <!-- Comparação: Atual vs Projetado -->
      @if (s.suggestions.length > 0 && s.projected_allocation.length > 0) {
        <div class="p-5 rounded-lg bg-panel border border-border">
          <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
            <lucide-icon name="git-compare" size="18"></lucide-icon> Alocação Projetada
          </h2>
          <p class="text-sm text-muted mb-4">Como ficará sua carteira após executar as sugestões:</p>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <!-- Atual -->
            <div>
              <h3 class="text-sm font-semibold mb-3 text-muted">Alocação Atual</h3>
              <div class="flex flex-col gap-2">
                @for (item of s.current_allocation; track item.category) {
                  <div class="flex items-center justify-between gap-3 p-2 rounded bg-bg-2 border border-border">
                    <span class="tag tag-cat" [class]="'cat-' + item.category">{{ ui.categoryLabel(item.category) }}</span>
                    <div class="flex-1 h-3 rounded-full bg-bg overflow-hidden">
                      <div class="h-full rounded-full bg-muted transition-all" [style.width.%]="item.current_pct"></div>
                    </div>
                    <span class="text-xs text-tx font-medium w-14 text-right">{{ item.current_pct | number: '1.1-1' }}%</span>
                  </div>
                }
              </div>
            </div>

            <!-- Projetado -->
            <div>
              <h3 class="text-sm font-semibold mb-3 text-accent">Alocação Projetada</h3>
              <div class="flex flex-col gap-2">
                @for (item of s.projected_allocation; track item.category) {
                  <div class="flex items-center justify-between gap-3 p-2 rounded bg-bg-2 border border-accent/30">
                    <span class="tag tag-cat" [class]="'cat-' + item.category">{{ ui.categoryLabel(item.category) }}</span>
                    <div class="flex-1 h-3 rounded-full bg-bg overflow-hidden">
                      <div class="h-full rounded-full bg-accent transition-all" [style.width.%]="item.projected_pct"></div>
                    </div>
                    <span class="text-xs text-tx font-medium w-14 text-right">{{ item.projected_pct | number: '1.1-1' }}%</span>
                  </div>
                }
              </div>
            </div>
          </div>
        </div>
      }
    } @else if (!loading.loading()) {
      <div class="empty p-6 rounded-lg bg-panel border border-border text-center">
        <lucide-icon name="wand-sparkles" size="32" class="text-muted mx-auto mb-3"></lucide-icon>
        <h3 class="text-lg font-semibold m-0 mb-2 text-tx">Gere sua estratégia personalizada</h3>
        <p class="text-sm text-muted m-0">
          Clique em "Gerar nova estratégia" para receber sugestões baseadas no seu perfil,
          carteira atual e metas de alocação.
        </p>
      </div>
    }
  `,
})
export class StrategyComponent implements OnInit {
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);

  strategy = signal<InvestmentStrategy | null>(null);

  ngOnInit(): void {
    this.loadStrategy();
  }

  loadStrategy(): void {
    this.svc.getStrategy().subscribe({
      next: (data) => {
        this.strategy.set(data);
      },
      error: () => {},
      complete: () => {},
    });
  }

  riskClass(risk: string): string {
    const map: Record<string, string> = {
      'Baixo': 'tag-success',
      'Médio': 'tag-warning',
      'Alto': 'tag-danger',
    };
    return map[risk] || 'tag-muted';
  }

  totalToInvest(strategy: InvestmentStrategy): number {
    return strategy.suggestions.reduce((sum, s) => sum + s.invest_amount, 0);
  }

  verdictClassFromString(verdict: string): string {
    if (verdict === 'STRONG_BUY' || verdict === 'BUY') return 'v-buy';
    if (verdict === 'STRONG_SELL' || verdict === 'SELL') return 'v-sell';
    if (verdict === 'HOLD') return 'v-hold';
    return 'v-unknown';
  }

  assetLabel(type: string): string {
    const map: Record<string, string> = {
      'br_stock': 'Ação BR',
      'fii': 'FII',
      'us_stock': 'Ação EUA',
      'crypto': 'Cripto',
    };
    return map[type] || type;
  }
}
