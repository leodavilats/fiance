import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { DashboardResponse, LoadingService, RecommendService, UiHelperService } from '../../core';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private svc = inject(RecommendService);
  private router = inject(Router);
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

  goToStrategy(): void {
    this.router.navigate(['/strategy']);
  }

  formatDate(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
    });
  }
}
