import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/score_ruler.dart';

class QuickInvestView extends ConsumerStatefulWidget {
  const QuickInvestView({super.key});

  @override
  ConsumerState<QuickInvestView> createState() => _QuickInvestViewState();
}

class _QuickInvestViewState extends ConsumerState<QuickInvestView> {
  final _cashCtrl = TextEditingController(text: '1000');

  bool _useGoals = true;
  bool _prioritizeRebalance = true;

  bool _loading = false;
  String? _error;
  QuickInvestResult? _result;

  @override
  void dispose() {
    _cashCtrl.dispose();
    super.dispose();
  }

  Future<void> _run() async {
    final cash = double.tryParse(_cashCtrl.text.replaceAll(',', '.'));
    if (cash == null || cash <= 0) {
      setState(() => _error = 'Informe quanto você tem para aportar.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final result = await ref.read(apiRepositoryProvider).quickInvest(
        cashAvailable: cash,
        useCurrentGoals: _useGoals,
        prioritizeRebalance: _prioritizeRebalance,
      );
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
          _error = 'Não foi possível calcular agora: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 24),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Quanto você tem para aportar?',
                  style: theme.textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  'A sugestão respeita suas metas de alocação e o que já está na '
                  'carteira, incluindo a renda fixa.',
                  style: theme.textTheme.bodySmall,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _cashCtrl,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(
                    labelText: 'Valor disponível (R\$)',
                  ),
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  value: _useGoals,
                  onChanged: (v) => setState(() => _useGoals = v),
                  title: const Text('Usar minhas metas de alocação'),
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  value: _prioritizeRebalance,
                  onChanged: (v) => setState(() => _prioritizeRebalance = v),
                  title: const Text('Priorizar rebalanceamento'),
                  subtitle: const Text('Reforça primeiro o que está abaixo da meta'),
                ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(
                      _error!,
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                  ),
                const SizedBox(height: 4),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _loading ? null : _run,
                    icon: const Icon(Icons.bolt_outlined),
                    label: Text(_loading ? 'Calculando…' : 'Sugerir aportes'),
                  ),
                ),
              ],
            ),
          ),
        ),
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
        ],
      ],
    );
  }
}

/// Diz por que o número não está na tela.
///
/// Fora do modo prescritivo o servidor retira o valor que instrui. Sem esta
/// nota o traço leria como dado faltando, e não como retido de propósito.
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

/// Dinheiro que o backend pode reter.
///
/// `affirmation.apply` anula o valor que instrui fora do modo prescritivo, e
/// `formatCurrency(null)` diria R$ 0,00 — retido viraria zero na tela.
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
