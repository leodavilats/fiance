import { inject, Injectable, signal } from '@angular/core';
import { DipAnalysisResponse } from '../models';
import { RecommendService } from './recommend.service';

@Injectable({ providedIn: 'root' })
export class DipAnalysisService {
  private readonly api = inject(RecommendService);

  readonly analysis = signal<DipAnalysisResponse | null>(null);
  readonly open = signal(false);
  readonly loadingTicker = signal<string | null>(null);

  show(ticker: string): void {
    this.loadingTicker.set(ticker);
    this.api.dipAnalysis(ticker).subscribe({
      next: data => {
        this.analysis.set(data);
        this.open.set(true);
        this.loadingTicker.set(null);
      },
      error: () => this.loadingTicker.set(null),
    });
  }

  close(): void {
    this.open.set(false);
    this.analysis.set(null);
  }
}
