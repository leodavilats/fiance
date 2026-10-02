import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/providers.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/nav_action.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/segments.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../month/widgets/feed_charts.dart';
import 'patrimony_actions.dart';
import 'widgets/patrimony_closed_trades.dart';
import 'widgets/patrimony_composition.dart';
import 'widgets/patrimony_fixed_income.dart';
import 'widgets/patrimony_positions.dart';
import 'widgets/patrimony_summary.dart';

class PatrimonyScreen extends ConsumerWidget {
  const PatrimonyScreen({super.key, this.groupMode = FiAssetGroupMode.value});

  final FiAssetGroupMode groupMode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Patrimônio'),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(dashboardProvider);
          ref.invalidate(fixedIncomeProvider);
        },
        child: dashboard.when(
          loading: () => FiSkeleton.page(
            sections: const [2, 4, 3],
            label: 'Carregando sua carteira',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar sua carteira',
            action: 'carregar sua carteira',
            onRetry: () => ref.invalidate(dashboardProvider),
          ),
          data: (data) {
            if (data.positions.isEmpty) {
              return FiEmptyState(
                title: 'Sua carteira ainda está vazia',
                body: 'A carteira é a base de tudo: sem ela o fiance não tem o que avaliar, '
                    'comparar com meta ou usar para sugerir aporte.',
                hint: 'Cadastre o que você já tem — ticker, quantidade e preço médio.',
                action: FiButton.primary(
                  label: 'Adicionar primeiro ativo',
                  onPressed: () => openAddPositionDialog(context, ref),
                ),
                secondary: FiButton.secondary(
                  label: 'Cadastrar aplicação de renda fixa',
                  onPressed: () => context.go('/patrimonio/renda-fixa'),
                ),
              );
            }

            final negociados = fiTradedPositions(data.positions);
            final idade = formatAge(
              oldestStamp(negociados.map((p) => p.asOf)),
            );

            return ListView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                FiSpace.s3,
                FiLayout.gutter,
                FiLayout.scrollTail,
              ),
              children: [
                FiPortfolioSummary(summary: data.summary),

                if (data.allocations.isNotEmpty)
                  FiSection(
                    title: switch (groupMode) {
                      FiAssetGroupMode.value => 'Onde está concentrado, por ativo',
                      FiAssetGroupMode.category => 'Onde está concentrado, por classe',
                      FiAssetGroupMode.sector => 'Onde está concentrado, por setor',
                    },
                    trailing: _GroupModeSegments(current: groupMode),
                    child: FiCompositionBlock(
                      allocations: data.allocations,
                      positions: data.positions,
                      mode: switch (groupMode) {
                        FiAssetGroupMode.value => FiCompositionMode.position,
                        FiAssetGroupMode.category => FiCompositionMode.category,
                        FiAssetGroupMode.sector => FiCompositionMode.sector,
                      },
                    ),
                  ),

                FiSection(
                  title: 'Evolução',
                  hint: data.snapshots.length > 1
                      ? 'A distância entre as duas linhas é o seu lucro — o que subiu por '
                            'aporte fica na linha de baixo.'
                      : null,
                  action: FiNavAction(
                    label: 'Projeção — aportando assim, onde eu chego?',
                    onPressed: () => context.push('/patrimonio/projecao'),
                  ),
                  child: data.snapshots.length > 1
                      ? FiEvolutionChart(snapshots: data.snapshots)
                      : const FiEmptyLine(
                          'A linha do tempo aparece a partir da segunda leitura da carteira.',
                        ),
                ),

                const FiBenchmarkSection(),

                const FiFixedIncomeSection(),

                FiSection(
                  title: 'Ativos negociados',
                  count: negociados.length,
                  hint: idade.isEmpty ? null : 'Cotações lidas $idade.',
                  action: FiButton.secondary(
                    label: 'Adicionar ativo',
                    icon: Icons.add,
                    onPressed: () => openAddPositionDialog(context, ref),
                  ),
                  child: FiGroupedPositionsList(
                    positions: data.positions,
                    mode: groupMode,
                    onRemove: (p) => removePosition(context, ref, p),
                    onSell: (p) => openSellDialog(context, ref, p),
                  ),
                ),

                const FiClosedTradesSection(),

                const _WhereItComesFrom(),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _GroupModeSegments extends StatelessWidget {
  const _GroupModeSegments({required this.current});

  final FiAssetGroupMode current;

  @override
  Widget build(BuildContext context) {
    return FiSegments<FiAssetGroupMode>(
      selected: current,
      semanticsPrefix: 'Ver a carteira por',
      options: const {
        FiAssetGroupMode.value: 'Valor',
        FiAssetGroupMode.category: 'Classe',
        FiAssetGroupMode.sector: 'Setor',
      },
      onSelect: (v) => GoRouter.of(context).go('/patrimonio?por=${v.slug}'),
    );
  }
}

class _WhereItComesFrom extends ConsumerWidget {
  const _WhereItComesFrom();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final proventos = ref.watch(dividendsProvider);
    final razao = ref.watch(ledgerProvider);

    return FiSection(
      title: 'De onde vem este patrimônio',
      hint: 'A posição e o preço médio acima são reconstruídos a partir dos seus lançamentos.',
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Proventos',
            value: proventos.valueOrNull == null
                ? null
                : formatCurrency(proventos.valueOrNull!.receivedLast12m),
            detail: proventos.when(
              data: (d) => d.totalCount == 0
                  ? 'Nada registrado ainda — o calendário pode ter sugestões'
                  : '${d.totalCount} ${d.totalCount == 1 ? 'crédito' : 'créditos'} '
                        'nos últimos 12 meses',
              loading: () => 'Lendo o que os seus ativos pagaram',
              error: (err, _) => fiErrorMessage(err, action: 'ler os seus proventos'),
            ),
            onTap: () => context.go('/patrimonio/proventos'),
          ),
          FiDataRow(
            label: 'Livro-razão',
            value: razao.valueOrNull == null ? null : '${razao.valueOrNull!.count}',
            detail: razao.when(
              data: (d) => d.items.isEmpty
                  ? 'Nenhum lançamento — a carteira veio de declaração de posição'
                  : 'O último em ${formatDate(d.items.first.tradedOn)}',
              loading: () => 'Lendo os seus lançamentos',
              error: (err, _) => fiErrorMessage(err, action: 'ler o seu livro-razão'),
            ),
            onTap: () => context.go('/patrimonio/razao'),
          ),
          FiDataRow(
            label: 'Sugestões seguidas',
            detail: 'O resultado das compras feitas a partir de uma leitura, contra o Ibovespa',
            onTap: () => context.go('/patrimonio/seguidas'),
          ),
        ],
      ),
    );
  }
}
