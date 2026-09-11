import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/cash_models.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/search_action.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/format.dart';
import '../../core/mes.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/nav_action.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';

class SobraScreen extends ConsumerWidget {
  const SobraScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sobra = ref.watch(surplusProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sobra'),
        actions: const [FiSearchAction()],
      ),
      body: sobra.when(
        loading: () => FiSkeleton.tela(
          shape: FiSkeletonShape.verdict,
          count: 1,
          label: 'Calculando sua sobra',
        ),
        error: (e, _) => FiErrorState(
          error: e,
          action: 'calcular sua sobra',
          onRetry: () => ref.invalidate(surplusProvider),
        ),
        data: (s) => s.hasCash ? _Corpo(sobra: s) : const _SemCaixa(),
      ),
    );
  }
}

class _Corpo extends ConsumerWidget {
  const _Corpo({required this.sobra});

  final Surplus sobra;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final m = sobra.month;
    final passos = sobra.cascade.steps;
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
            eyebrow: 'Sobra de ${nomeDoMes(m.month)}',
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
            action: temAporte
                ? FiNavAction(
                    label: 'Alocação × meta',
                    onPressed: () => GoRouter.of(context).go('/sobra/desvio'),
                  )
                : null,
            child: Column(
              children: [
                for (final p in passos)
                  _Passo(
                    passo: p,
                    numerado: passos.length > 1,
                    destino: p.type == CascadeStepType.contribution
                        ? () => GoRouter.of(context).go('/sobra/aporte')
                        : null,
                  ),
                if (!temAporte) const _SemAporte(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Passo extends StatelessWidget {
  const _Passo({required this.passo, this.numerado = true, this.destino});

  final CascadeStep passo;
  final bool numerado;

  final VoidCallback? destino;

  static const _rotulos = {
    CascadeStepType.debt: 'Dívida',
    CascadeStepType.reserve: 'Reserva',
    CascadeStepType.contribution: 'Aporte',
  };

  static const _origem = {
    'carteira': 'Medido contra o que a sua carteira rendeu.',
    'referencia_rf': 'Medido contra a referência de renda fixa.',
    'sem_taxa_informada': 'Sem a taxa da dívida não há como classificar o custo.',
    'sem_referencia': 'Sem carteira nem referência, a comparação usa o CDI.',
    'gasto_fixo_proprio': 'A base é o seu gasto fixo, não um número de mercado.',
    'meta': 'A ordem sai da alocação-alvo que você declarou.',
    'score': 'Sem alocação-alvo declarada, a ordem sai pelo score do ativo.',
  };

  FiState get _estado => passo.type == CascadeStepType.debt
      ? FiState.adverse
      : FiState.neutral;

  @override
  Widget build(BuildContext context) {
    final cor = fiStateColor(_estado, Theme.of(context).brightness);

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
                          numerado
                              ? '${passo.order} · ${_rotulos[passo.type] ?? ''}'
                              : (_rotulos[passo.type] ?? ''),
                          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                        ),
                      ),
                      Text(
                        formatCurrency(passo.amount),
                        style: FiType.metricSm.copyWith(color: fiInk1(context)),
                      ),
                    ],
                  ),
                  const SizedBox(height: FiSpace.s2),
                  Text(
                    passo.reason,
                    style: FiType.body.copyWith(color: fiInk1(context)),
                  ),
                  if (passo.falsifier != null) ...[
                    const SizedBox(height: FiSpace.s1),
                    Text(
                      passo.falsifier!,
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),
                  ],
                  if (_origem[passo.reference] != null) ...[
                    const SizedBox(height: FiSpace.s1),
                    Text(
                      _origem[passo.reference]!,
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),
                  ],
                  if (destino != null) ...[
                    const SizedBox(height: FiSpace.s3),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: FiButton.primary(
                        label: 'Onde aportar ${formatCurrency(passo.amount)}',
                        onPressed: destino,
                      ),
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

class _SemAporte extends StatelessWidget {
  const _SemAporte();

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

class _SemCaixa extends StatelessWidget {
  const _SemCaixa();

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
