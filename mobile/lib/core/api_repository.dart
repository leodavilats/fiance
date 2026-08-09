import 'package:dio/dio.dart';

import 'models.dart';

class ApiRepository {
  ApiRepository(this._dio);

  final Dio _dio;

  Future<DashboardData> getDashboard() async {
    final res = await _dio.get('/dashboard');
    return DashboardData.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<StoredPortfolioItem>> getPortfolio() async {
    final res = await _dio.get('/portfolio');
    return (res.data['items'] as List)
        .map((e) => StoredPortfolioItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> savePortfolio(List<StoredPortfolioItem> items) async {
    await _dio.put('/portfolio', data: {
      'items': items
          .map((i) => {
                'ticker': i.ticker,
                'quantity': i.quantity,
                'avg_price': i.avgPrice,
                'category': i.category,
              })
          .toList(),
    });
  }

  Future<void> deletePosition(String ticker) async {
    await _dio.delete('/portfolio/$ticker');
  }

  Future<List<Opportunity>> getOpportunities({String search = ''}) async {
    final res = await _dio.get('/opportunities', queryParameters: {
      'page_size': 30,
      'sort_by': 'score',
      'sort_order': 'desc',
      if (search.isNotEmpty) 'search': search,
    });
    return (res.data['items'] as List)
        .map((e) => Opportunity.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Preferences> getPreferences() async {
    final res = await _dio.get('/preferences');
    return Preferences.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Preferences> savePreferences({
    required double cashAvailable,
    double? passiveIncomeGoal,
  }) async {
    final res = await _dio.put('/preferences', data: {
      'cash_available': cashAvailable,
      'passive_income_goal': passiveIncomeGoal,
    });
    return Preferences.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<SectorSummary>> getSectorsSummary({String category = 'acoes_br'}) async {
    final res = await _dio.get('/sectors-summary', queryParameters: {'category': category});
    return (res.data['sectors'] as List)
        .map((e) => SectorSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<DipScanItem>> dipScan({double minScore = 40, int top = 12, String? category}) async {
    final res = await _dio.get('/dip-scanner', queryParameters: {
      'min_score': minScore,
      'top': top,
      if (category != null && category.isNotEmpty) 'category': category,
    });
    return (res.data['items'] as List)
        .map((e) => DipScanItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> quickInvest({
    required double cashAvailable,
    bool useCurrentGoals = true,
    bool prioritizeRebalance = true,
    double minOrderValue = 100,
  }) async {
    final res = await _dio.post('/quick-invest', data: {
      'cash_available': cashAvailable,
      'use_current_goals': useCurrentGoals,
      'prioritize_rebalance': prioritizeRebalance,
      'min_order_value': minOrderValue,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getStrategy() async {
    final res = await _dio.get('/strategy');
    return res.data as Map<String, dynamic>;
  }

  Future<AssetAnalysis> analyzeAsset(String symbol) async {
    final res = await _dio.get('/asset/$symbol');
    return AssetAnalysis.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ReferenceRates> getRendaFixaRates() async {
    final res = await _dio.get('/renda-fixa/taxas');
    return ReferenceRates.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<RendaFixaResult>> compareRendaFixa(List<Map<String, dynamic>> ativos) async {
    final res = await _dio.post('/renda-fixa/comparar', data: {'ativos': ativos});
    return (res.data['resultados'] as List)
        .map((e) => RendaFixaResult.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Goal>> getGoals() async {
    final res = await _dio.get('/goals');
    return (res.data as List).map((e) => Goal.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Goal>> saveGoals(List<Goal> goals) async {
    final res = await _dio.put('/goals', data: {'goals': goals.map((g) => g.toJson()).toList()});
    return (res.data as List).map((e) => Goal.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<SectorGoal>> getSectorGoals() async {
    final res = await _dio.get('/sector-goals');
    return (res.data as List).map((e) => SectorGoal.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<SectorGoal>> saveSectorGoals(List<SectorGoal> goals) async {
    final res = await _dio.put('/sector-goals', data: {
      'sector_goals': goals.map((g) => g.toJson()).toList(),
    });
    return (res.data as List).map((e) => SectorGoal.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<PriceAlert>> getAlerts() async {
    final res = await _dio.get('/alerts');
    return (res.data as List).map((e) => PriceAlert.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> createAlert({
    required String ticker,
    required String condition,
    required double targetPrice,
    String? note,
  }) async {
    await _dio.post('/alerts', data: {
      'ticker': ticker,
      'condition': condition,
      'target_price': targetPrice,
      'note': note,
    });
  }

  Future<void> deleteAlert(int id) async {
    await _dio.delete('/alerts/$id');
  }
}
