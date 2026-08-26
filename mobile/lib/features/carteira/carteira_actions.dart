import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import '../../core/format.dart';

/// As três escritas de carteira: adicionar, remover e vender.
///
/// Viviam como métodos privados de `AssetsScreen`, o que amarrava o diálogo à
/// tela. Como funções de topo, a mesma venda pode ser disparada da lista de
/// posições ou da página do ativo sem duplicar formulário.

Future<void> openAddPositionDialog(BuildContext context, WidgetRef ref) async {
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
          TickerAutocompleteField(
            controller: tickerCtrl,
            labelText: 'Ticker (ex: PETR4)',
          ),
          const SizedBox(height: 16),
          TextField(
            controller: qtyCtrl,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
            ),
            decoration: const InputDecoration(labelText: 'Quantidade'),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: priceCtrl,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
            ),
            decoration: const InputDecoration(labelText: 'Preço médio'),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, true),
          child: const Text('Salvar'),
        ),
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
        const SnackBar(
          content: Text('Preencha ticker, quantidade e preço corretamente'),
        ),
      );
    }
    return;
  }

  try {
    await ref.read(apiRepositoryProvider).upsertPosition(
      ticker: ticker,
      quantity: quantity,
      avgPrice: avgPrice,
    );
    ref.invalidate(dashboardProvider);
    ref.invalidate(portfolioProvider);
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(fiErrorMessage(e, action: 'salvar este ativo'))));
    }
  }
}

Future<void> deletePosition(WidgetRef ref, String ticker) async {
  await ref.read(apiRepositoryProvider).deletePosition(ticker);
  ref.invalidate(dashboardProvider);
  ref.invalidate(portfolioProvider);
}

Future<void> openSellDialog(
  BuildContext context,
  WidgetRef ref,
  PortfolioPosition position,
) async {
  final qtyCtrl = TextEditingController(text: '${position.quantity}');
  final priceCtrl = TextEditingController(
    text: '${position.currentPrice ?? position.avgPrice}',
  );

  final confirmed = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('Vender ${position.ticker}'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: qtyCtrl,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
            ),
            decoration: InputDecoration(
              labelText: 'Quantidade (máx. ${position.quantity})',
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: priceCtrl,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
            ),
            decoration: const InputDecoration(labelText: 'Preço de venda'),
          ),
          const SizedBox(height: 8),
          Text(
            'Lucro/prejuízo, IR e histórico serão calculados automaticamente.',
            style: TextStyle(fontSize: 12, color: fiInk2(context)),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, true),
          child: const Text('Confirmar venda'),
        ),
      ],
    ),
  );

  if (confirmed != true) return;

  final quantity = double.tryParse(qtyCtrl.text.replaceAll(',', '.'));
  final sellPrice = double.tryParse(priceCtrl.text.replaceAll(',', '.'));

  if (quantity == null ||
      quantity <= 0 ||
      quantity > position.quantity ||
      sellPrice == null ||
      sellPrice <= 0) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Quantidade ou preço inválidos')),
      );
    }
    return;
  }

  try {
    final trade = await ref
        .read(apiRepositoryProvider)
        .sellPosition(
          ticker: position.ticker,
          quantity: quantity,
          sellPrice: sellPrice,
        );
    ref.invalidate(dashboardProvider);
    ref.invalidate(portfolioProvider);
    ref.invalidate(closedTradesProvider);
    if (context.mounted) {
      final lucro = trade.netProfit >= 0 ? 'lucro' : 'prejuízo';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Venda registrada: $lucro líquido de '
            '${formatCurrency(trade.netProfit.abs())}'
            '${trade.irAmount > 0 ? ' (IR: ${formatCurrency(trade.irAmount)})' : ''}',
          ),
        ),
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(fiErrorMessage(e, action: 'registrar esta venda'))));
    }
  }
}
