import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { BenchmarkResponse, DashboardResponse, RecommendService } from '../../core';
import { BenchmarkChartComponent } from '../benchmark-chart/benchmark-chart.component';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { PatrimonyChartComponent } from '../patrimony-chart/patrimony-chart.component';
import { SkeletonComponent } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-performance',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    PageHeaderComponent,
    PatrimonyChartComponent,
    BenchmarkChartComponent,
    SkeletonComponent,
  ],
  template: `
    <app-page-header
      title="Desempenho"
      question="Meu dinheiro está rendendo — e está rendendo mais que o CDI?"
    />

    <div class="flex flex-col gap-6">
      <section>
        <p class="fi-eyebrow text-ink-3 m-0 mb-2">Evolução do patrimônio</p>

        <!-- veredito: a leitura do período é a conclusão que esta tela existe para dar -->
        @if (vereditoPatrimonio(); as frase) {
          <p class="fi-verdict text-ink m-0 mb-4 max-w-reading">{{ frase }}</p>
        }

        @if (snapshots().length > 1) {
          <app-patrimony-chart [snapshots]="snapshots()" />
        } @else if (carregando()) {
          <app-skeleton shape="row" [count]="4" />
        } @else {
          <p class="fi-body text-ink-2 m-0">
            Ainda não há histórico suficiente. O fiance guarda um retrato da carteira por dia — a
            curva aparece a partir do segundo dia.
          </p>
        }
      </section>

      <section class="fi-block">
        <p class="fi-eyebrow text-ink-3 m-0 mb-2">Carteira, CDI e Ibovespa</p>

        @if (benchmark(); as b) {
          <p class="fi-verdict text-ink m-0 mb-4 max-w-reading">{{ vereditoBenchmark(b) }}</p>

          <app-benchmark-chart [points]="b.points" [ibovAvailable]="b.ibov_available" />

          <p class="fi-caption text-ink-3 mt-3 mb-0 max-w-reading">
            Retorno ponderado no tempo: aportes entram como aporte, não como rentabilidade.
            {{ origemDaTaxa(b) }}
          </p>
        } @else if (carregando()) {
          <app-skeleton shape="verdict" />
        } @else {
          <p class="fi-body text-ink-2 m-0">
            Não conseguimos montar a comparação agora.
            <button type="button" class="btn-link underline" (click)="load()">
              Tentar de novo
            </button>
          </p>
        }
      </section>
    </div>
  `,
})
export class PerformanceComponent implements OnInit {
  private readonly svc = inject(RecommendService);

  readonly snapshots = signal<DashboardResponse['snapshots']>([]);
  readonly benchmark = signal<BenchmarkResponse | null>(null);
  readonly carregando = signal(true);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.carregando.set(true);
    this.svc.dashboard().subscribe({
      next: d => this.snapshots.set(d.snapshots ?? []),
      error: () => undefined,
    });
    this.svc.getBenchmark().subscribe({
      next: b => {
        this.benchmark.set(b);
        this.carregando.set(false);
      },
      error: () => {
        this.benchmark.set(null);
        this.carregando.set(false);
      },
    });
  }

  readonly vereditoPatrimonio = computed<string | null>(() => {
    const s = this.snapshots();
    if (s.length < 2) return null;

    const primeiro = s[0].total_current;
    const ultimo = s[s.length - 1].total_current;
    if (!primeiro) return null;

    const delta = ultimo - primeiro;
    const pct = (delta / primeiro) * 100;
    const dias = s.length;

    if (Math.abs(pct) < 0.05) {
      return `Seu patrimônio está praticamente onde estava há ${dias} dias, em ${this.moeda(ultimo)}.`;
    }
    const verbo = delta > 0 ? 'subiu' : 'caiu';
    return (
      `Seu patrimônio ${verbo} de ${this.moeda(primeiro)} para ${this.moeda(ultimo)} ` +
      `nos últimos ${dias} dias — ${this.sinal(delta)}${this.moeda(Math.abs(delta))}, ` +
      `${this.pct(Math.abs(pct))}.`
    );
  });

  vereditoBenchmark(b: BenchmarkResponse): string {
    if (b.points.length < 2) {
      return 'Ainda não há histórico suficiente para comparar com o CDI e o Ibovespa.';
    }

    const carteira = b.portfolio_return_pct;
    const cdi = b.cdi_return_pct;
    const diferenca = carteira - cdi;

    const base =
      `No período, sua carteira rendeu ${this.pct(carteira)} e o CDI, ${this.pct(cdi)}` +
      (b.ibov_return_pct != null ? `; o Ibovespa, ${this.pct(b.ibov_return_pct)}` : '');

    if (Math.abs(diferenca) < 0.1) return `${base} — praticamente empatados.`;

    const lado = diferenca > 0 ? 'acima' : 'abaixo';
    const pontos = Math.abs(diferenca);
    const unidade = pontos === 1 ? 'ponto percentual' : 'pontos percentuais';
    return `${base} — ${pontos.toFixed(1).replace('.', ',')} ${unidade} ${lado} do CDI.`;
  }

  origemDaTaxa(b: BenchmarkResponse): string {
    const origem =
      {
        bcb: 'CDI do Banco Central.',
        bcb_cache_vencido: 'CDI de um cache vencido do Banco Central — a fonte não respondeu.',
        estimativa: 'CDI estimado: o Banco Central não respondeu e não havia cache.',
      }[b.cdi_source] ?? '';

    const base =
      b.cdi_basis === 'taxa_atual_composta'
        ? ' A curva extrapola a taxa de hoje para trás, então é referência, não o acumulado histórico.'
        : '';

    return origem + base;
  }

  private moeda(v: number): string {
    return `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  }

  private pct(v: number): string {
    return `${v.toFixed(1).replace('.', ',')}%`;
  }

  private sinal(v: number): string {
    return v >= 0 ? '+' : '−';
  }
}
