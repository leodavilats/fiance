import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/nav_action.dart';
import '../surplus/allocation_drift_screen.dart' show fiRelevantGapPp;
import 'widgets/feed_health.dart';
import 'widgets/feed_patrimony.dart';
import 'widgets/feed_tiles.dart';

const _topBuysLimit = 3;

class FeedScreen extends ConsumerWidget {
  const FeedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    final whatsNew = ref.watch(whatsNewProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('O que mudou'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'O que aconteceu',
            onPressed: () => context.push('/mes/atividade'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(dashboardProvider);
          ref.invalidate(whatsNewProvider);
        },
        child: dashboard.when(
          loading: () => FiSkeleton.screen(
            shape: FiSkeletonShape.row,
            count: 5,
            label: 'Carregando o que mudou',
          ),
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
            padding: const EdgeInsets.fromLTRB(
              FiLayout.gutter,
              FiSpace.s3,
              FiLayout.gutter,
              FiLayout.scrollTail,
            ),
            children: [
              FiPatrimonyBlock(summary: data.summary),
              if (data.freshness != null)
                FiFreshnessLine(freshness: data.freshness!),

              FiSection(
                title: 'O que mudou',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: _feed(ref, data, whatsNew),
                ),
              ),

              ..._nextAction(context, data),

              if (data.health != null)
                FiSection(
                  title: 'Como está a carteira',
                  child: FiHealthBlock(health: data.health!),
                ),

              if (data.topBuys.isNotEmpty)
                FiSection(
                  title: 'Em destaque',
                  hint: 'As leituras mais fortes do universo coberto hoje.',
                  action: FiNavAction(
                    label: 'Ver todas as oportunidades',
                    onPressed: () => context.go('/descobrir'),
                  ),
                  child: Column(
                    children: data.topBuys
                        .take(_topBuysLimit)
                        .map(
                          (o) => FiOpportunityTile(
                            opportunity: o,
                            onTap: () => context.push('/ativo/${o.ticker}'),
                          ),
                        )
                        .toList(),
                  ),
                ),

              const SizedBox(height: FiSpace.s8),
              Align(
                alignment: Alignment.centerLeft,
                child: FiNavAction(
                  label: 'Abrir o patrimônio',
                  onPressed: () => context.go('/patrimonio'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _feed(
    WidgetRef ref,
    DashboardData data,
    AsyncValue<WhatsNew> whatsNew,
  ) {
    final tiles = <(int, Widget)>[];

    for (final alert in data.alerts) {
      tiles.add((_severityRank(alert.severity), FiAlertTile(alert: alert)));
    }

    List<Widget> ordenados() {
      tiles.sort((a, b) => a.$1.compareTo(b.$1));
      return tiles.map((t) => t.$2).toList();
    }

    return whatsNew.when(
      loading: () => [
        ...ordenados(),
        const FiSkeleton(shape: FiSkeletonShape.row, count: 3),
      ],
      error: (e, _) => [
        ...ordenados(),
        FiErrorState(
          error: e,
          action: 'carregar o que mudou',
          onRetry: () => ref.invalidate(whatsNewProvider),
        ),
      ],
      data: (wn) {
        for (final item in wn.items) {
          if (item.kind == 'empty') continue;
          tiles.add((_severityRank(item.severity), FiWhatsNewTile(item: item)));
        }
        if (tiles.isEmpty) {
          return const [FiEmptyLine('Nada mudou desde a sua última visita.')];
        }
        return ordenados();
      },
    );
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
            .where((a) => a.delta.abs() >= fiRelevantGapPp)
            .toList()
          ..sort((a, b) => b.delta.abs().compareTo(a.delta.abs()));

    if (candidates.isEmpty) return const [];

    final gap = candidates.first;
    final below = gap.delta < 0;

    return [
      FiSection(
        title: 'Próxima ação',
        action: FiButton.primary(
          label: 'Ver alocação × meta',
          onPressed: () => context.go('/sobra/desvio'),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${gap.label} está ${below ? 'abaixo' : 'acima'} da sua meta.',
              style: fiSerif(FiType.verdictSm).copyWith(color: fiInk1(context)),
            ),
            const SizedBox(height: FiSpace.s2),
            Text(
              'Sua exposição está ${formatDecimal(gap.delta.abs())} pontos percentuais '
              '${below ? 'abaixo' : 'acima'} do objetivo '
              '(${formatPercent(gap.current, digits: 1)} contra '
              '${formatPercent(gap.target, digits: 1)}). '
              'É o maior desvio da sua carteira hoje.',
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
          ],
        ),
      ),
    ];
  }
}
