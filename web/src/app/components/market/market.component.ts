import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DipAnalysisResponse, RecommendService } from '../../core';
import { AnalyzeAssetComponent } from './analyze-asset/analyze-asset.component';
import { CompareAssetsComponent } from './compare-assets/compare-assets.component';
import { ContributionSimulatorComponent } from './contribution-simulator/contribution-simulator.component';
import { DipAnalysisModalComponent } from './dip-analysis-modal/dip-analysis-modal.component';
import { DipScannerComponent } from './dip-scanner/dip-scanner.component';
import { FollowedSuggestionsComponent } from './followed-suggestions/followed-suggestions.component';
import { IncomeCompareComponent } from './income-compare/income-compare.component';
import { OpportunitiesListComponent } from './opportunities-list/opportunities-list.component';
import { RebalanceSuggestionsComponent } from './rebalance-suggestions/rebalance-suggestions.component';
import { RendaFixaComponent } from './renda-fixa/renda-fixa.component';
import { LucideAngularModule } from 'lucide-angular';

type MarketTab = 'opportunities' | 'rebalance' | 'ferramentas';
type OppMode = 'todas' | 'queda';
type ToolMode = 'analisar' | 'renda_fixa' | 'rf_vs_bolsa' | 'comparar' | 'projecao';

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
    IncomeCompareComponent,
    FollowedSuggestionsComponent,
  ],
  templateUrl: './market.component.html',
  styleUrls: ['./market.component.scss'],
})
export class MarketComponent implements OnInit {
  private api = inject(RecommendService);
  private route = inject(ActivatedRoute);

  readonly activeTab = signal<MarketTab>('opportunities');
  readonly oppMode = signal<OppMode>('todas');
  readonly toolMode = signal<ToolMode>('analisar');

  ngOnInit(): void {
    // Alertas e "o que mudou" navegam para cá pedindo uma aba específica; sem
    // isso a ação levava sempre para a aba default.
    const params = this.route.snapshot.queryParamMap;

    const tab = params.get('tab') as MarketTab | null;
    if (tab && ['opportunities', 'rebalance', 'ferramentas'].includes(tab)) {
      this.activeTab.set(tab);
    }

    const tool = params.get('tool') as ToolMode | null;
    if (tool) {
      this.activeTab.set('ferramentas');
      this.toolMode.set(tool);
    }
  }

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
