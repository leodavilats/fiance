import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/theme.dart';

class DesvioScreen extends ConsumerWidget {
  const DesvioScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(rebalanceSuggestionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Alocação × meta')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(rebalanceSuggestionsProvider),
        child: async.when(
          loading: () => FiSkeleton.tela(
            shape: FiSkeletonShape.row,
            count: 5,
            label: 'Cruzando sua carteira com as metas',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos cruzar sua carteira com as metas',
            action: 'cruzar sua carteira com as metas que você declarou',
            onRetry: () => ref.invalidate(rebalanceSuggestionsProvider),
          ),
          data: (data) {
            final gaps = data.allocationGaps;
            final biggest = data.biggestGap;

            if (gaps.isEmpty) {
              return ListView(
                children: [
                  FiEmptyState(
                    title: 'Você ainda não declarou metas de alocação',
                    body: 'Sem elas o fiance não tem contra o que comparar a sua carteira — e '
                        'um alvo de mercado inventado seria pior que alvo nenhum.',
                    action: FiButton.primary(
                      label: 'Declarar metas de alocação',
                      onPressed: () => context.go('/voce/objetivos'),
                    ),
                  ),
                ],
              );
            }

            return ListView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                FiSpace.s2,
                FiLayout.gutter,
                FiLayout.scrollTail,
              ),
              children: [
                Text(
                  'ONDE VOCÊ ESTÁ × ONDE DEVERIA ESTAR',
                  style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                ),
                const SizedBox(height: FiSpace.s4),

                for (final gap in gaps)
                  _GapRow(
                    gap: gap,
                    escala: escalaDosGaps(gaps),
                    isBiggest: biggest != null && gap.category == biggest.category,
                  ),

                if (biggest != null)
                  FiSection(
                    title: 'A leitura',
                    action: FiButton.primary(
                      label: 'Tenho dinheiro para aportar',
                      onPressed: () => context.go('/sobra/aporte'),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Seu maior desvio está em ${categoryLabel(biggest.category)}.',
                          style: fiSerif(FiType.verdict).copyWith(color: fiInk1(context)),
                        ),
                        const SizedBox(height: FiSpace.s2),
                        Text(
                          'Sua exposição está '
                          '${biggest.gapPct.abs().toStringAsFixed(1)} pontos percentuais '
                          '${biggest.isBelowTarget ? 'abaixo' : 'acima'} do objetivo '
                          '(${biggest.currentPct.toStringAsFixed(1)}% contra '
                          '${biggest.targetPct.toStringAsFixed(1)}%).',
                          style: FiType.body.copyWith(color: fiInk2(context)),
                        ),
                        const SizedBox(height: FiSpace.s3),
                        Text(
                          biggest.isBelowTarget
                              ? 'Para aproximar sua carteira da meta, o próximo aporte poderia '
                                    'priorizar ${categoryLabel(biggest.category)}.'
                              : 'A categoria ${categoryLabel(biggest.category)} passou da meta. '
                                    'Novos aportes em outras classes reequilibram sem precisar '
                                    'vender.',
                          style: FiType.body.copyWith(color: fiInk2(context)),
                        ),
                      ],
                    ),
                  ),

                if (data.items.isNotEmpty)
                  FiSection(
                    title: 'Posições para revisar',
                    count: data.items.length,
                    child: Column(
                      children: [
                        for (final item in data.items) _RebalanceObject(item: item),
                      ],
                    ),
                  ),

                if (data.taxDisclaimer != null) ...[
                  const SizedBox(height: FiSpace.s5),
                  Text(
                    data.taxDisclaimer!,
                    style: FiType.caption.copyWith(color: fiInk3(context)),
                  ),
                ],

                FiSection(
                  title: 'Ferramentas',
                  child: FiRows(
                    children: [
                      FiDataRow(
                        label: 'Ajustar minhas metas',
                        onTap: () => context.go('/voce/objetivos'),
                      ),
                      FiDataRow(
                        label: 'Comparar títulos de renda fixa',
                        onTap: () => context.go('/descobrir/renda-fixa'),
                      ),
                      FiDataRow(
                        label: 'Renda fixa × bolsa',
                        onTap: () => context.go('/descobrir/renda-fixa-vs-bolsa'),
                      ),
                      FiDataRow(
                        label: 'Projetar renda passiva',
                        onTap: () => context.go('/patrimonio/projecao'),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: FiSpace.s6),
                Text(
                  'Estimativas a partir de dado público. Não é recomendação de investimento.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

double escalaDosGaps(List<AllocationGap> gaps) {
  var maior = 0.0;
  for (final gap in gaps) {
    if (gap.currentPct > maior) maior = gap.currentPct;
    if (gap.targetPct > maior) maior = gap.targetPct;
  }
  if (maior <= 0) return 100;
  return (maior * 1.15).clamp(10, 100);
}

class _GapRow extends StatelessWidget {
  const _GapRow({
    required this.gap,
    required this.isBiggest,
    required this.escala,
  });

  final AllocationGap gap;
  final bool isBiggest;
  final double escala;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink1 = fiInk1Of(brightness);
    final ink3 = fiInk3Of(brightness);

    final relevante = gap.gapPct.abs() >= 2;
    final falta = gap.gapPct > 0;
    final corDaCategoria = categoryColor(gap.category, brightness);
    final corDoDesvio = relevante
        ? fiStateColor(FiState.attention, brightness)
        : ink3;

    final atual = (gap.currentPct / escala).clamp(0.0, 1.0);
    final meta = (gap.targetPct / escala).clamp(0.0, 1.0);
    final inicioDoDesvio = atual < meta ? atual : meta;
    final fimDoDesvio = atual < meta ? meta : atual;

    return Semantics(
      label:
          '${categoryLabel(gap.category)}: '
          '${gap.currentPct.toStringAsFixed(1)}% da carteira contra meta de '
          '${gap.targetPct.toStringAsFixed(1)}% — '
          '${gap.gapPct.abs().toStringAsFixed(1)} pontos percentuais '
          '${falta ? 'abaixo' : 'acima'}',
      child: ExcludeSemantics(
        child: Padding(
          padding: const EdgeInsets.only(bottom: FiSpace.s5),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Expanded(
                    child: Text(
                      categoryLabel(gap.category),
                      style: FiType.body.copyWith(
                        color: ink1,
                        fontWeight: isBiggest ? FontWeight.w600 : FontWeight.w400,
                      ),
                    ),
                  ),
                  Text(
                    '${gap.currentPct.toStringAsFixed(0)}%',
                    style: FiType.figure.copyWith(color: ink1),
                  ),
                  Text(
                    ' de ${gap.targetPct.toStringAsFixed(0)}%',
                    style: FiType.caption.copyWith(color: ink3),
                  ),
                ],
              ),
              const SizedBox(height: FiSpace.s2),
              LayoutBuilder(
                builder: (context, constraints) {
                  final largura = constraints.maxWidth;
                  return SizedBox(
                    height: 12,
                    child: Stack(
                      children: [
                        Positioned(
                          left: 0,
                          right: 0,
                          top: 2,
                          height: 8,
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: fiGround2(brightness),
                              borderRadius: BorderRadius.circular(FiRadius.sm),
                            ),
                          ),
                        ),
                        Positioned(
                          left: largura * inicioDoDesvio,
                          width: largura * (fimDoDesvio - inicioDoDesvio),
                          top: 2,
                          height: 8,
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: corDoDesvio.withValues(
                                alpha: falta ? 0.22 : 0.32,
                              ),
                              borderRadius: BorderRadius.circular(FiRadius.sm),
                            ),
                          ),
                        ),
                        Positioned(
                          left: 0,
                          width: largura * atual,
                          top: 2,
                          height: 8,
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: corDaCategoria,
                              borderRadius: BorderRadius.circular(FiRadius.sm),
                            ),
                          ),
                        ),
                        Positioned(
                          left: (largura * meta - 1).clamp(0.0, largura - 2),
                          top: 0,
                          bottom: 0,
                          width: 2,
                          child: ColoredBox(color: ink1),
                        ),
                      ],
                    ),
                  );
                },
              ),
              const SizedBox(height: FiSpace.s1),
              Text(
                relevante
                    ? (falta
                          ? 'faltam ${gap.gapPct.abs().toStringAsFixed(1)} p.p. para a meta'
                          : '${gap.gapPct.abs().toStringAsFixed(1)} p.p. acima da meta')
                    : 'dentro da meta',
                style: FiType.caption.copyWith(color: corDoDesvio),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RebalanceObject extends StatelessWidget {
  const _RebalanceObject({required this.item});

  final RebalanceItem item;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final estado = _actionState(item.action);

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        onTap: () => context.push('/ativo/${item.ticker}'),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    item.ticker,
                    style: FiType.ticker.copyWith(color: fiInk1(context)),
                  ),
                ),
                FiTag(label: _actionLabel(item.action), state: estado),
              ],
            ),
            if (item.reasons.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s2),
              Text(
                item.reasons.first,
                style: FiType.body.copyWith(color: fiInk2(context)),
              ),
            ],
            if (item.requiresTaxReview) ...[
              const SizedBox(height: FiSpace.s1),
              Text(
                'Vender aqui pode gerar IR — vale conferir antes.',
                style: FiType.caption.copyWith(
                  color: fiStateColor(FiState.attention, brightness),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _actionLabel(String action) => switch (action) {
    'comprar_mais' => 'Abaixo da meta',
    'vender' => 'Sinal de venda',
    'realocar' => 'Realocar',
    _ => 'Manter',
  };

  FiState _actionState(String action) => switch (action) {
    'comprar_mais' => FiState.favorable,
    'vender' => FiState.adverse,
    'realocar' => FiState.attention,
    _ => FiState.neutral,
  };
}
