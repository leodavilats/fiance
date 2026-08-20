import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AllocationCategory,
  AssetAnalysis,
  BenchmarkResponse,
  ClosedTradesResponse,
  CompareResponse,
  DashboardResponse,
  DipAnalysisResponse,
  DipScannerResponse,
  DividendPayload,
  DividendReceived,
  DividendsReceivedResponse,
  FixedIncomeListResponse,
  FixedIncomePayload,
  FixedIncomePosition,
  FollowedSuggestionPayload,
  FollowedSuggestion,
  FollowedSuggestionsResponse,
  Goal,
  IncomeCompareResponse,
  InvestmentStrategy,
  OpportunitiesFrequency,
  OpportunitiesResponse,
  PassiveIncomeProjectionRequest,
  PassiveIncomeProjectionResponse,
  PortfolioEvaluationRequest,
  PortfolioEvaluationResponse,
  PortfolioItem,
  PortfolioStateResponse,
  Preferences,
  PriceAlert,
  RiskProfile,
  PriceAlertTriggered,
  QuickInvestRequest,
  QuickInvestResponse,
  RebalanceSuggestionsResponse,
  RendaFixaCompareRequest,
  RendaFixaCompareResponse,
  ReferenceRates,
  SectorGoal,
  SectorsSummaryResponse,
  SellRequest,
  ClosedTrade,
  TickerSuggestion,
  WhatsNewResponse,
} from '../models';

@Injectable({ providedIn: 'root' })
export class RecommendService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;

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

  /**
   * Importação explícita: substitui a carteira inteira. Escrita destrutiva —
   * use `upsertPosition`/`deletePosition` para o cadastro do dia a dia.
   */
  savePortfolio(items: PortfolioItem[]): Observable<PortfolioStateResponse> {
    return this.http.put<PortfolioStateResponse>(`${this.base}/portfolio`, { items });
  }

  /** Cria ou atualiza uma posição sem tocar nas outras. */
  upsertPosition(item: PortfolioItem): Observable<PortfolioStateResponse> {
    return this.http.post<PortfolioStateResponse>(`${this.base}/portfolio/position`, item);
  }

  deletePosition(ticker: string): Observable<PortfolioStateResponse> {
    return this.http.delete<PortfolioStateResponse>(
      `${this.base}/portfolio/position/${encodeURIComponent(ticker)}`
    );
  }

  // --- renda fixa (entidade persistida no servidor) ---

  getFixedIncome(): Observable<FixedIncomeListResponse> {
    return this.http.get<FixedIncomeListResponse>(`${this.base}/fixed-income`);
  }

  createFixedIncome(payload: FixedIncomePayload): Observable<FixedIncomePosition> {
    return this.http.post<FixedIncomePosition>(`${this.base}/fixed-income`, payload);
  }

  updateFixedIncome(
    id: number,
    payload: Partial<FixedIncomePayload>
  ): Observable<FixedIncomePosition> {
    return this.http.put<FixedIncomePosition>(`${this.base}/fixed-income/${id}`, payload);
  }

  deleteFixedIncome(id: number): Observable<{ deleted: number }> {
    return this.http.delete<{ deleted: number }>(`${this.base}/fixed-income/${id}`);
  }

  // --- proventos recebidos (fato, não estimativa) ---

  getDividendsReceived(estimatedMonthly?: number): Observable<DividendsReceivedResponse> {
    let params = new HttpParams();
    if (estimatedMonthly != null) {
      params = params.set('estimated_monthly', estimatedMonthly);
    }
    return this.http.get<DividendsReceivedResponse>(`${this.base}/dividends/received`, {
      params,
    });
  }

  createDividendReceived(payload: DividendPayload): Observable<DividendReceived> {
    return this.http.post<DividendReceived>(`${this.base}/dividends/received`, payload);
  }

  updateDividendReceived(
    id: number,
    payload: Partial<DividendPayload>
  ): Observable<DividendReceived> {
    return this.http.put<DividendReceived>(`${this.base}/dividends/received/${id}`, payload);
  }

  deleteDividendReceived(id: number): Observable<{ deleted: number }> {
    return this.http.delete<{ deleted: number }>(`${this.base}/dividends/received/${id}`);
  }

  // --- renda fixa x ativos na mesma conta ---

  incomeCompare(amount = 10_000, horizonMonths = 12): Observable<IncomeCompareResponse> {
    const params = new HttpParams().set('amount', amount).set('horizon_months', horizonMonths);
    return this.http.get<IncomeCompareResponse>(`${this.base}/income-compare`, { params });
  }

  // --- ciclo decisão -> execução -> resultado ---

  getFollowedSuggestions(): Observable<FollowedSuggestionsResponse> {
    return this.http.get<FollowedSuggestionsResponse>(`${this.base}/suggestions/followed`);
  }

  registerFollowedSuggestion(payload: FollowedSuggestionPayload): Observable<FollowedSuggestion> {
    return this.http.post<FollowedSuggestion>(`${this.base}/suggestions/followed`, payload);
  }

  deleteFollowedSuggestion(id: number): Observable<{ deleted: number }> {
    return this.http.delete<{ deleted: number }>(`${this.base}/suggestions/followed/${id}`);
  }

  sellPosition(req: SellRequest): Observable<ClosedTrade> {
    return this.http.post<ClosedTrade>(`${this.base}/portfolio/sell`, req);
  }

  getClosedTrades(): Observable<ClosedTradesResponse> {
    return this.http.get<ClosedTradesResponse>(`${this.base}/portfolio/trades`);
  }

  dashboard(): Observable<DashboardResponse> {
    return this.http.get<DashboardResponse>(`${this.base}/dashboard`);
  }

  /** O que mudou desde a última visita, com uma ação por linha. */
  whatsNew(): Observable<WhatsNewResponse> {
    return this.http.get<WhatsNewResponse>(`${this.base}/whats-new`);
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

  /**
   * PUT parcial: só o que vier definido é enviado, e só o que for enviado é
   * gravado. Mandar o objeto inteiro era o que apagava `cash_available` a
   * cada salvamento da tela de Configurações.
   */
  savePreferences(patch: Partial<Preferences>): Observable<Preferences> {
    const body: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(patch)) {
      if (value !== undefined) body[key] = value;
    }
    return this.http.put<Preferences>(`${this.base}/preferences`, body);
  }

  /** Atalho para a única preferência que Estratégia/Quick Invest escrevem. */
  saveCashAvailable(cashAvailable: number): Observable<Preferences> {
    return this.savePreferences({ cash_available: cashAvailable });
  }

  getStrategy(cashAvailable = 0): Observable<InvestmentStrategy> {
    return this.http.get<InvestmentStrategy>(`${this.base}/strategy`, {
      params: { cash_available: cashAvailable },
    });
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

  getSectorGoals(): Observable<SectorGoal[]> {
    return this.http.get<SectorGoal[]>(`${this.base}/sector-goals`);
  }

  saveSectorGoals(sectorGoals: SectorGoal[]): Observable<SectorGoal[]> {
    return this.http.put<SectorGoal[]>(`${this.base}/sector-goals`, { sector_goals: sectorGoals });
  }

  quickInvest(req: QuickInvestRequest): Observable<QuickInvestResponse> {
    return this.http.post<QuickInvestResponse>(`${this.base}/quick-invest`, req);
  }

  getRebalanceSuggestions(): Observable<RebalanceSuggestionsResponse> {
    return this.http.get<RebalanceSuggestionsResponse>(`${this.base}/rebalance-suggestions`);
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

  sectorsSummary(category = 'acoes_br'): Observable<SectorsSummaryResponse> {
    const params = new HttpParams().set('category', category);
    return this.http.get<SectorsSummaryResponse>(`${this.base}/sectors-summary`, { params });
  }

  searchTickers(query: string, limit = 8): Observable<{ items: TickerSuggestion[] }> {
    const params = new HttpParams().set('q', query).set('limit', limit);
    return this.http.get<{ items: TickerSuggestion[] }>(`${this.base}/universe/search`, {
      params,
    });
  }

  getBenchmark(): Observable<BenchmarkResponse> {
    return this.http.get<BenchmarkResponse>(`${this.base}/benchmark`);
  }

  compareAssets(tickers: string[]): Observable<CompareResponse> {
    const params = new HttpParams().set('tickers', tickers.join(','));
    return this.http.get<CompareResponse>(`${this.base}/compare`, { params });
  }
}
