import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';

void invalidateCashReaders(void Function(ProviderOrFamily provider) invalidate) {
  invalidate(cashMonthProvider);
  invalidate(cashEntriesProvider);
  invalidate(debtsProvider);
  invalidate(surplusProvider);
  invalidate(quickInvestProvider);
}
