import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { DipAnalysisResponse, RecommendService } from '../../core';
import { AnalyzeAssetComponent } from './analyze-asset/analyze-asset.component';
import { CompareAssetsComponent } from './compare-assets/compare-assets.component';
import { ContributionSimulatorComponent } from './contribution-simulator/contribution-simulator.component';
import { DipAnalysisModalComponent } from './dip-analysis-modal/dip-analysis-modal.component';
import { DipScannerComponent } from './dip-scanner/dip-scanner.component';
import { OpportunitiesListComponent } from './opportunities-list/opportunities-list.component';
import { RebalanceSuggestionsComponent } from './rebalance-suggestions/rebalance-suggestions.component';
import { RendaFixaComponent } from './renda-fixa/renda-fixa.component';
import { LucideAngularModule } from 'lucide-angular';

type MarketTab = 'opportunities' | 'rebalance' | 'ferramentas';
type OppMode = 'todas' | 'queda';
type ToolMode = 'analisar' | 'renda_fixa' | 'comparar' | 'projecao';

@Component({
  selector: 'app-market',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    OpportunitiesListComponent,
    DipScannerComponent,
    AnalyzeAssetComponent,
    RendaFixaComponent,
    DipAnalysisModalComponent,
    CompareAssetsComponent,
    ContributionSimulatorComponent,
    RebalanceSuggestionsComponent,
  ],
  templateUrl: './market.component.html',
  styleUrls: ['./market.component.scss'],
})
export class MarketComponent {
  private api = inject(RecommendService);

  readonly activeTab = signal<MarketTab>('opportunities');
  readonly oppMode = signal<OppMode>('todas');
  readonly toolMode = signal<ToolMode>('analisar');

  readonly dipAnalysis = signal<DipAnalysisResponse | null>(null);
  readonly showAnalysis = signal(false);

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
