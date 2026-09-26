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
import '../../core/widgets/nav_action.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import 'cash_entry_sheet.dart';
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

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mês'),
        actions: [
          IconButton(
            tooltip: 'Trocar de mês',
            icon: const Icon(Icons.calendar_month_outlined),
            onPressed: () => _pickMonth(context, ref, entries.valueOrNull),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => openCashEntrySheet(context, ref),
        icon: const Icon(Icons.add),
        label: const Text('Lançar'),
      ),
      body: mesAsync.when(
        loading: () => FiSkeleton.screen(
          shape: FiSkeletonShape.metric,
          count: 1,
          label: 'Carregando seu mês',
        ),
        error: (e, _) => FiErrorState(
          error: e,
          action: 'carregar seu mês',
          onRetry: () => ref.invalidate(cashMonthProvider),
        ),
        data: (m) => _Body(
          cashMonth: m,
          entries: entries.valueOrNull ?? const [],
          debts: debts.valueOrNull ?? const [],
          isCurrentMonth: cashMonth == currentMonth(),
        ),
      ),
    );
  }

  Future<void> _pickMonth(
    BuildContext context,
    WidgetRef ref,
    List<CashEntry>? entries,
  ) async {
    final meses = <String>{currentMonth()};
    for (final e in entries ?? const <CashEntry>[]) {
      meses.add(e.accrualOn.substring(0, 7));
    }
    final ordenados = meses.toList()..sort((a, b) => b.compareTo(a));
    final current = ref.read(selectedMonthProvider);

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
                    label: monthName(m),
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
    required this.isCurrentMonth,
  });

  final CashMonth cashMonth;
  final List<CashEntry> entries;
  final List<Debt> debts;
  final bool isCurrentMonth;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final semLancamento = entries.isNotEmpty && entries.every((e) => e.derived);
    if (entries.isEmpty || semLancamento) {
      return _EmptyMonth(onAddEntry: () => openCashEntrySheet(context, ref));
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
      onRefresh: () async {
        ref.invalidate(cashMonthProvider);
        ref.invalidate(cashEntriesProvider);
        ref.invalidate(debtsProvider);
      },
      child: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          88,
        ),
        children: [
          _Verdict(verdict: v, cashMonth: cashMonth, isCurrentMonth: isCurrentMonth),

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
                  for (final bill in cashMonth.due) _DueRow(bill: bill),
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

class _Verdict extends StatelessWidget {
  const _Verdict({
    required this.verdict,
    required this.cashMonth,
    required this.isCurrentMonth,
  });

  final MonthVerdict verdict;
  final CashMonth cashMonth;
  final bool isCurrentMonth;

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
          source: 'Seus lançamentos de caixa, mais os proventos derivados do seu razão.',
          limitation:
              'A leitura é do mês escolhido. Dívida sem taxa informada não entra na classe de '
              'dívida caseira.',
        ),

        const SizedBox(height: FiSpace.s4),
        FiHeadline(
          eyebrow: isCurrentMonth
              ? 'Livre agora'
              : 'Sobrou em ${monthName(cashMonth.month)}',
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
                ? 'Descontando o que ainda deve sair, a sobra parte de '
                      '${formatCurrency(cashMonth.surplusLow)}.'
                : 'Sem mês fechado ainda não há como estimar o que falta sair, então a sobra '
                      'é o próprio livre.',
            style: FiType.body.copyWith(color: fiInk2(context)),
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
              'Vira administrável a ${formatPercent(debt.flipRate)} ao mês.',
              style: FiType.caption.copyWith(color: fiInk3(context)),
            ),
        ],
      ),
    );
  }
}

class _DueRow extends ConsumerWidget {
  const _DueRow({required this.bill});

  final CashDueEntry bill;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FiDataRow(
      leading: _Day(day: dayOf(bill.dueOn)),
      label: bill.description,
      detail: formatCurrency(bill.amount),
      trailing: FiButton.quiet(
        label: 'Marcar paga',
        onPressed: bill.id == null
            ? null
            : () async {
                await ref
                    .read(apiRepositoryProvider)
                    .markCashEntryPaid(bill.id!);
                ref.invalidate(cashMonthProvider);
                ref.invalidate(cashEntriesProvider);
              },
      ),
    );
  }
}

class _Day extends StatelessWidget {
  const _Day({required this.day});

  final String day;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 24,
      child: Text(
        day,
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
          ? (entry.derived ? 'do seu razão' : (entrada ? 'a receber' : 'a vencer'))
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
                'vem do razão',
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
            label: 'Lançar o primeiro mês',
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
