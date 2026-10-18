import 'models.dart';

class ImportIssue {
  ImportIssue({required this.line, required this.message, this.field, this.raw = ''});

  final int line;
  final String message;
  final String? field;
  final String raw;

  factory ImportIssue.fromJson(Map<String, dynamic> j) => ImportIssue(
    line: (j['line'] as num?)?.toInt() ?? 0,
    message: j['message'] as String? ?? '',
    field: j['field'] as String?,
    raw: j['raw'] as String? ?? '',
  );
}

class ImportRow {
  ImportRow({required this.line, required this.entry, this.duplicateOf});

  final int line;
  final LedgerEntry entry;
  final int? duplicateOf;

  bool get isDuplicate => duplicateOf != null;

  factory ImportRow.fromJson(Map<String, dynamic> j) => ImportRow(
    line: (j['line'] as num?)?.toInt() ?? 0,
    entry: LedgerEntry.fromJson({...j, 'id': null}),
    duplicateOf: (j['duplicate_of'] as num?)?.toInt(),
  );
}

class ImportPreview {
  ImportPreview({
    required this.format,
    required this.rows,
    required this.issues,
    required this.ok,
    required this.duplicates,
  });

  final String format;
  final List<ImportRow> rows;
  final List<ImportIssue> issues;
  final bool ok;
  final int duplicates;

  List<ImportRow> get fresh => rows.where((r) => !r.isDuplicate).toList();

  List<ImportRow> get repeated => rows.where((r) => r.isDuplicate).toList();

  factory ImportPreview.fromJson(Map<String, dynamic> j) => ImportPreview(
    format: j['format'] as String? ?? '',
    rows: ((j['rows'] as List?) ?? const [])
        .map((e) => ImportRow.fromJson(e as Map<String, dynamic>))
        .toList(),
    issues: ((j['issues'] as List?) ?? const [])
        .map((e) => ImportIssue.fromJson(e as Map<String, dynamic>))
        .toList(),
    ok: j['ok'] as bool? ?? false,
    duplicates: (j['duplicates'] as num?)?.toInt() ?? 0,
  );
}

class ImportResult {
  ImportResult({required this.imported, required this.skippedDuplicates});

  final int imported;
  final int skippedDuplicates;

  factory ImportResult.fromJson(Map<String, dynamic> j) => ImportResult(
    imported: (j['imported'] as num?)?.toInt() ?? 0,
    skippedDuplicates: (j['skipped_duplicates'] as num?)?.toInt() ?? 0,
  );
}

class B3Duplicate {
  B3Duplicate({required this.id, required this.day, this.quantity, this.price, this.amount});

  final int id;
  final String day;
  final double? quantity;
  final double? price;
  final double? amount;

  static B3Duplicate? fromJson(Object? raw) {
    if (raw is! Map<String, dynamic>) return null;
    return B3Duplicate(
      id: (raw['id'] as num?)?.toInt() ?? 0,
      day: raw['day'] as String? ?? '',
      quantity: (raw['quantity'] as num?)?.toDouble(),
      price: (raw['price'] as num?)?.toDouble(),
      amount: (raw['amount'] as num?)?.toDouble(),
    );
  }
}

class B3ImportRow {
  B3ImportRow({
    required this.line,
    required this.target,
    required this.kind,
    required this.symbol,
    required this.day,
    required this.quantity,
    required this.price,
    required this.amount,
    this.settledOn,
    this.duplicate,
  });

  final int line;
  final String target;
  final String kind;
  final String symbol;
  final String day;
  final String? settledOn;
  final double quantity;
  final double price;
  final double amount;
  final B3Duplicate? duplicate;

  bool get isDividend => target == 'provento';

  bool get isDuplicate => duplicate != null;

  factory B3ImportRow.fromJson(Map<String, dynamic> j) => B3ImportRow(
    line: (j['line'] as num?)?.toInt() ?? 0,
    target: j['target'] as String? ?? 'operacao',
    kind: j['kind'] as String? ?? '',
    symbol: j['symbol'] as String? ?? '',
    day: j['day'] as String? ?? '',
    settledOn: j['settled_on'] as String?,
    quantity: (j['quantity'] as num?)?.toDouble() ?? 0,
    price: (j['price'] as num?)?.toDouble() ?? 0,
    amount: (j['amount'] as num?)?.toDouble() ?? 0,
    duplicate: B3Duplicate.fromJson(j['duplicate']),
  );
}

class B3ImportPreview {
  B3ImportPreview({
    required this.format,
    required this.rows,
    required this.issues,
    required this.warnings,
    required this.ok,
  });

  final String format;
  final List<B3ImportRow> rows;
  final List<ImportIssue> issues;
  final List<ImportIssue> warnings;
  final bool ok;

  static List<ImportIssue> _issues(Object? raw) => ((raw as List?) ?? const [])
      .map((e) => ImportIssue.fromJson(e as Map<String, dynamic>))
      .toList();

  factory B3ImportPreview.fromJson(Map<String, dynamic> j) => B3ImportPreview(
    format: j['format'] as String? ?? '',
    rows: ((j['rows'] as List?) ?? const [])
        .map((e) => B3ImportRow.fromJson(e as Map<String, dynamic>))
        .toList(),
    issues: _issues(j['issues']),
    warnings: _issues(j['warnings']),
    ok: j['ok'] as bool? ?? false,
  );
}

class B3ImportResult {
  B3ImportResult({
    required this.operations,
    required this.dividends,
    required this.skippedDuplicates,
  });

  final int operations;
  final int dividends;
  final int skippedDuplicates;

  factory B3ImportResult.fromJson(Map<String, dynamic> j) => B3ImportResult(
    operations: (j['operations'] as num?)?.toInt() ?? 0,
    dividends: (j['dividends'] as num?)?.toInt() ?? 0,
    skippedDuplicates: (j['skipped_duplicates'] as num?)?.toInt() ?? 0,
  );
}

class ReconciledPosition {
  ReconciledPosition({required this.quantity, required this.avgPrice});

  final double quantity;
  final double avgPrice;

  static ReconciledPosition? fromJson(Object? raw) {
    if (raw is! Map<String, dynamic>) return null;
    return ReconciledPosition(
      quantity: (raw['quantity'] as num?)?.toDouble() ?? 0,
      avgPrice: (raw['avg_price'] as num?)?.toDouble() ?? 0,
    );
  }
}

class ReconciliationDifference {
  ReconciliationDifference({
    required this.ticker,
    required this.reason,
    this.stored,
    this.projected,
  });

  final String ticker;
  final String reason;
  final ReconciledPosition? stored;
  final ReconciledPosition? projected;

  bool get positionWithoutLedger => reason == 'posicao_sem_razao';

  factory ReconciliationDifference.fromJson(Map<String, dynamic> j) => ReconciliationDifference(
    ticker: j['ticker'] as String? ?? '',
    reason: j['reason'] as String? ?? '',
    stored: ReconciledPosition.fromJson(j['stored']),
    projected: ReconciledPosition.fromJson(j['projected']),
  );
}

class Reconciliation {
  Reconciliation({
    required this.positions,
    required this.projected,
    required this.differences,
    required this.inSync,
  });

  final int positions;
  final int projected;
  final List<ReconciliationDifference> differences;
  final bool inSync;

  List<ReconciliationDifference> get withoutLedger =>
      differences.where((d) => d.positionWithoutLedger).toList();

  factory Reconciliation.fromJson(Map<String, dynamic> j) => Reconciliation(
    positions: (j['positions'] as num?)?.toInt() ?? 0,
    projected: (j['projected'] as num?)?.toInt() ?? 0,
    differences: ((j['differences'] as List?) ?? const [])
        .map((e) => ReconciliationDifference.fromJson(e as Map<String, dynamic>))
        .toList(),
    inSync: j['in_sync'] as bool? ?? false,
  );
}

class FollowedSuggestion {
  FollowedSuggestion({
    required this.id,
    required this.ticker,
    required this.source,
    required this.action,
    required this.quantity,
    required this.price,
    required this.followedOn,
    required this.invested,
    required this.daysHeld,
    this.scoreAtSuggestion,
    this.verdictAtSuggestion,
    this.entryId,
    this.currentValue,
    this.pnl,
    this.pnlPct,
    this.ibovPctSince,
    this.beatIbov,
  });

  final int id;
  final String ticker;
  final String source;
  final String action;
  final double quantity;
  final double price;
  final String followedOn;
  final double invested;
  final int daysHeld;
  final double? scoreAtSuggestion;
  final String? verdictAtSuggestion;
  final int? entryId;
  final double? currentValue;
  final double? pnl;
  final double? pnlPct;
  final double? ibovPctSince;
  final bool? beatIbov;

  factory FollowedSuggestion.fromJson(Map<String, dynamic> j) => FollowedSuggestion(
    id: (j['id'] as num).toInt(),
    ticker: j['ticker'] as String? ?? '',
    source: j['source'] as String? ?? '',
    action: j['action'] as String? ?? 'comprar',
    quantity: (j['quantity'] as num?)?.toDouble() ?? 0,
    price: (j['price'] as num?)?.toDouble() ?? 0,
    followedOn: j['followed_on'] as String? ?? '',
    invested: (j['invested'] as num?)?.toDouble() ?? 0,
    daysHeld: (j['days_held'] as num?)?.toInt() ?? 0,
    scoreAtSuggestion: (j['score_at_suggestion'] as num?)?.toDouble(),
    verdictAtSuggestion: j['verdict_at_suggestion'] as String?,
    entryId: (j['entry_id'] as num?)?.toInt(),
    currentValue: (j['current_value'] as num?)?.toDouble(),
    pnl: (j['pnl'] as num?)?.toDouble(),
    pnlPct: (j['pnl_pct'] as num?)?.toDouble(),
    ibovPctSince: (j['ibov_pct_since'] as num?)?.toDouble(),
    beatIbov: j['beat_ibov'] as bool?,
  );
}

class SuggestionOutcomeGroup {
  SuggestionOutcomeGroup({
    required this.source,
    required this.count,
    required this.invested,
    required this.pnlPct,
    this.ibovPct,
  });

  final String source;
  final int count;
  final double invested;
  final double pnlPct;
  final double? ibovPct;

  factory SuggestionOutcomeGroup.fromJson(Map<String, dynamic> j) => SuggestionOutcomeGroup(
    source: j['source'] as String? ?? '',
    count: (j['count'] as num?)?.toInt() ?? 0,
    invested: (j['invested'] as num?)?.toDouble() ?? 0,
    pnlPct: (j['pnl_pct'] as num?)?.toDouble() ?? 0,
    ibovPct: (j['ibov_pct'] as num?)?.toDouble(),
  );
}

class FollowedSuggestions {
  FollowedSuggestions({
    required this.items,
    required this.totalInvested,
    required this.totalCurrentValue,
    required this.totalPnl,
    required this.totalPnlPct,
    required this.bySource,
    required this.summary,
    required this.totalCount,
    this.ibovPctSamePeriod,
    this.beatIbov,
    this.nextCursor,
    this.hasMore = false,
  });

  final List<FollowedSuggestion> items;
  final double totalInvested;
  final double totalCurrentValue;
  final double totalPnl;
  final double totalPnlPct;
  final List<SuggestionOutcomeGroup> bySource;
  final String summary;
  final int totalCount;
  final double? ibovPctSamePeriod;
  final bool? beatIbov;
  final String? nextCursor;
  final bool hasMore;

  factory FollowedSuggestions.fromJson(Map<String, dynamic> j) => FollowedSuggestions(
    items: ((j['items'] as List?) ?? const [])
        .map((e) => FollowedSuggestion.fromJson(e as Map<String, dynamic>))
        .toList(),
    totalInvested: (j['total_invested'] as num?)?.toDouble() ?? 0,
    totalCurrentValue: (j['total_current_value'] as num?)?.toDouble() ?? 0,
    totalPnl: (j['total_pnl'] as num?)?.toDouble() ?? 0,
    totalPnlPct: (j['total_pnl_pct'] as num?)?.toDouble() ?? 0,
    bySource: ((j['by_source'] as List?) ?? const [])
        .map((e) => SuggestionOutcomeGroup.fromJson(e as Map<String, dynamic>))
        .toList(),
    summary: j['summary'] as String? ?? '',
    totalCount: (j['total_count'] as num?)?.toInt() ?? 0,
    ibovPctSamePeriod: (j['ibov_pct_same_period'] as num?)?.toDouble(),
    beatIbov: j['beat_ibov'] as bool?,
    nextCursor: j['next_cursor'] as String?,
    hasMore: j['has_more'] as bool? ?? false,
  );
}
