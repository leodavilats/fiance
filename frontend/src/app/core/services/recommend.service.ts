import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  AssetAnalysis,
  DashboardResponse,
  DipAnalysisResponse,
  DipScannerResponse,
  DividendRankingResponse,
  Goal,
  InvestmentStrategy,
  OpportunitiesResponse,
  PortfolioEvaluationRequest,
  PortfolioEvaluationResponse,
  PortfolioItem,
  PortfolioStateResponse,
  Preferences,
  RecommendRequest,
  RecommendResponse,
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
    return this.http.get<AssetAnalysis>(
      `${this.base}/asset/${encodeURIComponent(symbol)}`,
      { params },
    );
  }

  dipAnalysis(symbol: string, desiredYield = 0.06): Observable<DipAnalysisResponse> {
    const params = new HttpParams().set('desired_yield', desiredYield);
    return this.http.get<DipAnalysisResponse>(
      `${this.base}/asset/${encodeURIComponent(symbol)}/dip-analysis`,
      { params },
    );
  }

  dipScanner(
    minScore = 40,
    top = 12,
    desiredYield = 0.06,
    universe?: string,
  ): Observable<DipScannerResponse> {
    let params = new HttpParams()
      .set('min_score', minScore)
      .set('top', top)
      .set('desired_yield', desiredYield);
    if (universe) params = params.set('universe', universe);
    return this.http.get<DipScannerResponse>(`${this.base}/dip-scanner`, { params });
  }

  evaluatePortfolio(
    req: PortfolioEvaluationRequest,
  ): Observable<PortfolioEvaluationResponse> {
    return this.http.post<PortfolioEvaluationResponse>(
      `${this.base}/portfolio/evaluate`,
      req,
    );
  }

  dividendsRanking(universe?: string, top = 15): Observable<DividendRankingResponse> {
    let params = new HttpParams().set('top', top);
    if (universe) params = params.set('universe', universe);
    return this.http.get<DividendRankingResponse>(`${this.base}/dividends/ranking`, {
      params,
    });
  }

  getPortfolio(): Observable<PortfolioStateResponse> {
    return this.http.get<PortfolioStateResponse>(`${this.base}/portfolio`);
  }

  savePortfolio(items: PortfolioItem[]): Observable<PortfolioStateResponse> {
    return this.http.put<PortfolioStateResponse>(`${this.base}/portfolio`, { items });
  }

  deletePosition(ticker: string): Observable<{ deleted: string }> {
    return this.http.delete<{ deleted: string }>(
      `${this.base}/portfolio/${encodeURIComponent(ticker)}`,
    );
  }

  refreshPortfolio(desiredYield = 0.06): Observable<PortfolioEvaluationResponse> {
    const params = new HttpParams().set('desired_yield', desiredYield);
    return this.http.post<PortfolioEvaluationResponse>(
      `${this.base}/portfolio/refresh`,
      null,
      { params },
    );
  }

  dashboard(): Observable<DashboardResponse> {
    return this.http.get<DashboardResponse>(`${this.base}/dashboard`);
  }

  opportunities(
    includeHeld = false,
    onlyBuy = true,
    page = 1,
    pageSize = 50,
    sortBy = 'score',
    sortOrder = 'desc'
  ): Observable<OpportunitiesResponse> {
    const params = new HttpParams()
      .set('include_held', includeHeld)
      .set('only_buy', onlyBuy)
      .set('page', page)
      .set('page_size', pageSize)
      .set('sort_by', sortBy)
      .set('sort_order', sortOrder);
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
      `${this.base}/watchlist/${encodeURIComponent(ticker)}`,
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
}
