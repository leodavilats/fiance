import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { DipAnalysisResponse, RecommendService } from '../../core';
import { AnalyzeAssetComponent } from './analyze-asset/analyze-asset.component';
import { DipAnalysisModalComponent } from './dip-analysis-modal/dip-analysis-modal.component';
import { DipScannerComponent } from './dip-scanner/dip-scanner.component';
import { InvestmentStrategyComponent } from './investment-strategy/investment-strategy.component';
import { OpportunitiesListComponent } from './opportunities-list/opportunities-list.component';
import { QuickInvestComponent } from './quick-invest/quick-invest.component';
import { RendaFixaComponent } from './renda-fixa/renda-fixa.component';
import { LucideAngularModule } from 'lucide-angular';
import { SectorsComponent } from '../sectors/sectors.component';

type MarketTab = 'opportunities' | 'investir' | 'ferramentas';
type OppMode = 'todas' | 'setores' | 'queda';
type ToolMode = 'analisar' | 'renda_fixa';

@Component({
  selector: 'app-market',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    SectorsComponent,
    OpportunitiesListComponent,
    DipScannerComponent,
    AnalyzeAssetComponent,
    QuickInvestComponent,
    InvestmentStrategyComponent,
    RendaFixaComponent,
    DipAnalysisModalComponent,
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

  goToRendaFixa() {
    this.activeTab.set('ferramentas');
    this.toolMode.set('renda_fixa');
  }
}
