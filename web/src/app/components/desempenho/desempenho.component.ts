import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';
import { BenchmarkResponse, DashboardResponse, RecommendService } from '../../core';
import { BenchmarkChartComponent } from '../benchmark-chart/benchmark-chart.component';
import { PatrimonyChartComponent } from '../patrimony-chart/patrimony-chart.component';

@Component({
  selector: 'app-desempenho',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, PatrimonyChartComponent, BenchmarkChartComponent],
  template: `
    <div class="flex flex-col gap-6">
      <section>
        <p class="fi-eyebrow text-ink-3 m-0 mb-1">Como meu patrimônio evoluiu?</p>
        <h2 class="fi-title text-ink m-0 mb-4">Evolução do patrimônio</h2>
        @if (snapshots().length > 1) {
          <app-patrimony-chart [snapshots]="snapshots()" />
        } @else {
          <p class="fi-body text-ink-2 m-0">
            Ainda não há histórico suficiente. O fiance guarda um retrato da carteira por dia — a
            curva aparece a partir do segundo dia.
          </p>
        }
      </section>

      <section class="pt-6 border-t border-hairline">
        <p class="fi-eyebrow text-ink-3 m-0 mb-1">Estou superando o mercado?</p>
        <h2 class="fi-title text-ink m-0 mb-4">Carteira, CDI e Ibovespa</h2>
        @if (benchmark(); as b) {
          <app-benchmark-chart [points]="b.points" [ibovAvailable]="b.ibov_available" />
          <p class="fi-caption text-ink-3 mt-3 mb-0">
            Retorno ponderado no tempo: aportes entram como aporte, não como rentabilidade.
          </p>
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
export class DesempenhoComponent implements OnInit {
  private readonly svc = inject(RecommendService);

  readonly snapshots = signal<DashboardResponse['snapshots']>([]);
  readonly benchmark = signal<BenchmarkResponse | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.svc.dashboard().subscribe({
      next: d => this.snapshots.set(d.snapshots ?? []),
      error: () => {},
    });
    this.svc.getBenchmark().subscribe({
      next: b => this.benchmark.set(b),
      error: () => this.benchmark.set(null),
    });
  }
}
