import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/score_ruler.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/nav_action.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/skeleton.dart';

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
    final theme = Theme.of(context);

    if (_loading) {
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

    return ListView(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 24),
      children: [
        Text(
          _simulando
              ? 'Simulando um aporte de ${_dinheiroOuTraco(_result?.totalCash)}.'
              : 'O valor vem da sua sobra deste mês: '
                    '${_dinheiroOuTraco(_result?.totalCash)}. A distribuição respeita suas '
                    'metas de alocação e o que já está na carteira, incluindo a renda fixa.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s2),
        if (!_simulando)
          Align(
            alignment: Alignment.centerLeft,
            child: FiNavAction(
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
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Valor a simular (R\$)'),
                  onSubmitted: (_) => _simularOutroValor(),
                ),
              ),
              const SizedBox(width: FiSpace.s3),
              FilledButton(
                onPressed: _simularOutroValor,
                child: const Text('Simular'),
              ),
            ],
          ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              fiErrorMessage(_error!, action: 'calcular onde aportar'),
              style: TextStyle(color: theme.colorScheme.error),
            ),
          ),
        const SizedBox(height: FiSpace.s4),
        if (_result != null) ...[
          const SizedBox(height: 16),
          if (_result!.affirmation?.prescriptive == false)
            _NotaDeAfirmacao(texto: _result!.affirmation!.disclaimer),
          _QuickInvestSummary(result: _result!),
          const SizedBox(height: 12),
          if (_result!.allocations.isEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  _result!.summary,
                  style: theme.textTheme.bodyMedium,
                ),
              ),
            )
          else
            for (final allocation in _result!.allocations)
              _AllocationCard(allocation: allocation),

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
      ],
    );
  }
}

class _NotaDeAfirmacao extends StatelessWidget {
  const _NotaDeAfirmacao({required this.texto});

  final String texto;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        '$texto Por isso o quanto aportar em cada ativo aparece como —.',
        style: theme.textTheme.bodySmall,
      ),
    );
  }
}

String _dinheiroOuTraco(double? valor) =>
    valor == null ? '—' : formatCurrency(valor);

class _QuickInvestSummary extends StatelessWidget {
  const _QuickInvestSummary({required this.result});

  final QuickInvestResult result;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(result.summary, style: theme.textTheme.bodyMedium),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Alocado', style: theme.textTheme.labelSmall),
                      Text(_dinheiroOuTraco(result.allocatedCash)),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Sobra em caixa', style: theme.textTheme.labelSmall),
                      Text(_dinheiroOuTraco(result.remainingCash)),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _AllocationCard extends StatelessWidget {
  const _AllocationCard({required this.allocation});

  final QuickInvestAllocation allocation;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final band = allocation.score != null
        ? scoreBand(allocation.score!, theme.brightness)
        : null;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(categoryIcon(allocation.category), size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        allocation.ticker,
                        style: theme.textTheme.titleMedium,
                      ),
                      Text(
                        allocation.name ?? categoryLabel(allocation.category),
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                if (band != null)
                  Text(
                    band.text,
                    style: theme.textTheme.bodySmall?.copyWith(color: band.color),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Comprar', style: theme.textTheme.labelSmall),
                      Text(
                        allocation.suggestedQuantity == null
                            ? '—'
                            : '${allocation.suggestedQuantity} cota(s)',
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Preço', style: theme.textTheme.labelSmall),
                      Text(_dinheiroOuTraco(allocation.currentPrice)),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Total', style: theme.textTheme.labelSmall),
                      Text(_dinheiroOuTraco(allocation.suggestedInvestment)),
                    ],
                  ),
                ),
              ],
            ),
            if (allocation.rationale.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(allocation.rationale, style: theme.textTheme.bodySmall),
            ],
          ],
        ),
      ),
    );
  }
}
