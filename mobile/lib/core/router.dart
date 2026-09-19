import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/patrimony/patrimony_screen.dart';
import '../features/patrimony/widgets/patrimony_positions.dart';
import '../features/patrimony/dividends_screen.dart';
import '../features/patrimony/ledger_screen.dart';
import '../features/assets/fixed_income_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/splash_screen.dart';
import '../features/config/config_screen.dart';
import '../features/config/delete_account_screen.dart';
import '../features/month/feed_screen.dart';
import '../features/month/debts_screen.dart';
import '../features/month/month_screen.dart';
import '../features/surplus/surplus_screen.dart';
import '../features/surplus/allocation_drift_screen.dart';
import '../features/config/goals_screen.dart';
import '../features/month/activity_screen.dart';
import '../features/tools/income_compare_view.dart';
import '../features/market/opportunities_tab.dart';
import '../features/market/quick_invest_view.dart';
import '../features/shell/app_shell.dart';
import '../features/shell/branch_pager.dart';
import '../features/shell/tool_screen.dart';
import '../features/tools/tools_views.dart';

final appRouter = GoRouter(
  initialLocation: '/splash',
  routes: [
    GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),

    GoRoute(path: '/dashboard', redirect: (_, _) => '/mes'),
    GoRoute(path: '/hoje', redirect: (_, _) => '/mes'),
    GoRoute(path: '/hoje/atividade', redirect: (_, _) => '/mes/atividade'),
    GoRoute(path: '/estrategia', redirect: (_, _) => '/sobra/desvio'),
    GoRoute(path: '/estrategia/aporte', redirect: (_, _) => '/sobra/aporte'),
    GoRoute(path: '/estrategia/metas', redirect: (_, _) => '/voce/objetivos'),
    GoRoute(
      path: '/estrategia/renda-fixa',
      redirect: (_, _) => '/descobrir/renda-fixa',
    ),
    GoRoute(
      path: '/estrategia/renda-fixa-vs-bolsa',
      redirect: (_, _) => '/descobrir/renda-fixa-vs-bolsa',
    ),
    GoRoute(
      path: '/estrategia/projecao',
      redirect: (_, _) => '/patrimonio/projecao',
    ),
    GoRoute(path: '/assets', redirect: (_, _) => '/patrimonio'),
    GoRoute(path: '/carteira', redirect: (_, _) => '/patrimonio'),
    GoRoute(path: '/market', redirect: (_, _) => '/descobrir'),
    GoRoute(path: '/config', redirect: (_, _) => '/voce'),

    StatefulShellRoute(
      builder: (context, state, navigationShell) =>
          AppShell(navigationShell: navigationShell),
      navigatorContainerBuilder: (context, navigationShell, children) =>
          FiBranchPager(navigationShell: navigationShell, children: children),
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/mes',
              builder: (context, state) => const MonthScreen(),
              routes: [
                GoRoute(
                  path: 'atividade',
                  builder: (context, state) => const ActivityScreen(),
                ),
                GoRoute(
                  path: 'feed',
                  builder: (context, state) => const FeedScreen(),
                ),
                GoRoute(
                  path: 'dividas',
                  builder: (context, state) => const DebtsScreen(),
                ),
              ],
            ),
          ],
        ),

        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/sobra',
              builder: (context, state) => const SurplusScreen(),
              routes: [
                GoRoute(
                  path: 'aporte',
                  builder: (context, state) => const ToolScreen(
                    title: 'Onde aportar',
                    question:
                        'Recebi dinheiro — onde ele faz mais diferença agora?',
                    child: QuickInvestView(),
                  ),
                ),
                GoRoute(
                  path: 'desvio',
                  builder: (context, state) => const AllocationDriftScreen(),
                ),
              ],
            ),
          ],
        ),

        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/patrimonio',
              builder: (context, state) => PatrimonyScreen(
                groupMode: FiAssetGroupMode.fromSlug(
                  state.uri.queryParameters['por'],
                ),
              ),
              routes: [
                GoRoute(
                  path: 'renda-fixa',
                  builder: (context, state) => const FixedIncomeScreen(),
                ),
                GoRoute(
                  path: 'razao',
                  builder: (context, state) => const LedgerScreen(),
                ),
                GoRoute(
                  path: 'proventos',
                  builder: (context, state) => const DividendsScreen(),
                ),
                GoRoute(
                  path: 'projecao',
                  builder: (context, state) => const ToolScreen(
                    title: 'Projeção',
                    question: 'Aportando assim, onde eu chego?',
                    child: ContributionSimulatorView(),
                  ),
                ),
              ],
            ),
          ],
        ),

        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/descobrir',
              builder: (context, state) => const _DiscoverScreen(),
              routes: [
                GoRoute(
                  path: 'quedas',
                  builder: (context, state) => const ToolScreen(
                    title: 'Quedas',
                    question: 'Caiu por quê — e os fundamentos seguem de pé?',
                    child: OpportunitiesTab(initialOnlyDip: true),
                  ),
                ),
                GoRoute(
                  path: 'comparar',
                  builder: (context, state) => const ToolScreen(
                    title: 'Comparar ativos',
                    question:
                        'Entre estes ativos, qual está melhor posicionado?',
                    child: CompareAssetsView(),
                  ),
                ),
                GoRoute(
                  path: 'renda-fixa',
                  builder: (context, state) => const ToolScreen(
                    title: 'Renda fixa',
                    question:
                        'Entre estes títulos, qual rende mais depois do IR?',
                    child: FixedIncomeSimulatorView(),
                  ),
                ),
                GoRoute(
                  path: 'renda-fixa-vs-bolsa',
                  builder: (context, state) => const ToolScreen(
                    title: 'Renda fixa × bolsa',
                    question:
                        'Com a Selic nesse patamar, vale mais o CDB ou o FII?',
                    child: IncomeCompareView(),
                  ),
                ),
              ],
            ),
          ],
        ),


        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/voce',
              builder: (context, state) => const ConfigScreen(),
              routes: [
                GoRoute(
                  path: 'objetivos',
                  builder: (context, state) => const GoalsScreen(),
                ),
                GoRoute(
                  path: 'investir',
                  builder: (context, state) => const InvestingScreen(),
                ),
                GoRoute(
                  path: 'avisos',
                  builder: (context, state) => const NotificationsScreen(),
                ),
                GoRoute(
                  path: 'aparencia',
                  builder: (context, state) => const AppearanceScreen(),
                ),
                GoRoute(
                  path: 'conta',
                  builder: (context, state) => const AccountScreen(),
                  routes: [
                    GoRoute(
                      path: 'excluir',
                      builder: (context, state) => const DeleteAccountScreen(),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ],
    ),

    GoRoute(
      path: '/ativo/:ticker',
      builder: (context, state) => ToolScreen(
        title: state.pathParameters['ticker']?.toUpperCase() ?? 'Ativo',
        child: AnalyzeAssetView(initialTicker: state.pathParameters['ticker']),
      ),
    ),
  ],
);

class _DiscoverScreen extends StatelessWidget {
  const _DiscoverScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Descobrir'),
        actions: [
          IconButton(
            tooltip: 'Comparar ativos',
            icon: const Icon(Icons.compare_arrows),
            onPressed: () => context.go('/descobrir/comparar'),
          ),
        ],
      ),
      body: const OpportunitiesTab(),
    );
  }
}
