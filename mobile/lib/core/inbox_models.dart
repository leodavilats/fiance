class InboxItem {
  InboxItem({
    required this.id,
    required this.kind,
    required this.severity,
    required this.title,
    required this.detail,
    required this.createdAt,
    this.ticker,
    this.action,
    this.actionLabel,
    this.readAt,
  });

  final int id;
  final String kind;
  final String severity;
  final String title;
  final String detail;
  final String? ticker;
  final String? action;
  final String? actionLabel;
  final double createdAt;
  final double? readAt;

  bool get unread => readAt == null;

  DateTime get arrivedAt =>
      DateTime.fromMillisecondsSinceEpoch((createdAt * 1000).round());

  InboxItem markedRead() => InboxItem(
    id: id,
    kind: kind,
    severity: severity,
    title: title,
    detail: detail,
    createdAt: createdAt,
    ticker: ticker,
    action: action,
    actionLabel: actionLabel,
    readAt: readAt ?? DateTime.now().millisecondsSinceEpoch / 1000,
  );

  factory InboxItem.fromJson(Map<String, dynamic> j) => InboxItem(
    id: (j['id'] as num?)?.toInt() ?? 0,
    kind: j['kind'] as String? ?? '',
    severity: j['severity'] as String? ?? 'info',
    title: j['title'] as String? ?? '',
    detail: j['detail'] as String? ?? '',
    ticker: j['ticker'] as String?,
    action: j['action'] as String?,
    actionLabel: j['action_label'] as String?,
    createdAt: (j['created_at'] as num?)?.toDouble() ?? 0,
    readAt: (j['read_at'] as num?)?.toDouble(),
  );
}

class InboxPage {
  InboxPage({
    required this.items,
    required this.unread,
    this.nextCursor,
    this.hasMore = false,
  });

  final List<InboxItem> items;
  final int unread;
  final String? nextCursor;
  final bool hasMore;

  factory InboxPage.fromJson(Map<String, dynamic> j) => InboxPage(
    items: ((j['items'] as List?) ?? const [])
        .map((e) => InboxItem.fromJson(e as Map<String, dynamic>))
        .toList(),
    unread: (j['unread'] as num?)?.toInt() ?? 0,
    nextCursor: j['next_cursor'] as String?,
    hasMore: j['has_more'] as bool? ?? false,
  );
}
