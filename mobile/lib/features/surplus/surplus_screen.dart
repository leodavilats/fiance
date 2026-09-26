import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/cash_models.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/format.dart';
import '../../core/month.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/widgets/allocation_gap.dart';
import '../../core/widgets/nav_action.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/score_ruler.dart';

class SurplusScreen extends ConsumerWidget {
  const SurplusScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final surplus = ref.watch(surplusProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sobra'),
      ),
      body: surplus.when(
        loading: () => FiSkeleton.screen(
          shape: FiSkeletonShape.verdict,
          count: 1,
          label: 'Calculando sua sobra',
        ),
        error: (e, _) => FiErrorState(
          error: e,
          action: 'calcular sua sobra',
          onRetry: () => ref.invalidate(surplusProvider),
        ),
        data: (s) => s.hasCash ? _Body(surplus: s) : const _NoCash(),
      ),
    );
  }
}

class _Body extends ConsumerWidget {
  const _Body({required this.surplus});

  final Surplus surplus;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final m = surplus.month;
    final passos = surplus.cascade.steps;
    final temAporte = passos.any((p) => p.type == CascadeStepType.contribution);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(surplusProvider),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: [
          FiHeadline(
            eyebrow: 'Sobra de ${monthName(m.month)}',
            figure: m.hasRange
                ? '${formatCurrency(m.surplusLow)} — ${formatCurrency(m.surplusHigh)}'
                : formatCurrency(m.freeNow),
            support: m.hasRange
                ? 'A faixa é o número: o piso desconta o gasto variável que ainda deve sair, '
                      'estimado a partir de ${m.estimate.baseMonths.length} '
                      '${m.estimate.baseMonths.length == 1 ? 'mês fechado' : 'meses fechados'} seus.'
                : 'Sem mês fechado ainda não há base para estimar o que falta sair, então a '
                      'sobra é o próprio livre agora.',
          ),

          FiProvenance(
            summary: 'Como chegamos nesta faixa',
            method:
                'O livre agora, menos o gasto variável ainda esperado no mês. A estimativa sai '
                'só do seu histórico, com até três meses fechados.',
            source: m.estimate.baseMonths.isEmpty
                ? 'Sem mês fechado, não há histórico para estimar.'
                : 'Meses fechados usados: ${m.estimate.baseMonths.join(', ')}.',
            limitation:
                'Pagamento de dívida não entra na base: se entrasse, a estimativa diria que a '
                'rotina custa o que a dívida custa.',
          ),

          FiSection(
            title: passos.length > 1 ? 'A ordem' : 'O que fazer com ela',
            hint: passos.length > 1
                ? 'Cada passo consome a sobra antes do seguinte.'
                : null,

            child: Column(
              children: [
                for (final p in passos)
                  _Step(step: p, numbered: passos.length > 1),
                if (!temAporte) const _NoContribution(),
              ],
            ),
          ),

          if (temAporte) const _WhereToContribute(),
          if (temAporte) const _AgainstTarget(),
        ],
      ),
    );
  }
}

class _WhereToContribute extends ConsumerWidget {
  const _WhereToContribute();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final aporte = ref.watch(quickInvestProvider);

    return aporte.when(
      loading: () => const FiSection(
        title: 'Onde aportar',
        child: FiSkeleton(shape: FiSkeletonShape.row, count: 3),
      ),
      error: (e, _) => FiSection(
        title: 'Onde aportar',
        child: FiErrorState(
          error: e,
          action: 'calcular onde aportar',
          onRetry: () => ref.invalidate(quickInvestProvider),
        ),
      ),
      data: (r) {
        if (!r.hasDestination) {
          return FiSection(
            title: 'Onde aportar',
            child: FiEmptyLine(
              r.summary.isEmpty
                  ? 'Sem meta declarada não há alvo contra o que distribuir a sobra.'
                  : r.summary,
            ),
          );
        }

        final primeiros = r.allocations.take(3).toList();
        final restantes = r.allocations.length - primeiros.length;

        return FiSection(
          title: 'Onde aportar',
          hint: r.basis == 'goals'
              ? 'Do que está mais longe da alocação-alvo para o que está mais perto.'
              : 'Sem alocação-alvo declarada, a ordem sai pelo score do ativo.',
          action: FiNavAction(
            label: restantes > 0
                ? 'Ver os outros $restantes e simular'
                : 'Simular outro valor',
            onPressed: () => GoRouter.of(context).go('/sobra/aporte'),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final a in primeiros) _ContributionDestination(allocation: a),
              if (r.fixedIncome != null)
                _FixedIncomeDestination(slice: r.fixedIncome!),
            ],
          ),
        );
      },
    );
  }
}

class _ContributionDestination extends StatelessWidget {
  const _ContributionDestination({required this.allocation});

  final QuickInvestAllocation allocation;

  @override
  Widget build(BuildContext context) {
    final a = allocation;
    final brightness = Theme.of(context).brightness;

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        onTap: () => GoRouter.of(context).push('/ativo/${a.ticker}'),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        a.ticker,
                        style: FiType.ticker.copyWith(color: fiInk1(context)),
                      ),
                      Text(
                        a.name ?? categoryLabel(a.category),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: FiType.caption.copyWith(color: fiInk2(context)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: FiSpace.s3),
                FiTag.series(
                  label: categoryLabel(a.category),
                  color: categoryColor(a.category, brightness),
                ),
              ],
            ),
            if (a.score != null) ...[
              const SizedBox(height: FiSpace.s3),
              ScoreRuler(
                score: a.score!,
                size: ScoreRulerSize.inline,
                subject: 'Score de ${a.ticker}',
              ),
            ],
            const SizedBox(height: FiSpace.s3),
            Text(
              a.suggestedQuantity == null
                  ? '${_valueOrDash(a.suggestedInvestment)} · '
                        '${_valueOrDash(a.currentPrice)} por cota'
                  : '${a.suggestedQuantity} cota(s) · '
                        '${_valueOrDash(a.currentPrice)} cada · '
                        '${_valueOrDash(a.suggestedInvestment)}',
              style: FiType.caption.copyWith(color: fiInk2(context)),
            ),
            if (a.rationale.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s1),
              Text(
                a.rationale,
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _FixedIncomeDestination extends StatelessWidget {
  const _FixedIncomeDestination({required this.slice});

  final QuickInvestFixedIncome slice;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        onTap: () => GoRouter.of(context).go('/descobrir/renda-fixa'),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    'Renda fixa',
                    style: FiType.ticker.copyWith(color: fiInk1(context)),
                  ),
                ),
                const SizedBox(width: FiSpace.s3),
                Text(
                  _valueOrDash(slice.amount),
                  style: FiType.figure.copyWith(color: fiInk1(context)),
                ),
              ],
            ),
            const SizedBox(height: FiSpace.s2),
            Text(
              slice.rationale,
              style: FiType.caption.copyWith(color: fiInk2(context)),
            ),
          ],
        ),
      ),
    );
  }
}

String _valueOrDash(double? valor) =>
    valor == null ? '—' : formatCurrency(valor);

class _AgainstTarget extends ConsumerWidget {
  const _AgainstTarget();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final desvio = ref.watch(rebalanceSuggestionsProvider);

    return desvio.maybeWhen(
      loading: () => const FiSection(
        title: 'Contra a sua meta',
        child: FiSkeleton(shape: FiSkeletonShape.row, count: 3),
      ),
      data: (data) {
        final gaps = data.allocationGaps;
        if (gaps.isEmpty) {
          return FiSection(
            title: 'Contra a sua meta',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const FiEmptyLine(
                  'Você ainda não declarou metas de alocação. Sem elas o aporte acima sai pelo '
                  'score do ativo, e não por onde a sua carteira está desequilibrada.',
                ),
                const SizedBox(height: FiSpace.s3),
                FiNavAction(
                  label: 'Declarar metas de alocação',
                  onPressed: () => GoRouter.of(context).go('/voce/objetivos'),
                ),
              ],
            ),
          );
        }

        final maiores = [...gaps]
          ..sort((a, b) => b.gapPct.abs().compareTo(a.gapPct.abs()));
        final mostrados = maiores.take(3).toList();

        return FiSection(
          title: 'Contra a sua meta',
          hint: 'Os maiores desvios são o que o próximo aporte reequilibra.',
          action: FiNavAction(
            label: data.items.isEmpty
                ? 'Ver a alocação inteira'
                : 'Ver a alocação e ${data.items.length} '
                      '${data.items.length == 1 ? 'posição' : 'posições'}',
            onPressed: () => GoRouter.of(context).go('/sobra/desvio'),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final gap in mostrados)
                FiAllocationGap(
                  label: categoryLabel(gap.category),
                  currentPct: gap.currentPct,
                  targetPct: gap.targetPct,
                  barColor: categoryColor(
                    gap.category,
                    Theme.of(context).brightness,
                  ),
                ),
            ],
          ),
        );
      },
      orElse: () => const SizedBox.shrink(),
    );
  }
}

class _Step extends StatelessWidget {
  const _Step({required this.step, this.numbered = true});

  final CascadeStep step;
  final bool numbered;

  static const _labels = {
    CascadeStepType.debt: 'Dívida',
    CascadeStepType.reserve: 'Reserva',
    CascadeStepType.contribution: 'Aporte',
  };

  static const _origin = {
    'carteira': 'Medido contra o que a sua carteira rendeu.',
    'referencia_rf': 'Medido contra a referência de renda fixa.',
    'sem_taxa_informada': 'Sem a taxa da dívida não há como classificar o custo.',
    'sem_referencia': 'Sem carteira nem referência, a comparação usa o CDI.',
    'gasto_fixo_proprio': 'A base é o seu gasto fixo, não um número de mercado.',
    'meta': 'A ordem sai da alocação-alvo que você declarou.',
    'score': 'Sem alocação-alvo declarada, a ordem sai pelo score do ativo.',
  };

  FiState get _state => step.type == CascadeStepType.debt
      ? FiState.adverse
      : FiState.neutral;

  @override
  Widget build(BuildContext context) {
    final cor = fiStateColor(_state, Theme.of(context).brightness);

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s6),
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(width: 3, color: cor),
            const SizedBox(width: FiSpace.s4),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.baseline,
                    textBaseline: TextBaseline.alphabetic,
                    children: [
                      Expanded(
                        child: Text(
                          numbered
                              ? '${step.order} · ${_labels[step.type] ?? ''}'
                              : (_labels[step.type] ?? ''),
                          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                        ),
                      ),
                      Text(
                        formatCurrency(step.amount),
                        style: FiType.metricSm.copyWith(color: fiInk1(context)),
                      ),
                    ],
                  ),
                  const SizedBox(height: FiSpace.s2),
                  Text(
                    step.reason,
                    style: FiType.body.copyWith(color: fiInk1(context)),
                  ),
                  if (step.falsifier != null) ...[
                    const SizedBox(height: FiSpace.s1),
                    Text(
                      step.falsifier!,
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),
                  ],
                  if (_origin[step.reference] != null) ...[
                    const SizedBox(height: FiSpace.s1),
                    Text(
                      _origin[step.reference]!,
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NoContribution extends StatelessWidget {
  const _NoContribution();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: FiSpace.s2),
      child: Text(
        'A ordem termina sem passo de aporte, e isso é a resposta certa: com o que está acima '
        'consumindo a sobra, não aportar rende mais que aportar.',
        style: fiSerif(FiType.verdictSm).copyWith(color: fiInk1(context)),
      ),
    );
  }
}

class _NoCash extends StatelessWidget {
  const _NoCash();

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        FiEmptyState(
          title: 'Ainda não sei seu mês',
          body: 'A sobra sai do que entrou e do que saiu, e para isso preciso dos seus '
              'lançamentos. Comece pelo que se repete: o salário e os dois ou três maiores '
              'gastos fixos.',
          action: FiButton.primary(
            label: 'Ir para o Mês',
            onPressed: () => GoRouter.of(context).go('/mes'),
          ),
        ),
      ],
    );
  }
}
