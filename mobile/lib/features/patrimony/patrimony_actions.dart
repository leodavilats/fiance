import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import '../../core/format.dart';
import '../assets/fixed_income_screen.dart';
import 'ledger_screen.dart';
import 'widgets/form_fields.dart';
import 'widgets/patrimony_positions.dart';

Future<void> openAddPositionDialog(BuildContext context, WidgetRef ref) async {
  final kind = await showModalBottomSheet<_AssetKind>(
    context: context,
    showDragHandle: true,
    builder: (context) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          FiSpace.s5,
          0,
          FiSpace.s5,
          FiSpace.s6,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'O que você quer adicionar?',
              style: FiType.pageTitle.copyWith(color: fiInk1(context)),
            ),
            const SizedBox(height: FiSpace.s4),
            FiRows(
              children: [
                FiDataRow(
                  label: 'Ativo negociado',
                  detail: 'Ação, FII, BDR ou ETF — por ticker',
                  onTap: () => Navigator.pop(context, _AssetKind.traded),
                ),
                FiDataRow(
                  label: 'Aplicação de renda fixa',
                  detail: 'CDB, LCI, LCA, Tesouro — por taxa e vencimento',
                  onTap: () => Navigator.pop(context, _AssetKind.fixedIncome),
                ),
              ],
            ),
          ],
        ),
      ),
    ),
  );

  if (kind == null || !context.mounted) return;

  if (kind == _AssetKind.fixedIncome) {
    await openFixedIncomeForm(context, ref);
    return;
  }

  await _openPositionForm(context, ref);
}

enum _AssetKind { traded, fixedIncome }

class _PositionOutcome {
  const _PositionOutcome.saved({
    required this.ticker,
    required this.quantity,
    required this.replaced,
  }) : toLedger = false;

  const _PositionOutcome.toLedger(this.ticker)
    : quantity = 0,
      replaced = false,
      toLedger = true;

  final String ticker;
  final double quantity;
  final bool replaced;
  final bool toLedger;
}

Future<void> _openPositionForm(BuildContext context, WidgetRef ref) async {
  final atuais = [
    for (final p in ref.read(dashboardProvider).valueOrNull?.positions ?? const <PortfolioPosition>[])
      if (!fiIsFixedIncomePosition(p)) p,
  ];

  final resultado = await showDialog<_PositionOutcome>(
    context: context,
    builder: (_) => _PositionDialog(held: atuais),
  );
  if (resultado == null || !context.mounted) return;

  if (resultado.toLedger) {
    await openLedgerEntryForm(context, ref, symbol: resultado.ticker);
    return;
  }

  ref.invalidate(dashboardProvider);
  ref.invalidate(portfolioProvider);
  fiNotify(
    context,
    resultado.replaced
        ? 'Posição de ${resultado.ticker} substituída: agora são '
              '${formatQuantity(resultado.quantity)} un.'
        : '${resultado.ticker} entrou na carteira com ${formatQuantity(resultado.quantity)} un.',
  );
}

String? _positive(String? texto, String mensagem) {
  final n = parseDecimal(texto);
  return n == null || n <= 0 ? mensagem : null;
}

class _PositionDialog extends ConsumerStatefulWidget {
  const _PositionDialog({required this.held});

  final List<PortfolioPosition> held;

  @override
  ConsumerState<_PositionDialog> createState() => _PositionDialogState();
}

class _PositionDialogState extends ConsumerState<_PositionDialog> {
  final _formKey = GlobalKey<FormState>();
  final _ticker = TextEditingController();
  final _quantity = TextEditingController();
  final _price = TextEditingController();

  bool _saving = false;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _ticker.addListener(_onTicker);
  }

  @override
  void dispose() {
    _ticker.removeListener(_onTicker);
    _ticker.dispose();
    _quantity.dispose();
    _price.dispose();
    super.dispose();
  }

  void _onTicker() {
    if (mounted) setState(() {});
  }

  String get _symbol => _ticker.text.trim().toUpperCase();

  PortfolioPosition? get _existing =>
      widget.held.where((p) => p.ticker.toUpperCase() == _symbol).firstOrNull;

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    final existente = _existing;
    final quantidade = parseDecimal(_quantity.text)!;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await ref.read(apiRepositoryProvider).upsertPosition(
        ticker: _symbol,
        quantity: quantidade,
        avgPrice: parseDecimal(_price.text)!,
      );
      if (!mounted) return;
      Navigator.pop(
        context,
        _PositionOutcome.saved(
          ticker: _symbol,
          quantity: quantidade,
          replaced: existente != null,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = e;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final existente = _existing;
    final atencao = fiStateColor(FiState.attention, Theme.of(context).brightness);

    return AlertDialog(
      title: const Text('Adicionar ativo'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FiTickerFormField(controller: _ticker, labelText: 'Ticker (ex: PETR4)'),
              if (existente != null) ...[
                const SizedBox(height: FiSpace.s3),
                Text(
                  'Você já tem ${formatQuantity(existente.quantity)} un. de ${existente.ticker} — '
                  'salvar substitui a posição; para somar uma compra, registre no razão.',
                  style: FiType.caption.copyWith(color: atencao),
                ),
                const SizedBox(height: FiSpace.s1),
                FiButton.quiet(
                  label: 'Registrar compra no razão',
                  onPressed: _saving
                      ? null
                      : () => Navigator.pop(context, _PositionOutcome.toLedger(existente.ticker)),
                ),
              ],
              const SizedBox(height: FiSpace.s4),
              TextFormField(
                controller: _quantity,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: existente == null ? 'Quantidade' : 'Quantidade total, depois de salvar',
                ),
                validator: (v) => _positive(v, 'Informe uma quantidade positiva'),
              ),
              const SizedBox(height: FiSpace.s4),
              TextFormField(
                controller: _price,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'Preço médio', prefixText: 'R\$ '),
                validator: (v) => _positive(v, 'Informe um preço médio positivo'),
              ),
              if (_error != null) ...[
                const SizedBox(height: FiSpace.s4),
                FiInlineError(fiErrorMessage(_error!, action: 'salvar este ativo')),
              ],
            ],
          ),
        ),
      ),
      actions: [
        FiButton.quiet(
          label: 'Cancelar',
          onPressed: _saving ? null : () => Navigator.pop(context),
        ),
        FiButton.primary(
          label: existente == null ? 'Salvar' : 'Substituir posição',
          busy: _saving,
          onPressed: _save,
        ),
      ],
    );
  }
}

Future<bool> removePosition(
  BuildContext context,
  WidgetRef ref,
  PortfolioPosition position,
) async {
  final confirmado = await fiConfirm(
    context,
    title: 'Remover ${position.ticker} da carteira?',
    body: 'A posição sai do patrimônio e das análises, e o razão ganha uma declaração de posição '
        'zerada. Se você vendeu, use Vender: remover não apura lucro nem imposto.',
    confirmLabel: 'Remover',
  );
  if (!confirmado || !context.mounted) return false;

  final removido = await fiAttempt(
    context,
    () => ref.read(apiRepositoryProvider).deletePosition(position.ticker),
    action: 'remover este ativo',
    success: '${position.ticker} saiu da carteira.',
  );
  if (removido) invalidateLedgerReaders(ref);
  return removido;
}

Future<void> openSellDialog(
  BuildContext context,
  WidgetRef ref,
  PortfolioPosition position,
) async {
  final trade = await showDialog<ClosedTrade>(
    context: context,
    builder: (_) => _SellDialog(position: position),
  );
  if (trade == null || !context.mounted) return;

  invalidateLedgerReaders(ref);
  ref.invalidate(closedTradesProvider);
  final lucro = trade.netProfit >= 0 ? 'lucro' : 'prejuízo';
  fiNotify(
    context,
    'Venda registrada: $lucro líquido de ${formatCurrency(trade.netProfit.abs())}'
    '${trade.irAmount > 0 ? ' (IR: ${formatCurrency(trade.irAmount)})' : ''}',
  );
}

DateTime _today() {
  final agora = DateTime.now();
  return DateTime(agora.year, agora.month, agora.day);
}

class _SellDialog extends ConsumerStatefulWidget {
  const _SellDialog({required this.position});

  final PortfolioPosition position;

  @override
  ConsumerState<_SellDialog> createState() => _SellDialogState();
}

class _SellDialogState extends ConsumerState<_SellDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _quantity = TextEditingController(
    text: formatForInput(widget.position.quantity),
  );
  late final TextEditingController _price = TextEditingController(
    text: formatForInput(widget.position.currentPrice ?? widget.position.avgPrice),
  );

  DateTime _date = _today();
  bool _saving = false;
  Object? _error;

  @override
  void dispose() {
    _quantity.dispose();
    _price.dispose();
    super.dispose();
  }

  String? _validateQuantity(String? texto) {
    final n = parseDecimal(texto);
    if (n == null || n <= 0) return 'Informe uma quantidade positiva';
    final temos = widget.position.quantity;
    if (n > temos + 1e-9) {
      return 'Você tem ${formatQuantity(temos)} un. — não dá para vender mais que isso';
    }
    return null;
  }

  Future<void> _pickDate() async {
    final hoje = _today();
    final escolhida = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: hoje.subtract(const Duration(days: 89)),
      lastDate: hoje,
    );
    if (escolhida != null) setState(() => _date = escolhida);
  }

  double? get _soldAt {
    if (!_date.isBefore(_today())) return null;
    final meioDia = DateTime(_date.year, _date.month, _date.day, 12);
    return meioDia.millisecondsSinceEpoch / 1000;
  }

  Future<void> _sell() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final trade = await ref.read(apiRepositoryProvider).sellPosition(
        ticker: widget.position.ticker,
        quantity: parseDecimal(_quantity.text)!,
        sellPrice: parseDecimal(_price.text)!,
        soldAt: _soldAt,
      );
      if (mounted) Navigator.pop(context, trade);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = e;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.position;

    return AlertDialog(
      title: Text('Vender ${p.ticker}'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _quantity,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: 'Quantidade (máx. ${formatQuantity(p.quantity)})',
                ),
                validator: _validateQuantity,
              ),
              const SizedBox(height: FiSpace.s4),
              TextFormField(
                controller: _price,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Preço de venda',
                  prefixText: 'R\$ ',
                ),
                validator: (v) => _positive(v, 'Informe um preço de venda positivo'),
              ),
              const SizedBox(height: FiSpace.s2),
              FiDataRow(
                label: 'Data da venda',
                value: formatDate(_date.toIso8601String().substring(0, 10)),
                detail: 'Até 90 dias atrás',
                onTap: _saving ? null : _pickDate,
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                'Lucro/prejuízo, IR e histórico serão calculados automaticamente.',
                style: FiType.caption.copyWith(color: fiInk2(context)),
              ),
              if (_error != null) ...[
                const SizedBox(height: FiSpace.s4),
                FiInlineError(fiErrorMessage(_error!, action: 'registrar esta venda')),
              ],
            ],
          ),
        ),
      ),
      actions: [
        FiButton.quiet(
          label: 'Cancelar',
          onPressed: _saving ? null : () => Navigator.pop(context),
        ),
        FiButton.primary(
          label: 'Confirmar venda',
          busy: _saving,
          onPressed: _sell,
        ),
      ],
    );
  }
}
