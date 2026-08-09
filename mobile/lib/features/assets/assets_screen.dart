import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';

class AssetsScreen extends ConsumerWidget {
  const AssetsScreen({super.key});

  Future<void> _openAddDialog(BuildContext context, WidgetRef ref) async {
    final tickerCtrl = TextEditingController();
    final qtyCtrl = TextEditingController();
    final priceCtrl = TextEditingController();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Adicionar ativo'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: tickerCtrl,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(labelText: 'Ticker (ex: PETR4)'),
            ),
            TextField(
              controller: qtyCtrl,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Quantidade'),
            ),
            TextField(
              controller: priceCtrl,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Preço médio'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Salvar')),
        ],
      ),
    );

    if (confirmed != true) return;

    final ticker = tickerCtrl.text.trim().toUpperCase();
    final quantity = double.tryParse(qtyCtrl.text.replaceAll(',', '.'));
    final avgPrice = double.tryParse(priceCtrl.text.replaceAll(',', '.'));

    if (ticker.isEmpty || quantity == null || avgPrice == null) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Preencha ticker, quantidade e preço corretamente')),
        );
      }
      return;
    }

    final repo = ref.read(apiRepositoryProvider);
    final current = await repo.getPortfolio();
    final updated = [
      ...current.where((i) => i.ticker != ticker),
      StoredPortfolioItem(ticker: ticker, quantity: quantity, avgPrice: avgPrice, category: 'auto'),
    ];
    await repo.savePortfolio(updated);
    ref.invalidate(portfolioProvider);
    ref.invalidate(dashboardProvider);
  }

  Future<void> _delete(BuildContext context, WidgetRef ref, String ticker) async {
    await ref.read(apiRepositoryProvider).deletePosition(ticker);
    ref.invalidate(portfolioProvider);
    ref.invalidate(dashboardProvider);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final portfolio = ref.watch(portfolioProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Meus Ativos')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openAddDialog(context, ref),
        child: const Icon(Icons.add),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(portfolioProvider),
        child: portfolio.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(child: Text('Erro: $err')),
          data: (items) {
            if (items.isEmpty) {
              return ListView(
                children: const [
                  Padding(
                    padding: EdgeInsets.all(32),
                    child: Text(
                      'Nenhum ativo cadastrado ainda. Toque em + pra adicionar.',
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: items.length,
              itemBuilder: (context, index) {
                final item = items[index];
                return Dismissible(
                  key: ValueKey(item.ticker),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    color: Colors.red.shade400,
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  onDismissed: (_) => _delete(context, ref, item.ticker),
                  child: ListTile(
                    title: Text(item.ticker, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('${item.quantity} un. · PM ${formatCurrency(item.avgPrice)}'),
                    trailing: Text(formatCurrency(item.quantity * item.avgPrice)),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
