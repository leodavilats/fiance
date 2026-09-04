import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import 'widgets/hoje_health.dart';
import 'widgets/hoje_patrimony.dart';
import 'widgets/hoje_tiles.dart';

const _minGapPp = 2.0;

const _topBuysLimit = 3;

class HojeScreen extends ConsumerWidget {
  const HojeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    final whatsNew = ref.watch(whatsNewProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Hoje'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: 'Buscar ativo, título ou tela',
            onPressed: () => context.push('/busca'),
          ),
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'O que aconteceu',
            onPressed: () => context.go('/hoje/atividade'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(dashboardProvider);
          ref.invalidate(whatsNewProvider);
        },
        child: dashboard.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar seu resumo',
            action: 'carregar seu resumo',
            onRetry: () {
              ref.invalidate(dashboardProvider);
              ref.invalidate(whatsNewProvider);
            },
          ),
          data: (data) => ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              FiPatrimonyBlock(summary: data.summary),
              if (data.freshness != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: FiFreshnessLine(freshness: data.freshness!),
                ),

              if (data.health != null) ...[
                const SizedBox(height: 24),
                const FiSectionTitle(
                  icon: Icons.health_and_safety_outlined,
                  title: 'Como está a carteira',
                ),
                FiHealthBlock(health: data.health!),
              ],

              const SizedBox(height: 24),
              const FiSectionTitle(
                icon: Icons.auto_awesome_outlined,
                title: 'O que mudou',
              ),
              ..._feed(context, data, whatsNew),

              ..._nextAction(context, data),

              if (data.topBuys.isNotEmpty) ...[
                const SizedBox(height: 24),
                const FiSectionTitle(
                  icon: Icons.trending_up,
                  title: 'Em destaque',
                ),
                ...data.topBuys
                    .take(_topBuysLimit)
                    .map((o) => FiOpportunityTile(opportunity: o)),
                _MoreLink(
                  label: 'Ver todas as oportunidades',
                  route: '/descobrir',
                ),
              ],

              const SizedBox(height: 24),
              _MoreLink(label: 'Abrir a carteira', route: '/carteira'),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _feed(
    BuildContext context,
    DashboardData data,
    AsyncValue<WhatsNew> whatsNew,
  ) {
    final tiles = <(int, Widget)>[];

    for (final alert in data.alerts) {
      tiles.add((_severityRank(alert.severity), FiAlertTile(alert: alert)));
    }

    whatsNew.whenData((wn) {
      for (final item in wn.items) {
        if (item.kind == 'empty') continue;
        tiles.add((_severityRank(item.severity), FiWhatsNewTile(item: item)));
      }
    });

    if (tiles.isEmpty) {
      return [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Text(
            'Nada mudou desde a sua última visita.',
            style: TextStyle(color: fiInk2(context)),
          ),
        ),
      ];
    }

    tiles.sort((a, b) => a.$1.compareTo(b.$1));
    return tiles.map((t) => t.$2).toList();
  }

  int _severityRank(String severity) {
    switch (severity) {
      case 'critical':
      case 'high':
        return 0;
      case 'warning':
      case 'medium':
        return 1;
      case 'positive':
        return 3;
      default:
        return 2;
    }
  }

  List<Widget> _nextAction(BuildContext context, DashboardData data) {
    final candidates =
        data.allocations
            .where((a) => a.targetPct != null)
            .map(
              (a) => (
                label: categoryLabel(a.category),
                current: a.currentPct,
                target: a.targetPct!,
                delta: a.currentPct - a.targetPct!,
              ),
            )
            .where((a) => a.delta.abs() >= _minGapPp)
            .toList()
          ..sort((a, b) => b.delta.abs().compareTo(a.delta.abs()));

    if (candidates.isEmpty) return const [];

    final gap = candidates.first;
    final below = gap.delta < 0;

    return [
      const SizedBox(height: 24),
      const FiSectionTitle(icon: Icons.flag_outlined, title: 'Próxima ação'),
      Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${gap.label} está ${below ? 'abaixo' : 'acima'} da sua meta',
                style: fiSerif(
                  Theme.of(context).textTheme.titleMedium ?? const TextStyle(),
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Sua exposição está ${gap.delta.abs().toStringAsFixed(1)} pontos percentuais '
                '${below ? 'abaixo' : 'acima'} do objetivo '
                '(${gap.current.toStringAsFixed(1)}% contra ${gap.target.toStringAsFixed(1)}%).',
                style: TextStyle(color: fiInk2(context)),
              ),
              const SizedBox(height: 4),
              Text(
                'É o maior desvio da sua carteira hoje.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
              const SizedBox(height: 14),
              FilledButton(
                onPressed: () => context.go('/estrategia'),
                child: const Text('Ver estratégia'),
              ),
            ],
          ),
        ),
      ),
    ];
  }
}

class _MoreLink extends StatelessWidget {
  const _MoreLink({required this.label, required this.route});

  final String label;
  final String route;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: TextButton(
        onPressed: () => context.go(route),
        child: Text('$label →'),
      ),
    );
  }
}
