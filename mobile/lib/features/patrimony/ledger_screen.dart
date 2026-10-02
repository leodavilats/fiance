import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/vocabulary.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/chip.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/disclosure.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import 'widgets/form_fields.dart';

Future<void> openLedgerEntryForm(
  BuildContext context,
  WidgetRef ref, {
  String? symbol,
}) async {
  final salvo = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: _LedgerEntryForm(symbol: symbol),
    ),
  );

  if (salvo == true) {
    invalidateLedgerReaders(ref);
    if (context.mounted) fiNotify(context, 'Lançamento registrado. A carteira foi refeita com ele.');
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
                    hint: 'Registre uma compra, uma venda ou um evento corporativo — ou traga '
                        'o extrato da corretora de uma vez.',
                    action: FiButton.primary(
                      label: 'Registrar lançamento',
                      icon: Icons.add,
                      onPressed: () => openLedgerEntryForm(context, ref),
                    ),
                    secondary: FiButton.secondary(
                      label: 'Importar extrato',
                      icon: Icons.upload_file_outlined,
                      onPressed: () => context.push('/patrimonio/razao/importar'),
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
                FiSection(
                  title: filtro.isEmpty
                      ? 'Lançamentos'
                      : 'Recorte · ${_filterInWords(filtro)}',
                  count: data.count,
                  trailing: const _FilterButton(),
                  child: Column(
                    children: [
                      for (final item in data.items)
                        _LedgerEntryRow(
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

Future<bool> deleteLedgerEntry(
  BuildContext context,
  WidgetRef ref,
  LedgerEntry item,
) async {
  final id = item.id;
  if (id == null) return false;

  final confirmado = await fiConfirm(
    context,
    title: 'Apagar ${ledgerKindLabel(item.kind).toLowerCase()} de ${item.symbol}?',
    body: 'A carteira é reconstruída sem este lançamento, e a apuração do mês muda junto.',
    confirmLabel: 'Apagar',
  );
  if (!confirmado || !context.mounted) return false;

  final apagado = await fiAttempt(
    context,
    () => ref.read(apiRepositoryProvider).deleteTransaction(id),
    action: 'apagar este lançamento',
    success: 'Lançamento apagado. A carteira foi refeita sem ele.',
  );
  if (apagado) invalidateLedgerReaders(ref);
  return apagado;
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

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Text(
            'RECORTE · ${_filterInWords(filtro).toUpperCase()}',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: FiType.eyebrow.copyWith(color: fiInk3(context)),
          ),
        ),
        const SizedBox(width: FiSpace.s3),
        const _FilterButton(),
      ],
    );
  }
}

class _FilterButton extends ConsumerWidget {
  const _FilterButton();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activeCount = ref.watch(ledgerFilterProvider).activeCount;

    return FiButton.secondary(
      label: activeCount == 0 ? 'Filtros' : 'Filtros · $activeCount',
      icon: Icons.tune,
      onPressed: () => openLedgerFilterSheet(context),
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
          _LedgerEntryRow(
            item: item,
            onDelete: () async {
              final apagado = await deleteLedgerEntry(context, ref, item);
              if (apagado && mounted) setState(() => _extras.remove(item));
            },
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
        const SizedBox(height: FiSpace.s3),
        Wrap(
          spacing: FiSpace.s2,
          runSpacing: FiSpace.s2,
          children: [
            FiButton.secondary(
              label: 'Importar extrato',
              icon: Icons.upload_file_outlined,
              onPressed: () => context.push('/patrimonio/razao/importar'),
            ),
            FiButton.quiet(
              label: 'Conferir com o razão',
              icon: Icons.fact_check_outlined,
              onPressed: () => context.push('/patrimonio/razao/conferir'),
            ),
          ],
        ),
      ],
    );
  }
}

bool _showsPrice(LedgerEntry item) =>
    item.hasPrice || (item.kind == 'adjust' && item.price > 0);

bool _showsQuantity(LedgerEntry item) => item.hasQuantity || item.kind == 'adjust';

String _entryDetail(LedgerEntry item) {
  if (item.kind == 'split') {
    return 'De ${formatQuantity(item.ratioFrom)} para ${formatQuantity(item.ratioTo)}';
  }
  if (item.kind == 'amortization') return 'Valor devolvido';
  if (_showsPrice(item)) {
    return '${formatQuantity(item.quantity)} × ${formatCurrency(item.price)}';
  }
  if (_showsQuantity(item)) return '${formatQuantity(item.quantity)} un.';
  return '';
}

String? _entryValue(LedgerEntry item) {
  if (item.kind == 'amortization') return formatCurrency(item.amount);
  if (_showsPrice(item)) return formatCurrency(item.grossValue);
  return null;
}

class FiEntryDate extends StatelessWidget {
  const FiEntryDate({super.key, required this.isoDate});

  final String isoDate;

  @override
  Widget build(BuildContext context) {
    final completa = formatDate(isoDate);
    final partes = completa.split('/');

    return SizedBox(
      width: 44,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: partes.length == 3
            ? [
                Text(
                  '${partes[0]}/${partes[1]}',
                  style: FiType.figure.copyWith(color: fiInk2(context)),
                ),
                Text(partes[2], style: FiType.caption.copyWith(color: fiInk3(context))),
              ]
            : [Text(completa, style: FiType.caption.copyWith(color: fiInk3(context)))],
      ),
    );
  }
}

class _LedgerEntryRow extends StatelessWidget {
  const _LedgerEntryRow({required this.item, required this.onDelete});

  final LedgerEntry item;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final detalhe = _entryDetail(item);

    return FiDisclosure(
      leading: FiEntryDate(isoDate: item.tradedOn),
      title: '${item.symbol} · ${ledgerKindLabel(item.kind)}',
      detail: detalhe.isEmpty ? null : detalhe,
      value: _entryValue(item),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          FiRows(
            children: [
              FiDataRow(label: 'Data', value: formatDate(item.tradedOn), dense: true),
              if (_showsQuantity(item))
                FiDataRow(
                  label: 'Quantidade',
                  value: formatQuantity(item.quantity),
                  dense: true,
                ),
              if (_showsPrice(item))
                FiDataRow(
                  label: item.kind == 'adjust' ? 'Preço médio' : 'Preço',
                  value: formatCurrency(item.price),
                  dense: true,
                ),
              if (item.hasPrice)
                FiDataRow(
                  label: 'Valor bruto',
                  value: formatCurrency(item.grossValue),
                  dense: true,
                ),
              if (item.fees > 0)
                FiDataRow(label: 'Custos', value: formatCurrency(item.fees), dense: true),
              if (item.kind == 'split')
                FiDataRow(
                  label: 'Proporção',
                  value: '${formatQuantity(item.ratioFrom)} : '
                      '${formatQuantity(item.ratioTo)}',
                  dense: true,
                ),
              if (item.kind == 'amortization')
                FiDataRow(
                  label: 'Valor devolvido',
                  value: formatCurrency(item.amount),
                  dense: true,
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
          if (item.id != null) ...[
            const SizedBox(height: FiSpace.s3),
            FiButton.danger(label: 'Apagar lançamento', onPressed: onDelete),
          ],
        ],
      ),
    );
  }
}

class _LedgerEntryForm extends ConsumerStatefulWidget {
  const _LedgerEntryForm({this.symbol});

  final String? symbol;

  @override
  ConsumerState<_LedgerEntryForm> createState() => _LedgerEntryFormState();
}

class _LedgerEntryFormState extends ConsumerState<_LedgerEntryForm> {
  final _formKey = GlobalKey<FormState>();
  late final _ticker = TextEditingController(text: widget.symbol ?? '');
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
  Object? _error;

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

  double _number(TextEditingController c) => parseDecimal(c.text) ?? 0;

  String? _positive(String? texto, String mensagem) {
    final n = parseDecimal(texto);
    return n == null || n <= 0 ? mensagem : null;
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() {
      _saving = true;
      _error = null;
    });
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
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = e;
      });
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
              FiTickerFormField(controller: _ticker),
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
                  validator: (v) => _positive(v, 'Informe uma quantidade positiva'),
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
                  validator: (v) => _positive(v, 'Informe um preço positivo'),
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
                        validator: (v) => _positive(v, 'Informe a proporção'),
                      ),
                    ),
                    const SizedBox(width: FiSpace.s3),
                    Expanded(
                      child: TextFormField(
                        controller: _to,
                        decoration: const InputDecoration(labelText: 'Para'),
                        keyboardType: TextInputType.number,
                        validator: (v) => _positive(v, 'Informe a proporção'),
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
                  validator: (v) => _positive(v, 'Informe o valor devolvido'),
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
                validator: (v) {
                  if ((v ?? '').trim().isEmpty) return null;
                  final n = parseDecimal(v);
                  return n == null || n < 0 ? 'Informe um valor, ou deixe 0' : null;
                },
              ),
              const SizedBox(height: FiSpace.s3),
              TextFormField(
                controller: _note,
                decoration: const InputDecoration(labelText: 'Observação (opcional)'),
              ),
              const SizedBox(height: FiSpace.s5),
              if (_error != null)
                FiInlineError(fiErrorMessage(_error!, action: 'registrar o lançamento')),
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
