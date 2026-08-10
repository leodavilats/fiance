import 'package:go_router/go_router.dart';

import '../features/assets/assets_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/config/config_screen.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/market/market_screen.dart';
import '../features/shell/app_shell.dart';

final appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) =>
          AppShell(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/dashboard',
              builder: (context, state) => const DashboardScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/assets',
              builder: (context, state) => const AssetsScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/market',
              builder: (context, state) => const MarketScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/config',
              builder: (context, state) => const ConfigScreen(),
            ),
          ],
        ),
      ],
    ),
  ],
);
