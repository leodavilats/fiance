import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  ActionKind,
  BenchmarkResponse,
  DashboardResponse,
  LoadingService,
  RecommendService,
  UiHelperService,
  WhatsNewResponse,
} from '../../core';
import { BenchmarkChartComponent, PatrimonyChartComponent } from '../index';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, PatrimonyChartComponent, BenchmarkChartComponent],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private svc = inject(RecommendService);
  private router = inject(Router);
  readonly ui = inject(UiHelperService);
  readonly loading = inject(LoadingService);
  readonly Math = Math;

  data = signal<DashboardResponse | null>(null);
  benchmark = signal<BenchmarkResponse | null>(null);
  whatsNew = signal<WhatsNewResponse | null>(null);
  isInitialLoad = signal(true);
  hasError = signal(false);
  showHealthInfo = signal(false);

  toggleHealthInfo(): void {
    this.showHealthInfo.update(v => !v);
  }

  healthBand(score: number): 'good' | 'warn' | 'error' {
    if (score >= 70) return 'good';
    if (score >= 40) return 'warn';
    return 'error';
  }

  healthBandLabel(score: number): string {
    const band = this.healthBand(score);
    return band === 'good' ? 'Bom' : band === 'warn' ? 'Atenção' : 'Ruim';
  }

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(): void {
    this.hasError.set(false);
    this.svc.dashboard().subscribe({
      next: res => {
        this.data.set(res);
        this.isInitialLoad.set(false);
      },
      error: () => {
        this.hasError.set(true);
        this.isInitialLoad.set(false);
      },
      complete: () => {},
    });

    this.svc.getBenchmark().subscribe({
      next: res => this.benchmark.set(res),
      error: () => this.benchmark.set(null),
    });

    this.svc.whatsNew().subscribe({
      next: res => this.whatsNew.set(res),
      error: () => this.whatsNew.set(null),
    });
  }

  /**
   * Leva cada alerta/novidade ao seu desfecho.
   *
   * A única ação oferecida na tela era `goToMarket()`: alta carga cognitiva,
   * nenhum desfecho.
   */
  runAction(action: ActionKind | null, ticker?: string | null): void {
    switch (action) {
      case 'analyze':
        this.router.navigate(['/assets']);
        break;
      case 'sell':
        this.router.navigate(['/assets']);
        break;
      case 'rebalance':
        this.router.navigate(['/market'], { queryParams: { tab: 'rebalance' } });
        break;
      case 'goals':
        this.router.navigate(['/config']);
        break;
      case 'fixed_income':
        this.router.navigate(['/assets/cadastro']);
        break;
      case 'market':
      default:
        this.router.navigate(['/market'], ticker ? { queryParams: { ticker } } : {});
    }
  }

  whatsNewIcon(kind: string): string {
    const map: Record<string, string> = {
      patrimony: 'trending-up',
      verdict_change: 'trending-down',
      allocation: 'scale',
      maturity: 'calendar-clock',
      new_opportunity: 'sparkles',
      tax: 'receipt',
      empty: 'check',
    };
    return map[kind] || 'info';
  }

  whatsNewToneClass(severity: string): string {
    const map: Record<string, string> = {
      positive: 'border-green-500/40 bg-green-500/5',
      warning: 'border-yellow-500/40 bg-yellow-500/5',
      critical: 'border-red-500/40 bg-red-500/5',
      info: 'border-border bg-panel-2',
    };
    return map[severity] || 'border-border bg-panel-2';
  }

  /** Idade do dado de mercado em linguagem de gente. */
  freshnessLabel(): string {
    const freshness = this.data()?.freshness;
    if (!freshness) return '';

    const age = freshness.market_data_age_seconds;
    if (age == null) return 'cotações sem carimbo de tempo';

    if (age < 120) return 'cotações de agora';
    if (age < 3600) return `cotações de ${Math.round(age / 60)} min atrás`;

    const hours = Math.round(age / 3600);
    return `cotações de ${hours} h atrás`;
  }

  ratesSourceLabel(): string {
    const source = this.data()?.freshness?.rates_source;
    if (!source) return '';
    return source === 'bcb' ? 'CDI/Selic do Banco Central' : 'CDI/Selic estimados';
  }

  goToMarket(): void {
    this.router.navigate(['/market']);
  }

  formatDate(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
    });
  }
}
