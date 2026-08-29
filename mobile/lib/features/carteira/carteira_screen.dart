import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../hoje/widgets/hoje_charts.dart';
import 'carteira_actions.dart';
import 'widgets/carteira_closed_trades.dart';
import 'widgets/carteira_composition.dart';
import 'widgets/carteira_positions.dart';
import 'widgets/carteira_summary.dart';

/// "Como está meu patrimônio?"
///
/// A leitura desce sempre na mesma ordem — **tamanho, qualidade, direção,
/// detalhe**:
///
/// 1. quanto eu tenho (e quanto disso é renda fixa);
/// 2. onde está concentrado, comparado à meta;
/// 3. como vem rendendo, contra o CDI e o Ibovespa;
/// 4. cada posição, uma a uma;
/// 5. o que já foi encerrado.
///
/// A evolução do patrimônio e o comparativo com benchmark **mudaram de tela**:
/// estavam em Hoje disputando espaço com a decisão do dia, e a pergunta que
/// respondem ("estou rendendo mais que o CDI?") é de patrimônio, não de
/// novidade.
class CarteiraScreen extends ConsumerWidget {
  const CarteiraScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    final fixedIncome = ref.watch(fixedIncomeProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Carteira'),
        actions: [
          IconButton(
            tooltip: 'Renda fixa',
            icon: const Icon(Icons.account_balance_outlined),
            onPressed: () => context.go('/carteira/renda-fixa'),
          ),
        ],
      ),
      floatingActionButton: dashboard.hasValue
          ? FloatingActionButton(
              tooltip: 'Adicionar ativo',
              onPressed: () => openAddPositionDialog(context, ref),
              child: const Icon(Icons.add),
            )
          : null,
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(dashboardProvider);
          ref.invalidate(fixedIncomeProvider);
        },
        child: dashboard.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar sua carteira',
            action: 'carregar sua carteira',
            onRetry: () => ref.invalidate(dashboardProvider),
          ),
          data: (data) {
            if (data.positions.isEmpty) {
              return _EmptyCarteira(onAdd: () => openAddPositionDialog(context, ref));
            }

            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 88),
              children: [
                FiCarteiraSummary(summary: data.summary),
                fixedIncome.maybeWhen(
                  data: (fi) => fi.visiveis.isEmpty
                      ? const SizedBox.shrink()
                      : Padding(
                          padding: const EdgeInsets.only(top: 20),
                          child: FiFixedIncomeSummary(data: fi),
                        ),
                  orElse: () => const SizedBox.shrink(),
                ),

                if (data.allocations.isNotEmpty) ...[
                  const SizedBox(height: 24),
                  const FiSectionTitle(
                    icon: Icons.donut_small_outlined,
                    title: 'Onde está concentrado',
                  ),
                  FiCompositionBlock(
                    allocations: data.allocations,
                    positions: data.positions,
                  ),
                ],

                const SizedBox(height: 24),
                const FiBenchmarkSection(),
                if (data.snapshots.length > 1) ...[
                  const SizedBox(height: 20),
                  const FiSectionTitle(
                    icon: Icons.show_chart,
                    title: 'Evolução do patrimônio',
                  ),
                  FiEvolutionChart(snapshots: data.snapshots),
                ],

                const SizedBox(height: 24),
                FiSectionTitle(
                  icon: Icons.receipt_long_outlined,
                  title: 'Ativos negociados (${data.positions.length})',
                ),
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: SegmentedButton<FiAssetGroupMode>(
                    segments: const [
                      ButtonSegment(
                        value: FiAssetGroupMode.value,
                        label: Text('Por valor'),
                      ),
                      ButtonSegment(
                        value: FiAssetGroupMode.category,
                        label: Text('Por categoria'),
                      ),
                      ButtonSegment(
                        value: FiAssetGroupMode.sector,
                        label: Text('Por setor'),
                      ),
                    ],
                    selected: {ref.watch(fiAssetGroupModeProvider)},
                    onSelectionChanged: (s) =>
                        ref.read(fiAssetGroupModeProvider.notifier).state = s.first,
                  ),
                ),
                FiGroupedPositionsList(
                  positions: data.positions,
                  mode: ref.watch(fiAssetGroupModeProvider),
                  onDelete: (ticker) => deletePosition(ref, ticker),
                  onSell: (p) => openSellDialog(context, ref, p),
                ),

                const SizedBox(height: 24),
                const FiClosedTradesSection(),
              ],
            );
          },
        ),
      ),
    );
  }
}

/// Vazio que diz o que falta, por quê e qual é o próximo passo (§42).
class _EmptyCarteira extends StatelessWidget {
  const _EmptyCarteira({required this.onAdd});

  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 48, 24, 24),
      children: [
        Icon(Icons.inbox_outlined, size: 40, color: fiInk3(context)),
        const SizedBox(height: 16),
        Text(
          'Nenhuma posição cadastrada',
          style: fiSerif(Theme.of(context).textTheme.titleMedium ?? const TextStyle()),
        ),
        const SizedBox(height: 8),
        Text(
          'A carteira é a base de tudo: sem ela o fiance não tem o que avaliar, '
          'comparar com meta ou usar para sugerir aporte.',
          style: TextStyle(color: fiInk2(context)),
        ),
        const SizedBox(height: 8),
        Text(
          'Cadastre o que você já tem — ticker, quantidade e preço médio.',
          style: TextStyle(color: fiInk3(context), fontSize: 12),
        ),
        const SizedBox(height: 20),
        FilledButton(onPressed: onAdd, child: const Text('Adicionar ativo')),
      ],
    );
  }
}
