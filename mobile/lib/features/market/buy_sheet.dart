import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/controls.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';

const _tiposNegociadosPorUnidade = {'br_stock', 'bdr', 'fii', 'etf'};

class _Registro {
  const _Registro({required this.quantity, this.followError});

  final double quantity;
  final Object? followError;
}

Future<bool> openBuySheet(
  BuildContext context,
  WidgetRef ref, {
  required String ticker,
  double? currentPrice,
  String? verdict,
  String? assetType,
}) async {
  final roteador = GoRouter.maybeOf(context);
  final registro = await showModalBottomSheet<_Registro>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: _BuyForm(
        ticker: ticker,
        currentPrice: currentPrice,
        verdict: verdict,
        wholeUnits: assetType == null || _tiposNegociadosPorUnidade.contains(assetType),
      ),
    ),
  );

  if (registro == null) return false;

  invalidateLedgerReaders(ref);

  if (context.mounted) {
    final falha = registro.followError;
    fiNotify(
      context,
      [
        'Compra de ${formatQuantity(registro.quantity)} $ticker registrada.',
        if (falha != null) fiErrorMessage(falha, action: 'acompanhar o resultado dela'),
      ].join(' '),
      actionLabel: roteador == null ? null : 'Ver no Patrimônio',
      onAction: roteador == null ? null : () => roteador.go('/patrimonio'),
    );
  }

  return true;
}

class _BuyForm extends ConsumerStatefulWidget {
  const _BuyForm({
    required this.ticker,
    required this.wholeUnits,
    this.currentPrice,
    this.verdict,
  });

  final String ticker;
  final double? currentPrice;
  final String? verdict;
  final bool wholeUnits;

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
  Object? _saveError;

  @override
  void initState() {
    super.initState();
    _price = TextEditingController(
      text: widget.currentPrice == null ? '' : formatDecimal(widget.currentPrice, digits: 2),
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

  void _recompute() => setState(() => _saveError = null);

  double _number(TextEditingController c) => parseDecimal(c.text) ?? 0;

  double get _total => _number(_quantityFormat) * _number(_price) + _number(_fees);

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() {
      _saving = true;
      _saveError = null;
    });
    final api = ref.read(apiRepositoryProvider);
    final quantidade = _number(_quantityFormat);
    try {
      final entryId = await api
          .createTransaction(
            kind: 'buy',
            symbol: widget.ticker,
            tradedOn: _date.toIso8601String().substring(0, 10),
            quantity: quantidade,
            price: _number(_price),
            fees: _number(_fees),
          );
      Object? falhaAoAcompanhar;
      if (widget.verdict != null && _follow) {
        try {
          await api.followFromLedger(
            entryId: entryId,
            source: 'opportunities',
            verdictAtSuggestion: widget.verdict,
          );
        } catch (e) {
          falhaAoAcompanhar = e;
        }
      }
      if (mounted) {
        Navigator.pop(
          context,
          _Registro(quantity: quantidade, followError: falhaAoAcompanhar),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _saving = false;
          _saveError = e;
        });
      }
    }
  }

  Future<void> _pickDate() async {
    final escolhida = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2000),
      lastDate: DateTime.now(),
    );
    if (escolhida != null && mounted) setState(() => _date = escolhida);
  }

  @override
  Widget build(BuildContext context) {
    final carteira = ref.watch(portfolioProvider);
    final falha = _saveError;

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
                keyboardType: widget.wholeUnits
                    ? TextInputType.number
                    : const TextInputType.numberWithOptions(decimal: true),
                validator: (v) {
                  final n = parseDecimal(v);
                  if (n == null || n <= 0) return 'Informe quantas você comprou';
                  if (widget.wholeUnits && n != n.truncateToDouble()) {
                    return 'Na bolsa a compra é em unidades inteiras';
                  }
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
                  final n = parseDecimal(v);
                  if (n == null || n <= 0) return 'Informe o preço pago';
                  return null;
                },
              ),
              const SizedBox(height: FiSpace.s3),
              FiRows(
                children: [
                  FiDataRow(
                    label: 'Data da compra',
                    value: formatDate(_date.toIso8601String().substring(0, 10)),
                    onTap: _saving ? null : _pickDate,
                  ),
                ],
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
                validator: (v) {
                  if ((v ?? '').trim().isEmpty) return null;
                  final n = parseDecimal(v);
                  if (n == null) return 'Informe as taxas, ou 0 se não houve';
                  if (n < 0) return 'Taxa não fica negativa: use 0 se não houve';
                  return null;
                },
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
                FiRows(
                  children: [
                    FiDataRow(
                      label: 'Acompanhar o resultado desta compra',
                      detail: 'Entra em Sugestões seguidas, medida contra o Ibovespa a partir da '
                          'data da compra. Dá para deixar de acompanhar depois.',
                      trailing: FiSwitch(
                        label: 'Acompanhar o resultado desta compra',
                        value: _follow,
                        onChanged: _saving ? null : (v) => setState(() => _follow = v),
                      ),
                    ),
                  ],
                ),
              ],
              if (falha != null)
                Padding(
                  padding: const EdgeInsets.only(top: FiSpace.s4),
                  child: Semantics(
                    liveRegion: true,
                    child: Text(
                      fiErrorMessage(falha, action: 'registrar esta compra'),
                      style: FiType.caption.copyWith(
                        color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
                      ),
                    ),
                  ),
                ),
              const SizedBox(height: FiSpace.s5),
              FiButton.primary(
                label: 'Adicionar à carteira',
                busy: _saving,
                onPressed: _save,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
