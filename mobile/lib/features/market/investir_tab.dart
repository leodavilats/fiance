import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/providers.dart';

class InvestirTab extends ConsumerStatefulWidget {
  const InvestirTab({super.key});

  @override
  ConsumerState<InvestirTab> createState() => _InvestirTabState();
}

class _InvestirTabState extends ConsumerState<InvestirTab> {
  final _cashCtrl = TextEditingController();
  bool _loadingQuickInvest = false;
  bool _loadingStrategy = false;
  Map<String, dynamic>? _quickInvestResult;
  Map<String, dynamic>? _strategyResult;
  String? _error;

  @override
  void initState() {
    super.initState();
    ref.read(preferencesProvider.future).then((p) {
      if (mounted) _cashCtrl.text = p.cashAvailable.toStringAsFixed(2);
    });
  }

  Future<void> _runQuickInvest() async {
    final cash = double.tryParse(_cashCtrl.text.replaceAll(',', '.'));
    if (cash == null || cash <= 0) {
      setState(() => _error = 'Informe um valor de caixa válido');
      return;
    }
    setState(() {
      _loadingQuickInvest = true;
      _error = null;
    });
    try {
      final result = await ref.read(apiRepositoryProvider).quickInvest(cashAvailable: cash);
      setState(() => _quickInvestResult = result);
    } catch (e) {
      setState(() => _error = 'Erro ao gerar sugestão: $e');
    } finally {
      setState(() => _loadingQuickInvest = false);
    }
  }

  Future<void> _runStrategy() async {
    setState(() {
      _loadingStrategy = true;
      _error = null;
    });
    try {
      final result = await ref.read(apiRepositoryProvider).getStrategy();
      setState(() => _strategyResult = result);
    } catch (e) {
      setState(() => _error = 'Erro ao gerar estratégia: $e');
    } finally {
      setState(() => _loadingStrategy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Sugestão por caixa disponível', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        TextField(
          controller: _cashCtrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Valor disponível (R\$)', border: OutlineInputBorder()),
        ),
        const SizedBox(height: 8),
        FilledButton(
          onPressed: _loadingQuickInvest ? null : _runQuickInvest,
          child: _loadingQuickInvest
              ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('Gerar sugestão'),
        ),
        if (_error != null)
          Padding(padding: const EdgeInsets.only(top: 8), child: Text(_error!, style: const TextStyle(color: Colors.red))),
        if (_quickInvestResult != null) _QuickInvestResultView(data: _quickInvestResult!),
        const Divider(height: 32),
        const Text('Estratégia gerada por IA', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        FilledButton.tonal(
          onPressed: _loadingStrategy ? null : _runStrategy,
          child: _loadingStrategy
              ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('Gerar estratégia IA'),
        ),
        if (_strategyResult != null) _StrategyResultView(data: _strategyResult!),
      ],
    );
  }
}

class _QuickInvestResultView extends StatelessWidget {
  const _QuickInvestResultView({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final allocations = (data['allocations'] as List?) ?? [];
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(data['summary'] as String? ?? '', style: const TextStyle(fontStyle: FontStyle.italic)),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Alocado: ${formatCurrency((data['allocated_cash'] as num?)?.toDouble())}'),
              Text('Sobra: ${formatCurrency((data['remaining_cash'] as num?)?.toDouble())}'),
            ],
          ),
          const SizedBox(height: 8),
          ...allocations.map((a) {
            final m = a as Map<String, dynamic>;
            return Card(
              child: ListTile(
                title: Text('${m['ticker']} · ${formatCurrency((m['suggested_investment'] as num?)?.toDouble())}'),
                subtitle: Text(m['rationale'] as String? ?? ''),
                trailing: Text('${m['suggested_quantity']} un.'),
              ),
            );
          }),
        ],
      ),
    );
  }
}

class _StrategyResultView extends StatelessWidget {
  const _StrategyResultView({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final profile = data['profile'] as Map<String, dynamic>?;
    final gaps = (data['allocation_gaps'] as List?) ?? [];
    final suggestions = (data['suggestions'] as List?) ?? [];

    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (profile != null) ...[
            Text('Perfil: ${profile['type'] ?? ''}', style: const TextStyle(fontWeight: FontWeight.bold)),
            Text(profile['description'] as String? ?? '', style: TextStyle(color: Colors.grey.shade600)),
            const SizedBox(height: 12),
          ],
          Text(data['summary'] as String? ?? '', style: const TextStyle(fontStyle: FontStyle.italic)),
          if (gaps.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('Ajustes necessários', style: TextStyle(fontWeight: FontWeight.bold)),
            ...gaps.map((g) {
              final m = g as Map<String, dynamic>;
              final gapPct = (m['gap_pct'] as num?)?.toDouble() ?? 0;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('${m['category']}'),
                    Text(
                      '${m['action']} ${formatCurrency((m['gap_value'] as num?)?.toDouble().abs())}',
                      style: TextStyle(color: gapPct > 0 ? Colors.green.shade700 : Colors.orange.shade700),
                    ),
                  ],
                ),
              );
            }),
          ],
          if (suggestions.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('Sugestões de investimento', style: TextStyle(fontWeight: FontWeight.bold)),
            ...suggestions.map((s) {
              final m = s as Map<String, dynamic>;
              return Card(
                child: ListTile(
                  title: Text('${m['ticker']} · ${formatCurrency((m['invest_amount'] as num?)?.toDouble())}'),
                  subtitle: Text(m['objective'] as String? ?? ''),
                  trailing: Text(m['verdict'] as String? ?? ''),
                ),
              );
            }),
          ],
        ],
      ),
    );
  }
}
