import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/providers.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/segments.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../mes/widgets/feed_charts.dart';
import 'patrimonio_actions.dart';
import 'widgets/patrimonio_closed_trades.dart';
import 'widgets/patrimonio_composition.dart';
import 'widgets/patrimonio_fixed_income.dart';
import 'widgets/patrimonio_positions.dart';
import 'widgets/patrimonio_summary.dart';

class PatrimonioScreen extends ConsumerWidget {
  const PatrimonioScreen({super.key, this.recorte = FiAssetGroupMode.value});

  final FiAssetGroupMode recorte;

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
          loading: () => FiSkeleton.pagina(
            secoes: const [2, 4, 3],
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
                  label: 'Cadastrar renda fixa',
                  onPressed: () => context.go('/patrimonio/renda-fixa'),
                ),
              );
            }

            final idade = formatIdade(
              carimboMaisAntigo(data.positions.map((p) => p.asOf)),
            );

            return ListView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                FiSpace.s3,
                FiLayout.gutter,
                FiLayout.scrollTail,
              ),
              children: [
                FiCarteiraSummary(summary: data.summary),

                if (data.allocations.isNotEmpty)
                  FiSection(
                    title: recorte == FiAssetGroupMode.sector
                        ? 'Onde está concentrado, por setor'
                        : 'Onde está concentrado, por classe',
                    trailing: _Recorte(atual: recorte),
                    child: FiCompositionBlock(
                      allocations: data.allocations,
                      positions: data.positions,
                      mode: recorte == FiAssetGroupMode.sector
                          ? FiCompositionMode.sector
                          : FiCompositionMode.asset,
                    ),
                  ),

                if (data.snapshots.length > 1)
                  FiSection(
                    title: 'Evolução',
                    hint: 'A distância entre as duas linhas é o seu lucro — o que subiu por '
                        'aporte fica na linha de baixo.',
                    child: FiEvolutionChart(snapshots: data.snapshots),
                  ),

                const FiBenchmarkSection(),

                const FiFixedIncomeSection(),

                FiSection(
                  title: 'Ativos negociados',
                  count: data.positions.length,
                  hint: idade.isEmpty ? null : 'Cotações lidas $idade.',
                  action: FiButton.secondary(
                    label: 'Adicionar ativo',
                    icon: Icons.add,
                    onPressed: () => openAddPositionDialog(context, ref),
                  ),
                  child: FiGroupedPositionsList(
                    positions: data.positions,
                    mode: recorte,
                    onDelete: (ticker) => deletePosition(ref, ticker),
                    onSell: (p) => openSellDialog(context, ref, p),
                  ),
                ),

                const FiClosedTradesSection(),

                const _DeOndeVem(),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Recorte extends StatelessWidget {
  const _Recorte({required this.atual});

  final FiAssetGroupMode atual;

  @override
  Widget build(BuildContext context) {
    return FiSegments<FiAssetGroupMode>(
      selected: atual,
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

class _DeOndeVem extends ConsumerWidget {
  const _DeOndeVem();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final proventos = ref.watch(proventosProvider);
    final razao = ref.watch(razaoProvider);

    return FiSection(
      title: 'De onde vem este patrimônio',
      hint: 'A posição e o preço médio acima são reconstruídos a partir dos seus lançamentos.',
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Proventos',
            value: proventos.maybeWhen(
              data: (d) => formatCurrency(d.receivedLast12m),
              orElse: () => null,
            ),
            detail: proventos.maybeWhen(
              data: (d) => d.totalCount == 0
                  ? 'Nada registrado ainda — o calendário pode ter sugestões'
                  : '${d.totalCount} ${d.totalCount == 1 ? 'crédito' : 'créditos'} '
                        'nos últimos 12 meses',
              orElse: () => 'Lendo o que os seus ativos pagaram',
            ),
            onTap: () => context.go('/patrimonio/proventos'),
          ),
          FiDataRow(
            label: 'Livro-razão',
            value: razao.maybeWhen(
              data: (d) => '${d.count}',
              orElse: () => null,
            ),
            detail: razao.maybeWhen(
              data: (d) => d.items.isEmpty
                  ? 'Nenhum lançamento — a carteira veio de declaração de posição'
                  : 'O último em ${formatDate(d.items.first.tradedOn)}',
              orElse: () => 'Lendo os seus lançamentos',
            ),
            onTap: () => context.go('/patrimonio/razao'),
          ),
        ],
      ),
    );
  }
}
