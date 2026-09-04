import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import {
  DipAnalysisService,
  DipScanItem,
  DipVerdict,
  FiState,
  RecommendService,
  fiDipDiagnosis,
  fiDipScoreBands,
  stateTextClass,
} from '../../../core';
import { EmptyStateComponent } from '../../empty-state/empty-state.component';
import { ScoreRulerComponent } from '../../score-ruler/score-ruler.component';
import { SkeletonComponent } from '../../skeleton/skeleton.component';

const DIAGNOSIS: Record<DipVerdict, keyof typeof fiDipDiagnosis> = {
  OPORTUNIDADE: 'healthy',
  NEUTRO: 'investigate',
  ARMADILHA: 'structural',
};

const RELAXED_MIN_SCORE = 25;

@Component({
  selector: 'app-dip-scanner',
  standalone: true,
  imports: [
    CommonModule,
    EmptyStateComponent,
    LucideAngularModule,
    ReactiveFormsModule,
    RouterLink,
    ScoreRulerComponent,
    SkeletonComponent,
  ],
  templateUrl: './dip-scanner.component.html',
})
export class DipScannerComponent implements OnInit {
  private readonly api = inject(RecommendService);
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly dip = inject(DipAnalysisService);

  readonly dipBands = fiDipScoreBands;

  readonly dipResults = signal<{ items: DipScanItem[] } | null>(null);
  readonly scanning = signal(false);

  readonly scanForm = this.fb.nonNullable.group({
    min_score: [40, [Validators.required, Validators.min(0), Validators.max(100)]],
    top: [12, [Validators.required, Validators.min(1), Validators.max(30)]],
    category: [''],
  });

  readonly minScore = computed(() => this.scanForm.getRawValue().min_score);

  ngOnInit(): void {
    const q = this.route.snapshot.queryParamMap;
    this.scanForm.patchValue({
      min_score: Number(q.get('min_score') ?? 40),
      top: Number(q.get('top') ?? 12),
      category: q.get('category') ?? '',
    });
    if (q.keys.length > 0) this.runScan();
  }

  runScan(): void {
    if (this.scanForm.invalid) return;
    const { min_score, top, category } = this.scanForm.getRawValue();

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { min_score, top, category: category || null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });

    this.scanning.set(true);
    this.api.dipScanner(min_score, top, undefined, category || undefined).subscribe({
      next: data => {
        this.dipResults.set(data);
        this.scanning.set(false);
      },
      error: () => this.scanning.set(false),
    });
  }

  relaxFilter(): void {
    this.scanForm.patchValue({ min_score: RELAXED_MIN_SCORE });
    this.runScan();
  }

  showDipAnalysis(ticker: string): void {
    this.dip.show(ticker);
  }

  dipLabel(verdict: DipVerdict): string {
    return fiDipDiagnosis[DIAGNOSIS[verdict]].label;
  }

  dipClass(verdict: DipVerdict): string {
    const map: Record<FiState, string> = {
      favorable: 'v-buy',
      attention: 'v-hold',
      adverse: 'v-sell',
      neutral: 'v-unknown',
      indeterminate: 'v-unknown',
    };
    return map[fiDipDiagnosis[DIAGNOSIS[verdict]].state];
  }

  dipIcon(verdict: DipVerdict): string {
    const state = fiDipDiagnosis[DIAGNOSIS[verdict]].state;
    if (state === 'favorable') return 'circle-check';
    if (state === 'attention') return 'triangle-alert';
    return 'circle-alert';
  }

  stateClass(verdict: DipVerdict): string {
    return stateTextClass(fiDipDiagnosis[DIAGNOSIS[verdict]].state);
  }
}
