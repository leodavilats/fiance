import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/help_tooltip.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/score_ruler.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/theme.dart';

const fiRelevantGapPp = 2.0;

class AllocationDriftScreen extends ConsumerWidget {
  const AllocationDriftScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(rebalanceSuggestionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Desvio de alocação')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(rebalanceSuggestionsProvider),
        child: async.when(
          loading: () => FiSkeleton.screen(
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
            final maior = data.biggestGap;
            final biggest =
                maior != null && maior.gapPct.abs() >= fiRelevantGapPp ? maior : null;
            final revisarImposto =
                data.taxDisclaimer != null && data.items.any((i) => i.requiresTaxReview);

            if (gaps.isEmpty) return _NoGaps(hasItems: data.items.isNotEmpty);

            return ListView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                FiSpace.s2,
                FiLayout.gutter,
                FiLayout.scrollTail,
              ),
              children: [
                Text(
                  'SUA CARTEIRA CONTRA A META',
                  style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                ),
                const SizedBox(height: FiSpace.s4),

                for (final gap in gaps)
                  _GapRow(
                    gap: gap,
                    scale: gapScale(gaps),
                    isBiggest: biggest != null && gap.category == biggest.category,
                  ),

                if (biggest == null)
                  FiSection(
                    title: 'A leitura',
                    action: FiButton.primary(
                      label: 'Tenho dinheiro para aportar',
                      onPressed: () => context.go('/sobra/aporte'),
                    ),
                    child: FiEmptyLine(
                      'Nenhuma classe está a ${formatPoints(fiRelevantGapPp, digits: 0)} ou mais '
                      'da meta, então não há desvio que peça ajuste agora.',
                    ),
                  )
                else
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
                          'Sua exposição está ${formatPoints(biggest.gapPct.abs())} '
                          '${biggest.isBelowTarget ? 'abaixo' : 'acima'} da meta '
                          '(${formatPercent(biggest.currentPct, digits: 1)} contra '
                          '${formatPercent(biggest.targetPct, digits: 0)}).',
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
                    trailing: const _RankingProfile(),
                    child: Column(
                      children: [
                        for (final item in data.items) _RebalanceObject(item: item),
                      ],
                    ),
                  ),

                if (revisarImposto) ...[
                  const SizedBox(height: FiSpace.s5),
                  Text(
                    data.taxDisclaimer!,
                    style: FiType.caption.copyWith(color: fiInk3(context)),
                  ),
                ],

              ],
            );
          },
        ),
      ),
    );
  }
}

double gapScale(List<AllocationGap> gaps) {
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
    required this.scale,
  });

  final AllocationGap gap;
  final bool isBiggest;
  final double scale;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ink1 = fiInk1Of(brightness);
    final ink3 = fiInk3Of(brightness);

    final band = fiBandFor(gap.gapPct.abs(), fiAllocationGapBands, 1);
    final relevante = band.id != 'on-target';
    final falta = gap.gapPct > 0;
    final categoryBarColor = categoryColor(gap.category, brightness);
    final driftColor = band.id == 'relevant'
        ? fiStateColor(FiState.attention, brightness)
        : ink3;

    final current = (gap.currentPct / scale).clamp(0.0, 1.0);
    final meta = (gap.targetPct / scale).clamp(0.0, 1.0);
    final inicioDoDesvio = current < meta ? current : meta;
    final fimDoDesvio = current < meta ? meta : current;

    return Semantics(
      label:
          '${categoryLabel(gap.category)}: '
          '${formatPercent(gap.currentPct, digits: 1)} da carteira contra meta de '
          '${formatPercent(gap.targetPct, digits: 0)} — '
          '${relevante ? '${formatDecimal(gap.gapPct.abs())} pontos percentuais '
                    '${falta ? 'abaixo' : 'acima'}' : 'na meta'}',
      child: ExcludeSemantics(
        child: Padding(
          padding: const EdgeInsets.only(bottom: FiSpace.s5),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: double.infinity,
                child: Wrap(
                  alignment: WrapAlignment.spaceBetween,
                  crossAxisAlignment: WrapCrossAlignment.end,
                  spacing: FiSpace.s3,
                  children: [
                    Text(
                      categoryLabel(gap.category),
                      style: FiType.body.copyWith(
                        color: ink1,
                        fontWeight: isBiggest ? FontWeight.w600 : FontWeight.w400,
                      ),
                    ),
                    Text.rich(
                      TextSpan(
                        children: [
                          TextSpan(
                            text: formatPercent(gap.currentPct, digits: 1),
                            style: FiType.figure.copyWith(color: ink1),
                          ),
                          TextSpan(
                            text: ' de ${formatPercent(gap.targetPct, digits: 0)}',
                            style: FiType.caption.copyWith(color: ink3),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
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
                              color: driftColor.withValues(
                                alpha: falta ? 0.22 : 0.32,
                              ),
                              borderRadius: BorderRadius.circular(FiRadius.sm),
                            ),
                          ),
                        ),
                        Positioned(
                          left: 0,
                          width: largura * current,
                          top: 2,
                          height: 8,
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: categoryBarColor,
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
                          ? 'faltam ${formatPoints(gap.gapPct.abs())} para a meta'
                          : '${formatPoints(gap.gapPct.abs())} acima da meta')
                    : 'na meta',
                style: FiType.caption.copyWith(color: driftColor),
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
                const SizedBox(width: FiSpace.s2),
                Flexible(
                  child: FiTag(label: _actionLabel(item.action), state: estado),
                ),
              ],
            ),
            if (item.reasons.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s2),
              for (final razao in item.reasons.take(3))
                Padding(
                  padding: const EdgeInsets.only(bottom: FiSpace.s1),
                  child: Text(
                    razao,
                    style: FiType.body.copyWith(color: fiInk2(context)),
                  ),
                ),
            ],
            if (item.reallocateTo != null) ...[
              const SizedBox(height: FiSpace.s2),
              _Reallocation(
                target: item.reallocateTo!,
                sentence: item.adjustmentSentence,
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _actionLabel(String action) => switch (action) {
    'comprar_mais' => 'Abaixo da meta',
    'vender' => 'Acima do preço justo',
    'realocar' => 'Acima do preço justo',
    _ => 'Sem ajuste',
  };

  FiState _actionState(String action) => switch (action) {
    'vender' || 'realocar' => FiState.attention,
    _ => FiState.neutral,
  };
}

class _Reallocation extends StatelessWidget {
  const _Reallocation({required this.target, this.sentence});

  final RebalanceTarget target;
  final String? sentence;

  @override
  Widget build(BuildContext context) {
    final detalhe = [
      target.label ?? target.name,
      if (target.price != null) formatAge(target.asOf),
    ].whereType<String>().where((t) => t.isNotEmpty).join(' · ');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'PARA ONDE IRIA',
          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
        ),
        if (sentence != null) ...[
          const SizedBox(height: FiSpace.s1),
          Text(
            sentence!,
            style: fiSerif(FiType.verdictSm).copyWith(color: fiInk1(context)),
          ),
        ],
        FiRows(
          children: [
            FiDataRow(
              label: target.ticker,
              value: target.price == null ? null : formatCurrency(target.price),
              detail: detalhe.isEmpty ? null : detalhe,
              onTap: () => context.push('/ativo/${target.ticker}'),
            ),
            if (target.fairLow != null && target.fairHigh != null)
              FiDataRow(
                label: 'Faixa de preço justo',
                value: '${formatCurrency(target.fairLow)} a ${formatCurrency(target.fairHigh)}',
              ),
          ],
        ),
        const SizedBox(height: FiSpace.s2),
        ScoreRuler(
          score: target.score,
          size: ScoreRulerSize.list,
          subject: 'Score de ${target.ticker}',
        ),
        const SizedBox(height: FiSpace.s2),
        const FiProvenance(
          summary: 'Como chegamos nesta troca',
          method:
              'A troca aparece quando o ativo que você tem está acima da faixa de preço justo '
              'e há, numa classe abaixo da sua meta de alocação, um ativo abaixo da faixa. '
              'Entre eles, o de maior score.',
          source: 'Suas posições, suas metas de alocação e preços da BRAPI.',
          limitation:
              'Não considera imposto, corretagem nem o seu preço médio. A faixa é a do modelo '
              'da classe do ativo; a folha dele mostra a base.',
        ),
      ],
    );
  }
}

class _NoGaps extends ConsumerWidget {
  const _NoGaps({required this.hasItems});

  final bool hasItems;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final metas = ref.watch(goalsProvider);

    return metas.when(
      loading: () => FiSkeleton.screen(
        shape: FiSkeletonShape.row,
        count: 3,
        label: 'Lendo suas metas de alocação',
      ),
      error: (err, _) => FiErrorState(
        error: err,
        action: 'ler suas metas de alocação',
        onRetry: () => ref.invalidate(goalsProvider),
      ),
      data: (goals) {
        final declarou = goals.any((g) => g.declared);
        final vazio = !declarou
            ? FiEmptyState(
                title: 'Você ainda não declarou metas de alocação',
                body: 'Sem elas o fiance não tem contra o que comparar a sua carteira — e '
                    'um alvo de mercado inventado seria pior que alvo nenhum.',
                action: FiButton.primary(
                  label: 'Declarar metas de alocação',
                  onPressed: () => context.go('/voce/objetivos'),
                ),
              )
            : !hasItems
            ? FiEmptyState(
                title: 'Ainda não há carteira para comparar com as metas',
                body: 'Cadastre suas posições ou sua renda fixa e o desvio aparece aqui.',
                action: FiButton.primary(
                  label: 'Ir para o Patrimônio',
                  onPressed: () => context.go('/patrimonio'),
                ),
              )
            : FiEmptyState(
                title: 'Nenhuma classe está longe da sua meta de alocação',
                body: 'Sua carteira está perto do que você declarou, então não há desvio a '
                    'corrigir agora.',
                action: FiButton.primary(
                  label: 'Tenho dinheiro para aportar',
                  onPressed: () => context.go('/sobra/aporte'),
                ),
              );

        return ListView(children: [vazio]);
      },
    );
  }
}

class _RankingProfile extends ConsumerWidget {
  const _RankingProfile();

  static const _labels = {
    'conservative': 'conservador',
    'moderate': 'moderado',
    'aggressive': 'arrojado',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prefs = ref.watch(preferencesProvider);

    return prefs.maybeWhen(
      data: (p) {
        final label = _labels[p.riskProfile] ?? p.riskProfile;
        return HelpTooltip(termKey: 'perfil_de_risco', label: 'perfil $label');
      },
      orElse: () => const SizedBox.shrink(),
    );
  }
}
