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

Future<void> openLedgerEntryForm(BuildContext context, WidgetRef ref) async {
  final salvo = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: const _LedgerEntryForm(),
    ),
  );

  if (salvo == true) {
    ref.invalidate(ledgerProvider);
    ref.invalidate(filteredLedgerProvider);
    ref.invalidate(portfolioProvider);
    ref.invalidate(dashboardProvider);
  }
}

const double _fabTail = 88;

class LedgerScreen extends ConsumerWidget {
  const LedgerScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final page = ref.watch(filteredLedgerProvider);
    final filtro = ref.watch(ledgerFilterProvider);

    final emptyLedger =
        (page.valueOrNull?.items.isEmpty ?? false) && filtro.isEmpty;

    return Scaffold(
      appBar: AppBar(title: const Text('Livro-razão')),
      floatingActionButton: emptyLedger
          ? null
          : FloatingActionButton.extended(
              onPressed: () => openLedgerEntryForm(context, ref),
              icon: const Icon(Icons.add),
              label: const Text('Registrar'),
            ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(filteredLedgerProvider),
        child: page.when(
          loading: () => FiSkeleton.screen(
            shape: FiSkeletonShape.row,
            count: 6,
            label: 'Carregando seus lançamentos',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar seus lançamentos',
            action: 'carregar o livro-razão',
            onRetry: () => ref.invalidate(filteredLedgerProvider),
          ),
          data: (data) {
            if (data.items.isEmpty && !filtro.isEmpty) {
              return ListView(
                padding: const EdgeInsets.fromLTRB(
                  FiLayout.gutter,
                  FiSpace.s3,
                  FiLayout.gutter,
                  _fabTail,
                ),
                children: [
                  const _FilterBar(),
                  const SizedBox(height: FiSpace.s5),
                  FiEmptyState(
                    title: 'Nenhum lançamento com estes filtros',
                    body: 'O corte atual não deixou nada passar. Os lançamentos continuam '
                        'no razão — o que mudou foi só o recorte.',
                    action: FiButton.secondary(
                      label: 'Limpar filtros',
                      onPressed: () =>
                          ref.read(ledgerFilterProvider.notifier).state =
                              const LedgerFilter(),
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
                      onPressed: () => openLedgerEntryForm(context, ref),
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
                _fabTail,
              ),
              children: [
                const _Header(),
                const SizedBox(height: FiSpace.s5),
                const _FilterBar(),
                FiSection(
                  title: 'Lançamentos',
                  count: data.items.length,
                  child: Column(
                    children: [
                      for (final item in data.items)
                        _LedgerEntryObject(
                          item: item,
                          onDelete: () => deleteLedgerEntry(context, ref, item),
                        ),
                    ],
                  ),
                ),
                if (data.hasMore && data.nextCursor != null)
                  Padding(
                    padding: const EdgeInsets.only(top: FiSpace.s3),
                    child: _OlderEntries(cursor: data.nextCursor!),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

Future<void> deleteLedgerEntry(
  BuildContext context,
  WidgetRef ref,
  LedgerEntry item,
) async {
  final confirmado = await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(
        'Apagar ${ledgerKindLabel(item.kind).toLowerCase()} de ${item.symbol}?',
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
    ref.invalidate(ledgerProvider);
    ref.invalidate(filteredLedgerProvider);
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

const _ledgerKindLabels = {
  'buy': 'Compras',
  'sell': 'Vendas',
  'split': 'Desdobramentos',
  'bonus': 'Bonificações',
  'transfer_in': 'Transferências recebidas',
  'transfer_out': 'Transferências enviadas',
  'amortization': 'Amortizações',
  'adjust': 'Declarações de posição',
};

const _ledgerPeriods = {
  'mes': 'Este mês',
  'ano': 'Este ano',
  '12m': 'Últimos 12 meses',
};

String _filterInWords(LedgerFilter filtro) {
  final partes = <String>[
    if (filtro.period != null) _ledgerPeriods[filtro.period] ?? filtro.period!,
    if (filtro.kinds.length == 1)
      _ledgerKindLabels[filtro.kinds.first] ?? filtro.kinds.first
    else if (filtro.kinds.length > 1)
      '${filtro.kinds.length} tipos',
    if (filtro.symbol != null) filtro.symbol!,
  ];
  return partes.join(' · ');
}

class _FilterBar extends ConsumerWidget {
  const _FilterBar();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtro = ref.watch(ledgerFilterProvider);
    final activeCount = filtro.activeCount;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Text(
            filtro.isEmpty
                ? 'TODOS OS LANÇAMENTOS'
                : 'RECORTE · ${_filterInWords(filtro).toUpperCase()}',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: FiType.eyebrow.copyWith(color: fiInk3(context)),
          ),
        ),
        const SizedBox(width: FiSpace.s3),
        FiButton.secondary(
          label: activeCount == 0 ? 'Filtros' : 'Filtros · $activeCount',
          icon: Icons.tune,
          onPressed: () => openLedgerFilterSheet(context),
        ),
      ],
    );
  }
}

Future<void> openLedgerFilterSheet(BuildContext context) => showModalBottomSheet<void>(
  context: context,
  isScrollControlled: true,
  showDragHandle: true,
  constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
  builder: (context) => Padding(
    padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
    child: const _LedgerFilterSheet(),
  ),
);

class _LedgerFilterSheet extends ConsumerWidget {
  const _LedgerFilterSheet();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtro = ref.watch(ledgerFilterProvider);
    final notifier = ref.read(ledgerFilterProvider.notifier);

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
                for (final e in _ledgerPeriods.entries)
                  FiChoiceChip(
                    label: e.value,
                    selected: filtro.period == e.key,
                    onSelected: () => notifier.state = filtro.period == e.key
                        ? filtro.copyWith(clearPeriod: true)
                        : filtro.copyWith(period: e.key),
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
                for (final e in _ledgerKindLabels.entries)
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
            _TickerFilter(current: filtro.symbol),

            const SizedBox(height: FiSpace.s6),
            FiButton.primary(
              label: 'Ver os lançamentos',
              expand: true,
              onPressed: () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: FiSpace.s2),
            FiButton.quiet(
              label: 'Limpar o recorte',
              onPressed: filtro.isEmpty
                  ? null
                  : () => notifier.state = const LedgerFilter(),
            ),
          ],
        ),
      ),
    );
  }
}

class _TickerFilter extends ConsumerStatefulWidget {
  const _TickerFilter({this.current});

  final String? current;

  @override
  ConsumerState<_TickerFilter> createState() => _TickerFilterState();
}

class _TickerFilterState extends ConsumerState<_TickerFilter> {
  final _ticker = TextEditingController();

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final current = widget.current;
    if (current != null) {
      return Align(
        alignment: Alignment.centerLeft,
        child: FiChoiceChip(
          label: 'Só $current',
          selected: true,
          onSelected: () {
            _ticker.clear();
            ref.read(ledgerFilterProvider.notifier).state = ref
                .read(ledgerFilterProvider)
                .copyWith(clearSymbol: true);
          },
        ),
      );
    }

    return TickerAutocompleteField(
      controller: _ticker,
      labelText: 'Filtrar por ativo',
      onSelected: (s) {
        ref.read(ledgerFilterProvider.notifier).state = ref
            .read(ledgerFilterProvider)
            .copyWith(symbol: s.ticker);
      },
    );
  }
}

class _OlderEntries extends ConsumerStatefulWidget {
  const _OlderEntries({required this.cursor});

  final String cursor;

  @override
  ConsumerState<_OlderEntries> createState() => _OlderEntriesState();
}

class _OlderEntriesState extends ConsumerState<_OlderEntries> {
  final List<LedgerEntry> _extras = [];
  String? _cursor;
  bool _loading = false;
  Object? _error;

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final filtro = ref.read(ledgerFilterProvider);
      final page = await ref
          .read(apiRepositoryProvider)
          .getTransactions(
            symbol: filtro.symbol,
            kinds: filtro.kinds,
            tradedFrom: fiPeriodStart(filtro.period),
            cursor: _cursor ?? widget.cursor,
          );
      if (!mounted) return;
      setState(() {
        _extras.addAll(page.items);
        _cursor = page.hasMore ? page.nextCursor : null;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e;
        _loading = false;
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
          _LedgerEntryObject(
            item: item,
            onDelete: () => deleteLedgerEntry(context, ref, item),
          ),
        if (_error != null) ...[
          const SizedBox(height: FiSpace.s2),
          Text(
            fiErrorMessage(_error!, action: 'carregar os lançamentos anteriores'),
            style: FiType.caption.copyWith(
              color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
            ),
          ),
        ],
        const SizedBox(height: FiSpace.s2),
        if (temMais)
          FiButton.secondary(
            label: _loading ? 'Carregando…' : 'Carregar os anteriores',
            busy: _loading,
            onPressed: _loading ? null : _load,
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

class _Header extends StatelessWidget {
  const _Header();

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

class _LedgerEntryObject extends StatelessWidget {
  const _LedgerEntryObject({required this.item, required this.onDelete});

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
                FiTag.series(
                  label: ledgerKindLabel(item.kind),
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
                if (item.hasQuantity)
                  FiDataRow(
                    label: 'Quantidade',
                    value: formatQuantity(item.quantity),
                  ),
                if (item.hasPrice)
                  FiDataRow(label: 'Preço', value: formatCurrency(item.price)),
                if (item.hasPrice)
                  FiDataRow(
                    label: 'Valor bruto',
                    value: formatCurrency(item.grossValue),
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

class _LedgerEntryForm extends ConsumerStatefulWidget {
  const _LedgerEntryForm();

  @override
  ConsumerState<_LedgerEntryForm> createState() => _LedgerEntryFormState();
}

class _LedgerEntryFormState extends ConsumerState<_LedgerEntryForm> {
  final _formKey = GlobalKey<FormState>();
  final _ticker = TextEditingController();
  final _quantityFormat = TextEditingController();
  final _price = TextEditingController();
  final _fees = TextEditingController(text: '0');
  final _from = TextEditingController(text: '1');
  final _to = TextEditingController(text: '2');
  final _amount = TextEditingController();
  final _note = TextEditingController();

  String _kind = 'buy';
  DateTime _date = DateTime.now();
  bool _saving = false;

  @override
  void dispose() {
    _ticker.dispose();
    _quantityFormat.dispose();
    _price.dispose();
    _fees.dispose();
    _from.dispose();
    _to.dispose();
    _amount.dispose();
    _note.dispose();
    super.dispose();
  }

  bool get _needsQuantity => const {
    'buy',
    'sell',
    'bonus',
    'transfer_in',
    'transfer_out',
    'adjust',
  }.contains(_kind);

  bool get _needsPrice => _kind == 'buy' || _kind == 'sell' || _kind == 'adjust';

  double _number(TextEditingController c) =>
      double.tryParse(c.text.trim().replaceAll(',', '.')) ?? 0;

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _saving = true);
    try {
      await ref
          .read(apiRepositoryProvider)
          .createTransaction(
            kind: _kind,
            symbol: _ticker.text.trim().toUpperCase(),
            tradedOn: _date.toIso8601String().substring(0, 10),
            quantity: _needsQuantity ? _number(_quantityFormat) : 0,
            price: _needsPrice ? _number(_price) : 0,
            fees: _number(_fees),
            ratioFrom: _kind == 'split' ? _number(_from) : 1,
            ratioTo: _kind == 'split' ? _number(_to) : 1,
            amount: _kind == 'amortization' ? _number(_amount) : 0,
            note: _note.text.trim().isEmpty ? null : _note.text.trim(),
          );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(fiErrorMessage(e, action: 'registrar o lançamento'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final explicacao = ledgerKindExplanation(_kind);

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
                  for (final e in fiLedgerKinds.entries)
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
              if (_needsQuantity) ...[
                const SizedBox(height: FiSpace.s3),
                TextFormField(
                  controller: _quantityFormat,
                  decoration: const InputDecoration(labelText: 'Quantidade'),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    final n = double.tryParse((v ?? '').replaceAll(',', '.'));
                    if (n == null || n <= 0) return 'Informe uma quantidade positiva';
                    return null;
                  },
                ),
              ],
              if (_needsPrice) ...[
                const SizedBox(height: FiSpace.s3),
                TextFormField(
                  controller: _price,
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
                        controller: _from,
                        decoration: const InputDecoration(labelText: 'De'),
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    const SizedBox(width: FiSpace.s3),
                    Expanded(
                      child: TextFormField(
                        controller: _to,
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
                  controller: _amount,
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
                controller: _fees,
                decoration: const InputDecoration(
                  labelText: 'Custos da operação',
                  prefixText: 'R\$ ',
                  helperText: 'Corretagem e emolumentos. Entram no custo e no imposto.',
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _note,
                decoration: const InputDecoration(labelText: 'Observação (opcional)'),
              ),
              const SizedBox(height: FiSpace.s5),
              FiButton.primary(
                label: _saving ? 'Registrando…' : 'Registrar lançamento',
                onPressed: _saving ? null : _save,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
