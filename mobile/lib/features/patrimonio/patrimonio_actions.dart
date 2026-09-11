import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import '../../core/format.dart';
import '../assets/fixed_income_screen.dart';

/// O que entra na carteira: um papel negociado, ou uma aplicação de renda fixa.
///
/// A renda fixa tinha uma porta só, e ficava dentro da tela de renda fixa — quem chegava pelo
/// botão de adicionar ativo só conseguia lançar ticker. Renda fixa é classe de primeira classe
/// no domínio, e a escolha do tipo é a primeira pergunta, não um caminho paralelo.
Future<void> openAddPositionDialog(BuildContext context, WidgetRef ref) async {
  final tipo = await showModalBottomSheet<_TipoDeAtivo>(
    context: context,
    builder: (context) => SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 20, 16, 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text('O que você quer adicionar?', style: FiType.title),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.show_chart_outlined),
            title: const Text('Ativo negociado'),
            subtitle: const Text('Ação, FII, BDR ou ETF — por ticker'),
            onTap: () => Navigator.pop(context, _TipoDeAtivo.negociado),
          ),
          ListTile(
            leading: const Icon(Icons.account_balance_outlined),
            title: const Text('Renda fixa'),
            subtitle: const Text('CDB, LCI, LCA, Tesouro — por taxa e vencimento'),
            onTap: () => Navigator.pop(context, _TipoDeAtivo.rendaFixa),
          ),
          const SizedBox(height: 8),
        ],
      ),
    ),
  );

  if (tipo == null || !context.mounted) return;

  if (tipo == _TipoDeAtivo.rendaFixa) {
    await abrirFormDeRendaFixa(context, ref);
    return;
  }

  await _abrirFormDePosicao(context, ref);
}

enum _TipoDeAtivo { negociado, rendaFixa }

Future<void> _abrirFormDePosicao(BuildContext context, WidgetRef ref) async {
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
            style: FiType.caption.copyWith(color: fiInk2(context)),
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
