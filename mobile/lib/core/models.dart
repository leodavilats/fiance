class PortfolioPosition {
  PortfolioPosition({
    required this.ticker,
    required this.name,
    required this.quantity,
    required this.avgPrice,
    required this.currentPrice,
    required this.invested,
    required this.currentValue,
    required this.pnl,
    required this.pnlPct,
    required this.verdict,
    required this.label,
    required this.categoryResolved,
    required this.dividendYield,
    required this.sector,
    this.reasons = const [],
  });

  final String ticker;
  final String? name;
  final double quantity;
  final double avgPrice;
  final double? currentPrice;
  final double invested;
  final double? currentValue;
  final double? pnl;
  final double? pnlPct;
  final String verdict;
  final String label;
  final String categoryResolved;
  final double? dividendYield;
  final String? sector;
  final List<String> reasons;

  factory PortfolioPosition.fromJson(Map<String, dynamic> j) =>
      PortfolioPosition(
        ticker: j['ticker'] as String,
        name: j['name'] as String?,
        quantity: (j['quantity'] as num).toDouble(),
        avgPrice: (j['avg_price'] as num).toDouble(),
        currentPrice: (j['current_price'] as num?)?.toDouble(),
        invested: (j['invested'] as num).toDouble(),
        currentValue: (j['current_value'] as num?)?.toDouble(),
        pnl: (j['pnl'] as num?)?.toDouble(),
        pnlPct: (j['pnl_pct'] as num?)?.toDouble(),
        verdict: j['verdict'] as String? ?? '',
        label: j['label'] as String? ?? '',
        categoryResolved: j['category_resolved'] as String? ?? 'trade',
        dividendYield: (j['dividend_yield'] as num?)?.toDouble(),
        sector: j['sector'] as String?,
        reasons:
            (j['reasons'] as List?)?.map((e) => e as String).toList() ??
            const [],
      );
}

class StoredPortfolioItem {
  StoredPortfolioItem({
    required this.ticker,
    required this.quantity,
    required this.avgPrice,
    required this.category,
  });

  final String ticker;
  final double quantity;
  final double avgPrice;
  final String category;

  factory StoredPortfolioItem.fromJson(Map<String, dynamic> j) =>
      StoredPortfolioItem(
        ticker: j['ticker'] as String,
        quantity: (j['quantity'] as num).toDouble(),
        avgPrice: (j['avg_price'] as num).toDouble(),
        category: j['category'] as String? ?? 'auto',
      );

  Map<String, dynamic> toJson() => {
    'ticker': ticker,
    'quantity': quantity,
    'avg_price': avgPrice,
    'category': category,
  };
}

class ClosedTrade {
  ClosedTrade({
    required this.id,
    required this.ticker,
    required this.category,
    required this.quantity,
    required this.avgPrice,
    required this.sellPrice,
    required this.grossProfit,
    required this.irRate,
    required this.irAmount,
    required this.netProfit,
    required this.soldAt,
  });

  final int id;
  final String ticker;
  final String category;
  final double quantity;
  final double avgPrice;
  final double sellPrice;
  final double grossProfit;
  final double irRate;
  final double irAmount;
  final double netProfit;
  final double soldAt;

  factory ClosedTrade.fromJson(Map<String, dynamic> j) => ClosedTrade(
    id: j['id'] as int,
    ticker: j['ticker'] as String,
    category: j['category'] as String,
    quantity: (j['quantity'] as num).toDouble(),
    avgPrice: (j['avg_price'] as num).toDouble(),
    sellPrice: (j['sell_price'] as num).toDouble(),
    grossProfit: (j['gross_profit'] as num).toDouble(),
    irRate: (j['ir_rate'] as num).toDouble(),
    irAmount: (j['ir_amount'] as num).toDouble(),
    netProfit: (j['net_profit'] as num).toDouble(),
    soldAt: (j['sold_at'] as num).toDouble(),
  );
}

class ClosedTradesResponse {
  ClosedTradesResponse({
    required this.trades,
    required this.totalRealizedPnl,
    required this.totalIrPaid,
  });

  final List<ClosedTrade> trades;
  final double totalRealizedPnl;
  final double totalIrPaid;

  factory ClosedTradesResponse.fromJson(Map<String, dynamic> j) =>
      ClosedTradesResponse(
        trades: (j['trades'] as List)
            .map((e) => ClosedTrade.fromJson(e as Map<String, dynamic>))
            .toList(),
        totalRealizedPnl: (j['total_realized_pnl'] as num).toDouble(),
        totalIrPaid: (j['total_ir_paid'] as num).toDouble(),
      );
}

class TickerSuggestion {
  TickerSuggestion({required this.ticker, required this.name});

  final String ticker;
  final String name;

  factory TickerSuggestion.fromJson(Map<String, dynamic> j) => TickerSuggestion(
    ticker: j['ticker'] as String,
    name: j['name'] as String? ?? '',
  );
}

class DashboardSummary {
  DashboardSummary({
    required this.totalInvested,
    required this.totalCurrent,
    required this.totalPnl,
    required this.totalPnlPct,
    required this.cashAvailable,
    required this.monthlyDividendsEstimate,
    required this.passiveIncomeGoal,
    required this.passiveIncomeProgress,
    required this.positionsCount,
  });

  final double totalInvested;
  final double totalCurrent;
  final double totalPnl;
  final double totalPnlPct;
  final double cashAvailable;
  final double monthlyDividendsEstimate;
  final double? passiveIncomeGoal;
  final double? passiveIncomeProgress;
  final int positionsCount;

  factory DashboardSummary.fromJson(Map<String, dynamic> j) => DashboardSummary(
    totalInvested: (j['total_invested'] as num).toDouble(),
    totalCurrent: (j['total_current'] as num).toDouble(),
    totalPnl: (j['total_pnl'] as num).toDouble(),
    totalPnlPct: (j['total_pnl_pct'] as num).toDouble(),
    cashAvailable: (j['cash_available'] as num).toDouble(),
    monthlyDividendsEstimate: (j['monthly_dividends_estimate'] as num)
        .toDouble(),
    passiveIncomeGoal: (j['passive_income_goal'] as num?)?.toDouble(),
    passiveIncomeProgress: (j['passive_income_progress'] as num?)?.toDouble(),
    positionsCount: j['positions_count'] as int,
  );
}

class CategoryAllocation {
  CategoryAllocation({
    required this.category,
    required this.currentValue,
    required this.currentPct,
    required this.targetPct,
  });

  final String category;
  final double currentValue;
  final double currentPct;
  final double? targetPct;

  factory CategoryAllocation.fromJson(Map<String, dynamic> j) =>
      CategoryAllocation(
        category: j['category'] as String,
        currentValue: (j['current_value'] as num).toDouble(),
        currentPct: (j['current_pct'] as num).toDouble(),
        targetPct: (j['target_pct'] as num?)?.toDouble(),
      );
}

class PortfolioAlert {
  PortfolioAlert({
    required this.severity,
    required this.title,
    required this.detail,
    required this.ticker,
  });

  final String severity;
  final String title;
  final String detail;
  final String? ticker;

  factory PortfolioAlert.fromJson(Map<String, dynamic> j) => PortfolioAlert(
    severity: j['severity'] as String? ?? 'info',
    title: j['title'] as String? ?? '',
    detail: j['detail'] as String? ?? '',
    ticker: j['ticker'] as String?,
  );
}

class DashboardData {
  DashboardData({
    required this.summary,
    required this.positions,
    required this.allocations,
    required this.topBuys,
    required this.topSells,
    required this.alerts,
  });

  final DashboardSummary summary;
  final List<PortfolioPosition> positions;
  final List<CategoryAllocation> allocations;
  final List<Opportunity> topBuys;
  final List<PortfolioPosition> topSells;
  final List<PortfolioAlert> alerts;

  factory DashboardData.fromJson(Map<String, dynamic> j) => DashboardData(
    summary: DashboardSummary.fromJson(j['summary'] as Map<String, dynamic>),
    positions: (j['positions'] as List)
        .map((e) => PortfolioPosition.fromJson(e as Map<String, dynamic>))
        .toList(),
    allocations: (j['allocations'] as List)
        .map((e) => CategoryAllocation.fromJson(e as Map<String, dynamic>))
        .toList(),
    topBuys: (j['top_buys'] as List)
        .map((e) => Opportunity.fromJson(e as Map<String, dynamic>))
        .toList(),
    topSells: (j['top_sells'] as List)
        .map((e) => PortfolioPosition.fromJson(e as Map<String, dynamic>))
        .toList(),
    alerts: (j['alerts'] as List)
        .map((e) => PortfolioAlert.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class Opportunity {
  Opportunity({
    required this.ticker,
    required this.name,
    required this.price,
    required this.fairPrice,
    required this.marginOfSafety,
    required this.dividendYield,
    required this.verdict,
    required this.label,
    required this.sector,
    required this.score,
  });

  final String ticker;
  final String? name;
  final double? price;
  final double? fairPrice;
  final double? marginOfSafety;
  final double? dividendYield;
  final String verdict;
  final String label;
  final String? sector;
  final double score;

  factory Opportunity.fromJson(Map<String, dynamic> j) => Opportunity(
    ticker: j['ticker'] as String,
    name: j['name'] as String?,
    price: (j['price'] as num?)?.toDouble(),
    fairPrice: (j['fair_price'] as num?)?.toDouble(),
    marginOfSafety: (j['margin_of_safety'] as num?)?.toDouble(),
    dividendYield: (j['dividend_yield'] as num?)?.toDouble(),
    verdict: j['verdict'] as String? ?? '',
    label: j['label'] as String? ?? '',
    sector: j['sector'] as String?,
    score: (j['score'] as num?)?.toDouble() ?? 0,
  );
}

class SectorAsset {
  SectorAsset({
    required this.ticker,
    required this.name,
    required this.score,
    required this.dividendYield,
  });

  final String ticker;
  final String? name;
  final double score;
  final double? dividendYield;

  factory SectorAsset.fromJson(Map<String, dynamic> j) => SectorAsset(
    ticker: j['ticker'] as String,
    name: j['name'] as String?,
    score: (j['score'] as num?)?.toDouble() ?? 0,
    dividendYield: (j['dividend_yield'] as num?)?.toDouble(),
  );
}

class SectorSummary {
  SectorSummary({
    required this.sector,
    required this.count,
    required this.avgScore,
    required this.avgDy,
    required this.topAssets,
  });

  final String sector;
  final int count;
  final double avgScore;
  final double avgDy;
  final List<SectorAsset> topAssets;

  factory SectorSummary.fromJson(Map<String, dynamic> j) => SectorSummary(
    sector: j['sector'] as String,
    count: j['count'] as int,
    avgScore: (j['avg_score'] as num).toDouble(),
    avgDy: (j['avg_dy'] as num).toDouble(),
    topAssets: (j['top_assets'] as List)
        .map((e) => SectorAsset.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class DipScanItem {
  DipScanItem({
    required this.symbol,
    required this.name,
    required this.price,
    required this.dipScore,
    required this.verdictLabel,
    required this.dropFromHighPct,
    required this.marginOfSafety,
    required this.topReason,
  });

  final String symbol;
  final String? name;
  final double? price;
  final double dipScore;
  final String verdictLabel;
  final double? dropFromHighPct;
  final double? marginOfSafety;
  final String topReason;

  factory DipScanItem.fromJson(Map<String, dynamic> j) => DipScanItem(
    symbol: j['symbol'] as String,
    name: j['name'] as String?,
    price: (j['price'] as num?)?.toDouble(),
    dipScore: (j['dip_score'] as num).toDouble(),
    verdictLabel: j['verdict_label'] as String? ?? '',
    dropFromHighPct: (j['drop_from_52w_high_pct'] as num?)?.toDouble(),
    marginOfSafety: (j['margin_of_safety'] as num?)?.toDouble(),
    topReason: j['top_reason'] as String? ?? '',
  );
}

class AssetAnalysis {
  AssetAnalysis({
    required this.symbol,
    required this.name,
    required this.sector,
    required this.price,
    required this.bazin,
    required this.graham,
    required this.consensus,
    required this.marginOfSafety,
    required this.rsi14,
    required this.trend,
    required this.verdict,
    required this.label,
    required this.reasons,
  });

  final String symbol;
  final String? name;
  final String? sector;
  final double? price;
  final double? bazin;
  final double? graham;
  final double? consensus;
  final double? marginOfSafety;
  final double? rsi14;
  final String trend;
  final String verdict;
  final String label;
  final List<String> reasons;

  factory AssetAnalysis.fromJson(Map<String, dynamic> j) {
    final fp = j['fair_price'] as Map<String, dynamic>;
    final tech = j['technical'] as Map<String, dynamic>;
    final dec = j['decision'] as Map<String, dynamic>;
    return AssetAnalysis(
      symbol: j['symbol'] as String,
      name: j['name'] as String?,
      sector: j['sector'] as String?,
      price: (j['price'] as num?)?.toDouble(),
      bazin: (fp['bazin'] as num?)?.toDouble(),
      graham: (fp['graham'] as num?)?.toDouble(),
      consensus: (fp['consensus'] as num?)?.toDouble(),
      marginOfSafety: (fp['margin_of_safety'] as num?)?.toDouble(),
      rsi14: (tech['rsi_14'] as num?)?.toDouble(),
      trend: tech['trend'] as String? ?? 'unknown',
      verdict: dec['verdict'] as String? ?? '',
      label: dec['label'] as String? ?? '',
      reasons:
          (dec['reasons'] as List?)?.map((e) => e as String).toList() ?? [],
    );
  }
}

class ReferenceRates {
  ReferenceRates({
    required this.cdiAnual,
    required this.selicAnual,
    required this.ipcaAnual,
  });

  final double cdiAnual;
  final double selicAnual;
  final double ipcaAnual;

  factory ReferenceRates.fromJson(Map<String, dynamic> j) => ReferenceRates(
    cdiAnual: (j['cdi_anual'] as num).toDouble(),
    selicAnual: (j['selic_anual'] as num).toDouble(),
    ipcaAnual: (j['ipca_anual'] as num).toDouble(),
  );
}

class RendaFixaResult {
  RendaFixaResult({
    required this.tipo,
    required this.nome,
    required this.valorInvestido,
    required this.valorLiquido,
    required this.rendimentoLiquido,
    required this.taxaLiquidaAa,
    required this.melhorOpcao,
  });

  final String tipo;
  final String? nome;
  final double valorInvestido;
  final double valorLiquido;
  final double rendimentoLiquido;
  final double taxaLiquidaAa;
  final bool melhorOpcao;

  factory RendaFixaResult.fromJson(Map<String, dynamic> j) => RendaFixaResult(
    tipo: j['tipo'] as String,
    nome: j['nome'] as String?,
    valorInvestido: (j['valor_investido'] as num).toDouble(),
    valorLiquido: (j['valor_liquido'] as num).toDouble(),
    rendimentoLiquido: (j['rendimento_liquido'] as num).toDouble(),
    taxaLiquidaAa: (j['taxa_liquida_aa'] as num).toDouble(),
    melhorOpcao: j['melhor_opcao'] as bool? ?? false,
  );
}

class Goal {
  Goal({required this.category, required this.targetPct, this.targetValue});

  final String category;
  final double targetPct;
  final double? targetValue;

  factory Goal.fromJson(Map<String, dynamic> j) => Goal(
    category: j['category'] as String,
    targetPct: (j['target_pct'] as num).toDouble(),
    targetValue: (j['target_value'] as num?)?.toDouble(),
  );

  Map<String, dynamic> toJson() => {
    'category': category,
    'target_pct': targetPct,
    'target_value': targetValue,
    'deadline': null,
  };

  Goal copyWith({double? targetPct}) => Goal(
    category: category,
    targetPct: targetPct ?? this.targetPct,
    targetValue: targetValue,
  );
}

class SectorGoal {
  SectorGoal({required this.sector, required this.targetPct});

  final String sector;
  final double targetPct;

  factory SectorGoal.fromJson(Map<String, dynamic> j) => SectorGoal(
    sector: j['sector'] as String,
    targetPct: (j['target_pct'] as num).toDouble(),
  );

  Map<String, dynamic> toJson() => {'sector': sector, 'target_pct': targetPct};

  SectorGoal copyWith({double? targetPct}) =>
      SectorGoal(sector: sector, targetPct: targetPct ?? this.targetPct);
}

class PriceAlert {
  PriceAlert({
    required this.id,
    required this.ticker,
    required this.condition,
    required this.targetPrice,
    required this.note,
    required this.triggeredAt,
  });

  final int id;
  final String ticker;
  final String condition;
  final double targetPrice;
  final String? note;
  final double? triggeredAt;

  factory PriceAlert.fromJson(Map<String, dynamic> j) => PriceAlert(
    id: j['id'] as int,
    ticker: j['ticker'] as String,
    condition: j['condition'] as String,
    targetPrice: (j['target_price'] as num).toDouble(),
    note: j['note'] as String?,
    triggeredAt: (j['triggered_at'] as num?)?.toDouble(),
  );
}

class Preferences {
  Preferences({
    required this.cashAvailable,
    required this.passiveIncomeGoal,
    required this.desiredYieldStock,
    required this.desiredYieldFii,
    required this.desiredYieldInt,
    this.notifyPriceAlerts = true,
    this.notifyNewOpportunities = true,
  });

  final double cashAvailable;
  final double? passiveIncomeGoal;
  final double desiredYieldStock;
  final double desiredYieldFii;
  final double desiredYieldInt;
  final bool notifyPriceAlerts;
  final bool notifyNewOpportunities;

  factory Preferences.fromJson(Map<String, dynamic> j) => Preferences(
    cashAvailable: (j['cash_available'] as num).toDouble(),
    passiveIncomeGoal: (j['passive_income_goal'] as num?)?.toDouble(),
    desiredYieldStock: (j['desired_yield_stock'] as num).toDouble(),
    desiredYieldFii: (j['desired_yield_fii'] as num).toDouble(),
    desiredYieldInt: (j['desired_yield_int'] as num).toDouble(),
    notifyPriceAlerts: j['notify_price_alerts'] as bool? ?? true,
    notifyNewOpportunities: j['notify_new_opportunities'] as bool? ?? true,
  );
}
