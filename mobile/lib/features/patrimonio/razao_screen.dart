import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/vocabulary.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/chip.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';

Future<void> abrirFormDeLancamento(BuildContext context, WidgetRef ref) async {
  final salvo = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: const _LancamentoForm(),
    ),
  );

  if (salvo == true) {
    ref.invalidate(razaoProvider);
    ref.invalidate(razaoFiltradoProvider);
    ref.invalidate(portfolioProvider);
    ref.invalidate(dashboardProvider);
  }
}

const double _rodapeDoFab = 88;

class RazaoScreen extends ConsumerWidget {
  const RazaoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pagina = ref.watch(razaoFiltradoProvider);
    final filtro = ref.watch(razaoFiltroProvider);

    final razaoEmBranco =
        (pagina.valueOrNull?.items.isEmpty ?? false) && filtro.vazio;

    return Scaffold(
      appBar: AppBar(title: const Text('Livro-razão')),
      floatingActionButton: razaoEmBranco
          ? null
          : FloatingActionButton.extended(
              onPressed: () => abrirFormDeLancamento(context, ref),
              icon: const Icon(Icons.add),
              label: const Text('Registrar'),
            ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(razaoFiltradoProvider),
        child: pagina.when(
          loading: () => FiSkeleton.tela(
            shape: FiSkeletonShape.row,
            count: 6,
            label: 'Carregando seus lançamentos',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar seus lançamentos',
            action: 'carregar o livro-razão',
            onRetry: () => ref.invalidate(razaoFiltradoProvider),
          ),
          data: (data) {
            if (data.items.isEmpty && !filtro.vazio) {
              return ListView(
                padding: const EdgeInsets.fromLTRB(
                  FiLayout.gutter,
                  FiSpace.s3,
                  FiLayout.gutter,
                  _rodapeDoFab,
                ),
                children: [
                  const _BarraDeFiltros(),
                  const SizedBox(height: FiSpace.s5),
                  FiEmptyState(
                    title: 'Nenhum lançamento com estes filtros',
                    body: 'O corte atual não deixou nada passar. Os lançamentos continuam '
                        'no razão — o que mudou foi só o recorte.',
                    action: FiButton.secondary(
                      label: 'Limpar filtros',
                      onPressed: () =>
                          ref.read(razaoFiltroProvider.notifier).state =
                              const RazaoFiltro(),
                    ),
                  ),
                ],
              );
            }

            if (data.items.isEmpty) {
              return ListView(
                children: [
                  FiEmptyState(
                    title: 'Nenhum lançamento registrado',
                    body: 'O livro-razão é a fonte da sua carteira: a posição, o preço médio e a '
                        'apuração de imposto são reconstruídos a partir dele, nunca guardados '
                        'em separado.',
                    hint: 'Registre uma compra, uma venda ou um evento corporativo.',
                    action: FiButton.primary(
                      label: 'Registrar lançamento',
                      icon: Icons.add,
                      onPressed: () => abrirFormDeLancamento(context, ref),
                    ),
                  ),
                ],
              );
            }

            return ListView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                FiSpace.s3,
                FiLayout.gutter,
                _rodapeDoFab,
              ),
              children: [
                const _Cabecalho(),
                const SizedBox(height: FiSpace.s5),
                const _BarraDeFiltros(),
                FiSection(
                  title: 'Lançamentos',
                  count: data.items.length,
                  child: Column(
                    children: [
                      for (final item in data.items)
                        _LancamentoObject(
                          item: item,
                          onDelete: () => apagarLancamento(context, ref, item),
                        ),
                    ],
                  ),
                ),
                if (data.hasMore && data.nextCursor != null)
                  Padding(
                    padding: const EdgeInsets.only(top: FiSpace.s3),
                    child: _MaisAntigos(cursor: data.nextCursor!),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

Future<void> apagarLancamento(
  BuildContext context,
  WidgetRef ref,
  LedgerEntry item,
) async {
  final confirmado = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(
        'Apagar ${lancamentoTipoLabel(item.kind).toLowerCase()} de ${item.symbol}?',
      ),
      content: const Text(
        'A carteira é reconstruída sem este lançamento, e a apuração do mês muda junto.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, true),
          child: const Text('Apagar'),
        ),
      ],
    ),
  );
  if (confirmado != true || item.id == null) return;

  try {
    await ref.read(apiRepositoryProvider).deleteTransaction(item.id!);
    ref.invalidate(razaoProvider);
    ref.invalidate(razaoFiltradoProvider);
    ref.invalidate(portfolioProvider);
    ref.invalidate(dashboardProvider);
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(fiErrorMessage(e, action: 'apagar este lançamento')),
        ),
      );
    }
  }
}

const _tiposDeLancamento = {
  'buy': 'Compras',
  'sell': 'Vendas',
  'split': 'Desdobramentos',
  'bonus': 'Bonificações',
  'transfer_in': 'Transferências recebidas',
  'transfer_out': 'Transferências enviadas',
  'amortization': 'Amortizações',
  'adjust': 'Declarações de posição',
};

const _periodosDoRazao = {
  'mes': 'Este mês',
  'ano': 'Este ano',
  '12m': 'Últimos 12 meses',
};

String _recorteEmPalavras(RazaoFiltro filtro) {
  final partes = <String>[
    if (filtro.periodo != null) _periodosDoRazao[filtro.periodo] ?? filtro.periodo!,
    if (filtro.kinds.length == 1)
      _tiposDeLancamento[filtro.kinds.first] ?? filtro.kinds.first
    else if (filtro.kinds.length > 1)
      '${filtro.kinds.length} tipos',
    if (filtro.symbol != null) filtro.symbol!,
  ];
  return partes.join(' · ');
}

class _BarraDeFiltros extends ConsumerWidget {
  const _BarraDeFiltros();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtro = ref.watch(razaoFiltroProvider);
    final ativos = filtro.ativos;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Text(
            filtro.vazio
                ? 'TODOS OS LANÇAMENTOS'
                : 'RECORTE · ${_recorteEmPalavras(filtro).toUpperCase()}',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: FiType.eyebrow.copyWith(color: fiInk3(context)),
          ),
        ),
        const SizedBox(width: FiSpace.s3),
        FiButton.secondary(
          label: ativos == 0 ? 'Filtros' : 'Filtros · $ativos',
          icon: Icons.tune,
          onPressed: () => abrirFolhaDeFiltros(context),
        ),
      ],
    );
  }
}

Future<void> abrirFolhaDeFiltros(BuildContext context) => showModalBottomSheet<void>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
  builder: (context) => Padding(
    padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
    child: const _FolhaDeFiltros(),
  ),
);

class _FolhaDeFiltros extends ConsumerWidget {
  const _FolhaDeFiltros();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtro = ref.watch(razaoFiltroProvider);
    final notifier = ref.read(razaoFiltroProvider.notifier);

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiSpace.s5,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Recortar o razão',
              style: FiType.title.copyWith(color: fiInk1(context)),
            ),
            const SizedBox(height: FiSpace.s2),
            Text(
              'O recorte muda o que a lista mostra, nunca o que está lançado.',
              style: FiType.caption.copyWith(color: fiInk3(context)),
            ),

            const SizedBox(height: FiSpace.s5),
            Text(
              'PERÍODO',
              style: FiType.eyebrow.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            Wrap(
              spacing: FiSpace.s2,
              runSpacing: FiSpace.s2,
              children: [
                for (final e in _periodosDoRazao.entries)
                  FiChoiceChip(
                    label: e.value,
                    selected: filtro.periodo == e.key,
                    onSelected: () => notifier.state = filtro.periodo == e.key
                        ? filtro.copyWith(limparPeriodo: true)
                        : filtro.copyWith(periodo: e.key),
                  ),
              ],
            ),

            const SizedBox(height: FiSpace.s5),
            Text(
              'TIPO DE LANÇAMENTO',
              style: FiType.eyebrow.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            Wrap(
              spacing: FiSpace.s2,
              runSpacing: FiSpace.s2,
              children: [
                for (final e in _tiposDeLancamento.entries)
                  FiChoiceChip(
                    label: e.value,
                    selected: filtro.kinds.contains(e.key),
                    onSelected: () {
                      final tipos = [...filtro.kinds];
                      if (!tipos.remove(e.key)) tipos.add(e.key);
                      notifier.state = filtro.copyWith(kinds: tipos);
                    },
                  ),
              ],
            ),

            const SizedBox(height: FiSpace.s5),
            Text(
              'ATIVO',
              style: FiType.eyebrow.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            _FiltroDeTicker(atual: filtro.symbol),

            const SizedBox(height: FiSpace.s6),
            FiButton.primary(
              label: 'Ver os lançamentos',
              expand: true,
              onPressed: () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: FiSpace.s2),
            FiButton.quiet(
              label: 'Limpar o recorte',
              onPressed: filtro.vazio
                  ? null
                  : () => notifier.state = const RazaoFiltro(),
            ),
          ],
        ),
      ),
    );
  }
}

class _FiltroDeTicker extends ConsumerStatefulWidget {
  const _FiltroDeTicker({this.atual});

  final String? atual;

  @override
  ConsumerState<_FiltroDeTicker> createState() => _FiltroDeTickerState();
}

class _FiltroDeTickerState extends ConsumerState<_FiltroDeTicker> {
  final _ticker = TextEditingController();

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final atual = widget.atual;
    if (atual != null) {
      return Align(
        alignment: Alignment.centerLeft,
        child: FiChoiceChip(
          label: 'Só $atual',
          selected: true,
          onSelected: () {
            _ticker.clear();
            ref.read(razaoFiltroProvider.notifier).state = ref
                .read(razaoFiltroProvider)
                .copyWith(limparSymbol: true);
          },
        ),
      );
    }

    return TickerAutocompleteField(
      controller: _ticker,
      labelText: 'Filtrar por ativo',
      onSelected: (s) {
        ref.read(razaoFiltroProvider.notifier).state = ref
            .read(razaoFiltroProvider)
            .copyWith(symbol: s.ticker);
      },
    );
  }
}

class _MaisAntigos extends ConsumerStatefulWidget {
  const _MaisAntigos({required this.cursor});

  final String cursor;

  @override
  ConsumerState<_MaisAntigos> createState() => _MaisAntigosState();
}

class _MaisAntigosState extends ConsumerState<_MaisAntigos> {
  final List<LedgerEntry> _extras = [];
  String? _cursor;
  bool _carregando = false;
  Object? _erro;

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final filtro = ref.read(razaoFiltroProvider);
      final pagina = await ref
          .read(apiRepositoryProvider)
          .getTransactions(
            symbol: filtro.symbol,
            kinds: filtro.kinds,
            tradedFrom: fiInicioDoPeriodo(filtro.periodo),
            cursor: _cursor ?? widget.cursor,
          );
      if (!mounted) return;
      setState(() {
        _extras.addAll(pagina.items);
        _cursor = pagina.hasMore ? pagina.nextCursor : null;
        _carregando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _erro = e;
        _carregando = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final temMais = _extras.isEmpty || _cursor != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final item in _extras)
          _LancamentoObject(
            item: item,
            onDelete: () => apagarLancamento(context, ref, item),
          ),
        if (_erro != null) ...[
          const SizedBox(height: FiSpace.s2),
          Text(
            fiErrorMessage(_erro!, action: 'carregar os lançamentos anteriores'),
            style: FiType.caption.copyWith(
              color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
            ),
          ),
        ],
        const SizedBox(height: FiSpace.s2),
        if (temMais)
          FiButton.secondary(
            label: _carregando ? 'Carregando…' : 'Carregar os anteriores',
            busy: _carregando,
            onPressed: _carregando ? null : _carregar,
          )
        else
          Text(
            'Fim do razão — não há lançamento anterior a estes.',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
      ],
    );
  }
}

class _Cabecalho extends StatelessWidget {
  const _Cabecalho();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'A carteira é reconstruída daqui',
          style: FiType.title.copyWith(color: fiInk1(context)),
        ),
        const SizedBox(height: FiSpace.s2),
        Text(
          'Cada linha é um fato, e a posição, o preço médio e o imposto do mês são projeções '
          'dele.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s2),
        const FiProvenance(
          summary: 'Como a posição é reconstruída',
          method: 'Preço médio pela convenção brasileira: a venda reduz quantidade e custo, '
              'nunca a média. Evento corporativo entra como lançamento, não como correção.',
          source: 'Seus lançamentos — registrados aqui ou importados de extrato.',
          limitation: 'Uma declaração de posição ancora a linha do tempo: compra com data '
              'anterior a ela é descartada, porque já está dentro do que foi declarado.',
        ),
      ],
    );
  }
}

class _LancamentoObject extends StatelessWidget {
  const _LancamentoObject({required this.item, required this.onDelete});

  final LedgerEntry item;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    item.symbol,
                    style: FiType.title.copyWith(color: fiInk1(context)),
                  ),
                ),
                const SizedBox(width: FiSpace.s2),
                FiTag.serie(
                  label: lancamentoTipoLabel(item.kind),
                  color: fiInk2(context),
                ),
                IconButton(
                  onPressed: onDelete,
                  icon: const Icon(Icons.delete_outline),
                  tooltip: 'Apagar lançamento',
                  iconSize: 20,
                ),
              ],
            ),
            FiRows(
              children: [
                FiDataRow(label: 'Data', value: formatDate(item.tradedOn)),
                if (item.temQuantidade)
                  FiDataRow(
                    label: 'Quantidade',
                    value: formatQuantity(item.quantity),
                  ),
                if (item.temPreco)
                  FiDataRow(label: 'Preço', value: formatCurrency(item.price)),
                if (item.temPreco)
                  FiDataRow(
                    label: 'Valor bruto',
                    value: formatCurrency(item.valorBruto),
                  ),
                if (item.fees > 0)
                  FiDataRow(label: 'Custos', value: formatCurrency(item.fees)),
                if (item.kind == 'split')
                  FiDataRow(
                    label: 'Proporção',
                    value: '${formatQuantity(item.ratioFrom)} : '
                        '${formatQuantity(item.ratioTo)}',
                  ),
                if (item.kind == 'amortization')
                  FiDataRow(
                    label: 'Valor devolvido',
                    value: formatCurrency(item.amount),
                  ),
              ],
            ),
            if ((item.note ?? '').isNotEmpty) ...[
              const SizedBox(height: FiSpace.s2),
              Text(
                item.note!,
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _LancamentoForm extends ConsumerStatefulWidget {
  const _LancamentoForm();

  @override
  ConsumerState<_LancamentoForm> createState() => _LancamentoFormState();
}

class _LancamentoFormState extends ConsumerState<_LancamentoForm> {
  final _formKey = GlobalKey<FormState>();
  final _ticker = TextEditingController();
  final _quantidade = TextEditingController();
  final _preco = TextEditingController();
  final _custos = TextEditingController(text: '0');
  final _de = TextEditingController(text: '1');
  final _para = TextEditingController(text: '2');
  final _valor = TextEditingController();
  final _nota = TextEditingController();

  String _kind = 'buy';
  DateTime _data = DateTime.now();
  bool _salvando = false;

  @override
  void dispose() {
    _ticker.dispose();
    _quantidade.dispose();
    _preco.dispose();
    _custos.dispose();
    _de.dispose();
    _para.dispose();
    _valor.dispose();
    _nota.dispose();
    super.dispose();
  }

  bool get _pedeQuantidade => const {
    'buy',
    'sell',
    'bonus',
    'transfer_in',
    'transfer_out',
    'adjust',
  }.contains(_kind);

  bool get _pedePreco => _kind == 'buy' || _kind == 'sell' || _kind == 'adjust';

  double _numero(TextEditingController c) =>
      double.tryParse(c.text.trim().replaceAll(',', '.')) ?? 0;

  Future<void> _salvar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _salvando = true);
    try {
      await ref
          .read(apiRepositoryProvider)
          .createTransaction(
            kind: _kind,
            symbol: _ticker.text.trim().toUpperCase(),
            tradedOn: _data.toIso8601String().substring(0, 10),
            quantity: _pedeQuantidade ? _numero(_quantidade) : 0,
            price: _pedePreco ? _numero(_preco) : 0,
            fees: _numero(_custos),
            ratioFrom: _kind == 'split' ? _numero(_de) : 1,
            ratioTo: _kind == 'split' ? _numero(_para) : 1,
            amount: _kind == 'amortization' ? _numero(_valor) : 0,
            note: _nota.text.trim().isEmpty ? null : _nota.text.trim(),
          );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() => _salvando = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(fiErrorMessage(e, action: 'registrar o lançamento'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final explicacao = lancamentoTipoExplicacao(_kind);

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
                'Novo lançamento',
                style: FiType.title.copyWith(color: fiInk1(context)),
              ),
              const SizedBox(height: FiSpace.s4),
              DropdownButtonFormField<String>(
                initialValue: _kind,
                decoration: const InputDecoration(labelText: 'Tipo'),
                items: [
                  for (final e in fiTiposDeLancamento.entries)
                    DropdownMenuItem(value: e.key, child: Text(e.value)),
                ],
                onChanged: (v) => setState(() => _kind = v ?? 'buy'),
              ),
              if (explicacao.isNotEmpty) ...[
                const SizedBox(height: FiSpace.s2),
                Text(
                  explicacao,
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ],
              const SizedBox(height: FiSpace.s3),
              TickerAutocompleteField(controller: _ticker),
              const SizedBox(height: FiSpace.s3),
              InputDecorator(
                decoration: const InputDecoration(labelText: 'Data da operação'),
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
              if (_pedeQuantidade) ...[
                const SizedBox(height: FiSpace.s3),
                TextFormField(
                  controller: _quantidade,
                  decoration: const InputDecoration(labelText: 'Quantidade'),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    final n = double.tryParse((v ?? '').replaceAll(',', '.'));
                    if (n == null || n <= 0) return 'Informe uma quantidade positiva';
                    return null;
                  },
                ),
              ],
              if (_pedePreco) ...[
                const SizedBox(height: FiSpace.s3),
                TextFormField(
                  controller: _preco,
                  decoration: const InputDecoration(
                    labelText: 'Preço por unidade',
                    prefixText: 'R\$ ',
                  ),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    final n = double.tryParse((v ?? '').replaceAll(',', '.'));
                    if (n == null || n <= 0) return 'Informe um preço positivo';
                    return null;
                  },
                ),
              ],
              if (_kind == 'split') ...[
                const SizedBox(height: FiSpace.s3),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _de,
                        decoration: const InputDecoration(labelText: 'De'),
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    const SizedBox(width: FiSpace.s3),
                    Expanded(
                      child: TextFormField(
                        controller: _para,
                        decoration: const InputDecoration(labelText: 'Para'),
                        keyboardType: TextInputType.number,
                      ),
                    ),
                  ],
                ),
              ],
              if (_kind == 'amortization') ...[
                const SizedBox(height: FiSpace.s3),
                TextFormField(
                  controller: _valor,
                  decoration: const InputDecoration(
                    labelText: 'Valor devolvido',
                    prefixText: 'R\$ ',
                  ),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    final n = double.tryParse((v ?? '').replaceAll(',', '.'));
                    if (n == null || n <= 0) return 'Informe o valor devolvido';
                    return null;
                  },
                ),
              ],
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _custos,
                decoration: const InputDecoration(
                  labelText: 'Custos da operação',
                  prefixText: 'R\$ ',
                  helperText: 'Corretagem e emolumentos. Entram no custo e no imposto.',
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _nota,
                decoration: const InputDecoration(labelText: 'Observação (opcional)'),
              ),
              const SizedBox(height: FiSpace.s5),
              FiButton.primary(
                label: _salvando ? 'Registrando…' : 'Registrar lançamento',
                onPressed: _salvando ? null : _salvar,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
