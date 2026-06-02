import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import {
  DipAnalysisResponse,
  DipScanItem,
  OpportunitiesResponse,
  Opportunity,
  RecommendService,
  UiHelperService,
} from '../../core';

type MarketTab = 'opportunities' | 'dip-scanner';

@Component({
  selector: 'app-market',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, LucideAngularModule],
  templateUrl: './market.component.html',
  styleUrls: ['./market.component.scss'],
})
export class MarketComponent {
  private api = inject(RecommendService);
  readonly helper = inject(UiHelperService);
  private fb = inject(FormBuilder);

  readonly activeTab = signal<MarketTab>('opportunities');
  readonly opportunities = signal<OpportunitiesResponse | null>(null);
  readonly dipResults = signal<{ items: DipScanItem[] } | null>(null);
  readonly dipAnalysis = signal<DipAnalysisResponse | null>(null);
  readonly showAnalysis = signal(false);

  filterText = '';
  filterMinDy: number | null = null;
  filterMinMos: number | null = null;
  filterCategory = '';
  onlyInteresting = false;

  scanForm = this.fb.nonNullable.group({
    min_score: [40, [Validators.required, Validators.min(0), Validators.max(100)]],
    top: [12, [Validators.required, Validators.min(1), Validators.max(30)]],
    category: [''],
  });

  ngOnInit() {
    this.loadOpportunities();
  }

  onFilterChange() {
    this.loadOpportunities();
  }

  loadOpportunities() {
    this.api
      .opportunities(
        false,
        1,
        100,
        'score',
        'desc',
        this.filterText,
        this.filterMinDy,
        this.filterMinMos,
        '',
        '',
        this.filterCategory,
        this.onlyInteresting
      )
      .subscribe(data => this.opportunities.set(data));
  }

  runScan() {
    if (this.scanForm.invalid) return;

    const { min_score, top, category } = this.scanForm.getRawValue();

    this.api
      .dipScanner(min_score, top, 0.06, undefined, category || undefined)
      .subscribe(data => this.dipResults.set(data));
  }

  showOpportunityDetails(ticker: string) {
    this.showDipAnalysis(ticker);
  }

  showDipAnalysis(ticker: string) {
    this.api.dipAnalysis(ticker).subscribe(data => {
      this.dipAnalysis.set(data);
      this.showAnalysis.set(true);
    });
  }

  closeAnalysis() {
    this.showAnalysis.set(false);
    this.dipAnalysis.set(null);
  }
}
