import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { DashboardResponse, LoadingService, RecommendService, UiHelperService } from '../../core';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="flex flex-col gap-5">
      <div class="flex items-center gap-3 flex-wrap">
        <button
          class="flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer bg-accent text-white border-0 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          (click)="loadDashboard()"
          [disabled]="loading.loading()"
        >
          <lucide-icon
            [name]="loading.loading() ? 'loader-circle' : 'refresh-cw'"
            size="16"
          ></lucide-icon>
          {{ loading.loading() ? 'Atualizando...' : 'Atualizar dados' }}
        </button>
        <span class="text-sm text-muted" *ngIf="data()?.last_updated">
          Última atualização: {{ ui.formatTimestamp(data()!.last_updated!) }}
        </span>
      </div>

      @if (data(); as d) {
        <!-- KPIs -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="p-4 rounded-lg bg-panel border border-border">
            <div class="flex items-center gap-2 text-sm text-muted mb-2">
              <lucide-icon name="wallet" size="14"></lucide-icon> Valor atual
            </div>
            <div class="text-2xl font-bold text-tx">
              R$ {{ d.summary.total_current | number: '1.2-2' }}
            </div>
            <div
              class="text-sm mt-1"
              [class.good]="d.summary.total_pnl >= 0"
              [class.warn]="d.summary.total_pnl < 0"
            >
              {{ d.summary.total_pnl >= 0 ? '+' : ''
              }}{{ d.summary.total_pnl | number: '1.2-2' }} ({{
                d.summary.total_pnl_pct | number: '1.2-2'
              }}%)
            </div>
          </div>
          <div class="p-4 rounded-lg bg-panel border border-border">
            <div class="flex items-center gap-2 text-sm text-muted mb-2">
              <lucide-icon name="chart-column" size="14"></lucide-icon> Investido
            </div>
            <div class="text-2xl font-bold text-tx">
              R$ {{ d.summary.total_invested | number: '1.2-2' }}
            </div>
            <div class="text-sm text-muted mt-1">{{ d.summary.positions_count }} ativos</div>
          </div>
          <div class="p-4 rounded-lg bg-panel border border-border">
            <div class="flex items-center gap-2 text-sm text-muted mb-2">
              <lucide-icon name="coins" size="14"></lucide-icon> Caixa disponível
            </div>
            <div class="text-2xl font-bold text-tx">
              R$ {{ d.summary.cash_available | number: '1.2-2' }}
            </div>
            <div class="text-sm text-muted mt-1">para alocar</div>
          </div>
          <div class="p-4 rounded-lg bg-panel border border-border">
            <div class="flex items-center gap-2 text-sm text-muted mb-2">
              <lucide-icon name="percent" size="14"></lucide-icon> Yield da carteira
            </div>
            <div class="text-2xl font-bold text-tx">
              {{
                d.summary.portfolio_yield != null
                  ? (d.summary.portfolio_yield | number: '1.2-2') + '%'
                  : '—'
              }}
            </div>
            <div class="text-sm text-muted mt-1">DY médio ponderado</div>
          </div>
        </div>

        <!-- Alertas -->
        @if (d.alerts.length > 0) {
          <div class="p-5 rounded-lg bg-panel border border-border">
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
              <lucide-icon name="triangle-alert" size="18"></lucide-icon> Alertas
            </h2>
            <div class="flex flex-col gap-2">
              @for (a of d.alerts; track a.title) {
                <div class="alert" [class]="'alert-' + a.severity">
                  <div class="flex items-center gap-2 font-medium text-sm">
                    <lucide-icon [name]="ui.alertIcon(a.kind)" size="14"></lucide-icon>
                    {{ a.title }}
                  </div>
                  <div class="text-sm text-muted mt-1">{{ a.detail }}</div>
                </div>
              }
            </div>
          </div>
        } @else if (d.positions.length > 0) {
          <div
            class="empty flex items-center gap-2 p-4 rounded-lg bg-panel border border-border text-muted"
          >
            <lucide-icon name="check" size="16"></lucide-icon>
            Nenhum alerta no momento. Sua carteira está dentro dos parâmetros.
          </div>
        }

        <!-- Top Buys / Sells -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div class="p-5 rounded-lg bg-panel border border-border">
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
              <lucide-icon name="trending-up" size="18"></lucide-icon> Oportunidades de compra
            </h2>
            @if (d.top_buys.length === 0) {
              <div class="text-muted">Nenhuma oportunidade clara no momento.</div>
            } @else {
              <div class="flex flex-col gap-3">
                @for (o of d.top_buys; track o.ticker) {
                  <div
                    class="flex justify-between items-start gap-4 p-3 rounded-lg bg-panel-2 border border-border hover:shadow-lg transition-shadow"
                  >
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap mb-1">
                        <div class="font-semibold text-base text-tx">{{ o.ticker }}</div>
                        <span class="tag">{{ ui.assetTypeLabel(o.asset_type) }}</span>
                        <span class="tag tag-cat" [class]="'cat-' + o.category_resolved">{{
                          ui.categoryLabel(o.category_resolved)
                        }}</span>
                      </div>
                      <div class="text-sm text-muted truncate mb-2">{{ o.name }}</div>
                      <div class="flex items-center gap-2 flex-wrap text-xs">
                        <span class="verdict-pill" [class]="ui.verdictClass(o.verdict)">{{
                          o.label
                        }}</span>
                        <span *ngIf="o.margin_of_safety != null" class="text-muted"
                          >MS: {{ o.margin_of_safety * 100 | number: '1.0-0' }}%</span
                        >
                        <span *ngIf="o.dividend_yield" class="text-muted"
                          >DY: {{ o.dividend_yield | number: '1.1-1' }}%</span
                        >
                      </div>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <div class="text-lg font-bold text-tx">
                        R$ {{ o.price | number: '1.2-2' }}
                      </div>
                      <div class="text-xs text-muted" *ngIf="o.fair_price">
                        justo: {{ o.fair_price | number: '1.2-2' }}
                      </div>
                      <div class="text-xs text-soft mt-1" *ngIf="o.suggested_quantity">
                        {{ o.suggested_quantity }} cotas · R$
                        {{ o.suggested_invest | number: '1.2-2' }}
                      </div>
                    </div>
                  </div>
                }
              </div>
            }
          </div>

          <div class="p-5 rounded-lg bg-panel border border-border">
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
              <lucide-icon name="trending-down" size="18"></lucide-icon> Atenção (sinal de venda)
            </h2>
            @if (d.top_sells.length === 0) {
              <div class="text-muted">Nenhum ativo com sinal de venda.</div>
            } @else {
              <div class="flex flex-col gap-3">
                @for (p of d.top_sells; track p.ticker) {
                  <div
                    class="flex justify-between items-start gap-4 p-3 rounded-lg bg-panel-2 border border-border hover:shadow-lg transition-shadow"
                  >
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 flex-wrap mb-1">
                        <div class="font-semibold text-base text-tx">{{ p.ticker }}</div>
                        <span class="tag">{{ ui.assetTypeLabel(p.asset_type) }}</span>
                      </div>
                      <div class="text-sm text-muted truncate mb-2">{{ p.name }}</div>
                      <div class="flex items-center gap-2 flex-wrap text-xs">
                        <span class="verdict-pill" [class]="ui.verdictClass(p.verdict)">{{
                          p.label
                        }}</span>
                        <span
                          *ngIf="p.pnl_pct != null"
                          [class.good]="p.pnl_pct >= 0"
                          [class.warn]="p.pnl_pct < 0"
                          class="text-xs"
                        >
                          PnL: {{ p.pnl_pct | number: '1.2-2' }}%
                        </span>
                      </div>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <div class="text-lg font-bold text-tx">
                        R$ {{ p.current_price | number: '1.2-2' }}
                      </div>
                      <div class="text-xs text-muted" *ngIf="p.fair_price">
                        justo: {{ p.fair_price | number: '1.2-2' }}
                      </div>
                    </div>
                  </div>
                }
              </div>
            }
          </div>
        </div>

        <!-- Alocação vs Metas -->
        <div class="p-5 rounded-lg bg-panel border border-border">
          <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
            <lucide-icon name="target" size="18"></lucide-icon> Alocação vs. metas
          </h2>
          <div class="flex flex-col gap-4">
            @for (a of d.allocations; track a.category) {
              <div class="flex flex-col gap-2">
                <div class="flex items-center justify-between gap-3">
                  <span class="tag tag-cat" [class]="'cat-' + a.category">{{
                    ui.categoryLabel(a.category)
                  }}</span>
                  <span class="text-sm text-muted">R$ {{ a.current_value | number: '1.2-2' }}</span>
                </div>
                <div class="relative h-6 rounded-full bg-bg-2 overflow-hidden">
                  <div
                    class="absolute inset-y-0 left-0 rounded-full bg-accent transition-all"
                    [style.width.%]="a.current_pct"
                  ></div>
                  <div
                    class="absolute top-0 bottom-0 w-0.5 bg-accent-2"
                    *ngIf="a.target_pct != null"
                    [style.left.%]="a.target_pct"
                  ></div>
                </div>
                <div class="flex items-center gap-2 text-sm">
                  <strong class="text-tx">{{ a.current_pct | number: '1.1-1' }}%</strong>
                  <span class="text-muted" *ngIf="a.target_pct != null">
                    / meta {{ a.target_pct }}%</span
                  >
                  <span
                    *ngIf="a.delta_pct != null && Math.abs(a.delta_pct) >= 2"
                    class="text-xs"
                    [class.good]="a.delta_pct >= 0"
                    [class.warn]="a.delta_pct < 0"
                  >
                    {{ a.delta_pct > 0 ? '+' : '' }}{{ a.delta_pct | number: '1.1-1' }}%
                  </span>
                </div>
              </div>
            }
          </div>
        </div>

        <!-- Gráfico de Evolução -->
        @if (d.snapshots.length >= 2) {
          <div class="p-5 rounded-lg bg-panel border border-border">
            <h2 class="flex items-center gap-2 text-xl font-bold m-0 mb-4 text-tx">
              <lucide-icon name="chart-column" size="18"></lucide-icon> Evolução do patrimônio
            </h2>
            <svg
              class="w-full h-24 stroke-accent stroke-[2] fill-none"
              viewBox="0 0 600 100"
              preserveAspectRatio="none"
            >
              <path [attr.d]="ui.snapshotPath(d.snapshots, 600, 90)" />
            </svg>
            <div class="text-xs text-muted text-right mt-2">{{ d.snapshots.length }} pontos</div>
          </div>
        }

        <div
          class="p-4 rounded-lg bg-panel-2 border border-border text-xs text-muted leading-relaxed"
        >
          {{ d.disclaimer }}
        </div>
      } @else if (!loading.loading()) {
        <div class="empty p-6 rounded-lg bg-panel border border-border">
          <h3 class="text-lg font-semibold m-0 mb-2 text-tx">Bem-vindo</h3>
          <p class="text-sm text-muted m-0">
            Vá em <strong>Meus Ativos</strong> para cadastrar sua carteira ou em
            <strong>Configurações</strong> para definir caixa, metas e watchlist.
          </p>
        </div>
      }
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  private svc = inject(RecommendService);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);
  readonly Math = Math;

  data = signal<DashboardResponse | null>(null);

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.svc.dashboard().subscribe({
      next: res => {
        this.data.set(res);
      },
      error: () => {},
      complete: () => {},
    });
  }
}
