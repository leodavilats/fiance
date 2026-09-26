import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/controls.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';

Future<bool> openBuySheet(
  BuildContext context,
  WidgetRef ref, {
  required String ticker,
  double? currentPrice,
  String? verdict,
}) async {
  final registrou = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: _BuyForm(ticker: ticker, currentPrice: currentPrice, verdict: verdict),
    ),
  );

  if (registrou == true) {
    ref.invalidate(portfolioProvider);
    ref.invalidate(dashboardProvider);
    ref.invalidate(ledgerProvider);
    ref.invalidate(followedSuggestionsProvider);
  }

  return registrou == true;
}

class _BuyForm extends ConsumerStatefulWidget {
  const _BuyForm({required this.ticker, this.currentPrice, this.verdict});

  final String ticker;
  final double? currentPrice;
  final String? verdict;

  @override
  ConsumerState<_BuyForm> createState() => _BuyFormState();
}

class _BuyFormState extends ConsumerState<_BuyForm> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _price;
  final _quantityFormat = TextEditingController();
  final _fees = TextEditingController(text: '0');

  DateTime _date = DateTime.now();
  bool _saving = false;
  bool _follow = true;

  @override
  void initState() {
    super.initState();
    _price = TextEditingController(
      text: widget.currentPrice == null
          ? ''
          : widget.currentPrice!.toStringAsFixed(2).replaceAll('.', ','),
    );
    _quantityFormat.addListener(_recompute);
    _price.addListener(_recompute);
    _fees.addListener(_recompute);
  }

  @override
  void dispose() {
    _price.dispose();
    _quantityFormat.dispose();
    _fees.dispose();
    super.dispose();
  }

  void _recompute() => setState(() {});

  double _number(TextEditingController c) =>
      double.tryParse(c.text.trim().replaceAll(',', '.')) ?? 0;

  double get _total => _number(_quantityFormat) * _number(_price) + _number(_fees);

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _saving = true);
    final api = ref.read(apiRepositoryProvider);
    final avisos = ScaffoldMessenger.of(context);
    try {
      final entryId = await api
          .createTransaction(
            kind: 'buy',
            symbol: widget.ticker,
            tradedOn: _date.toIso8601String().substring(0, 10),
            quantity: _number(_quantityFormat),
            price: _number(_price),
            fees: _number(_fees),
          );
      if (widget.verdict != null && _follow) {
        try {
          await api.followFromLedger(
            entryId: entryId,
            source: 'opportunities',
            verdictAtSuggestion: widget.verdict,
          );
        } catch (e) {
          avisos.showSnackBar(
            SnackBar(
              content: Text(
                'A compra entrou na carteira. '
                '${fiErrorMessage(e, action: 'acompanhar o resultado dela')}',
              ),
            ),
          );
        }
      }
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(fiErrorMessage(e, action: 'registrar esta compra'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final carteira = ref.watch(portfolioProvider);

    final jaTem = carteira.maybeWhen(
      data: (itens) => itens
          .cast<StoredPortfolioItem?>()
          .firstWhere(
            (i) => i?.ticker.toUpperCase() == widget.ticker.toUpperCase(),
            orElse: () => null,
          ),
      orElse: () => null,
    );

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiSpace.s5,
        ),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Comprei ${widget.ticker}',
                style: FiType.pageTitle.copyWith(color: fiInk1(context)),
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                jaTem == null
                    ? 'Entra na sua carteira como compra, e o preço médio nasce deste preço.'
                    : 'Você já tem ${formatQuantity(jaTem.quantity)} a preço médio de '
                          '${formatCurrency(jaTem.avgPrice)}. Esta compra soma à posição e '
                          'recalcula a média.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
              const SizedBox(height: FiSpace.s5),
              TextFormField(
                controller: _quantityFormat,
                autofocus: true,
                decoration: const InputDecoration(labelText: 'Quantidade'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (v) {
                  final n = double.tryParse((v ?? '').replaceAll(',', '.'));
                  if (n == null || n <= 0) return 'Informe quantas você comprou';
                  return null;
                },
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _price,
                decoration: InputDecoration(
                  labelText: 'Preço pago por unidade',
                  prefixText: 'R\$ ',
                  helperText: widget.currentPrice == null
                      ? null
                      : 'Veio a cotação de agora — troque pelo preço que você pagou.',
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (v) {
                  final n = double.tryParse((v ?? '').replaceAll(',', '.'));
                  if (n == null || n <= 0) return 'Informe o preço pago';
                  return null;
                },
              ),
              const SizedBox(height: FiSpace.s3),
              InputDecorator(
                decoration: const InputDecoration(labelText: 'Data da compra'),
                child: InkWell(
                  onTap: () async {
                    final escolhida = await showDatePicker(
                      context: context,
                      initialDate: _date,
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now(),
                    );
                    if (escolhida != null) setState(() => _date = escolhida);
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: FiSpace.s1),
                    child: Text(
                      formatDate(_date.toIso8601String().substring(0, 10)),
                      style: FiType.body.copyWith(color: fiInk1(context)),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _fees,
                decoration: const InputDecoration(
                  labelText: 'Corretagem e taxas',
                  prefixText: 'R\$ ',
                  helperText: 'Entram no custo, e por isso no imposto quando você vender.',
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
              if (_total > 0) ...[
                const SizedBox(height: FiSpace.s4),
                FiRows(
                  children: [
                    FiDataRow(
                      label: 'Total desembolsado',
                      value: formatCurrency(_total),
                      emphasis: true,
                    ),
                  ],
                ),
              ],
              if (widget.verdict != null) ...[
                const SizedBox(height: FiSpace.s4),
                FiSwitch(
                  label: 'Acompanhar o resultado desta compra',
                  value: _follow,
                  onChanged: _saving ? null : (v) => setState(() => _follow = v),
                ),
                Text(
                  'Ela entra em Patrimônio, Sugestões seguidas, medida contra o Ibovespa a partir '
                  'da data da compra. Dá para deixar de acompanhar depois.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ],
              const SizedBox(height: FiSpace.s5),
              FiButton.primary(
                label: _saving ? 'Registrando…' : 'Adicionar à carteira',
                onPressed: _saving ? null : _save,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
