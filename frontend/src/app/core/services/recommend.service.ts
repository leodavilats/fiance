import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
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
  WatchlistItem,
} from '../models';

@Injectable({ providedIn: 'root' })
export class RecommendService {
  private http = inject(HttpClient);
  private base = 'http://127.0.0.1:8000/api';

  recommend(req: RecommendRequest): Observable<RecommendResponse> {
    return this.http.post<RecommendResponse>(`${this.base}/recommend`, req);
  }

  analyzeAsset(symbol: string, desiredYield = 0.06): Observable<AssetAnalysis> {
    const params = new HttpParams().set('desired_yield', desiredYield);
    return this.http.get<AssetAnalysis>(`${this.base}/asset/${encodeURIComponent(symbol)}`, {
      params,
    });
  }

  dipAnalysis(symbol: string, desiredYield = 0.06): Observable<DipAnalysisResponse> {
    const params = new HttpParams().set('desired_yield', desiredYield);
    return this.http.get<DipAnalysisResponse>(
      `${this.base}/asset/${encodeURIComponent(symbol)}/dip-analysis`,
      { params }
    );
  }

  dipScanner(
    minScore = 40,
    top = 12,
    desiredYield = 0.06,
    universe?: string,
    category?: string
  ): Observable<DipScannerResponse> {
    let params = new HttpParams()
      .set('min_score', minScore)
      .set('top', top)
      .set('desired_yield', desiredYield);
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

  refreshPortfolio(desiredYield = 0.06): Observable<PortfolioEvaluationResponse> {
    const params = new HttpParams().set('desired_yield', desiredYield);
    return this.http.post<PortfolioEvaluationResponse>(`${this.base}/portfolio/refresh`, null, {
      params,
    });
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

    // Apenas adiciona min_dy e min_mos se tiverem valores válidos
    if (minDy !== null && minDy > 0) {
      params = params.set('min_dy', minDy);
    }
    if (minMos !== null && minMos !== 0) {
      params = params.set('min_mos', minMos);
    }

    return this.http.get<OpportunitiesResponse>(`${this.base}/opportunities`, { params });
  }

  getWatchlist(): Observable<WatchlistItem[]> {
    return this.http.get<WatchlistItem[]>(`${this.base}/watchlist`);
  }

  saveWatchlist(items: WatchlistItem[]): Observable<WatchlistItem[]> {
    return this.http.put<WatchlistItem[]>(`${this.base}/watchlist`, { items });
  }

  deleteWatchlist(ticker: string): Observable<{ deleted: string }> {
    return this.http.delete<{ deleted: string }>(
      `${this.base}/watchlist/${encodeURIComponent(ticker)}`
    );
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

  savePreferences(cash: number, desiredYield = 0.06): Observable<Preferences> {
    return this.http.put<Preferences>(`${this.base}/preferences`, {
      cash_available: cash,
      desired_yield: desiredYield,
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

  // Renda Fixa
  getReferencRates(): Observable<ReferenceRates> {
    return this.http.get<ReferenceRates>(`${this.base}/renda-fixa/taxas`);
  }

  analyzeRendaFixa(ativo: RendaFixaAsset): Observable<RendaFixaAnalysisResult> {
    return this.http.post<RendaFixaAnalysisResult>(`${this.base}/renda-fixa/analisar`, ativo);
  }

  compareRendaFixa(req: RendaFixaCompareRequest): Observable<RendaFixaCompareResponse> {
    return this.http.post<RendaFixaCompareResponse>(`${this.base}/renda-fixa/comparar`, req);
  }

  // Projeção de Renda Passiva
  projectPassiveIncome(
    req: PassiveIncomeProjectionRequest
  ): Observable<PassiveIncomeProjectionResponse> {
    return this.http.post<PassiveIncomeProjectionResponse>(
      `${this.base}/projection/passive-income`,
      req
    );
  }

  // Alocação Setorial
  analyzeSectorAllocation(
    targetAllocations: Record<string, number>
  ): Observable<SectorAllocationResponse> {
    return this.http.post<SectorAllocationResponse>(
      `${this.base}/projection/sector-allocation`,
      targetAllocations
    );
  }

  // Sector Goals
  getSectorGoals(): Observable<SectorGoal[]> {
    return this.http.get<SectorGoal[]>(`${this.base}/sector-goals`);
  }

  saveSectorGoals(sectorGoals: SectorGoal[]): Observable<SectorGoal[]> {
    return this.http.put<SectorGoal[]>(`${this.base}/sector-goals`, { sector_goals: sectorGoals });
  }

  // Quick Invest
  quickInvest(req: QuickInvestRequest): Observable<QuickInvestResponse> {
    return this.http.post<QuickInvestResponse>(`${this.base}/quick-invest`, req);
  }
}
