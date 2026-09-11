enum CashKind {
  income,
  expense;

  static CashKind fromJson(String v) =>
      v == 'income' ? CashKind.income : CashKind.expense;

  String get json => name;
}

enum DebtClass {
  expensive,
  manageable,
  noRate;

  static DebtClass fromJson(String? v) => switch (v) {
    'expensive' => DebtClass.expensive,
    'manageable' => DebtClass.manageable,
    _ => DebtClass.noRate,
  };
}

enum CascadeStepType {
  debt,
  reserve,
  contribution;

  static CascadeStepType fromJson(String? v) => switch (v) {
    'debt' => CascadeStepType.debt,
    'reserve' => CascadeStepType.reserve,
    _ => CascadeStepType.contribution,
  };
}

class CashEntry {
  CashEntry({
    required this.id,
    required this.kind,
    required this.category,
    required this.description,
    required this.amount,
    required this.dueOn,
    required this.paidOn,
    required this.derived,
  });

  final int id;
  final CashKind kind;
  final String category;
  final String description;
  final double amount;
  final String dueOn;
  final String? paidOn;

  final bool derived;

  bool get futura => paidOn == null;

  String get competencia => paidOn ?? dueOn;

  factory CashEntry.fromJson(Map<String, dynamic> j) => CashEntry(
    id: (j['id'] as num).toInt(),
    kind: CashKind.fromJson(j['kind'] as String),
    category: j['category'] as String? ?? '',
    description: j['description'] as String? ?? '',
    amount: (j['amount'] as num?)?.toDouble() ?? 0,
    dueOn: j['due_on'] as String? ?? '',
    paidOn: j['paid_on'] as String?,
    derived: j['derived'] as bool? ?? false,
  );
}

class CashDueEntry {
  CashDueEntry({
    required this.id,
    required this.category,
    required this.description,
    required this.amount,
    required this.dueOn,
  });

  final int? id;
  final String category;
  final String description;
  final double amount;
  final String dueOn;

  factory CashDueEntry.fromJson(Map<String, dynamic> j) => CashDueEntry(
    id: (j['id'] as num?)?.toInt(),
    category: j['category'] as String? ?? '',
    description: j['description'] as String? ?? '',
    amount: (j['amount'] as num?)?.toDouble() ?? 0,
    dueOn: j['due_on'] as String? ?? '',
  );
}

class CashEstimate {
  CashEstimate({
    required this.baseMonths,
    required this.expectedLow,
    required this.expectedHigh,
    required this.spentSoFar,
    required this.remainingLow,
    required this.remainingHigh,
  });

  final List<String> baseMonths;

  final double expectedLow;
  final double expectedHigh;
  final double spentSoFar;
  final double remainingLow;
  final double remainingHigh;

  factory CashEstimate.fromJson(Map<String, dynamic> j) => CashEstimate(
    baseMonths: ((j['base_months'] as List?) ?? const [])
        .map((e) => e as String)
        .toList(),
    expectedLow: (j['expected_low'] as num?)?.toDouble() ?? 0,
    expectedHigh: (j['expected_high'] as num?)?.toDouble() ?? 0,
    spentSoFar: (j['spent_so_far'] as num?)?.toDouble() ?? 0,
    remainingLow: (j['remaining_low'] as num?)?.toDouble() ?? 0,
    remainingHigh: (j['remaining_high'] as num?)?.toDouble() ?? 0,
  );
}

class CashMonth {
  CashMonth({
    required this.month,
    required this.received,
    required this.paid,
    required this.committed,
    required this.freeNow,
    required this.surplusLow,
    required this.surplusHigh,
    required this.hasRange,
    required this.incomeBaseline,
    required this.estimate,
    required this.due,
  });

  final String month;
  final double received;
  final double paid;
  final double committed;

  final double freeNow;

  final double surplusLow;
  final double surplusHigh;

  final bool hasRange;

  final double incomeBaseline;
  final CashEstimate estimate;
  final List<CashDueEntry> due;

  factory CashMonth.fromJson(Map<String, dynamic> j) => CashMonth(
    month: j['month'] as String? ?? '',
    received: (j['received'] as num?)?.toDouble() ?? 0,
    paid: (j['paid'] as num?)?.toDouble() ?? 0,
    committed: (j['committed'] as num?)?.toDouble() ?? 0,
    freeNow: (j['free_now'] as num?)?.toDouble() ?? 0,
    surplusLow: (j['surplus_low'] as num?)?.toDouble() ?? 0,
    surplusHigh: (j['surplus_high'] as num?)?.toDouble() ?? 0,
    hasRange: j['has_range'] as bool? ?? false,
    incomeBaseline: (j['income_baseline'] as num?)?.toDouble() ?? 0,
    estimate: CashEstimate.fromJson(
      (j['estimate'] as Map<String, dynamic>?) ?? const {},
    ),
    due: ((j['due'] as List?) ?? const [])
        .map((e) => CashDueEntry.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

class Debt {
  Debt({
    required this.id,
    required this.kind,
    required this.description,
    required this.balance,
    required this.monthlyRate,
    required this.debtClass,
    required this.referenceMonthly,
    required this.referenceSource,
    required this.flipRate,
  });

  final int? id;
  final String kind;
  final String description;
  final double balance;

  final double? monthlyRate;

  final DebtClass debtClass;

  final double? referenceMonthly;
  final String referenceSource;

  final double? flipRate;

  factory Debt.fromJson(Map<String, dynamic> j) => Debt(
    id: (j['id'] as num?)?.toInt(),
    kind: j['kind'] as String? ?? '',
    description: j['description'] as String? ?? '',
    balance: (j['balance'] as num?)?.toDouble() ?? 0,
    monthlyRate: (j['monthly_rate'] as num?)?.toDouble(),
    debtClass: DebtClass.fromJson(j['class'] as String?),
    referenceMonthly: (j['reference_monthly'] as num?)?.toDouble(),
    referenceSource: j['reference_source'] as String? ?? '',
    flipRate: (j['flip_rate'] as num?)?.toDouble(),
  );
}

class CascadeStep {
  CascadeStep({
    required this.order,
    required this.type,
    required this.amount,
    required this.reason,
    required this.falsifier,
    required this.reference,
  });

  final int order;
  final CascadeStepType type;
  final double amount;
  final String reason;

  final String? falsifier;

  final String? reference;

  factory CascadeStep.fromJson(Map<String, dynamic> j) => CascadeStep(
    order: (j['order'] as num?)?.toInt() ?? 0,
    type: CascadeStepType.fromJson(j['type'] as String?),
    amount: (j['amount'] as num?)?.toDouble() ?? 0,
    reason: j['reason'] as String? ?? '',
    falsifier: j['falsifier'] as String?,
    reference: j['reference'] as String?,
  );
}

class Cascade {
  Cascade({
    required this.surplusLow,
    required this.steps,
    required this.availableToInvest,
  });

  final double surplusLow;

  final List<CascadeStep> steps;

  final double availableToInvest;

  factory Cascade.fromJson(Map<String, dynamic> j) => Cascade(
    surplusLow: (j['surplus_low'] as num?)?.toDouble() ?? 0,
    steps: ((j['steps'] as List?) ?? const [])
        .map((e) => CascadeStep.fromJson(e as Map<String, dynamic>))
        .toList(),
    availableToInvest: (j['available_to_invest'] as num?)?.toDouble() ?? 0,
  );
}

class Surplus {
  Surplus({required this.month, required this.cascade, required this.hasCash});

  final CashMonth month;
  final Cascade cascade;

  final bool hasCash;

  factory Surplus.fromJson(Map<String, dynamic> j) => Surplus(
    month: CashMonth.fromJson(
      (j['month'] as Map<String, dynamic>?) ?? const {},
    ),
    cascade: Cascade.fromJson(
      (j['cascade'] as Map<String, dynamic>?) ?? const {},
    ),
    hasCash: j['has_cash'] as bool? ?? false,
  );
}

class CashVocabulary {
  CashVocabulary({
    required this.expenseCategories,
    required this.incomeCategories,
    required this.debtKinds,
  });

  final List<String> expenseCategories;
  final List<String> incomeCategories;
  final List<String> debtKinds;

  factory CashVocabulary.fromJson(Map<String, dynamic> j) => CashVocabulary(
    expenseCategories: ((j['expense_categories'] as List?) ?? const [])
        .map((e) => e as String)
        .toList(),
    incomeCategories: ((j['income_categories'] as List?) ?? const [])
        .map((e) => e as String)
        .toList(),
    debtKinds: ((j['debt_kinds'] as List?) ?? const [])
        .map((e) => e as String)
        .toList(),
  );
}

class CashTemplateCandidate {
  CashTemplateCandidate({
    required this.kind,
    required this.category,
    required this.description,
    required this.amount,
    required this.dueOn,
    required this.repeats,
    required this.alreadyThere,
  });

  final CashKind kind;
  final String category;
  final String description;
  final double amount;

  final String dueOn;

  final bool repeats;

  final bool alreadyThere;

  factory CashTemplateCandidate.fromJson(Map<String, dynamic> j) =>
      CashTemplateCandidate(
        kind: CashKind.fromJson(j['kind'] as String),
        category: j['category'] as String? ?? '',
        description: j['description'] as String? ?? '',
        amount: (j['amount'] as num?)?.toDouble() ?? 0,
        dueOn: j['due_on'] as String? ?? '',
        repeats: j['repeats'] as bool? ?? false,
        alreadyThere: j['already_there'] as bool? ?? false,
      );
}

class CashMonthTemplate {
  CashMonthTemplate({
    required this.source,
    required this.target,
    required this.candidates,
  });

  final String source;
  final String target;
  final List<CashTemplateCandidate> candidates;

  factory CashMonthTemplate.fromJson(Map<String, dynamic> j) =>
      CashMonthTemplate(
        source: j['source'] as String? ?? '',
        target: j['target'] as String? ?? '',
        candidates: ((j['candidates'] as List?) ?? const [])
            .map((e) => CashTemplateCandidate.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
