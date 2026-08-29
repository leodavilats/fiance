import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/design_tokens.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';

class EstrategiaScreen extends ConsumerWidget {
  const EstrategiaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(rebalanceSuggestionsProvider);
    final brightness = Theme.of(context).brightness;
    final isDark = brightness == Brightness.dark;
    final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;
    final ink3 = isDark ? FiColors.darkInk3 : FiColors.lightInk3;
    final hairline = isDark ? FiColors.darkHairline : FiColors.lightHairline;

    return Scaffold(
      appBar: AppBar(title: const Text('Estratégia')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(rebalanceSuggestionsProvider),
        child: async.when(
          loading: () => const _Skeleton(),
          error: (err, _) => _ErrorState(
            onRetry: () => ref.invalidate(rebalanceSuggestionsProvider),
          ),
          data: (data) {
            final gaps = data.allocationGaps;
            final biggest = data.biggestGap;

            return ListView(
              padding: const EdgeInsets.all(FiSpace.s4),
              children: [
                Text(
                  'ONDE VOCÊ ESTÁ × ONDE DEVERIA ESTAR',
                  style: FiType.eyebrow.copyWith(color: ink3),
                ),
                const SizedBox(height: FiSpace.s3),

                if (gaps.isEmpty)
                  _NoGoals(ink2: ink2)
                else
                  ...gaps.map(
                    (gap) => _GapRow(
                      gap: gap,
                      escala: escalaDosGaps(gaps),
                      isBiggest:
                          biggest != null && gap.category == biggest.category,
                    ),
                  ),

                if (gaps.isNotEmpty) ...[
                  const SizedBox(height: FiSpace.s6),
                  Divider(color: hairline, height: 1),
                  const SizedBox(height: FiSpace.s6),

                  if (biggest != null) ...[
                    Text(
                      'Seu maior gap está em ${categoryLabel(biggest.category)}.',
                      style: FiType.verdict.copyWith(
                        fontFamily: fiFontSerif,
                        color: isDark ? FiColors.darkInk1 : FiColors.lightInk1,
                      ),
                    ),
                    const SizedBox(height: FiSpace.s2),
                    Text(
                      'Sua exposição está ${biggest.gapPct.abs().toStringAsFixed(1)} pontos '
                      'percentuais ${biggest.isBelowTarget ? 'abaixo' : 'acima'} do objetivo '
                      '(${biggest.currentPct.toStringAsFixed(1)}% contra '
                      '${biggest.targetPct.toStringAsFixed(1)}%).',
                      style: FiType.body.copyWith(color: ink2),
                    ),
                    const SizedBox(height: FiSpace.s3),

                    Container(
                      padding: const EdgeInsets.all(FiSpace.s4),
                      decoration: BoxDecoration(
                        border: Border.all(color: hairline),
                        borderRadius: BorderRadius.circular(FiRadius.md),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'SUGESTÃO',
                            style: FiType.eyebrow.copyWith(color: ink3),
                          ),
                          const SizedBox(height: FiSpace.s2),
                          Text(
                            biggest.isBelowTarget
                                ? 'Para aproximar sua carteira da meta, o próximo aporte poderia '
                                      'priorizar ${categoryLabel(biggest.category)}.'
                                : 'A categoria ${categoryLabel(biggest.category)} passou da meta. '
                                      'Novos aportes em outras classes reequilibram sem precisar vender.',
                            style: FiType.body.copyWith(color: ink2),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: FiSpace.s4),
                  ],

                  FilledButton.icon(
                    onPressed: () => context.go('/estrategia/aporte'),
                    icon: const Icon(Icons.savings_outlined, size: 18),
                    label: const Text('Tenho dinheiro para aportar'),
                  ),
                ],

                if (data.items.isNotEmpty) ...[
                  const SizedBox(height: FiSpace.s6),
                  Divider(color: hairline, height: 1),
                  const SizedBox(height: FiSpace.s6),
                  Text(
                    'POSIÇÕES PARA REVISAR',
                    style: FiType.eyebrow.copyWith(color: ink3),
                  ),
                  const SizedBox(height: FiSpace.s3),
                  ...data.items.map((item) => _RebalanceTile(item: item)),
                ],

                if (data.taxDisclaimer != null) ...[
                  const SizedBox(height: FiSpace.s5),
                  Text(
                    data.taxDisclaimer!,
                    style: FiType.caption.copyWith(color: ink3),
                  ),
                ],

                const SizedBox(height: FiSpace.s6),
                Divider(color: hairline, height: 1),
                const SizedBox(height: FiSpace.s5),
                Text(
                  'FERRAMENTAS',
                  style: FiType.eyebrow.copyWith(color: ink3),
                ),
                const SizedBox(height: FiSpace.s2),
                _ToolLink(
                  label: 'Ajustar minhas metas',
                  icon: Icons.flag_outlined,
                  onTap: () => context.go('/estrategia/metas'),
                ),
                _ToolLink(
                  label: 'Comparar títulos de renda fixa',
                  icon: Icons.account_balance_outlined,
                  onTap: () => context.go('/estrategia/renda-fixa'),
                ),
                _ToolLink(
                  label: 'Renda fixa × bolsa',
                  icon: Icons.compare_arrows_outlined,
                  onTap: () => context.go('/estrategia/renda-fixa-vs-bolsa'),
                ),
                _ToolLink(
                  label: 'Projetar renda passiva',
                  icon: Icons.timeline_outlined,
                  onTap: () => context.go('/estrategia/projecao'),
                ),
                const SizedBox(height: FiSpace.s5),
                Text(
                  'Estimativas a partir de dado público. Não é recomendação de investimento.',
                  style: FiType.caption.copyWith(color: ink3),
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
    final isDark = brightness == Brightness.dark;
    final ink1 = isDark ? FiColors.darkInk1 : FiColors.lightInk1;
    final ink3 = isDark ? FiColors.darkInk3 : FiColors.lightInk3;
    final ground2 = isDark ? FiColors.darkGround2 : FiColors.lightGround2;

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
      child: Padding(
        padding: const EdgeInsets.only(bottom: FiSpace.s4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    categoryLabel(gap.category),
                    style: FiType.label.copyWith(
                      color: ink1,
                      fontWeight: isBiggest ? FontWeight.w600 : FontWeight.w500,
                    ),
                  ),
                ),
                Text(
                  '${gap.currentPct.toStringAsFixed(0)}%',
                  style: FiType.metricSm.copyWith(color: ink1),
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
                  height: 14,
                  child: Stack(
                    clipBehavior: Clip.none,
                    children: [
                      Positioned(
                        left: 0,
                        right: 0,
                        top: 3,
                        height: 8,
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            color: ground2,
                            borderRadius: BorderRadius.circular(FiRadius.sm),
                          ),
                        ),
                      ),
                      Positioned(
                        left: largura * inicioDoDesvio,
                        width: largura * (fimDoDesvio - inicioDoDesvio),
                        top: 3,
                        height: 8,
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            color: corDoDesvio.withValues(alpha: falta ? 0.22 : 0.32),
                            borderRadius: BorderRadius.circular(FiRadius.sm),
                          ),
                        ),
                      ),

                      Positioned(
                        left: 0,
                        width: largura * atual,
                        top: 3,
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
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            color: ink1,
                            borderRadius: BorderRadius.circular(1),
                          ),
                        ),
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
    );
  }
}

class _RebalanceTile extends StatelessWidget {
  const _RebalanceTile({required this.item});

  final RebalanceItem item;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final isDark = brightness == Brightness.dark;
    final ink1 = isDark ? FiColors.darkInk1 : FiColors.lightInk1;
    final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;
    final hairline = isDark ? FiColors.darkHairline : FiColors.lightHairline;

    return Container(
      margin: const EdgeInsets.only(bottom: FiSpace.s2),
      padding: const EdgeInsets.all(FiSpace.s3),
      decoration: BoxDecoration(
        border: Border.all(color: hairline),
        borderRadius: BorderRadius.circular(FiRadius.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  item.ticker,
                  style: FiType.ticker.copyWith(color: ink1),
                ),
              ),
              Text(
                _actionLabel(item.action),
                style: FiType.caption.copyWith(
                  color: fiStateColor(_actionState(item.action), brightness),
                ),
              ),
            ],
          ),
          if (item.reasons.isNotEmpty) ...[
            const SizedBox(height: FiSpace.s1),
            Text(item.reasons.first, style: FiType.body.copyWith(color: ink2)),
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

class _NoGoals extends StatelessWidget {
  const _NoGoals({required this.ink2});

  final Color ink2;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Você ainda não definiu metas de alocação. Sem elas, o fiance não tem contra o que '
          'comparar a sua carteira.',
          style: FiType.body.copyWith(color: ink2),
        ),
        const SizedBox(height: FiSpace.s3),
        FilledButton(
          onPressed: () => context.go('/estrategia/metas'),
          child: const Text('Definir metas'),
        ),
      ],
    );
  }
}

class _ToolLink extends StatelessWidget {
  const _ToolLink({
    required this.label,
    required this.icon,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return ListTile(
      contentPadding: EdgeInsets.zero,
      minVerticalPadding: FiSpace.s3,
      leading: Icon(icon, size: 20),
      title: Text(label, style: FiType.body),
      trailing: const Icon(Icons.chevron_right, size: 20),
      textColor: isDark ? FiColors.darkInk1 : FiColors.lightInk1,
      iconColor: isDark ? FiColors.darkInk2 : FiColors.lightInk2,
      onTap: onTap,
    );
  }
}

class _Skeleton extends StatelessWidget {
  const _Skeleton();

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final block = isDark ? FiColors.darkGround2 : FiColors.lightGround2;

    Widget bar(double width, double height) => Container(
      width: width,
      height: height,
      margin: const EdgeInsets.only(bottom: FiSpace.s3),
      decoration: BoxDecoration(
        color: block,
        borderRadius: BorderRadius.circular(4),
      ),
    );

    return ListView(
      padding: const EdgeInsets.all(FiSpace.s4),
      children: [
        bar(180, 12),
        for (var i = 0; i < 4; i++) bar(double.infinity, 20),
        const SizedBox(height: FiSpace.s4),
        bar(240, 24),
      ],
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;

    return ListView(
      padding: const EdgeInsets.all(FiSpace.s4),
      children: [
        Text(
          'Não conseguimos montar sua estratégia agora',
          style: FiType.verdict.copyWith(fontFamily: fiFontSerif),
        ),
        const SizedBox(height: FiSpace.s2),
        Text(
          'Pode ser a conexão ou uma instabilidade na fonte de cotações. Suas metas e posições '
          'estão salvas.',
          style: FiType.body.copyWith(color: ink2),
        ),
        const SizedBox(height: FiSpace.s4),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton(
            onPressed: onRetry,
            child: const Text('Tentar de novo'),
          ),
        ),
      ],
    );
  }
}
