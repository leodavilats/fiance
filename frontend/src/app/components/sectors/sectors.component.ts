import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { RecommendService, SectorsSummaryResponse, UiHelperService } from '../../core';
import { SkeletonComponent } from '../index';

@Component({
  selector: 'app-sectors',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, SkeletonComponent],
  templateUrl: './sectors.component.html',
})
export class SectorsComponent implements OnInit {
  private svc = inject(RecommendService);
  private router = inject(Router);
  readonly ui = inject(UiHelperService);

  data = signal<SectorsSummaryResponse | null>(null);
  hasError = signal(false);
  isLoading = signal(false);
  activeCategory = signal<string>('acoes_br');

  readonly categories = [
    { value: 'acoes_br', label: 'Ações BR' },
    { value: 'fiis', label: 'FIIs' },
    { value: 'acoes_int', label: 'Ações INT' },
    { value: 'cripto', label: 'Cripto' },
  ];

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.hasError.set(false);
    this.isLoading.set(true);
    this.svc.sectorsSummary(this.activeCategory()).subscribe({
      next: res => {
        this.data.set(res);
        this.isLoading.set(false);
      },
      error: () => {
        this.hasError.set(true);
        this.isLoading.set(false);
      },
    });
  }

  selectCategory(cat: string): void {
    this.activeCategory.set(cat);
    this.data.set(null);
    this.load();
  }

  goToOpportunities(sector: string): void {
    this.router.navigate(['/market'], { queryParams: { sector } });
  }

  scoreClass(score: number): string {
    if (score >= 70) return 'text-green-400';
    if (score >= 50) return 'text-yellow-400';
    return 'text-red-400';
  }

  dyClass(dy: number): string {
    if (dy >= 8) return 'text-green-400';
    if (dy >= 5) return 'text-accent';
    return 'text-muted';
  }
}
