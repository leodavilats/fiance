class PortfolioPosition {
  PortfolioPosition({
    required this.ticker,
    required this.name,
    required this.assetType,
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
    this.asOf,
    this.reasons = const [],
    this.confidence = 0,
    this.dataYears = 0,
    this.independentInputs = 0,
    this.trendBasis = 'none',
  });

  final String ticker;
  final String? name;
  final String assetType;
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

  final double? asOf;

  final List<String> reasons;
  final double confidence;
  final int dataYears;
  final int independentInputs;
  final String trendBasis;

  factory PortfolioPosition.fromJson(Map<String, dynamic> j) =>
      PortfolioPosition(
        ticker: j['ticker'] as String,
        name: j['name'] as String?,
        assetType: j['asset_type'] as String? ?? 'br_stock',
        quantity: (j['quantity'] as num).toDouble(),
        avgPrice: (j['avg_price'] as num).toDouble(),
        currentPrice: (j['current_price'] as num?)?.toDouble(),
        invested: (j['invested'] as num).toDouble(),
        currentValue: (j['current_value'] as num?)?.toDouble(),
        pnl: (j['pnl'] as num?)?.toDouble(),
        pnlPct: (j['pnl_pct'] as num?)?.toDouble(),
        verdict: j['verdict'] as String? ?? '',
        label: j['label'] as String? ?? '',
        categoryResolved: j['category_resolved'] as String? ?? 'acoes_br',
        dividendYield: (j['dividend_yield'] as num?)?.toDouble(),
        sector: j['sector'] as String?,
        asOf: (j['as_of'] as num?)?.toDouble(),
        reasons:
            (j['reasons'] as List?)?.map((e) => e as String).toList() ??
            const [],
        confidence: (j['confidence'] as num?)?.toDouble() ?? 0,
        dataYears: j['data_years'] as int? ?? 0,
        independentInputs: (j['independent_inputs'] as num?)?.toInt() ?? 0,
        trendBasis: j['trend_basis'] as String? ?? 'none',
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
    required this.month,
    required this.irIsProrated,
    this.dayTrade = false,
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
  final String month;
  final bool irIsProrated;
  final bool dayTrade;

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
    month: j['month'] as String? ?? '',
    irIsProrated: j['ir_is_prorated'] as bool? ?? false,
    dayTrade: j['day_trade'] as bool? ?? false,
  );
}

class MonthlyTaxAssessment {
  MonthlyTaxAssessment({
    required this.month,
    required this.category,
    required this.grossSales,
    required this.result,
    required this.exempt,
    required this.lossOffsetUsed,
    required this.taxableProfit,
    required this.irRate,
    required this.irAmount,
    required this.sales,
    required this.observation,
    this.dayTrade = false,
    this.irrfWithheld = 0,
    this.irrfDeducted = 0,
    this.irPayable,
  });

  final String month;
  final String category;
  final double grossSales;
  final double result;
  final bool exempt;
  final double lossOffsetUsed;
  final double taxableProfit;
  final double irRate;
  final double irAmount;
  final int sales;
  final String observation;
  final bool dayTrade;
  final double irrfWithheld;
  final double irrfDeducted;
  final double? irPayable;

  factory MonthlyTaxAssessment.fromJson(Map<String, dynamic> j) =>
      MonthlyTaxAssessment(
        month: j['month'] as String,
        category: j['category'] as String,
        grossSales: (j['gross_sales'] as num).toDouble(),
        result: (j['result'] as num).toDouble(),
        exempt: j['exempt'] as bool? ?? false,
        lossOffsetUsed: (j['loss_offset_used'] as num?)?.toDouble() ?? 0,
        taxableProfit: (j['taxable_profit'] as num?)?.toDouble() ?? 0,
        irRate: (j['ir_rate'] as num?)?.toDouble() ?? 0,
        irAmount: (j['ir_amount'] as num?)?.toDouble() ?? 0,
        sales: (j['sales'] as num?)?.toInt() ?? 0,
        observation: j['observation'] as String? ?? '',
        dayTrade: j['day_trade'] as bool? ?? false,
        irrfWithheld: (j['irrf_withheld'] as num?)?.toDouble() ?? 0,
        irrfDeducted: (j['irrf_deducted'] as num?)?.toDouble() ?? 0,
        irPayable: (j['ir_payable'] as num?)?.toDouble(),
      );
}

class ClosedTradesResponse {
  ClosedTradesResponse({
    required this.trades,
    required this.months,
    required this.totalRealizedPnl,
    required this.totalIrPaid,
  });

  final List<ClosedTrade> trades;
  final List<MonthlyTaxAssessment> months;
  final double totalRealizedPnl;
  final double totalIrPaid;

  factory ClosedTradesResponse.fromJson(Map<String, dynamic> j) =>
      ClosedTradesResponse(
        trades: (j['trades'] as List)
            .map((e) => ClosedTrade.fromJson(e as Map<String, dynamic>))
            .toList(),
        months: ((j['months'] as List?) ?? const [])
            .map((e) => MonthlyTaxAssessment.fromJson(e as Map<String, dynamic>))
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
    required this.monthlyDividendsEstimate,
    required this.passiveIncomeGoal,
    required this.passiveIncomeProgress,
    required this.positionsCount,
  });

  final double totalInvested;
  final double totalCurrent;
  final double totalPnl;
  final double totalPnlPct;
  final double monthlyDividendsEstimate;
  final double? passiveIncomeGoal;
  final double? passiveIncomeProgress;
  final int positionsCount;

  factory DashboardSummary.fromJson(Map<String, dynamic> j) => DashboardSummary(
    totalInvested: (j['total_invested'] as num).toDouble(),
    totalCurrent: (j['total_current'] as num).toDouble(),
    totalPnl: (j['total_pnl'] as num).toDouble(),
    totalPnlPct: (j['total_pnl_pct'] as num).toDouble(),
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
    required this.kind,
    required this.title,
    required this.detail,
    required this.ticker,
    required this.count,
    required this.action,
    required this.actionLabel,
  });

  final String severity;
  final String kind;
  final String title;
  final String detail;
  final String? ticker;
  final int count;
  final String? action;
  final String? actionLabel;

  factory PortfolioAlert.fromJson(Map<String, dynamic> j) => PortfolioAlert(
    severity: j['severity'] as String? ?? 'info',
    kind: j['kind'] as String? ?? '',
    title: j['title'] as String? ?? '',
    detail: j['detail'] as String? ?? '',
    ticker: j['ticker'] as String?,
    count: j['count'] as int? ?? 1,
    action: j['action'] as String?,
    actionLabel: j['action_label'] as String?,
  );
}

class DataFreshness {
  DataFreshness({
    required this.ratesSource,
    required this.marketDataAgeSeconds,
    required this.marketDataStale,
  });

  final String ratesSource;
  final double? marketDataAgeSeconds;
  final bool marketDataStale;

  factory DataFreshness.fromJson(Map<String, dynamic> j) => DataFreshness(
    ratesSource: j['rates_source'] as String? ?? 'estimativa',
    marketDataAgeSeconds: (j['market_data_age_seconds'] as num?)?.toDouble(),
    marketDataStale: j['market_data_stale'] as bool? ?? false,
  );

  String get label {
    final age = marketDataAgeSeconds;
    if (age == null) return 'Cotações sem carimbo de tempo';
    if (age < 120) return 'Cotações de agora';
    if (age < 3600) return 'Cotações de ${(age / 60).round()} min atrás';
    return 'Cotações de ${(age / 3600).round()} h atrás';
  }

  String get ratesLabel => ratesSource == 'bcb'
      ? 'CDI/Selic do Banco Central'
      : 'CDI/Selic estimados';
}

class WhatsNewItem {
  WhatsNewItem({
    required this.kind,
    required this.severity,
    required this.title,
    required this.detail,
    required this.ticker,
    required this.action,
    required this.actionLabel,
  });

  final String kind;
  final String severity;
  final String title;
  final String detail;
  final String? ticker;
  final String? action;
  final String? actionLabel;

  factory WhatsNewItem.fromJson(Map<String, dynamic> j) => WhatsNewItem(
    kind: j['kind'] as String? ?? '',
    severity: j['severity'] as String? ?? 'info',
    title: j['title'] as String? ?? '',
    detail: j['detail'] as String? ?? '',
    ticker: j['ticker'] as String?,
    action: j['action'] as String?,
    actionLabel: j['action_label'] as String?,
  );
}

class WhatsNew {
  WhatsNew({required this.items, required this.daysSince});

  final List<WhatsNewItem> items;
  final double? daysSince;

  factory WhatsNew.fromJson(Map<String, dynamic> j) => WhatsNew(
    items: (j['items'] as List? ?? const [])
        .map((e) => WhatsNewItem.fromJson(e as Map<String, dynamic>))
        .toList(),
    daysSince: (j['days_since'] as num?)?.toDouble(),
  );
}

class PortfolioSnapshot {
  PortfolioSnapshot({
    required this.capturedAt,
    required this.totalInvested,
    required this.totalCurrent,
    required this.totalPnl,
    required this.totalPnlPct,
  });

  final double capturedAt;
  final double totalInvested;
  final double totalCurrent;
  final double totalPnl;
  final double totalPnlPct;

  factory PortfolioSnapshot.fromJson(Map<String, dynamic> j) =>
      PortfolioSnapshot(
        capturedAt: (j['captured_at'] as num).toDouble(),
        totalInvested: (j['total_invested'] as num).toDouble(),
        totalCurrent: (j['total_current'] as num).toDouble(),
        totalPnl: (j['total_pnl'] as num).toDouble(),
        totalPnlPct: (j['total_pnl_pct'] as num).toDouble(),
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
    this.snapshots = const [],
    this.health,
    this.freshness,
  });

  final DashboardSummary summary;
  final List<PortfolioPosition> positions;
  final List<CategoryAllocation> allocations;
  final List<Opportunity> topBuys;
  final List<PortfolioPosition> topSells;
  final List<PortfolioAlert> alerts;
  final List<PortfolioSnapshot> snapshots;
  final PortfolioHealth? health;
  final DataFreshness? freshness;

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
    health: j['health'] != null
        ? PortfolioHealth.fromJson(j['health'] as Map<String, dynamic>)
        : null,
    topSells: (j['top_sells'] as List)
        .map((e) => PortfolioPosition.fromJson(e as Map<String, dynamic>))
        .toList(),
    alerts: (j['alerts'] as List)
        .map((e) => PortfolioAlert.fromJson(e as Map<String, dynamic>))
        .toList(),
    snapshots:
        (j['snapshots'] as List?)
            ?.map((e) => PortfolioSnapshot.fromJson(e as Map<String, dynamic>))
            .toList() ??
        const [],
    freshness: j['freshness'] != null
        ? DataFreshness.fromJson(j['freshness'] as Map<String, dynamic>)
        : null,
  );
}

class Opportunity {
  Opportunity({
    required this.ticker,
    required this.name,
    required this.price,
    this.asOf,
    required this.fairPrice,
    this.fairLow,
    this.fairHigh,
    required this.marginOfSafety,
    required this.dividendYield,
    required this.verdict,
    required this.label,
    this.basis = 'band',
    this.bandQuality = 'sem_faixa',
    this.independentInputs = 0,
    this.confidenceLabel = 'baixa',
    required this.sector,
    required this.score,
    this.confidence = 0,
    this.dataYears = 0,
    this.trendBasis = 'none',
    this.dataCompleteness = 1,
    this.changePercentDay,
    this.distanceFrom52wHighPct,
    this.range52wPosition,
    this.personalCeiling,
  });

  final String ticker;
  final String? name;
  final double? price;

  final double? asOf;

  final double? personalCeiling;

  final double? fairPrice;
  final double? fairLow;
  final double? fairHigh;
  final double? marginOfSafety;
  final double? dividendYield;
  final String verdict;
  final String label;

  final String basis;
  final String bandQuality;
  final int independentInputs;
  final String confidenceLabel;
  final String? sector;
  final double score;
  final double confidence;
  final int dataYears;
  final String trendBasis;
  final double dataCompleteness;
  final double? changePercentDay;
  final double? distanceFrom52wHighPct;
  final double? range52wPosition;

  factory Opportunity.fromJson(Map<String, dynamic> j) => Opportunity(
    ticker: j['ticker'] as String,
    name: j['name'] as String?,
    price: (j['price'] as num?)?.toDouble(),
    asOf: (j['as_of'] as num?)?.toDouble(),
    fairPrice: (j['fair_price'] as num?)?.toDouble(),
    fairLow: (j['fair_low'] as num?)?.toDouble(),
    fairHigh: (j['fair_high'] as num?)?.toDouble(),
    marginOfSafety: (j['margin_of_safety'] as num?)?.toDouble(),
    dividendYield: (j['dividend_yield'] as num?)?.toDouble(),
    verdict: j['verdict'] as String? ?? '',
    label: j['label'] as String? ?? '',
    basis: j['basis'] as String? ?? 'band',
    bandQuality: j['band_quality'] as String? ?? 'sem_faixa',
    independentInputs: (j['independent_inputs'] as num?)?.toInt() ?? 0,
    confidenceLabel: j['confidence_label'] as String? ?? 'baixa',
    sector: j['sector'] as String?,
    score: (j['score'] as num?)?.toDouble() ?? 0,
    confidence: (j['confidence'] as num?)?.toDouble() ?? 0,
    dataYears: j['data_years'] as int? ?? 0,
    trendBasis: j['trend_basis'] as String? ?? 'none',
    dataCompleteness: (j['data_completeness'] as num?)?.toDouble() ?? 1,
    changePercentDay: (j['change_percent_day'] as num?)?.toDouble(),
    distanceFrom52wHighPct: (j['distance_from_52w_high_pct'] as num?)?.toDouble(),
    range52wPosition: (j['range_52w_position'] as num?)?.toDouble(),
    personalCeiling: (j['personal_ceiling'] as num?)?.toDouble(),
  );
}

class AllocationGap {
  AllocationGap({
    required this.category,
    required this.targetPct,
    required this.currentPct,
    required this.gapPct,
    required this.targetValue,
    required this.currentValue,
    required this.gapValue,
    required this.action,
  });

  final String category;
  final double targetPct;
  final double currentPct;
  final double gapPct;
  final double targetValue;
  final double currentValue;
  final double gapValue;
  final String action;

  bool get isBelowTarget => gapPct > 0;

  factory AllocationGap.fromJson(Map<String, dynamic> j) => AllocationGap(
    category: j['category'] as String? ?? '',
    targetPct: (j['target_pct'] as num?)?.toDouble() ?? 0,
    currentPct: (j['current_pct'] as num?)?.toDouble() ?? 0,
    gapPct: (j['gap_pct'] as num?)?.toDouble() ?? 0,
    targetValue: (j['target_value'] as num?)?.toDouble() ?? 0,
    currentValue: (j['current_value'] as num?)?.toDouble() ?? 0,
    gapValue: (j['gap_value'] as num?)?.toDouble() ?? 0,
    action: j['action'] as String? ?? '',
  );
}

class RebalanceTarget {
  RebalanceTarget({
    required this.ticker,
    required this.name,
    required this.category,
    required this.score,
    required this.verdict,
  });

  final String ticker;
  final String? name;
  final String category;
  final double score;
  final String verdict;

  factory RebalanceTarget.fromJson(Map<String, dynamic> j) => RebalanceTarget(
    ticker: j['ticker'] as String,
    name: j['name'] as String?,
    category: j['category'] as String? ?? '',
    score: (j['score'] as num?)?.toDouble() ?? 0,
    verdict: j['verdict'] as String? ?? '',
  );
}

class RebalanceItem {
  RebalanceItem({
    required this.ticker,
    required this.name,
    required this.category,
    required this.verdict,
    required this.action,
    required this.currentValue,
    required this.quantity,
    required this.pnlPct,
    required this.reasons,
    required this.reallocateTo,
    required this.requiresTaxReview,
  });

  final String ticker;
  final String? name;
  final String category;
  final String verdict;
  final String action;
  final double? currentValue;
  final double? quantity;
  final double? pnlPct;
  final List<String> reasons;
  final RebalanceTarget? reallocateTo;
  final bool requiresTaxReview;

  factory RebalanceItem.fromJson(Map<String, dynamic> j) => RebalanceItem(
    ticker: j['ticker'] as String,
    name: j['name'] as String?,
    category: j['category'] as String? ?? '',
    verdict: j['verdict'] as String? ?? '',
    action: j['action'] as String? ?? 'manter',
    currentValue: (j['current_value'] as num?)?.toDouble(),
    quantity: (j['quantity'] as num?)?.toDouble(),
    pnlPct: (j['pnl_pct'] as num?)?.toDouble(),
    reasons: (j['reasons'] as List? ?? const [])
        .map((e) => e as String)
        .toList(),
    reallocateTo: j['realocar_para'] != null
        ? RebalanceTarget.fromJson(j['realocar_para'] as Map<String, dynamic>)
        : null,
    requiresTaxReview: j['requires_tax_review'] as bool? ?? false,
  );
}

class RebalanceSuggestions {
  RebalanceSuggestions({
    required this.allocationGaps,
    required this.items,
    required this.taxDisclaimer,
  });

  final List<AllocationGap> allocationGaps;
  final List<RebalanceItem> items;
  final String? taxDisclaimer;

  AllocationGap? get biggestGap {
    if (allocationGaps.isEmpty) return null;
    final sorted = [...allocationGaps]
      ..sort((a, b) => b.gapPct.abs().compareTo(a.gapPct.abs()));
    return sorted.first;
  }

  factory RebalanceSuggestions.fromJson(Map<String, dynamic> j) =>
      RebalanceSuggestions(
        allocationGaps: (j['allocation_gaps'] as List? ?? const [])
            .map((e) => AllocationGap.fromJson(e as Map<String, dynamic>))
            .toList(),
        items: (j['items'] as List? ?? const [])
            .map((e) => RebalanceItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        taxDisclaimer: j['tax_disclaimer'] as String?,
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
    required this.asOf,
    required this.dropFromHighPct,
    required this.verdict,
    required this.label,
    required this.fairLow,
    required this.fairHigh,
    required this.marginOfSafety,
    required this.topReason,
  });

  final String symbol;
  final String? name;
  final double? price;
  final double? asOf;
  final double dropFromHighPct;
  final String verdict;
  final String label;
  final double? fairLow;
  final double? fairHigh;
  final double? marginOfSafety;
  final String topReason;

  factory DipScanItem.fromJson(Map<String, dynamic> j) => DipScanItem(
    symbol: j['symbol'] as String,
    name: j['name'] as String?,
    price: (j['price'] as num?)?.toDouble(),
    asOf: (j['as_of'] as num?)?.toDouble(),
    dropFromHighPct: (j['drop_from_52w_high_pct'] as num?)?.toDouble() ?? 0,
    verdict: j['verdict'] as String? ?? '',
    label: j['label'] as String? ?? '',
    fairLow: (j['fair_low'] as num?)?.toDouble(),
    fairHigh: (j['fair_high'] as num?)?.toDouble(),
    marginOfSafety: (j['margin_of_safety'] as num?)?.toDouble(),
    topReason: j['top_reason'] as String? ?? '',
  );
}

class Falsifier {
  Falsifier({
    required this.metric,
    required this.condition,
    required this.becomesLabel,
    required this.current,
    required this.threshold,
    this.kind = 'gatilho',
  });

  final String metric;
  final String condition;
  final String becomesLabel;
  final double current;
  final double threshold;

  final String kind;

  bool get isPremise => kind == 'premissa';

  factory Falsifier.fromJson(Map<String, dynamic> j) => Falsifier(
    metric: j['metric'] as String? ?? '',
    condition: j['condition'] as String? ?? '',
    becomesLabel: j['becomes_label'] as String? ?? '',
    current: (j['current'] as num?)?.toDouble() ?? 0,
    threshold: (j['threshold'] as num?)?.toDouble() ?? 0,
    kind: j['kind'] as String? ?? 'gatilho',
  );
}

class FairMethod {
  FairMethod({
    required this.method,
    required this.input,
    required this.status,
    required this.note,
    this.value,
    this.role = '',
  });

  final String method;
  final String input;
  final String status;
  final String note;
  final double? value;

  final String role;

  bool get applies => status == 'ok' || status == 'destoa_dos_demais';

  factory FairMethod.fromJson(Map<String, dynamic> j) => FairMethod(
    method: j['method'] as String? ?? '',
    input: j['input'] as String? ?? '',
    status: j['status'] as String? ?? '',
    note: j['note'] as String? ?? '',
    value: (j['value'] as num?)?.toDouble(),
    role: j['role'] as String? ?? '',
  );
}

class FairConfirmation {
  FairConfirmation({required this.method, this.value, this.agreement = ''});

  final String method;
  final double? value;
  final String agreement;

  factory FairConfirmation.fromJson(Map<String, dynamic> j) => FairConfirmation(
    method: j['method'] as String? ?? '',
    value: (j['value'] as num?)?.toDouble(),
    agreement: j['agreement'] as String? ?? '',
  );
}

class FairIndicator {
  FairIndicator({required this.kind, this.value, this.passes, this.desiredYield});

  final String kind;
  final double? value;
  final bool? passes;
  final double? desiredYield;

  factory FairIndicator.fromJson(Map<String, dynamic> j) => FairIndicator(
    kind: j['kind'] as String? ?? '',
    value: (j['value'] as num?)?.toDouble(),
    passes: j['passes'] as bool?,
    desiredYield: (j['desired_yield'] as num?)?.toDouble(),
  );
}

class AssetAnalysis {
  AssetAnalysis({
    required this.symbol,
    required this.name,
    required this.assetType,
    required this.sector,
    required this.price,
    this.asOf,
    required this.graham,
    required this.principalValue,
    this.fairLow,
    this.fairHigh,
    required this.marginOfSafety,
    this.independentInputs = 0,
    this.bandQuality = 'sem_faixa',
    this.bandPosition,
    this.methods = const [],
    this.basis = 'band',
    this.confidenceLabel = 'baixa',
    this.dataYears = 0,
    this.dividendYield,
    required this.rsi14,
    required this.trend,
    this.trendBasis,
    required this.verdict,
    required this.label,
    required this.reasons,
    this.falsifiers = const [],
    this.fundamentals = const {},
    this.principal,
    this.qualityReasons = const [],
    this.confirmation,
    this.premises = const {},
    this.indicators = const [],
    this.personalCeiling,
  });

  final String symbol;
  final String? name;
  final String assetType;
  final String? sector;
  final double? price;

  final double? asOf;

  final double? graham;
  final double? principalValue;

  final double? fairLow;
  final double? fairHigh;
  final double? marginOfSafety;


  final int independentInputs;

  final String bandQuality;
  final double? bandPosition;

  final List<FairMethod> methods;

  final String basis;
  final String confidenceLabel;

  final int dataYears;

  final double? dividendYield;

  final double? rsi14;
  final String trend;

  final String? trendBasis;
  final String verdict;
  final String label;
  final List<String> reasons;

  final List<Falsifier> falsifiers;
  final Map<String, double?> fundamentals;

  final String? principal;
  final List<String> qualityReasons;
  final FairConfirmation? confirmation;
  final Map<String, dynamic> premises;
  final List<FairIndicator> indicators;
  final double? personalCeiling;

  double? premise(String key) => (premises[key] as num?)?.toDouble();

  FairIndicator? indicator(String kind) {
    for (final i in indicators) {
      if (i.kind == kind) return i;
    }
    return null;
  }

  factory AssetAnalysis.fromJson(Map<String, dynamic> j) {
    final fp = j['fair_price'] as Map<String, dynamic>;
    final tech = j['technical'] as Map<String, dynamic>;
    final dec = j['decision'] as Map<String, dynamic>;
    final fund = (j['fundamentals'] as Map<String, dynamic>?) ?? {};
    return AssetAnalysis(
      symbol: j['symbol'] as String,
      name: j['name'] as String?,
      assetType: j['asset_type'] as String? ?? 'br_stock',
      sector: j['sector'] as String?,
      price: (j['price'] as num?)?.toDouble(),
      asOf: (j['as_of'] as num?)?.toDouble(),
      graham: (fp['graham'] as num?)?.toDouble(),
      principalValue: (fp['principal_value'] as num?)?.toDouble(),
      fairLow: (fp['fair_low'] as num?)?.toDouble(),
      fairHigh: (fp['fair_high'] as num?)?.toDouble(),
      marginOfSafety: (fp['margin_of_safety'] as num?)?.toDouble(),
      independentInputs: (fp['independent_inputs'] as num?)?.toInt() ?? 0,
      bandQuality: fp['band_quality'] as String? ?? 'sem_faixa',
      bandPosition: (fp['band_position'] as num?)?.toDouble(),
      methods: ((fp['methods'] as List?) ?? const [])
          .map((e) => FairMethod.fromJson(e as Map<String, dynamic>))
          .toList(),
      basis: dec['basis'] as String? ?? 'band',
      confidenceLabel: dec['confidence_label'] as String? ?? 'baixa',
      dataYears: (fp['data_years'] as num?)?.toInt() ?? 0,
      dividendYield: (fp['dy_12m'] as num?)?.toDouble(),
      rsi14: (tech['rsi_14'] as num?)?.toDouble(),
      trend: tech['trend'] as String? ?? 'unknown',
      trendBasis: tech['trend_basis'] as String?,
      verdict: dec['verdict'] as String? ?? '',
      label: dec['label'] as String? ?? '',
      reasons:
          (dec['reasons'] as List?)?.map((e) => e as String).toList() ?? [],
      falsifiers:
          (dec['falsifiers'] as List?)
              ?.map((e) => Falsifier.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      fundamentals: fund.map((k, v) => MapEntry(k, (v as num?)?.toDouble())),
      principal: fp['principal'] as String?,
      qualityReasons:
          (fp['quality_reasons'] as List?)?.map((e) => e as String).toList() ?? const [],
      confirmation: fp['confirmation'] is Map<String, dynamic>
          ? FairConfirmation.fromJson(fp['confirmation'] as Map<String, dynamic>)
          : null,
      premises: (fp['premises'] as Map<String, dynamic>?) ?? const {},
      indicators: ((fp['indicators'] as List?) ?? const [])
          .map((e) => FairIndicator.fromJson(e as Map<String, dynamic>))
          .toList(),
      personalCeiling: (fp['personal_ceiling'] as num?)?.toDouble(),
    );
  }
}

class ReferenceRates {
  ReferenceRates({
    required this.cdiAnnual,
    required this.selicAnnual,
    required this.ipcaAnnual,
  });

  final double cdiAnnual;
  final double selicAnnual;
  final double ipcaAnnual;

  factory ReferenceRates.fromJson(Map<String, dynamic> j) => ReferenceRates(
    cdiAnnual: (j['cdi_anual'] as num).toDouble(),
    selicAnnual: (j['selic_anual'] as num).toDouble(),
    ipcaAnnual: (j['ipca_anual'] as num).toDouble(),
  );
}

class FixedIncomeResult {
  FixedIncomeResult({
    required this.kind,
    required this.name,
    required this.investedValue,
    required this.netValue,
    required this.netReturn,
    required this.netAnnualRate,
    required this.bestOption,
  });

  final String kind;
  final String? name;
  final double investedValue;
  final double netValue;
  final double netReturn;
  final double netAnnualRate;
  final bool bestOption;

  factory FixedIncomeResult.fromJson(Map<String, dynamic> j) => FixedIncomeResult(
    kind: j['tipo'] as String,
    name: j['nome'] as String?,
    investedValue: (j['valor_investido'] as num).toDouble(),
    netValue: (j['valor_liquido'] as num).toDouble(),
    netReturn: (j['rendimento_liquido'] as num).toDouble(),
    netAnnualRate: (j['taxa_liquida_aa'] as num).toDouble(),
    bestOption: j['melhor_opcao'] as bool? ?? false,
  );
}

class Goal {
  Goal({
    required this.category,
    required this.targetPct,
    this.targetValue,
    this.declared = true,
  });

  final String category;
  final double targetPct;
  final double? targetValue;

  final bool declared;

  factory Goal.fromJson(Map<String, dynamic> j) => Goal(
    category: j['category'] as String,
    targetPct: (j['target_pct'] as num).toDouble(),
    targetValue: (j['target_value'] as num?)?.toDouble(),
    declared: j['declared'] as bool? ?? true,
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
    declared: declared,
  );
}

class SectorGoal {
  SectorGoal({required this.sector, required this.targetPct, this.declared = true});

  final String sector;
  final double targetPct;

  final bool declared;

  factory SectorGoal.fromJson(Map<String, dynamic> j) => SectorGoal(
    sector: j['sector'] as String,
    targetPct: (j['target_pct'] as num).toDouble(),
    declared: j['declared'] as bool? ?? true,
  );

  Map<String, dynamic> toJson() => {'sector': sector, 'target_pct': targetPct};

  SectorGoal copyWith({double? targetPct}) => SectorGoal(
    sector: sector,
    targetPct: targetPct ?? this.targetPct,
    declared: declared,
  );
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
    required this.passiveIncomeGoal,
    required this.desiredYieldStock,
    required this.desiredYieldFii,
    required this.desiredYieldBdr,
    required this.desiredYieldEtf,
    this.notifyPriceAlerts = true,
    this.opportunitiesFrequency = 'weekly',
    this.riskProfile = 'moderate',
    this.detailLevel = 'completo',
    this.reserveMonthsTarget,
    this.preferredCategories = const [],
    this.preferredSectors = const [],
    this.excludedTickers = const [],
  });

  final double? passiveIncomeGoal;
  final double desiredYieldStock;
  final double desiredYieldFii;
  final double desiredYieldBdr;
  final double desiredYieldEtf;
  final bool notifyPriceAlerts;
  final String opportunitiesFrequency;
  final String riskProfile;
  final String detailLevel;

  final int? reserveMonthsTarget;
  final List<String> preferredCategories;
  final List<String> preferredSectors;
  final List<String> excludedTickers;

  factory Preferences.fromJson(Map<String, dynamic> j) => Preferences(
    passiveIncomeGoal: (j['passive_income_goal'] as num?)?.toDouble(),
    desiredYieldStock: (j['desired_yield_stock'] as num).toDouble(),
    desiredYieldFii: (j['desired_yield_fii'] as num).toDouble(),
    desiredYieldBdr: (j['desired_yield_bdr'] as num?)?.toDouble() ?? 0.04,
    desiredYieldEtf: (j['desired_yield_etf'] as num?)?.toDouble() ?? 0.04,
    notifyPriceAlerts: j['notify_price_alerts'] as bool? ?? true,
    opportunitiesFrequency: j['opportunities_frequency'] as String? ?? 'weekly',
    riskProfile: j['risk_profile'] as String? ?? 'moderate',
    detailLevel: j['detail_level'] as String? ?? 'completo',
    reserveMonthsTarget: (j['reserve_months_target'] as num?)?.toInt(),
    preferredCategories:
        (j['preferred_categories'] as List?)?.cast<String>() ?? const [],
    preferredSectors:
        (j['preferred_sectors'] as List?)?.cast<String>() ?? const [],
    excludedTickers:
        (j['excluded_tickers'] as List?)?.cast<String>() ?? const [],
  );
}

class PortfolioHealth {
  PortfolioHealth({
    required this.score,
    required this.concentrationScore,
    required this.sectorConcentrationScore,
    required this.diversificationScore,
    required this.riskScore,
    required this.topPositionTicker,
    required this.topPositionPct,
    required this.topSector,
    required this.topSectorPct,
    required this.warnings,
  });

  final double score;
  final double concentrationScore;
  final double sectorConcentrationScore;
  final double diversificationScore;
  final double riskScore;
  final String? topPositionTicker;
  final double? topPositionPct;
  final String? topSector;
  final double? topSectorPct;
  final List<String> warnings;

  factory PortfolioHealth.fromJson(Map<String, dynamic> j) => PortfolioHealth(
    score: (j['score'] as num).toDouble(),
    concentrationScore: (j['concentration_score'] as num).toDouble(),
    sectorConcentrationScore: (j['sector_concentration_score'] as num)
        .toDouble(),
    diversificationScore: (j['diversification_score'] as num).toDouble(),
    riskScore: (j['risk_score'] as num).toDouble(),
    topPositionTicker: j['top_position_ticker'] as String?,
    topPositionPct: (j['top_position_pct'] as num?)?.toDouble(),
    topSector: j['top_sector'] as String?,
    topSectorPct: (j['top_sector_pct'] as num?)?.toDouble(),
    warnings: (j['warnings'] as List?)?.map((e) => e as String).toList() ?? [],
  );
}

class BenchmarkPoint {
  BenchmarkPoint({
    required this.date,
    required this.portfolioPct,
    required this.cdiPct,
    required this.ibovPct,
  });

  final String date;
  final double portfolioPct;
  final double cdiPct;
  final double? ibovPct;

  factory BenchmarkPoint.fromJson(Map<String, dynamic> j) => BenchmarkPoint(
    date: j['date'] as String,
    portfolioPct: (j['portfolio_pct'] as num).toDouble(),
    cdiPct: (j['cdi_pct'] as num).toDouble(),
    ibovPct: (j['ibov_pct'] as num?)?.toDouble(),
  );
}

class BenchmarkResponse {
  BenchmarkResponse({
    required this.points,
    required this.ibovAvailable,
    required this.portfolioReturnPct,
    required this.cdiReturnPct,
    required this.ibovReturnPct,
  });

  final List<BenchmarkPoint> points;
  final bool ibovAvailable;
  final double portfolioReturnPct;
  final double cdiReturnPct;
  final double? ibovReturnPct;

  factory BenchmarkResponse.fromJson(Map<String, dynamic> j) =>
      BenchmarkResponse(
        points: (j['points'] as List)
            .map((e) => BenchmarkPoint.fromJson(e as Map<String, dynamic>))
            .toList(),
        ibovAvailable: j['ibov_available'] as bool? ?? false,
        portfolioReturnPct:
            (j['portfolio_return_pct'] as num?)?.toDouble() ?? 0,
        cdiReturnPct: (j['cdi_return_pct'] as num?)?.toDouble() ?? 0,
        ibovReturnPct: (j['ibov_return_pct'] as num?)?.toDouble(),
      );
}

class CompareResponse {
  CompareResponse({required this.items, required this.errors});

  final List<AssetAnalysis> items;
  final List<String> errors;

  factory CompareResponse.fromJson(Map<String, dynamic> j) => CompareResponse(
    items: (j['items'] as List)
        .map((e) => AssetAnalysis.fromJson(e as Map<String, dynamic>))
        .toList(),
    errors: (j['errors'] as List?)?.map((e) => e as String).toList() ?? [],
  );
}

class PassiveIncomeMonth {
  PassiveIncomeMonth({
    required this.month,
    required this.portfolioValue,
    required this.portfolioValueLow,
    required this.portfolioValueHigh,
    required this.passiveIncomeMonthly,
    required this.passiveIncomeMonthlyLow,
    required this.passiveIncomeMonthlyHigh,
  });

  final String month;
  final double portfolioValue;
  final double portfolioValueLow;
  final double portfolioValueHigh;
  final double passiveIncomeMonthly;
  final double passiveIncomeMonthlyLow;
  final double passiveIncomeMonthlyHigh;

  factory PassiveIncomeMonth.fromJson(Map<String, dynamic> j) =>
      PassiveIncomeMonth(
        month: j['month'] as String,
        portfolioValue: (j['portfolio_value'] as num).toDouble(),
        portfolioValueLow: (j['portfolio_value_low'] as num).toDouble(),
        portfolioValueHigh: (j['portfolio_value_high'] as num).toDouble(),
        passiveIncomeMonthly: (j['passive_income_monthly'] as num).toDouble(),
        passiveIncomeMonthlyLow: (j['passive_income_monthly_low'] as num)
            .toDouble(),
        passiveIncomeMonthlyHigh: (j['passive_income_monthly_high'] as num)
            .toDouble(),
      );
}

class ProjectionScenario {
  ProjectionScenario({
    required this.code,
    required this.label,
    required this.rationale,
    required this.finalPassiveIncomeMonthly,
    required this.finalPortfolioValue,
    required this.monthsToTarget,
  });

  final String code;
  final String label;

  final String rationale;
  final double finalPassiveIncomeMonthly;
  final double finalPortfolioValue;
  final int? monthsToTarget;

  factory ProjectionScenario.fromJson(Map<String, dynamic> j) =>
      ProjectionScenario(
        code: j['code'] as String,
        label: j['label'] as String,
        rationale: j['rationale'] as String,
        finalPassiveIncomeMonthly: (j['final_passive_income_monthly'] as num)
            .toDouble(),
        finalPortfolioValue: (j['final_portfolio_value'] as num).toDouble(),
        monthsToTarget: (j['months_to_target'] as num?)?.toInt(),
      );
}

class ProjectionTarget {
  ProjectionTarget({
    required this.monthlyIncome,
    required this.earliestMonths,
    required this.expectedMonths,
    required this.latestMonths,
    required this.reachedInAllScenarios,
  });

  final double monthlyIncome;
  final int? earliestMonths;
  final int? expectedMonths;

  final int? latestMonths;
  final bool reachedInAllScenarios;

  factory ProjectionTarget.fromJson(Map<String, dynamic> j) => ProjectionTarget(
    monthlyIncome: (j['monthly_income'] as num).toDouble(),
    earliestMonths: (j['earliest_months'] as num?)?.toInt(),
    expectedMonths: (j['expected_months'] as num?)?.toInt(),
    latestMonths: (j['latest_months'] as num?)?.toInt(),
    reachedInAllScenarios: j['reached_in_all_scenarios'] as bool? ?? false,
  );
}

class PassiveIncomeProjection {
  PassiveIncomeProjection({
    required this.currentPortfolioValue,
    required this.currentPassiveIncomeMonthly,
    required this.projections,
    required this.scenarios,
    required this.target,
    required this.targetMonthlyIncome,
    required this.disclaimer,
  });

  final double currentPortfolioValue;
  final double currentPassiveIncomeMonthly;
  final List<PassiveIncomeMonth> projections;
  final List<ProjectionScenario> scenarios;
  final ProjectionTarget? target;
  final double? targetMonthlyIncome;
  final String disclaimer;

  factory PassiveIncomeProjection.fromJson(Map<String, dynamic> j) =>
      PassiveIncomeProjection(
        currentPortfolioValue: (j['current_portfolio_value'] as num).toDouble(),
        currentPassiveIncomeMonthly:
            (j['current_passive_income_monthly'] as num).toDouble(),
        projections: (j['projections'] as List)
            .map((e) => PassiveIncomeMonth.fromJson(e as Map<String, dynamic>))
            .toList(),
        scenarios: ((j['scenarios'] as List?) ?? const [])
            .map((e) => ProjectionScenario.fromJson(e as Map<String, dynamic>))
            .toList(),
        target: j['target'] == null
            ? null
            : ProjectionTarget.fromJson(j['target'] as Map<String, dynamic>),
        targetMonthlyIncome: (j['target_monthly_income'] as num?)?.toDouble(),
        disclaimer: j['disclaimer'] as String? ?? '',
      );
}

class FixedIncomePosition {
  FixedIncomePosition({
    required this.id,
    required this.name,
    required this.kind,
    required this.investedValue,
    required this.rate,
    required this.rateKind,
    required this.cdiPercent,
    required this.appliedOn,
    required this.maturity,
    required this.liquidity,
    required this.irExempt,
    required this.hidden,
    required this.currentValue,
    required this.accruedReturn,
    required this.returnPct,
    required this.monthsElapsed,
    required this.effectiveAnnualRatePct,
    required this.equivalentYieldPct,
    required this.valueAtMaturity,
    required this.daysToMaturity,
    required this.maturingSoon,
  });

  final int id;
  final String name;
  final String kind;
  final double investedValue;
  final double rate;
  final String rateKind;
  final double? cdiPercent;
  final String appliedOn;
  final String? maturity;
  final String liquidity;
  final bool? irExempt;
  final bool hidden;

  final double currentValue;
  final double accruedReturn;
  final double returnPct;
  final double monthsElapsed;
  final double effectiveAnnualRatePct;
  final double equivalentYieldPct;

  final double? valueAtMaturity;
  final int? daysToMaturity;
  final bool maturingSoon;

  factory FixedIncomePosition.fromJson(Map<String, dynamic> j) =>
      FixedIncomePosition(
        id: j['id'] as int,
        name: j['nome'] as String,
        kind: j['tipo'] as String,
        investedValue: (j['valor_investido'] as num).toDouble(),
        rate: (j['taxa'] as num).toDouble(),
        rateKind: j['tipo_taxa'] as String? ?? 'pre_fixado',
        cdiPercent: (j['percentual_cdi'] as num?)?.toDouble(),
        appliedOn: j['data_aplicacao'] as String,
        maturity: j['vencimento'] as String?,
        liquidity: j['liquidez'] as String? ?? 'no_vencimento',
        irExempt: j['isento_ir'] as bool?,
        hidden: j['oculto'] as bool? ?? false,
        currentValue: (j['valor_atual'] as num).toDouble(),
        accruedReturn: (j['rendimento_acumulado'] as num).toDouble(),
        returnPct: (j['rendimento_pct'] as num).toDouble(),
        monthsElapsed: (j['meses_decorridos'] as num).toDouble(),
        effectiveAnnualRatePct: (j['taxa_anual_efetiva_pct'] as num).toDouble(),
        equivalentYieldPct: (j['yield_equivalente_pct'] as num).toDouble(),
        valueAtMaturity: (j['valor_no_vencimento'] as num?)?.toDouble(),
        daysToMaturity: j['dias_para_vencimento'] as int?,
        maturingSoon: j['vencimento_proximo'] as bool? ?? false,
      );
}

class FixedIncomeList {
  FixedIncomeList({
    required this.items,
    required this.totalInvested,
    required this.totalCurrent,
    required this.totalReturn,
    required this.returnPct,
    required this.averageAnnualRate,
    required this.cdiReference,
    required this.ratesOrigin,
  });

  final List<FixedIncomePosition> items;
  final double totalInvested;
  final double totalCurrent;
  final double totalReturn;
  final double returnPct;
  final double averageAnnualRate;
  final double cdiReference;
  final String ratesOrigin;

  List<FixedIncomePosition> get visible =>
      items.where((i) => !i.hidden).toList(growable: false);

  factory FixedIncomeList.fromJson(Map<String, dynamic> j) => FixedIncomeList(
    items: (j['items'] as List)
        .map((e) => FixedIncomePosition.fromJson(e as Map<String, dynamic>))
        .toList(),
    totalInvested: (j['total_investido'] as num).toDouble(),
    totalCurrent: (j['total_atual'] as num).toDouble(),
    totalReturn: (j['total_rendimento'] as num).toDouble(),
    returnPct: (j['rendimento_pct'] as num).toDouble(),
    averageAnnualRate: (j['taxa_media_aa'] as num).toDouble(),
    cdiReference: (j['cdi_referencia'] as num).toDouble(),
    ratesOrigin: j['fonte_taxas'] as String? ?? 'estimativa',
  );
}

class QuickInvestAllocation {
  QuickInvestAllocation({
    required this.ticker,
    required this.name,
    required this.category,
    required this.sector,
    required this.currentPrice,
    required this.suggestedQuantity,
    required this.suggestedInvestment,
    required this.rationale,
    required this.score,
    required this.dividendYield,
  });

  final String ticker;
  final String? name;
  final String category;
  final String? sector;
  final double? currentPrice;
  final int? suggestedQuantity;
  final double? suggestedInvestment;
  final String rationale;
  final double? score;
  final double? dividendYield;

  factory QuickInvestAllocation.fromJson(Map<String, dynamic> j) =>
      QuickInvestAllocation(
        ticker: j['ticker'] as String,
        name: j['name'] as String?,
        category: j['category'] as String? ?? '',
        sector: j['sector'] as String?,
        currentPrice: (j['current_price'] as num?)?.toDouble(),
        suggestedQuantity: (j['suggested_quantity'] as num?)?.toInt(),
        suggestedInvestment: (j['suggested_investment'] as num?)?.toDouble(),
        rationale: j['rationale'] as String? ?? '',
        score: (j['score'] as num?)?.toDouble(),
        dividendYield: (j['dividend_yield'] as num?)?.toDouble(),
      );
}

class AffirmationMode {
  AffirmationMode({required this.disclaimer, required this.prescriptive});

  final String disclaimer;
  final bool prescriptive;

  factory AffirmationMode.fromJson(Map<String, dynamic> j) => AffirmationMode(
    disclaimer: j['disclaimer'] as String? ?? '',
    prescriptive: j['prescriptive'] as bool? ?? false,
  );
}

class QuickInvestFixedIncome {
  QuickInvestFixedIncome({
    required this.amount,
    required this.referenceMonthlyPct,
    required this.referenceSource,
    required this.rationale,
  });

  final double? amount;

  final double? referenceMonthlyPct;
  final String referenceSource;
  final String rationale;

  factory QuickInvestFixedIncome.fromJson(Map<String, dynamic> j) =>
      QuickInvestFixedIncome(
        amount: (j['amount'] as num?)?.toDouble(),
        referenceMonthlyPct: (j['reference_monthly_pct'] as num?)?.toDouble(),
        referenceSource: j['reference_source'] as String? ?? 'estimativa',
        rationale: j['rationale'] as String? ?? '',
      );
}

class QuickInvestUnallocated {
  QuickInvestUnallocated({required this.value, required this.reason});

  final double? value;
  final String reason;

  factory QuickInvestUnallocated.fromJson(Map<String, dynamic> j) =>
      QuickInvestUnallocated(
        value: (j['value'] as num?)?.toDouble(),
        reason: j['reason'] as String? ?? '',
      );
}

class QuickInvestResult {
  QuickInvestResult({
    required this.totalCash,
    required this.allocatedCash,
    required this.remainingCash,
    required this.allocations,
    required this.summary,
    required this.affirmation,
    this.basis = 'goals',
    this.fixedIncome,
    this.unallocated = const [],
  });

  final double? totalCash;
  final double? allocatedCash;
  final double? remainingCash;
  final List<QuickInvestAllocation> allocations;
  final String summary;
  final AffirmationMode? affirmation;

  final String basis;

  final QuickInvestFixedIncome? fixedIncome;

  final List<QuickInvestUnallocated> unallocated;

  bool get hasDestination => allocations.isNotEmpty || fixedIncome != null;

  factory QuickInvestResult.fromJson(Map<String, dynamic> j) =>
      QuickInvestResult(
        totalCash: (j['total_cash'] as num?)?.toDouble(),
        allocatedCash: (j['allocated_cash'] as num?)?.toDouble(),
        remainingCash: (j['remaining_cash'] as num?)?.toDouble(),
        allocations: (j['allocations'] as List? ?? const [])
            .map(
              (e) => QuickInvestAllocation.fromJson(e as Map<String, dynamic>),
            )
            .toList(),
        summary: j['summary'] as String? ?? '',
        affirmation: j['affirmation'] != null
            ? AffirmationMode.fromJson(j['affirmation'] as Map<String, dynamic>)
            : null,
        basis: j['basis'] as String? ?? 'goals',
        fixedIncome: j['fixed_income'] != null
            ? QuickInvestFixedIncome.fromJson(
                j['fixed_income'] as Map<String, dynamic>,
              )
            : null,
        unallocated: (j['unallocated'] as List? ?? const [])
            .map(
              (e) => QuickInvestUnallocated.fromJson(e as Map<String, dynamic>),
            )
            .toList(),
      );
}

class ReferralStatus {
  ReferralStatus({
    required this.code,
    required this.rewardDays,
    required this.maxCreditedDays,
    required this.attributed,
    required this.qualified,
    required this.pending,
    required this.daysEarned,
  });

  final String code;
  final int rewardDays;
  final int maxCreditedDays;
  final int attributed;
  final int qualified;
  final int pending;
  final int daysEarned;

  factory ReferralStatus.fromJson(Map<String, dynamic> j) => ReferralStatus(
    code: j['code'] as String,
    rewardDays: (j['reward_days'] as num?)?.toInt() ?? 0,
    maxCreditedDays: (j['max_credited_days'] as num?)?.toInt() ?? 0,
    attributed: (j['attributed'] as num?)?.toInt() ?? 0,
    qualified: (j['qualified'] as num?)?.toInt() ?? 0,
    pending: (j['pending'] as num?)?.toInt() ?? 0,
    daysEarned: (j['days_earned'] as num?)?.toInt() ?? 0,
  );
}

class IncomeOption {
  IncomeOption({
    required this.kind,
    required this.label,
    required this.ticker,
    required this.netIncomeYieldPct,
    required this.incomeBasis,
    required this.hasUpside,
    required this.liquidity,
    required this.taxNote,
    required this.riskNote,
    required this.monthlyIncomeEstimate,
  });

  final String kind;
  final String label;
  final String? ticker;
  final double netIncomeYieldPct;
  final String incomeBasis;
  final bool hasUpside;
  final String liquidity;
  final String taxNote;
  final String riskNote;
  final double monthlyIncomeEstimate;

  factory IncomeOption.fromJson(Map<String, dynamic> j) => IncomeOption(
    kind: j['kind'] as String? ?? '',
    label: j['label'] as String? ?? '',
    ticker: j['ticker'] as String?,
    netIncomeYieldPct: (j['net_income_yield_pct'] as num?)?.toDouble() ?? 0,
    incomeBasis: j['income_basis'] as String? ?? '',
    hasUpside: j['has_upside'] as bool? ?? false,
    liquidity: j['liquidity'] as String? ?? '',
    taxNote: j['tax_note'] as String? ?? '',
    riskNote: j['risk_note'] as String? ?? '',
    monthlyIncomeEstimate:
        (j['monthly_income_estimate'] as num?)?.toDouble() ?? 0,
  );
}

class IncomeCompare {
  IncomeCompare({
    required this.amount,
    required this.horizonMonths,
    required this.cdiAnnual,
    required this.fixedIncome,
    required this.assets,
    required this.bestIncomeOption,
    required this.verdict,
    required this.disclaimer,
  });

  final double amount;
  final int horizonMonths;
  final double cdiAnnual;
  final List<IncomeOption> fixedIncome;
  final List<IncomeOption> assets;
  final IncomeOption? bestIncomeOption;
  final String verdict;
  final String disclaimer;

  static List<IncomeOption> _list(dynamic bruto) =>
      ((bruto as List?) ?? const [])
          .map((e) => IncomeOption.fromJson(e as Map<String, dynamic>))
          .toList();

  factory IncomeCompare.fromJson(Map<String, dynamic> j) => IncomeCompare(
    amount: (j['amount'] as num?)?.toDouble() ?? 0,
    horizonMonths: (j['horizon_months'] as num?)?.toInt() ?? 12,
    cdiAnnual: (j['cdi_anual'] as num?)?.toDouble() ?? 0,
    fixedIncome: _list(j['fixed_income']),
    assets: _list(j['assets']),
    bestIncomeOption: j['best_income_option'] == null
        ? null
        : IncomeOption.fromJson(
            j['best_income_option'] as Map<String, dynamic>,
          ),
    verdict: j['verdict'] as String? ?? '',
    disclaimer: j['disclaimer'] as String? ?? '',
  );
}

class SearchHit {
  SearchHit({
    required this.kind,
    required this.title,
    required this.subtitle,
    required this.ref,
  });

  final String kind;
  final String title;
  final String subtitle;
  final String ref;

  factory SearchHit.fromJson(Map<String, dynamic> j) => SearchHit(
    kind: j['kind'] as String? ?? '',
    title: j['title'] as String? ?? '',
    subtitle: j['subtitle'] as String? ?? '',
    ref: j['ref'] as String? ?? '',
  );
}

class SearchGroup {
  SearchGroup({required this.label, required this.items});

  final String label;
  final List<SearchHit> items;

  factory SearchGroup.fromJson(Map<String, dynamic> j) => SearchGroup(
    label: j['label'] as String? ?? '',
    items: ((j['items'] as List?) ?? const [])
        .map((e) => SearchHit.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class SearchResults {
  SearchResults({required this.groups, required this.total});

  final List<SearchGroup> groups;
  final int total;

  factory SearchResults.fromJson(Map<String, dynamic> j) => SearchResults(
    groups: ((j['groups'] as List?) ?? const [])
        .map((e) => SearchGroup.fromJson(e as Map<String, dynamic>))
        .toList(),
    total: (j['total'] as num?)?.toInt() ?? 0,
  );
}

class LedgerEntry {
  LedgerEntry({
    required this.id,
    required this.kind,
    required this.symbol,
    required this.tradedOn,
    this.quantity = 0,
    this.price = 0,
    this.fees = 0,
    this.ratioFrom = 1,
    this.ratioTo = 1,
    this.amount = 0,
    this.note,
  });

  final int? id;
  final String kind;
  final String symbol;
  final String tradedOn;
  final double quantity;
  final double price;
  final double fees;
  final double ratioFrom;
  final double ratioTo;
  final double amount;
  final String? note;

  bool get hasQuantity => const {
    'buy',
    'sell',
    'bonus',
    'transfer_in',
    'transfer_out',
  }.contains(kind);

  bool get hasPrice => kind == 'buy' || kind == 'sell';

  double get grossValue => quantity * price;

  factory LedgerEntry.fromJson(Map<String, dynamic> j) => LedgerEntry(
    id: (j['id'] as num?)?.toInt(),
    kind: j['kind'] as String? ?? 'buy',
    symbol: j['symbol'] as String? ?? '',
    tradedOn: j['traded_on'] as String? ?? '',
    quantity: (j['quantity'] as num?)?.toDouble() ?? 0,
    price: (j['price'] as num?)?.toDouble() ?? 0,
    fees: (j['fees'] as num?)?.toDouble() ?? 0,
    ratioFrom: (j['ratio_from'] as num?)?.toDouble() ?? 1,
    ratioTo: (j['ratio_to'] as num?)?.toDouble() ?? 1,
    amount: (j['amount'] as num?)?.toDouble() ?? 0,
    note: j['note'] as String?,
  );
}

class LedgerPage {
  LedgerPage({
    required this.items,
    required this.count,
    this.nextCursor,
    this.hasMore = false,
  });

  final List<LedgerEntry> items;
  final int count;
  final String? nextCursor;
  final bool hasMore;

  factory LedgerPage.fromJson(Map<String, dynamic> j) => LedgerPage(
    items: ((j['items'] as List?) ?? const [])
        .map((e) => LedgerEntry.fromJson(e as Map<String, dynamic>))
        .toList(),
    count: (j['count'] as num?)?.toInt() ?? 0,
    nextCursor: j['next_cursor'] as String?,
    hasMore: j['has_more'] as bool? ?? false,
  );
}

class DividendReceived {
  DividendReceived({
    required this.id,
    required this.ticker,
    required this.paidAt,
    required this.amount,
    this.kind = 'dividendo',
    this.note,
  });

  final int id;
  final String ticker;
  final String paidAt;
  final double amount;
  final String kind;
  final String? note;

  factory DividendReceived.fromJson(Map<String, dynamic> j) => DividendReceived(
    id: (j['id'] as num?)?.toInt() ?? 0,
    ticker: j['ticker'] as String? ?? '',
    paidAt: j['paid_at'] as String? ?? '',
    amount: (j['amount'] as num?)?.toDouble() ?? 0,
    kind: j['kind'] as String? ?? 'dividendo',
    note: j['note'] as String?,
  );
}

class DividendMonth {
  DividendMonth({required this.month, required this.total, required this.count});

  final String month;
  final double total;
  final int count;

  factory DividendMonth.fromJson(Map<String, dynamic> j) => DividendMonth(
    month: j['month'] as String? ?? '',
    total: (j['total'] as num?)?.toDouble() ?? 0,
    count: (j['count'] as num?)?.toInt() ?? 0,
  );
}

class DividendTickerTotal {
  DividendTickerTotal({required this.ticker, required this.total, required this.count});

  final String ticker;
  final double total;
  final int count;

  factory DividendTickerTotal.fromJson(Map<String, dynamic> j) => DividendTickerTotal(
    ticker: j['ticker'] as String? ?? '',
    total: (j['total'] as num?)?.toDouble() ?? 0,
    count: (j['count'] as num?)?.toInt() ?? 0,
  );
}

class DividendsReceived {
  DividendsReceived({
    required this.items,
    this.totalReceived = 0,
    this.receivedThisMonth = 0,
    this.receivedLast12m = 0,
    this.monthlyAverage12m = 0,
    this.byMonth = const [],
    this.byTicker = const [],
    this.estimatedMonthly,
    this.estimateAccuracyPct,
    this.totalCount = 0,
  });

  final List<DividendReceived> items;
  final double totalReceived;
  final double receivedThisMonth;
  final double receivedLast12m;
  final double monthlyAverage12m;
  final List<DividendMonth> byMonth;
  final List<DividendTickerTotal> byTicker;
  final double? estimatedMonthly;
  final double? estimateAccuracyPct;
  final int totalCount;

  factory DividendsReceived.fromJson(Map<String, dynamic> j) => DividendsReceived(
    items: ((j['items'] as List?) ?? const [])
        .map((e) => DividendReceived.fromJson(e as Map<String, dynamic>))
        .toList(),
    totalReceived: (j['total_received'] as num?)?.toDouble() ?? 0,
    receivedThisMonth: (j['received_this_month'] as num?)?.toDouble() ?? 0,
    receivedLast12m: (j['received_last_12m'] as num?)?.toDouble() ?? 0,
    monthlyAverage12m: (j['monthly_average_12m'] as num?)?.toDouble() ?? 0,
    byMonth: ((j['by_month'] as List?) ?? const [])
        .map((e) => DividendMonth.fromJson(e as Map<String, dynamic>))
        .toList(),
    byTicker: ((j['by_ticker'] as List?) ?? const [])
        .map((e) => DividendTickerTotal.fromJson(e as Map<String, dynamic>))
        .toList(),
    estimatedMonthly: (j['estimated_monthly'] as num?)?.toDouble(),
    estimateAccuracyPct: (j['estimate_accuracy_pct'] as num?)?.toDouble(),
    totalCount: (j['total_count'] as num?)?.toInt() ?? 0,
  );
}

class DividendSuggestion {
  DividendSuggestion({
    required this.ticker,
    required this.paidAt,
    required this.amount,
    this.quantityAtDate = 0,
    this.ratePerShare = 0,
    this.kind = 'dividendo',
    this.caveats = const [],
    this.quantityIsCurrent = false,
    this.exDate,
    this.entitlement = 'indeterminado',
  });

  final String ticker;
  final String paidAt;
  final double amount;
  final double quantityAtDate;
  final double ratePerShare;
  final String kind;
  final List<String> caveats;
  final bool quantityIsCurrent;
  final String? exDate;
  final String entitlement;

  bool get entitlementProven => entitlement == 'provado';

  factory DividendSuggestion.fromJson(Map<String, dynamic> j) => DividendSuggestion(
    ticker: j['ticker'] as String? ?? '',
    paidAt: j['paid_at'] as String? ?? '',
    amount: (j['amount'] as num?)?.toDouble() ?? 0,
    quantityAtDate: (j['quantity_at_date'] as num?)?.toDouble() ?? 0,
    ratePerShare: (j['rate_per_share'] as num?)?.toDouble() ?? 0,
    kind: j['kind'] as String? ?? 'dividendo',
    caveats: ((j['caveats'] as List?) ?? const []).map((e) => e.toString()).toList(),
    quantityIsCurrent: j['quantity_is_current'] as bool? ?? false,
    exDate: j['ex_date'] as String?,
    entitlement: j['entitlement'] as String? ?? 'indeterminado',
  );
}

class DividendPending {
  DividendPending({required this.items, this.note = '', this.count = 0});

  final List<DividendSuggestion> items;
  final String note;
  final int count;

  factory DividendPending.fromJson(Map<String, dynamic> j) => DividendPending(
    items: ((j['items'] as List?) ?? const [])
        .map((e) => DividendSuggestion.fromJson(e as Map<String, dynamic>))
        .toList(),
    note: j['note'] as String? ?? '',
    count: (j['count'] as num?)?.toInt() ?? 0,
  );
}

class AccountDeletionPolicy {
  AccountDeletionPolicy({
    required this.slaDays,
    required this.removes,
    required this.note,
    required this.confirmationPhrase,
  });

  final int slaDays;
  final List<String> removes;
  final String note;
  final String confirmationPhrase;

  factory AccountDeletionPolicy.fromJson(Map<String, dynamic> j) => AccountDeletionPolicy(
    slaDays: (j['sla_days'] as num?)?.toInt() ?? 0,
    removes: ((j['removes'] as List?) ?? const []).map((e) => e.toString()).toList(),
    note: j['note'] as String? ?? '',
    confirmationPhrase: j['confirmation_phrase'] as String? ?? 'EXCLUIR',
  );
}

class AccountExport {
  AccountExport({required this.bytes, required this.filename});

  final List<int> bytes;
  final String filename;
}

class OnboardingState {
  OnboardingState({
    required this.step,
    required this.totalSteps,
    required this.completed,
    required this.positions,
    required this.hasGoals,
    required this.reason,
  });

  final int step;
  final int totalSteps;
  final bool completed;
  final int positions;
  final bool hasGoals;
  final String reason;

  factory OnboardingState.fromJson(Map<String, dynamic> j) => OnboardingState(
    step: (j['step'] as num?)?.toInt() ?? 1,
    totalSteps: (j['total_steps'] as num?)?.toInt() ?? 3,
    completed: j['completed'] as bool? ?? false,
    positions: (j['positions'] as num?)?.toInt() ?? 0,
    hasGoals: j['has_goals'] as bool? ?? false,
    reason: j['reason'] as String? ?? '',
  );
}
