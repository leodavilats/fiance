import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/cash_models.dart';
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

/// A Sobra: "o que devo fazer com o que ficou?"
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
        loading: () => FiSkeleton.tela(shape: FiSkeletonShape.verdict, count: 1, label: 'Calculando sua sobra'),
        error: (e, _) => FiErrorState(
          error: e,
          action: 'calcular sua sobra',
          onRetry: () => ref.invalidate(surplusProvider),
        ),
        data: (s) => s.hasCash
            ? _Corpo(sobra: s)
            : const _SemCaixa(),
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
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          Text(
            'SOBRA DE ${nomeDoMes(m.month).toUpperCase()}',
            style: FiType.eyebrow.copyWith(color: fiInk3(context)),
          ),
          const SizedBox(height: FiSpace.s1),
          if (m.hasRange)
            Text(
              '${formatCurrency(m.surplusLow)} — ${formatCurrency(m.surplusHigh)}',
              style: FiType.moneyLg,
            )
          else
            Text(formatCurrency(m.freeNow), style: FiType.moneyLg),

          const SizedBox(height: FiSpace.s2),
          Text(
            m.hasRange
                ? 'A faixa é o número: o piso desconta o gasto variável que ainda deve sair, '
                      'estimado a partir de ${m.estimate.baseMonths.length} '
                      '${m.estimate.baseMonths.length == 1 ? 'mês fechado' : 'meses fechados'} seus.'
                : 'Sem mês fechado ainda não há base para estimar o que falta sair, então a '
                      'sobra é o próprio livre agora.',
            style: FiType.body.copyWith(color: fiInk2(context)),
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

          // Com um passo so, "A ordem" anunciava uma sequencia que nao existe -- e o unico
          // passo ficava com cara de item de lista. A cascata so se chama ordem quando ha o
          // que ordenar.
          FiSection(
            title: passos.length > 1 ? 'A ordem' : 'O que fazer com ela',
            hint: passos.length > 1
                ? 'Cada passo consome a sobra antes do seguinte.'
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

          if (temAporte)
            Align(
              alignment: Alignment.centerLeft,
              child: FiNavAction(
                label: 'Alocação × meta',
                onPressed: () => GoRouter.of(context).go('/sobra/desvio'),
              ),
            ),
        ],
      ),
    );
  }
}

/// Um passo da cascata: o quanto, a razão, e o que o derrubaria.
class _Passo extends StatelessWidget {
  const _Passo({required this.passo, this.numerado = true, this.destino});

  final CascadeStep passo;
  final bool numerado;

  /// A porta para onde o passo se resolve. Só o aporte tem uma.
  final VoidCallback? destino;

  static const _rotulos = {
    CascadeStepType.debt: 'Dívida',
    CascadeStepType.reserve: 'Reserva',
    CascadeStepType.contribution: 'Aporte',
  };

  /// `reference` é o nome interno da régua que decidiu o passo, e chegava cru à tela: quem
  /// lia a Sobra via a palavra `score` ou `gasto_fixo_proprio` solta embaixo do valor. O que
  /// a pessoa precisa saber é contra o que o passo foi medido.
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
      padding: const EdgeInsets.only(bottom: FiSpace.s5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(width: 3, height: 44, color: cor),
          const SizedBox(width: FiSpace.s3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        numerado
                            ? '${passo.order} · ${_rotulos[passo.type] ?? ''}'
                            : (_rotulos[passo.type] ?? ''),
                        style: FiType.eyebrow.copyWith(color: fiInk3(context)),
                      ),
                    ),
                    Text(formatCurrency(passo.amount), style: FiType.metricSm),
                  ],
                ),
                const SizedBox(height: FiSpace.s1),
                Text(passo.reason, style: FiType.body),
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
                  const SizedBox(height: FiSpace.s1),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: FiNavAction(
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
        style: FiType.verdict.copyWith(fontFamily: fiFontSerif),
      ),
    );
  }
}

class _SemCaixa extends StatelessWidget {
  const _SemCaixa();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Ainda não sei seu mês',
          style: FiType.verdict.copyWith(fontFamily: fiFontSerif),
        ),
        const SizedBox(height: FiSpace.s3),
        Text(
          'A sobra sai do que entrou e do que saiu, e para isso preciso dos seus lançamentos. '
          'Comece pelo que se repete: o salário e os dois ou três maiores gastos fixos.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s5),
        FilledButton.icon(
          onPressed: () => GoRouter.of(context).go('/mes'),
          icon: const Icon(Icons.arrow_forward),
          label: const Text('Ir para o Mês'),
        ),
      ],
    );
  }
}
