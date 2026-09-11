import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/provenance.dart';

class QuickInvestView extends ConsumerStatefulWidget {
  const QuickInvestView({super.key});

  @override
  ConsumerState<QuickInvestView> createState() => _QuickInvestViewState();
}

class _QuickInvestViewState extends ConsumerState<QuickInvestView> {
  final _cashCtrl = TextEditingController();

  /// Quando verdadeiro, a tela pergunta o valor em vez de usar a sobra do mês.
  bool _simulando = false;

  bool _loading = true;
  Object? _error;
  QuickInvestResult? _result;

  @override
  void initState() {
    super.initState();
    // A tela abre respondendo. O valor vem da cascata do caixa, no servidor -- pedir de novo
    // o número que o produto acabou de calcular era a ponte não estar construída, e o campo
    // ainda vinha preenchido com 1000, que não é o dinheiro de ninguém.
    _run();
  }

  @override
  void dispose() {
    _cashCtrl.dispose();
    super.dispose();
  }

  Future<void> _run({double? valor}) async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final result = await ref
          .read(apiRepositoryProvider)
          .quickInvest(cashAvailable: valor);
      if (mounted) {
        setState(() {
          _result = result;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e;
        });
      }
    }
  }

  void _simularOutroValor() {
    final valor = double.tryParse(_cashCtrl.text.replaceAll(',', '.'));
    if (valor == null || valor <= 0) {
      setState(() => _error = 'Informe um valor para simular.');
      return;
    }
    _run(valor: valor);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _result == null) {
      return FiSkeleton.tela(
        shape: FiSkeletonShape.row,
        count: 4,
        label: 'Calculando onde aportar',
      );
    }

    if (_error != null && _result == null) {
      return FiErrorState(
        error: _error!,
        action: 'calcular onde aportar',
        onRetry: () => _simulando ? _simularOutroValor() : _run(),
      );
    }

    final r = _result!;

    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s3,
        FiLayout.gutter,
        FiLayout.scrollTail,
      ),
      children: [
        FiHeadline(
          eyebrow: _simulando ? 'Valor simulado' : 'Sobra deste mês',
          figure: _dinheiroOuTraco(r.totalCash),
          support: _simulando
              ? 'A distribuição abaixo é sobre este valor, e não sobre a sua sobra.'
              : 'A distribuição respeita suas metas de alocação e o que já está na carteira, '
                    'incluindo a renda fixa.',
        ),

        const SizedBox(height: FiSpace.s3),
        if (!_simulando)
          Align(
            alignment: Alignment.centerLeft,
            child: FiButton.quiet(
              label: 'Simular outro valor',
              onPressed: () => setState(() => _simulando = true),
            ),
          )
        else
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: TextField(
                  controller: _cashCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(
                    labelText: 'Valor a simular (R\$)',
                  ),
                  onSubmitted: (_) => _simularOutroValor(),
                ),
              ),
              const SizedBox(width: FiSpace.s2),
              FiButton.secondary(
                label: 'Simular',
                busy: _loading,
                onPressed: _simularOutroValor,
              ),
            ],
          ),

        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: FiSpace.s3),
            child: Text(
              fiErrorMessage(_error!, action: 'calcular onde aportar'),
              style: FiType.body.copyWith(
                color: fiStateColor(
                  FiState.adverse,
                  Theme.of(context).brightness,
                ),
              ),
            ),
          ),

        const SizedBox(height: FiSpace.s5),
        Text(
          r.summary,
          style: fiSerif(FiType.verdictSm).copyWith(color: fiInk1(context)),
        ),
        const SizedBox(height: FiSpace.s4),
        FiFigures(
          figures: {
            'ALOCADO': _dinheiroOuTraco(r.allocatedCash),
            'FICA EM CAIXA': _dinheiroOuTraco(r.remainingCash),
          },
        ),
        if (r.affirmation?.prescriptive == false) ...[
          const SizedBox(height: FiSpace.s2),
          Text(
            '${r.affirmation!.disclaimer} Por isso o quanto aportar em cada ativo aparece '
            'como —.',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
        ],

        FiSection(
          title: 'A ordem de prioridade',
          count: r.allocations.isEmpty ? null : r.allocations.length,
          hint: r.allocations.isEmpty
              ? null
              : 'Do que está mais longe da meta para o que está mais perto.',
          child: r.allocations.isEmpty
              ? const FiEmptyLine(
                  'Sem metas de alocação declaradas não há alvo contra o que comparar, e a '
                  'distribuição sai vazia.',
                )
              : Column(
                  children: [
                    for (final allocation in r.allocations)
                      _Alocacao(allocation: allocation),
                  ],
                ),
        ),

        const SizedBox(height: FiSpace.s3),
        const FiProvenance(
          summary: 'Como chegamos nesta ordem',
          method:
              'Compara sua alocação atual com as metas por categoria e distribui o valor '
              'informado no que está mais abaixo do alvo. O score de cada ativo entra como '
              'desempate, na régua do sistema.',
          source: 'Suas posições e renda fixa, com metas de alocação e preços da BRAPI.',
          limitation:
              'É uma ordem de prioridade, não uma recomendação de compra. Sem metas '
              'declaradas não há alvo para comparar, e a distribuição sai vazia.',
        ),
      ],
    );
  }
}

String _dinheiroOuTraco(double? valor) =>
    valor == null ? '—' : formatCurrency(valor);

class _Alocacao extends StatelessWidget {
  const _Alocacao({required this.allocation});

  final QuickInvestAllocation allocation;

  @override
  Widget build(BuildContext context) {
    final a = allocation;
    final brightness = Theme.of(context).brightness;
    final band = a.score != null ? fiScoreBandFor(a.score!, null) : null;

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
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
                if (band != null)
                  FiTag(label: band.label, state: band.state)
                else
                  FiTag.serie(
                    label: categoryLabel(a.category),
                    color: categoryColor(a.category, brightness),
                  ),
              ],
            ),
            const SizedBox(height: FiSpace.s3),
            FiFigures(
              rule: false,
              figures: {
                'COMPRAR': a.suggestedQuantity == null
                    ? '—'
                    : '${a.suggestedQuantity} cota(s)',
                'PREÇO': _dinheiroOuTraco(a.currentPrice),
                'TOTAL': _dinheiroOuTraco(a.suggestedInvestment),
              },
            ),
            if (a.rationale.isNotEmpty) ...[
              const SizedBox(height: FiSpace.s3),
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
