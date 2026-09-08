import 'package:dio/dio.dart';

import 'auth_service.dart';
import 'cash_models.dart';
import 'models.dart';

class ApiRepository {
  ApiRepository(this._dio);

  final Dio _dio;

  Future<AppUser> getMe() async {
    final res = await _dio.get('/auth/me');
    return AppUser.fromJson(res.data as Map<String, dynamic>);
  }

  Future<DashboardData> getDashboard() async {
    final res = await _dio.get('/dashboard');
    return DashboardData.fromJson(res.data as Map<String, dynamic>);
  }

  Future<QuickInvestResult> quickInvest({
    required double cashAvailable,
    bool useCurrentGoals = true,
    bool prioritizeRebalance = true,
    double minOrderValue = 100,
  }) async {
    final res = await _dio.post(
      '/quick-invest',
      data: {
        'cash_available': cashAvailable,
        'use_current_goals': useCurrentGoals,
        'prioritize_rebalance': prioritizeRebalance,
        'min_order_value': minOrderValue,
      },
    );
    return QuickInvestResult.fromJson(res.data as Map<String, dynamic>);
  }

  Future<WhatsNew> getWhatsNew() async {
    final res = await _dio.get('/whats-new');
    return WhatsNew.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<StoredPortfolioItem>> getPortfolio() async {
    final res = await _dio.get('/portfolio');
    return (res.data['items'] as List)
        .map((e) => StoredPortfolioItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> upsertPosition({
    required String ticker,
    required double quantity,
    required double avgPrice,
    String category = 'auto',
  }) async {
    await _dio.post(
      '/portfolio/position',
      data: {
        'ticker': ticker,
        'quantity': quantity,
        'avg_price': avgPrice,
        'category': category,
      },
    );
  }

  Future<void> savePortfolio(List<StoredPortfolioItem> items) async {
    await _dio.put(
      '/portfolio',
      data: {
        'items': items
            .map(
              (i) => {
                'ticker': i.ticker,
                'quantity': i.quantity,
                'avg_price': i.avgPrice,
                'category': i.category,
              },
            )
            .toList(),
      },
    );
  }

  Future<void> deletePosition(String ticker) async {
    await _dio.delete('/portfolio/position/$ticker');
  }

  Future<FixedIncomeList> getFixedIncome() async {
    final res = await _dio.get('/fixed-income');
    return FixedIncomeList.fromJson(res.data as Map<String, dynamic>);
  }

  Future<FixedIncomePosition> createFixedIncome(
    Map<String, dynamic> payload,
  ) async {
    final res = await _dio.post('/fixed-income', data: payload);
    return FixedIncomePosition.fromJson(res.data as Map<String, dynamic>);
  }

  Future<FixedIncomePosition> updateFixedIncome(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final res = await _dio.put('/fixed-income/$id', data: payload);
    return FixedIncomePosition.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> deleteFixedIncome(int id) async {
    await _dio.delete('/fixed-income/$id');
  }

  Future<List<TickerSuggestion>> searchTickers(
    String query, {
    int limit = 8,
  }) async {
    if (query.trim().isEmpty) return [];
    final res = await _dio.get(
      '/universe/search',
      queryParameters: {'q': query, 'limit': limit},
    );
    return (res.data['items'] as List)
        .map((e) => TickerSuggestion.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ClosedTrade> sellPosition({
    required String ticker,
    required double quantity,
    required double sellPrice,
  }) async {
    final res = await _dio.post(
      '/portfolio/sell',
      data: {'ticker': ticker, 'quantity': quantity, 'sell_price': sellPrice},
    );
    return ClosedTrade.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ClosedTradesResponse> getClosedTrades() async {
    final res = await _dio.get('/portfolio/trades');
    return ClosedTradesResponse.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Opportunity>> getOpportunities({
    String search = '',
    String assetType = '',
    bool onlyInteresting = false,
    double? minDy,
    double? minMosPct,
  }) async {
    final res = await _dio.get(
      '/opportunities',
      queryParameters: {
        'page_size': 30,
        'sort_by': 'score',
        'sort_order': 'desc',
        if (search.isNotEmpty) 'search': search,
        if (assetType.isNotEmpty) 'asset_type': assetType,
        if (onlyInteresting) 'only_interesting': true,
        'min_dy': ?minDy,
        'min_mos': ?minMosPct,
      },
    );
    return (res.data['items'] as List)
        .map((e) => Opportunity.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RebalanceSuggestions> getRebalanceSuggestions() async {
    final res = await _dio.get('/rebalance-suggestions');
    return RebalanceSuggestions.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Preferences> getPreferences() async {
    final res = await _dio.get('/preferences');
    return Preferences.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Preferences> savePreferences({
    double? passiveIncomeGoal,
    bool? notifyPriceAlerts,
    String? opportunitiesFrequency,
    String? riskProfile,
    List<String>? preferredCategories,
    List<String>? preferredSectors,
    List<String>? excludedTickers,
  }) async {
    final data = <String, dynamic>{
      'passive_income_goal': passiveIncomeGoal,
      'notify_price_alerts': notifyPriceAlerts,
      'opportunities_frequency': opportunitiesFrequency,
      'risk_profile': riskProfile,
      'preferred_categories': preferredCategories,
      'preferred_sectors': preferredSectors,
      'excluded_tickers': excludedTickers,
    }..removeWhere((_, v) => v == null);

    final res = await _dio.put('/preferences', data: data);
    return Preferences.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<SectorSummary>> getSectorsSummary({
    String category = 'acoes_br',
  }) async {
    final res = await _dio.get(
      '/sectors-summary',
      queryParameters: {'category': category},
    );
    return (res.data['sectors'] as List)
        .map((e) => SectorSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<DipScanItem>> dipScan({
    double minScore = 40,
    int top = 12,
    String? category,
  }) async {
    final res = await _dio.get(
      '/dip-scanner',
      queryParameters: {
        'min_score': minScore,
        'top': top,
        if (category != null && category.isNotEmpty) 'category': category,
      },
    );
    return (res.data['items'] as List)
        .map((e) => DipScanItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<AssetAnalysis> analyzeAsset(String symbol) async {
    final res = await _dio.get('/asset/$symbol');
    return AssetAnalysis.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ReferenceRates> getRendaFixaRates() async {
    final res = await _dio.get('/renda-fixa/taxas');
    return ReferenceRates.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<RendaFixaResult>> compareRendaFixa(
    List<Map<String, dynamic>> ativos,
  ) async {
    final res = await _dio.post(
      '/renda-fixa/comparar',
      data: {'ativos': ativos},
    );
    return (res.data['resultados'] as List)
        .map((e) => RendaFixaResult.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Goal>> getGoals() async {
    final res = await _dio.get('/goals');
    return (res.data as List)
        .map((e) => Goal.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Goal>> saveGoals(List<Goal> goals) async {
    final res = await _dio.put(
      '/goals',
      data: {'goals': goals.map((g) => g.toJson()).toList()},
    );
    return (res.data as List)
        .map((e) => Goal.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<SectorGoal>> getSectorGoals() async {
    final res = await _dio.get('/sector-goals');
    return (res.data as List)
        .map((e) => SectorGoal.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<SectorGoal>> saveSectorGoals(List<SectorGoal> goals) async {
    final res = await _dio.put(
      '/sector-goals',
      data: {'sector_goals': goals.map((g) => g.toJson()).toList()},
    );
    return (res.data as List)
        .map((e) => SectorGoal.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<PriceAlert>> getAlerts() async {
    final res = await _dio.get('/alerts');
    return (res.data as List)
        .map((e) => PriceAlert.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> createAlert({
    required String ticker,
    required String condition,
    required double targetPrice,
    String? note,
  }) async {
    await _dio.post(
      '/alerts',
      data: {
        'ticker': ticker,
        'condition': condition,
        'target_price': targetPrice,
        'note': note,
      },
    );
  }

  Future<void> deleteAlert(int id) async {
    await _dio.delete('/alerts/$id');
  }

  Future<void> unregisterDeviceToken(String token) async {
    await _dio.delete(
      '/notifications/register-token',
      queryParameters: {'token': token},
    );
  }

  Future<void> registerDeviceToken({
    required String token,
    required String platform,
  }) async {
    await _dio.post(
      '/notifications/register-token',
      data: {'token': token, 'platform': platform},
    );
  }

  Future<BenchmarkResponse> getBenchmark() async {
    final res = await _dio.get('/benchmark');
    return BenchmarkResponse.fromJson(res.data as Map<String, dynamic>);
  }

  Future<CompareResponse> compareAssets(List<String> tickers) async {
    final res = await _dio.get(
      '/compare',
      queryParameters: {'tickers': tickers.join(',')},
    );
    return CompareResponse.fromJson(res.data as Map<String, dynamic>);
  }

  Future<PassiveIncomeProjection> projectPassiveIncome({
    required double monthlyContribution,
    required int monthsAhead,
    required double portfolioGrowthRate,
    required double dividendGrowthRate,
    required bool reinvestDividends,
    double? targetMonthlyIncome,
  }) async {
    final res = await _dio.post(
      '/projection/passive-income',
      data: {
        'monthly_contribution': monthlyContribution,
        'months_ahead': monthsAhead,
        'portfolio_growth_rate': portfolioGrowthRate,
        'dividend_growth_rate': dividendGrowthRate,
        'reinvest_dividends': reinvestDividends,
        'target_monthly_income': targetMonthlyIncome,
      },
    );
    return PassiveIncomeProjection.fromJson(res.data as Map<String, dynamic>);
  }

  Future<IncomeCompare> incomeCompare({
    required double amount,
    required int horizonMonths,
  }) async {
    final res = await _dio.get(
      '/income-compare',
      queryParameters: {'amount': amount, 'horizon_months': horizonMonths},
    );
    return IncomeCompare.fromJson(res.data as Map<String, dynamic>);
  }

  Future<SearchResults> search(String query) async {
    final res = await _dio.get('/search', queryParameters: {'q': query});
    return SearchResults.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ReferralStatus> referralStatus() async {
    final res = await _dio.get('/referral');
    return ReferralStatus.fromJson(res.data as Map<String, dynamic>);
  }

  Future<String> rotateReferralCode() async {
    final res = await _dio.post('/referral/rotate');
    return (res.data as Map<String, dynamic>)['code'] as String;
  }
  // ---------------------------------------------------------------------------
  // Caixa. Toda escrita passa por `cashflow_service` no backend, que reprojeta:
  // nenhuma rota escreve em `cash_store` direto.
  // ---------------------------------------------------------------------------

  Future<CashMonth> getCashMonth({String? month}) async {
    final res = await _dio.get(
      '/cashflow/month',
      queryParameters: month == null ? null : {'month': month},
    );
    return CashMonth.fromJson(res.data as Map<String, dynamic>);
  }

  /// Os lancamentos, ja com o provento derivado do razao montado na leitura -- ele nao esta na
  /// tabela, e e por isso que duplicar e impossivel por construcao.
  Future<List<CashEntry>> getCashEntries() async {
    final res = await _dio.get('/cashflow/entries');
    return (res.data as List)
        .map((e) => CashEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CashEntry> createCashEntry({
    required CashKind kind,
    required String category,
    required String description,
    required double amount,
    required String dueOn,
    String? paidOn,
  }) async {
    final res = await _dio.post(
      '/cashflow/entries',
      data: {
        'kind': kind.json,
        'category': category,
        'description': description,
        'amount': amount,
        'due_on': dueOn,
        'paid_on': paidOn,
      },
    );
    return CashEntry.fromJson(res.data as Map<String, dynamic>);
  }

  Future<CashEntry> updateCashEntry({
    required int id,
    required CashKind kind,
    required String category,
    required String description,
    required double amount,
    required String dueOn,
    String? paidOn,
  }) async {
    final res = await _dio.put(
      '/cashflow/entries/$id',
      data: {
        'kind': kind.json,
        'category': category,
        'description': description,
        'amount': amount,
        'due_on': dueOn,
        'paid_on': paidOn,
      },
    );
    return CashEntry.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> markCashEntryPaid(int id, {String? paidOn}) async {
    await _dio.post(
      '/cashflow/entries/$id/paid',
      data: {'paid_on': paidOn},
    );
  }

  Future<void> deleteCashEntry(int id) async {
    await _dio.delete('/cashflow/entries/$id');
  }

  Future<List<Debt>> getDebts() async {
    final res = await _dio.get('/cashflow/debts');
    return (res.data as List)
        .map((e) => Debt.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Debt> createDebt({
    required String kind,
    required String description,
    required double balance,
    double? monthlyRate,
  }) async {
    final res = await _dio.post(
      '/cashflow/debts',
      data: {
        'kind': kind,
        'description': description,
        'balance': balance,
        'monthly_rate': monthlyRate,
      },
    );
    return Debt.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> settleDebt(int id) async {
    await _dio.post('/cashflow/debts/$id/settled');
  }

  Future<Surplus> getSurplus({String? month}) async {
    final res = await _dio.get(
      '/surplus',
      queryParameters: month == null ? null : {'month': month},
    );
    return Surplus.fromJson(res.data as Map<String, dynamic>);
  }

  /// O molde do mes: LE, nao grava. A gravacao e `createCashEntriesBatch`, e as duas metades
  /// existem para que meio molde de mes nao seja possivel -- quem lancou nao teria como saber o
  /// que entrou e o que ficou de fora.
  Future<CashMonthTemplate> getMonthTemplate({
    required String target,
    String? source,
  }) async {
    final res = await _dio.get(
      '/cashflow/month/template',
      queryParameters: {
        'target': target,
        'source': ?source,
      },
    );
    return CashMonthTemplate.fromJson(res.data as Map<String, dynamic>);
  }

  /// Grava o lote inteiro ou nenhum.
  Future<List<CashEntry>> createCashEntriesBatch(
    List<CashTemplateCandidate> escolhidos,
  ) async {
    final res = await _dio.post(
      '/cashflow/entries/batch',
      data: {
        'entries': [
          for (final c in escolhidos)
            {
              'kind': c.kind.json,
              'category': c.category,
              'description': c.description,
              'amount': c.amount,
              'due_on': c.dueOn,
              // O copiado nasce A VENCER: o valor do mes que passou e fato daquele mes.
              'paid_on': null,
            },
        ],
      },
    );
    return (res.data as List)
        .map((e) => CashEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CashVocabulary> getCashVocabulary() async {
    final res = await _dio.get('/cashflow/vocabulary');
    return CashVocabulary.fromJson(res.data as Map<String, dynamic>);
  }
}
