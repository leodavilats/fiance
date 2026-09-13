import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';

Future<bool> abrirCompraDeAtivo(
  BuildContext context,
  WidgetRef ref, {
  required String ticker,
  double? precoAtual,
}) async {
  final registrou = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: _CompraForm(ticker: ticker, precoAtual: precoAtual),
    ),
  );

  if (registrou == true) {
    ref.invalidate(portfolioProvider);
    ref.invalidate(dashboardProvider);
    ref.invalidate(razaoProvider);
  }

  return registrou == true;
}

class _CompraForm extends ConsumerStatefulWidget {
  const _CompraForm({required this.ticker, this.precoAtual});

  final String ticker;
  final double? precoAtual;

  @override
  ConsumerState<_CompraForm> createState() => _CompraFormState();
}

class _CompraFormState extends ConsumerState<_CompraForm> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _preco;
  final _quantidade = TextEditingController();
  final _custos = TextEditingController(text: '0');

  DateTime _data = DateTime.now();
  bool _salvando = false;

  @override
  void initState() {
    super.initState();
    _preco = TextEditingController(
      text: widget.precoAtual == null
          ? ''
          : widget.precoAtual!.toStringAsFixed(2).replaceAll('.', ','),
    );
    _quantidade.addListener(_recalcular);
    _preco.addListener(_recalcular);
    _custos.addListener(_recalcular);
  }

  @override
  void dispose() {
    _preco.dispose();
    _quantidade.dispose();
    _custos.dispose();
    super.dispose();
  }

  void _recalcular() => setState(() {});

  double _numero(TextEditingController c) =>
      double.tryParse(c.text.trim().replaceAll(',', '.')) ?? 0;

  double get _total => _numero(_quantidade) * _numero(_preco) + _numero(_custos);

  Future<void> _salvar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _salvando = true);
    try {
      await ref
          .read(apiRepositoryProvider)
          .createTransaction(
            kind: 'buy',
            symbol: widget.ticker,
            tradedOn: _data.toIso8601String().substring(0, 10),
            quantity: _numero(_quantidade),
            price: _numero(_preco),
            fees: _numero(_custos),
          );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() => _salvando = false);
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
                controller: _quantidade,
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
                controller: _preco,
                decoration: InputDecoration(
                  labelText: 'Preço pago por unidade',
                  prefixText: 'R\$ ',
                  helperText: widget.precoAtual == null
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
                      initialDate: _data,
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now(),
                    );
                    if (escolhida != null) setState(() => _data = escolhida);
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: FiSpace.s1),
                    child: Text(
                      formatDate(_data.toIso8601String().substring(0, 10)),
                      style: FiType.body.copyWith(color: fiInk1(context)),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _custos,
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
              const SizedBox(height: FiSpace.s5),
              FiButton.primary(
                label: _salvando ? 'Registrando…' : 'Adicionar à carteira',
                onPressed: _salvando ? null : _salvar,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
