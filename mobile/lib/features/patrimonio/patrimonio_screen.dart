import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/search_action.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/segments.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../mes/widgets/feed_charts.dart';
import 'patrimonio_actions.dart';
import 'widgets/patrimonio_closed_trades.dart';
import 'widgets/patrimonio_composition.dart';
import 'widgets/patrimonio_positions.dart';
import 'widgets/patrimonio_summary.dart';

/// O Patrimonio: "quanto eu tenho, e como isso esta distribuido?"
class PatrimonioScreen extends ConsumerWidget {
  const PatrimonioScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    final fixedIncome = ref.watch(fixedIncomeProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Patrimônio'),
        actions: [
          const FiSearchAction(),
          IconButton(
            tooltip: 'Renda fixa',
            icon: const Icon(Icons.account_balance_outlined),
            onPressed: () => context.go('/patrimonio/renda-fixa'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(dashboardProvider);
          ref.invalidate(fixedIncomeProvider);
        },
        child: dashboard.when(
          loading: () => FiSkeleton.tela(
            shape: FiSkeletonShape.metric,
            count: 1,
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

                fixedIncome.maybeWhen(
                  data: (fi) => fi.visiveis.isEmpty
                      ? const SizedBox.shrink()
                      : FiFixedIncomeSummary(data: fi),
                  orElse: () => const SizedBox.shrink(),
                ),

                if (data.allocations.isNotEmpty)
                  _Composicao(
                    allocations: data.allocations,
                    positions: data.positions,
                  ),

                const FiBenchmarkSection(),

                if (data.snapshots.length > 1)
                  FiSection(
                    title: 'Evolução',
                    child: FiEvolutionChart(snapshots: data.snapshots),
                  ),

                FiSection(
                  title: 'Ativos negociados',
                  count: data.positions.length,
                  hint: idade.isEmpty ? null : 'Cotações lidas $idade.',
                  trailing: const _RecorteDeAtivos(),
                  action: FiButton.secondary(
                    label: 'Adicionar ativo',
                    icon: Icons.add,
                    onPressed: () => openAddPositionDialog(context, ref),
                  ),
                  child: FiGroupedPositionsList(
                    positions: data.positions,
                    mode: ref.watch(fiAssetGroupModeProvider),
                    onDelete: (ticker) => deletePosition(ref, ticker),
                    onSell: (p) => openSellDialog(context, ref, p),
                  ),
                ),

                const FiClosedTradesSection(),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _RecorteDeAtivos extends ConsumerWidget {
  const _RecorteDeAtivos();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final modo = ref.watch(fiAssetGroupModeProvider);

    return FiSegments<FiAssetGroupMode>(
      selected: modo,
      semanticsPrefix: 'Agrupar por',
      options: const {
        FiAssetGroupMode.value: 'Valor',
        FiAssetGroupMode.category: 'Classe',
        FiAssetGroupMode.sector: 'Setor',
      },
      onSelect: (v) => ref.read(fiAssetGroupModeProvider.notifier).state = v,
    );
  }
}

class _Composicao extends StatefulWidget {
  const _Composicao({required this.allocations, required this.positions});

  final List<CategoryAllocation> allocations;
  final List<PortfolioPosition> positions;

  @override
  State<_Composicao> createState() => _ComposicaoState();
}

class _ComposicaoState extends State<_Composicao> {
  FiCompositionMode _modo = FiCompositionMode.asset;

  @override
  Widget build(BuildContext context) {
    return FiSection(
      title: 'Onde está concentrado',
      trailing: FiSegments<FiCompositionMode>(
        selected: _modo,
        semanticsPrefix: 'Agrupar por',
        options: const {
          FiCompositionMode.asset: 'Classe',
          FiCompositionMode.sector: 'Setor',
        },
        onSelect: (v) => setState(() => _modo = v),
      ),
      child: FiCompositionBlock(
        allocations: widget.allocations,
        positions: widget.positions,
        mode: _modo,
      ),
    );
  }
}
