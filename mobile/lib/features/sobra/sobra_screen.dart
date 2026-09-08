import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/cash_models.dart';
import '../../core/format.dart';
import '../../core/mes.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';

/// A Sobra: "o que devo fazer com o que ficou?"
///
/// A tela mais importante do produto, e a que mais facilmente vira conselho. A transicao e
/// *disponivel -> contexto -> restricao -> possibilidade -> decisao*, e a decisao e de quem usa.
///
/// **E onde o mobile ganha do web.** A cascata e naturalmente uma sequencia vertical -- divida,
/// reserva, aporte -- e rolar e o gesto certo para percorrer uma sequencia. No web ela compete
/// com o subnav.
///
/// Tres coisas que esta tela nunca faz: dizer "compre", ordenar por "melhor", ou esconder que a
/// cascata pode terminar **sem passo de aporte**. Com divida caseira consumindo a sobra inteira,
/// nao aportar e a resposta certa -- e e por isso que o destino se chama Sobra, e nao Aporte.
class SobraScreen extends ConsumerWidget {
  const SobraScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sobra = ref.watch(surplusProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Sobra')),
      body: sobra.when(
        loading: () => const Center(child: CircularProgressIndicator()),
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
          // 1. Quanto ha. Projecao sai como FAIXA, nunca numero unico: a diferenca entre o piso
          //    e o teto *e* a estimativa de gasto variavel.
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
                // Sem mes fechado nao ha estimativa, e ausencia nao vira zero.
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

          // 2. A ordem, como sequencia.
          FiSection(
            title: 'A ordem',
            hint: 'Cada passo consome a sobra antes do seguinte.',
            child: Column(
              children: [
                for (final p in passos) _Passo(passo: p),
                if (!temAporte) const _SemAporte(),
              ],
            ),
          ),

          // 3. Onde, quando ha o que aportar.
          if (temAporte)
            FiSection(
              title: 'Onde',
              hint: 'Alternativas compatíveis com suas metas, com o critério visível.',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Restam ${formatCurrency(sobra.cascade.availableToInvest)} depois da '
                    'ordem acima.',
                    style: FiType.body.copyWith(color: fiInk2(context)),
                  ),
                  const SizedBox(height: FiSpace.s3),
                  Wrap(
                    spacing: FiSpace.s2,
                    runSpacing: FiSpace.s2,
                    children: [
                      OutlinedButton(
                        onPressed: () => GoRouter.of(context).go('/sobra/aporte'),
                        child: const Text('Onde aportar'),
                      ),
                      OutlinedButton(
                        onPressed: () => GoRouter.of(context).go('/sobra/desvio'),
                        child: const Text('Alocação × meta'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

/// Um passo da cascata: o quanto, a razão, e o que o derrubaria.
class _Passo extends StatelessWidget {
  const _Passo({required this.passo});

  final CascadeStep passo;

  static const _rotulos = {
    CascadeStepType.debt: 'Dívida',
    CascadeStepType.reserve: 'Reserva',
    CascadeStepType.contribution: 'Aporte',
  };

  /// Divida caseira e o unico passo que e julgamento adverso; reserva e aporte descrevem.
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
          // Fio de estado, não caixa: o passo é parte de uma sequência, não um objeto.
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
                        '${passo.order} · ${_rotulos[passo.type] ?? ''}',
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
                  // O falsificador nao e um aviso: e o raciocinio continuando.
                  Text(
                    passo.falsifier!,
                    style: FiType.caption.copyWith(color: fiInk3(context)),
                  ),
                ],
                if (passo.reference != null) ...[
                  const SizedBox(height: FiSpace.s1),
                  Text(
                    passo.reference!,
                    style: FiType.caption.copyWith(color: fiInk3(context)),
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
