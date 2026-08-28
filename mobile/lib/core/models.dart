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
    this.reasons = const [],
    this.confidence = 0,
    this.dataYears = 0,
    this.consensusMethods = 0,
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
  final List<String> reasons;
  final double confidence;
  final int dataYears;
  final int consensusMethods;
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
        reasons:
            (j['reasons'] as List?)?.map((e) => e as String).toList() ??
            const [],
        confidence: (j['confidence'] as num?)?.toDouble() ?? 0,
        dataYears: j['data_years'] as int? ?? 0,
        consensusMethods: j['consensus_methods'] as int? ?? 0,
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
    if (age == null) return 'cotacoes sem carimbo de tempo';
    if (age < 120) return 'cotacoes de agora';
    if (age < 3600) return 'cotacoes de ${(age / 60).round()} min atras';
    return 'cotacoes de ${(age / 3600).round()} h atras';
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
    required this.fairPrice,
    required this.marginOfSafety,
    required this.dividendYield,
    required this.verdict,
    required this.label,
    required this.sector,
    required this.score,
    this.confidence = 0,
    this.dataYears = 0,
    this.consensusMethods = 0,
    this.trendBasis = 'none',
    this.dataCompleteness = 1,
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
  final double confidence;
  final int dataYears;
  final int consensusMethods;
  final String trendBasis;
  final double dataCompleteness;

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
    confidence: (j['confidence'] as num?)?.toDouble() ?? 0,
    dataYears: j['data_years'] as int? ?? 0,
    consensusMethods: j['consensus_methods'] as int? ?? 0,
    trendBasis: j['trend_basis'] as String? ?? 'none',
    dataCompleteness: (j['data_completeness'] as num?)?.toDouble() ?? 1,
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
    required this.realocarPara,
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
  final RebalanceTarget? realocarPara;
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
    realocarPara: j['realocar_para'] != null
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

/// Uma condição verificável que muda o veredito.
///
/// Vem pronta do backend, derivada da mesma régua que produziu o veredito. Não
/// é texto editorial: por isso carrega o valor de hoje ao lado do limiar, para
/// a distância ser visível.
class Falsifier {
  Falsifier({
    required this.metric,
    required this.condition,
    required this.becomesLabel,
    required this.current,
    required this.threshold,
  });

  final String metric;
  final String condition;
  final String becomesLabel;
  final double current;
  final double threshold;

  factory Falsifier.fromJson(Map<String, dynamic> j) => Falsifier(
    metric: j['metric'] as String? ?? '',
    condition: j['condition'] as String? ?? '',
    becomesLabel: j['becomes_label'] as String? ?? '',
    current: (j['current'] as num?)?.toDouble() ?? 0,
    threshold: (j['threshold'] as num?)?.toDouble() ?? 0,
  );
}

class AssetAnalysis {
  AssetAnalysis({
    required this.symbol,
    required this.name,
    required this.assetType,
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
    this.falsifiers = const [],
    this.fundamentals = const {},
  });

  final String symbol;
  final String? name;
  final String assetType;
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

  /// O que faria a tese mudar. Lista vazia é resposta legítima: sem preço
  /// justo não há régua para ler ao contrário.
  final List<Falsifier> falsifiers;
  final Map<String, double?> fundamentals;

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
      falsifiers:
          (dec['falsifiers'] as List?)
              ?.map((e) => Falsifier.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      fundamentals: fund.map((k, v) => MapEntry(k, (v as num?)?.toDouble())),
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
    required this.passiveIncomeGoal,
    required this.desiredYieldStock,
    required this.desiredYieldFii,
    required this.desiredYieldBdr,
    required this.desiredYieldEtf,
    this.notifyPriceAlerts = true,
    this.opportunitiesFrequency = 'weekly',
    this.riskProfile = 'moderate',
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
  final List<String> preferredCategories;
  final List<String> preferredSectors;
  final List<String> excludedTickers;

  factory Preferences.fromJson(Map<String, dynamic> j) => Preferences(
    passiveIncomeGoal: (j['passive_income_goal'] as num?)?.toDouble(),
    desiredYieldStock: (j['desired_yield_stock'] as num).toDouble(),
    desiredYieldFii: (j['desired_yield_fii'] as num).toDouble(),
    desiredYieldBdr: (j['desired_yield_bdr'] as num).toDouble(),
    desiredYieldEtf: (j['desired_yield_etf'] as num?)?.toDouble() ?? 0.04,
    notifyPriceAlerts: j['notify_price_alerts'] as bool? ?? true,
    opportunitiesFrequency: j['opportunities_frequency'] as String? ?? 'weekly',
    riskProfile: j['risk_profile'] as String? ?? 'moderate',
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

  /// A premissa que gerou o número. Não é campo opcional de tela: um cenário
  /// sem a conta que o produziu é só um número maior ou menor.
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

  /// Nulo significa "não chega no horizonte projetado" — e isso é resposta,
  /// não falha. Omitir o cenário que não chega faria a meta parecer garantida.
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
    required this.nome,
    required this.tipo,
    required this.valorInvestido,
    required this.taxa,
    required this.tipoTaxa,
    required this.percentualCdi,
    required this.dataAplicacao,
    required this.vencimento,
    required this.liquidez,
    required this.isentoIr,
    required this.oculto,
    required this.valorAtual,
    required this.rendimentoAcumulado,
    required this.rendimentoPct,
    required this.mesesDecorridos,
    required this.taxaAnualEfetivaPct,
    required this.yieldEquivalentePct,
    required this.valorNoVencimento,
    required this.diasParaVencimento,
    required this.vencimentoProximo,
  });

  final int id;
  final String nome;
  final String tipo;
  final double valorInvestido;
  final double taxa;
  final String tipoTaxa;
  final double? percentualCdi;
  final String dataAplicacao;
  final String? vencimento;
  final String liquidez;
  final bool? isentoIr;
  final bool oculto;

  final double valorAtual;
  final double rendimentoAcumulado;
  final double rendimentoPct;
  final double mesesDecorridos;
  final double taxaAnualEfetivaPct;
  final double yieldEquivalentePct;

  final double? valorNoVencimento;
  final int? diasParaVencimento;
  final bool vencimentoProximo;

  factory FixedIncomePosition.fromJson(Map<String, dynamic> j) =>
      FixedIncomePosition(
        id: j['id'] as int,
        nome: j['nome'] as String,
        tipo: j['tipo'] as String,
        valorInvestido: (j['valor_investido'] as num).toDouble(),
        taxa: (j['taxa'] as num).toDouble(),
        tipoTaxa: j['tipo_taxa'] as String? ?? 'pre_fixado',
        percentualCdi: (j['percentual_cdi'] as num?)?.toDouble(),
        dataAplicacao: j['data_aplicacao'] as String,
        vencimento: j['vencimento'] as String?,
        liquidez: j['liquidez'] as String? ?? 'no_vencimento',
        isentoIr: j['isento_ir'] as bool?,
        oculto: j['oculto'] as bool? ?? false,
        valorAtual: (j['valor_atual'] as num).toDouble(),
        rendimentoAcumulado: (j['rendimento_acumulado'] as num).toDouble(),
        rendimentoPct: (j['rendimento_pct'] as num).toDouble(),
        mesesDecorridos: (j['meses_decorridos'] as num).toDouble(),
        taxaAnualEfetivaPct: (j['taxa_anual_efetiva_pct'] as num).toDouble(),
        yieldEquivalentePct: (j['yield_equivalente_pct'] as num).toDouble(),
        valorNoVencimento: (j['valor_no_vencimento'] as num?)?.toDouble(),
        diasParaVencimento: j['dias_para_vencimento'] as int?,
        vencimentoProximo: j['vencimento_proximo'] as bool? ?? false,
      );
}

class FixedIncomeList {
  FixedIncomeList({
    required this.items,
    required this.totalInvestido,
    required this.totalAtual,
    required this.totalRendimento,
    required this.rendimentoPct,
    required this.taxaMediaAa,
    required this.cdiReferencia,
    required this.fonteTaxas,
  });

  final List<FixedIncomePosition> items;
  final double totalInvestido;
  final double totalAtual;
  final double totalRendimento;
  final double rendimentoPct;
  final double taxaMediaAa;
  final double cdiReferencia;
  final String fonteTaxas;

  List<FixedIncomePosition> get visiveis =>
      items.where((i) => !i.oculto).toList(growable: false);

  factory FixedIncomeList.fromJson(Map<String, dynamic> j) => FixedIncomeList(
    items: (j['items'] as List)
        .map((e) => FixedIncomePosition.fromJson(e as Map<String, dynamic>))
        .toList(),
    totalInvestido: (j['total_investido'] as num).toDouble(),
    totalAtual: (j['total_atual'] as num).toDouble(),
    totalRendimento: (j['total_rendimento'] as num).toDouble(),
    rendimentoPct: (j['rendimento_pct'] as num).toDouble(),
    taxaMediaAa: (j['taxa_media_aa'] as num).toDouble(),
    cdiReferencia: (j['cdi_referencia'] as num).toDouble(),
    fonteTaxas: j['fonte_taxas'] as String? ?? 'estimativa',
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
  final double currentPrice;
  final int suggestedQuantity;
  final double suggestedInvestment;
  final String rationale;
  final double? score;
  final double? dividendYield;

  factory QuickInvestAllocation.fromJson(Map<String, dynamic> j) =>
      QuickInvestAllocation(
        ticker: j['ticker'] as String,
        name: j['name'] as String?,
        category: j['category'] as String? ?? '',
        sector: j['sector'] as String?,
        currentPrice: (j['current_price'] as num).toDouble(),
        suggestedQuantity: j['suggested_quantity'] as int,
        suggestedInvestment: (j['suggested_investment'] as num).toDouble(),
        rationale: j['rationale'] as String? ?? '',
        score: (j['score'] as num?)?.toDouble(),
        dividendYield: (j['dividend_yield'] as num?)?.toDouble(),
      );
}

class QuickInvestResult {
  QuickInvestResult({
    required this.totalCash,
    required this.allocatedCash,
    required this.remainingCash,
    required this.allocations,
    required this.summary,
  });

  final double totalCash;
  final double allocatedCash;
  final double remainingCash;
  final List<QuickInvestAllocation> allocations;
  final String summary;

  factory QuickInvestResult.fromJson(Map<String, dynamic> j) =>
      QuickInvestResult(
        totalCash: (j['total_cash'] as num).toDouble(),
        allocatedCash: (j['allocated_cash'] as num).toDouble(),
        remainingCash: (j['remaining_cash'] as num).toDouble(),
        allocations: (j['allocations'] as List)
            .map(
              (e) => QuickInvestAllocation.fromJson(e as Map<String, dynamic>),
            )
            .toList(),
        summary: j['summary'] as String? ?? '',
      );
}

/// O que a pessoa vê do programa de indicação.
///
/// Sem a lista de quem foi indicado, de propósito: quem clicou no link de
/// alguém não escolheu aparecer numa tela dessa pessoa. As contagens bastam.
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
