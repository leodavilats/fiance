import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api_client.dart';
import 'api_repository.dart';
import 'auth_service.dart';
import 'models.dart';
import 'notifications_service.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(apiBaseUrl: apiBaseUrl);
});

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.watch(authServiceProvider));
});

final apiRepositoryProvider = Provider<ApiRepository>((ref) {
  return ApiRepository(ref.watch(apiClientProvider).dio);
});

final notificationsServiceProvider = Provider<NotificationsService>((ref) {
  return NotificationsService(ref.watch(apiRepositoryProvider));
});

final currentUserProvider = StateProvider<AppUser?>((ref) => null);

final authStatusProvider = FutureProvider<AppUser?>((ref) async {
  final minDuration = Future<void>.delayed(const Duration(milliseconds: 1100));
  final authService = ref.watch(authServiceProvider);
  final token = await authService.readToken();
  if (token == null) {
    await minDuration;
    return null;
  }

  try {
    final user = await ref.watch(apiRepositoryProvider).getMe();
    ref.read(currentUserProvider.notifier).state = user;
    await minDuration;
    return user;
  } catch (_) {
    await authService.signOut();
    await minDuration;
    return null;
  }
});

final dashboardProvider = FutureProvider.autoDispose<DashboardData>((ref) {
  return ref.watch(apiRepositoryProvider).getDashboard();
});

final portfolioProvider = FutureProvider.autoDispose<List<StoredPortfolioItem>>(
  (ref) {
    return ref.watch(apiRepositoryProvider).getPortfolio();
  },
);

final opportunitiesSearchProvider = StateProvider.autoDispose<String>(
  (ref) => '',
);

final opportunitiesProvider = FutureProvider.autoDispose<List<Opportunity>>((
  ref,
) {
  final search = ref.watch(opportunitiesSearchProvider);
  return ref.watch(apiRepositoryProvider).getOpportunities(search: search);
});

final preferencesProvider = FutureProvider.autoDispose<Preferences>((ref) {
  return ref.watch(apiRepositoryProvider).getPreferences();
});

final sectorsCategoryProvider = StateProvider.autoDispose<String>(
  (ref) => 'acoes_br',
);

final sectorsSummaryProvider = FutureProvider.autoDispose<List<SectorSummary>>((
  ref,
) {
  final category = ref.watch(sectorsCategoryProvider);
  return ref.watch(apiRepositoryProvider).getSectorsSummary(category: category);
});

final goalsProvider = FutureProvider.autoDispose<List<Goal>>((ref) {
  return ref.watch(apiRepositoryProvider).getGoals();
});

final sectorGoalsProvider = FutureProvider.autoDispose<List<SectorGoal>>((ref) {
  return ref.watch(apiRepositoryProvider).getSectorGoals();
});

final alertsProvider = FutureProvider.autoDispose<List<PriceAlert>>((ref) {
  return ref.watch(apiRepositoryProvider).getAlerts();
});

final closedTradesProvider = FutureProvider.autoDispose<ClosedTradesResponse>((
  ref,
) {
  return ref.watch(apiRepositoryProvider).getClosedTrades();
});
