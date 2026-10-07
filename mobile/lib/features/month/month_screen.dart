import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/cash_models.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/format.dart';
import '../../core/month.dart';
import '../../core/month_verdict.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/labels.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import '../../core/widgets/nav_action.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import 'cash_entry_sheet.dart';
import 'cash_refresh.dart';
import 'month_template_sheet.dart';
import '../../core/widgets/disclosure.dart';

class MonthScreen extends ConsumerWidget {
  const MonthScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cashMonth = ref.watch(selectedMonthProvider);
    final mesAsync = ref.watch(cashMonthProvider);
    final entries = ref.watch(cashEntriesProvider);
    final debts = ref.watch(debtsProvider);

    final lista = entries.valueOrNull;
    final vazio = lista != null && (lista.isEmpty || lista.every((e) => e.derived));
    final lido = [mesAsync, entries, debts].every((a) => a.hasValue && !a.hasError);
    final mostraLancar = lido && !vazio;

    Widget carregando() => FiSkeleton.page(
      sections: const [2, 4],
      label: 'Carregando seu mês',
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mês'),
        actions: [
          IconButton(
            tooltip: 'O que mudou',
            icon: const Icon(Icons.notifications_none_outlined),
            onPressed: () => GoRouter.of(context).go('/mes/feed'),
          ),
          IconButton(
            tooltip: 'Trocar de mês',
            icon: const Icon(Icons.calendar_month_outlined),
            onPressed: () => _pickMonth(context, ref, entries.valueOrNull),
          ),
        ],
      ),
      floatingActionButton: mostraLancar
          ? FloatingActionButton.extended(
              onPressed: () => openCashEntrySheet(context, ref),
              icon: const Icon(Icons.add),
              label: const Text('Lançar'),
            )
          : null,
      body: mesAsync.when(
        loading: carregando,
        error: (e, _) => FiErrorState(
          error: e,
          action: 'carregar seu mês',
          onRetry: () => ref.invalidate(cashMonthProvider),
        ),
        data: (m) => entries.when(
          loading: carregando,
          error: (e, _) => FiErrorState(
            error: e,
            action: 'carregar seus lançamentos',
            onRetry: () => ref.invalidate(cashEntriesProvider),
          ),
          data: (lista) => debts.when(
            loading: carregando,
            error: (e, _) => FiErrorState(
              error: e,
              action: 'carregar suas dívidas',
              onRetry: () => ref.invalidate(debtsProvider),
            ),
            data: (dividas) => _Body(
              cashMonth: m,
              entries: lista,
              debts: dividas,
              monthOffset: cashMonth.compareTo(currentMonth()),
              onPickMonth: () => _pickMonth(context, ref, lista),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _pickMonth(
    BuildContext context,
    WidgetRef ref,
    List<CashEntry>? entries,
  ) async {
    final current = ref.read(selectedMonthProvider);
    final meses = <String>{currentMonth(), nextMonth(currentMonth()), current};
    for (final e in entries ?? const <CashEntry>[]) {
      meses.add(e.accrualOn.substring(0, 7));
    }
    final ordenados = meses.toList()..sort((a, b) => b.compareTo(a));

    final escolhido = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(
            FiSpace.s5,
            0,
            FiSpace.s5,
            FiSpace.s6,
          ),
          children: [
            Text(
              'QUAL MÊS',
              style: FiType.eyebrow.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s2),
            FiRows(
              children: [
                for (final m in ordenados)
                  FiDataRow(
                    label: monthTitle(m),
                    value: m == current ? 'em leitura' : null,
                    valueColor: m == current ? fiInk3(context) : null,
                    onTap: () => Navigator.of(context).pop(m),
                  ),
              ],
            ),
          ],
        ),
      ),
    );

    if (escolhido != null) {
      ref.read(selectedMonthProvider.notifier).state = escolhido;
    }
  }
}

class _Body extends ConsumerWidget {
  const _Body({
    required this.cashMonth,
    required this.entries,
    required this.debts,
    required this.monthOffset,
    required this.onPickMonth,
  });

  final CashMonth cashMonth;
  final List<CashEntry> entries;
  final List<Debt> debts;
  final int monthOffset;
  final VoidCallback onPickMonth;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final semLancamento = entries.isNotEmpty && entries.every((e) => e.derived);
    if (entries.isEmpty || semLancamento) {
      return _EmptyMonth(
        onAddEntry: () => openCashEntrySheet(context, ref, initialKind: CashKind.income),
      );
    }

    final caras = debts.where((d) => d.debtClass == DebtClass.expensive).toList();
    final v = monthVerdict(
      received: cashMonth.received,
      committed: cashMonth.committed,
      expensiveDebt: caras.isEmpty ? null : caras.first,
    );

    final doMes = entries
        .where((e) => e.accrualOn.startsWith(cashMonth.month))
        .toList()
      ..sort((a, b) => a.accrualOn.compareTo(b.accrualOn));

    return RefreshIndicator(
      onRefresh: () async => invalidateCashReaders(ref.invalidate),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          88,
        ),
        children: [
          _MonthHeader(month: cashMonth.month, onPickMonth: onPickMonth),
          const SizedBox(height: FiSpace.s3),
          _Verdict(verdict: v, cashMonth: cashMonth, monthOffset: monthOffset),

          if (caras.isNotEmpty)
            FiSection(
              title: 'Exige atenção',
              count: caras.length,
              action: FiNavAction(
                label: 'Ver dívidas',
                onPressed: () => GoRouter.of(context).go('/mes/dividas'),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [for (final d in caras) _DebtRow(debt: d)],
              ),
            ),

          if (cashMonth.due.isNotEmpty)
            FiSection(
              title: 'A vencer',
              count: cashMonth.due.length,
              child: FiRows(
                children: [
                  for (final bill in cashMonth.due)
                    _DueRow(key: ValueKey(bill.id ?? bill.description), bill: bill),
                ],
              ),
            ),

          FiSection(
            title: 'O mês',
            action: doMes.isEmpty
                ? FiButton.secondary(
                    icon: Icons.content_copy_outlined,
                    label:
                        'Repetir ${monthName(previousMonth(cashMonth.month)).split(' de ').first}',
                    onPressed: () => openMonthTemplateSheet(context, ref),
                  )
                : null,
            child: doMes.isEmpty
                ? FiEmptyLine(
                    'Nada lançado em ${monthName(cashMonth.month)}. Repetir o mês anterior traz o '
                    'que se repete por natureza, e deixa o gasto variável desmarcado.',
                  )
                : Column(
                    children: [for (final e in doMes) _MonthRow(entry: e)],
                  ),
          ),

          _ToSurplus(cashMonth: cashMonth),
        ],
      ),
    );
  }
}

class _MonthHeader extends StatelessWidget {
  const _MonthHeader({required this.month, required this.onPickMonth});

  final String month;
  final VoidCallback onPickMonth;

  @override
  Widget build(BuildContext context) {
    final marca = Theme.of(context).colorScheme.primary;
    final nome = monthTitle(month);

    return Align(
      alignment: Alignment.centerLeft,
      child: Semantics(
        button: true,
        label: 'Trocar de mês. Em leitura: $nome',
        excludeSemantics: true,
        child: TextButton(
          onPressed: onPickMonth,
          style: TextButton.styleFrom(
            padding: EdgeInsets.zero,
            minimumSize: const Size(0, FiLayout.minTouchTarget),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Flexible(
                child: Text(
                  nome,
                  style: FiType.title.copyWith(color: fiInk1(context)),
                ),
              ),
              const SizedBox(width: FiSpace.s1),
              Icon(Icons.expand_more, size: 20, color: marca),
            ],
          ),
        ),
      ),
    );
  }
}

class _Verdict extends StatelessWidget {
  const _Verdict({
    required this.verdict,
    required this.cashMonth,
    required this.monthOffset,
  });

  final MonthVerdict verdict;
  final CashMonth cashMonth;
  final int monthOffset;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          verdict.verdict,
          style: fiSerif(FiType.verdict).copyWith(
            color: fiStateColor(verdict.band.state, brightness),
          ),
        ),
        const SizedBox(height: FiSpace.s2),
        Text(
          verdict.reason,
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),

        const FiProvenance(
          summary: 'Como lemos seu mês',
          method:
              'Compara o que já está comprometido com o que entrou, na régua de pressão do mês.',
          source: 'Seus lançamentos de caixa, mais os proventos da sua carteira.',
          limitation:
              'A leitura é do mês escolhido. Dívida sem taxa informada não entra na classe de '
              'dívida cara.',
        ),

        const SizedBox(height: FiSpace.s4),
        FiHeadline(
          eyebrow: monthOffset == 0
              ? 'Livre agora'
              : monthOffset < 0
              ? 'Sobrou em ${monthName(cashMonth.month)}'
              : 'Livre em ${monthName(cashMonth.month)}, pelo que está lançado',
          figure: formatCurrency(cashMonth.freeNow),
        ),

        const SizedBox(height: FiSpace.s5),
        FiFigures(
          rule: false,
          figures: {
            'ENTROU': formatCurrency(cashMonth.received),
            'SAIU': formatCurrency(cashMonth.paid),
            'COMPROMETIDO': formatCurrency(cashMonth.committed),
          },
        ),

      ],
    );
  }
}

class _ToSurplus extends StatelessWidget {
  const _ToSurplus({required this.cashMonth});

  final CashMonth cashMonth;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: FiSpace.s8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Divider(
            color: Theme.of(context).dividerColor,
            height: 1,
            thickness: 1,
          ),
          const SizedBox(height: FiSpace.s4),
          Text(
            cashMonth.hasRange
                ? (cashMonth.surplusLow == cashMonth.surplusHigh
                      ? 'Descontando o que ainda deve sair, a sobra estimada é '
                            '${formatCurrency(cashMonth.surplusLow)}.'
                      : 'Descontando o que ainda deve sair, a sobra deve ficar entre '
                            '${formatCurrency(cashMonth.surplusLow)} e '
                            '${formatCurrency(cashMonth.surplusHigh)}.')
                : 'Sem mês fechado ainda não há como estimar o que falta sair, então a sobra '
                      'é o próprio livre.',
            style: FiType.body.copyWith(color: fiInk2(context)),
          ),
          const SizedBox(height: FiSpace.s2),
          FiNavAction(
            label: 'Ver a sobra',
            onPressed: () => GoRouter.of(context).go('/sobra'),
          ),
        ],
      ),
    );
  }
}

class _DebtRow extends StatelessWidget {
  const _DebtRow({required this.debt});

  final Debt debt;

  @override
  Widget build(BuildContext context) {
    final taxa = debt.monthlyRate;
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${debt.description}: ${formatCurrency(debt.balance)}'
            '${taxa == null ? '' : ' a ${formatPercent(taxa)} ao mês'}',
            style: FiType.body.copyWith(color: fiInk1(context)),
          ),
          if (debt.flipRate != null)
            Text(
              'Deixa de ser cara com taxa de até ${formatPercent(debt.flipRate)} ao mês.',
              style: FiType.caption.copyWith(color: fiInk3(context)),
            ),
        ],
      ),
    );
  }
}

class _DueRow extends ConsumerStatefulWidget {
  const _DueRow({super.key, required this.bill});

  final CashDueEntry bill;

  @override
  ConsumerState<_DueRow> createState() => _DueRowState();
}

class _DueRowState extends ConsumerState<_DueRow> {
  bool _busy = false;

  Future<void> _markPaid() async {
    final id = widget.bill.id!;
    final api = ref.read(apiRepositoryProvider);
    final container = ProviderScope.containerOf(context, listen: false);
    final original = ref
        .read(cashEntriesProvider)
        .valueOrNull
        ?.where((e) => e.id == id && !e.derived)
        .firstOrNull;

    setState(() => _busy = true);
    final pagou = await fiAttempt(
      context,
      () => api.markCashEntryPaid(id),
      action: 'marcar esta conta como paga',
      success: 'Conta marcada como paga',
      undo: original == null
          ? null
          : () async {
              await api.updateCashEntry(
                id: original.id,
                kind: original.kind,
                category: original.category,
                description: original.description,
                amount: original.amount,
                dueOn: original.dueOn,
                paidOn: null,
              );
              invalidateCashReaders(container.invalidate);
            },
    );
    if (pagou) invalidateCashReaders(container.invalidate);
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final bill = widget.bill;
    return FiDataRow(
      leading: _Day(day: dayOf(bill.dueOn)),
      label: bill.description,
      detail: formatCurrency(bill.amount),
      trailing: FiButton.quiet(
        label: 'Marcar paga',
        busy: _busy,
        onPressed: bill.id == null || _busy ? null : _markPaid,
      ),
    );
  }
}

class _Day extends StatelessWidget {
  const _Day({required this.day});

  final String day;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(minWidth: 24),
      child: Text(
        day,
        softWrap: false,
        style: FiType.figure.copyWith(color: fiInk3(context)),
      ),
    );
  }
}

class _MonthRow extends ConsumerWidget {
  const _MonthRow({required this.entry});

  final CashEntry entry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final entrada = entry.kind == CashKind.income;
    final cor = fiDirectionColor(entrada ? 1 : -1, Theme.of(context).brightness);

    return FiDisclosure(
      leading: _Day(day: dayOf(entry.accrualOn)),
      title: entry.description,
      detail: entry.isFuture || entry.derived
          ? (entry.derived ? 'provento da carteira' : (entrada ? 'a receber' : 'a vencer'))
          : null,
      value: '${entrada ? '+' : '−'}${formatCurrency(entry.amount)}',
      valueColor: cor,
      child: Row(
          children: [
            Expanded(
              child: Text(
                cashCategoryLabel(entry.kind, entry.category),
                style: FiType.caption.copyWith(color: fiInk2(context)),
              ),
            ),
            if (entry.derived)
              Text(
                'vem da sua carteira',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              )
            else
              FiButton.quiet(
                label: 'Editar lançamento',
                onPressed: () => openCashEntrySheet(context, ref, editing: entry),
              ),
          ],
        ),
    );
  }
}

class _EmptyMonth extends StatelessWidget {
  const _EmptyMonth({required this.onAddEntry});

  final VoidCallback onAddEntry;

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        FiEmptyState(
          title: 'Seu mês ainda não tem nada lançado',
          body: 'Comece pelo que se repete: o dia e o valor que você recebe, e os dois ou três '
              'maiores gastos fixos. Com isso a sobra do mês já sai, e ela é o que decide o '
              'próximo aporte.',
          action: FiButton.primary(
            label: 'Lançar o que você recebe',
            icon: Icons.add,
            onPressed: onAddEntry,
          ),
          secondary: FiButton.secondary(
            label: 'Cadastrar uma dívida',
            onPressed: () => GoRouter.of(context).go('/mes/dividas'),
          ),
        ),
      ],
    );
  }
}
