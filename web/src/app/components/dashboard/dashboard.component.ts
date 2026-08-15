import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  BenchmarkResponse,
  DashboardResponse,
  LoadingService,
  RecommendService,
  UiHelperService,
} from '../../core';
import { BenchmarkChartComponent, PatrimonyChartComponent } from '../index';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    PatrimonyChartComponent,
    BenchmarkChartComponent,
  ],
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
  isInitialLoad = signal(true);
  hasError = signal(false);

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
