import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/carteira/carteira_screen.dart';
import '../features/assets/fixed_income_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/splash_screen.dart';
import '../features/config/config_screen.dart';
import '../features/hoje/hoje_screen.dart';
import '../features/estrategia/estrategia_screen.dart';
import '../features/busca/busca_screen.dart';
import '../features/estrategia/metas_screen.dart';
import '../features/hoje/atividade_screen.dart';
import '../features/tools/income_compare_view.dart';
import '../features/market/opportunities_tab.dart';
import '../features/market/quick_invest_view.dart';
import '../features/shell/app_shell.dart';
import '../features/shell/tool_screen.dart';
import '../features/tools/tools_views.dart';

final appRouter = GoRouter(
  initialLocation: '/splash',
  routes: [
    GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),

    GoRoute(path: '/dashboard', redirect: (_, _) => '/hoje'),
    GoRoute(path: '/assets', redirect: (_, _) => '/carteira'),
    GoRoute(path: '/market', redirect: (_, _) => '/descobrir'),
    GoRoute(path: '/config', redirect: (_, _) => '/voce'),
    // Busca é camada, não destino: ela abre por cima de onde a pessoa está e
    // some. Colocá-la no bottom nav gastaria um dos cinco lugares com algo que
    // não é um lugar.
    GoRoute(path: '/busca', builder: (context, state) => const BuscaScreen()),

    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) =>
          AppShell(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/hoje',
              builder: (context, state) => const HojeScreen(),
              routes: [
                GoRoute(
                  path: 'atividade',
                  builder: (context, state) => const AtividadeScreen(),
                ),
              ],
            ),
          ],
        ),

        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/carteira',
              builder: (context, state) => const CarteiraScreen(),
              routes: [
                GoRoute(
                  path: 'renda-fixa',
                  builder: (context, state) => const FixedIncomeScreen(),
                ),
              ],
            ),
          ],
        ),

        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/descobrir',
              builder: (context, state) => const _DescobrirScreen(),
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
              ],
            ),
          ],
        ),

        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/estrategia',
              builder: (context, state) => const EstrategiaScreen(),
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
                  path: 'metas',
                  builder: (context, state) => const MetasScreen(),
                ),
                GoRoute(
                  path: 'renda-fixa',
                  builder: (context, state) => const ToolScreen(
                    title: 'Renda fixa',
                    question:
                        'Entre estes títulos, qual rende mais depois do IR?',
                    child: RendaFixaSimulatorView(),
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
              path: '/voce',
              builder: (context, state) => const ConfigScreen(),
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

class _DescobrirScreen extends StatelessWidget {
  const _DescobrirScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Descobrir'),
        actions: [
          IconButton(
            tooltip: 'Quedas',
            icon: const Icon(Icons.trending_down),
            onPressed: () => context.go('/descobrir/quedas'),
          ),
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
