import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AssetAnalysis,
  DashboardResponse,
  DipAnalysisResponse,
  DipScannerResponse,
  Goal,
  InvestmentStrategy,
  OpportunitiesResponse,
  PassiveIncomeProjectionRequest,
  PassiveIncomeProjectionResponse,
  PortfolioEvaluationRequest,
  PortfolioEvaluationResponse,
  PortfolioItem,
  PortfolioStateResponse,
  Preferences,
  PriceAlert,
  PriceAlertTriggered,
  QuickInvestRequest,
  QuickInvestResponse,
  RecommendRequest,
  RecommendResponse,
  RendaFixaAnalysisResult,
  RendaFixaAsset,
  RendaFixaCompareRequest,
  RendaFixaCompareResponse,
  ReferenceRates,
  SectorAllocationResponse,
  SectorGoal,
} from '../models';

@Injectable({ providedIn: 'root' })
export class RecommendService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;

  recommend(req: RecommendRequest): Observable<RecommendResponse> {
    return this.http.post<RecommendResponse>(`${this.base}/recommend`, req);
  }

  analyzeAsset(symbol: string): Observable<AssetAnalysis> {
    return this.http.get<AssetAnalysis>(`${this.base}/asset/${encodeURIComponent(symbol)}`);
  }

  dipAnalysis(symbol: string): Observable<DipAnalysisResponse> {
    return this.http.get<DipAnalysisResponse>(
      `${this.base}/asset/${encodeURIComponent(symbol)}/dip-analysis`
    );
  }

  dipScanner(
    minScore = 40,
    top = 12,
    universe?: string,
    category?: string
  ): Observable<DipScannerResponse> {
    let params = new HttpParams().set('min_score', minScore).set('top', top);
    if (universe) params = params.set('universe', universe);
    if (category) params = params.set('category', category);
    return this.http.get<DipScannerResponse>(`${this.base}/dip-scanner`, { params });
  }

  evaluatePortfolio(req: PortfolioEvaluationRequest): Observable<PortfolioEvaluationResponse> {
    return this.http.post<PortfolioEvaluationResponse>(`${this.base}/portfolio/evaluate`, req);
  }

  getPortfolio(): Observable<PortfolioStateResponse> {
    return this.http.get<PortfolioStateResponse>(`${this.base}/portfolio`);
  }

  savePortfolio(items: PortfolioItem[]): Observable<PortfolioStateResponse> {
    return this.http.put<PortfolioStateResponse>(`${this.base}/portfolio`, { items });
  }

  deletePosition(ticker: string): Observable<{ deleted: string }> {
    return this.http.delete<{ deleted: string }>(
      `${this.base}/portfolio/${encodeURIComponent(ticker)}`
    );
  }

  refreshPortfolio(): Observable<PortfolioEvaluationResponse> {
    return this.http.post<PortfolioEvaluationResponse>(`${this.base}/portfolio/refresh`, null);
  }

  dashboard(): Observable<DashboardResponse> {
    return this.http.get<DashboardResponse>(`${this.base}/dashboard`);
  }

  opportunities(
    includeHeld = false,
    page = 1,
    pageSize = 50,
    sortBy = 'score',
    sortOrder = 'desc',
    search = '',
    minDy: number | null = null,
    minMos: number | null = null,
    sector = '',
    assetType = '',
    category = '',
    onlyInteresting = false
  ): Observable<OpportunitiesResponse> {
    let params = new HttpParams()
      .set('include_held', includeHeld)
      .set('page', page)
      .set('page_size', pageSize)
      .set('sort_by', sortBy)
      .set('sort_order', sortOrder)
      .set('search', search)
      .set('sector', sector)
      .set('asset_type', assetType)
      .set('category', category)
      .set('only_interesting', onlyInteresting);

    if (minDy !== null && minDy > 0) {
      params = params.set('min_dy', minDy);
    }
    if (minMos !== null && minMos !== 0) {
      params = params.set('min_mos', minMos);
    }

    return this.http.get<OpportunitiesResponse>(`${this.base}/opportunities`, { params });
  }

  getGoals(): Observable<Goal[]> {
    return this.http.get<Goal[]>(`${this.base}/goals`);
  }

  saveGoals(goals: Goal[]): Observable<Goal[]> {
    return this.http.put<Goal[]>(`${this.base}/goals`, { goals });
  }

  getPreferences(): Observable<Preferences> {
    return this.http.get<Preferences>(`${this.base}/preferences`);
  }

  savePreferences(cash: number, passiveIncomeGoal?: number): Observable<Preferences> {
    return this.http.put<Preferences>(`${this.base}/preferences`, {
      cash_available: cash,
      passive_income_goal: passiveIncomeGoal ?? null,
    });
  }

  getStrategy(): Observable<InvestmentStrategy> {
    return this.http.get<InvestmentStrategy>(`${this.base}/strategy`);
  }

  clearCache(pattern = '*'): Observable<{ message: string; deleted: number }> {
    const params = new HttpParams().set('pattern', pattern);
    return this.http.post<{ message: string; deleted: number }>(`${this.base}/cache/clear`, null, {
      params,
    });
  }

  getReferencRates(): Observable<ReferenceRates> {
    return this.http.get<ReferenceRates>(`${this.base}/renda-fixa/taxas`);
  }

  analyzeRendaFixa(ativo: RendaFixaAsset): Observable<RendaFixaAnalysisResult> {
    return this.http.post<RendaFixaAnalysisResult>(`${this.base}/renda-fixa/analisar`, ativo);
  }

  compareRendaFixa(req: RendaFixaCompareRequest): Observable<RendaFixaCompareResponse> {
    return this.http.post<RendaFixaCompareResponse>(`${this.base}/renda-fixa/comparar`, req);
  }

  projectPassiveIncome(
    req: PassiveIncomeProjectionRequest
  ): Observable<PassiveIncomeProjectionResponse> {
    return this.http.post<PassiveIncomeProjectionResponse>(
      `${this.base}/projection/passive-income`,
      req
    );
  }

  analyzeSectorAllocation(
    targetAllocations: Record<string, number>
  ): Observable<SectorAllocationResponse> {
    return this.http.post<SectorAllocationResponse>(
      `${this.base}/projection/sector-allocation`,
      targetAllocations
    );
  }

  getSectorGoals(): Observable<SectorGoal[]> {
    return this.http.get<SectorGoal[]>(`${this.base}/sector-goals`);
  }

  saveSectorGoals(sectorGoals: SectorGoal[]): Observable<SectorGoal[]> {
    return this.http.put<SectorGoal[]>(`${this.base}/sector-goals`, { sector_goals: sectorGoals });
  }

  quickInvest(req: QuickInvestRequest): Observable<QuickInvestResponse> {
    return this.http.post<QuickInvestResponse>(`${this.base}/quick-invest`, req);
  }

  getAlerts(): Observable<PriceAlert[]> {
    return this.http.get<PriceAlert[]>(`${this.base}/alerts`);
  }

  checkAlerts(): Observable<PriceAlertTriggered[]> {
    return this.http.get<PriceAlertTriggered[]>(`${this.base}/alerts/check`);
  }

  createAlert(alert: {
    ticker: string;
    condition: string;
    target_price: number;
    note?: string;
  }): Observable<PriceAlert> {
    return this.http.post<PriceAlert>(`${this.base}/alerts`, alert);
  }

  deleteAlert(id: number): Observable<{ deleted: number }> {
    return this.http.delete<{ deleted: number }>(`${this.base}/alerts/${id}`);
  }
}
