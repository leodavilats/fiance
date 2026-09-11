import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/cash_models.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/search_action.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/format.dart';
import '../../core/mes.dart';
import '../../core/month_verdict.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/labels.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/nav_action.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import 'lancar_sheet.dart';
import 'molde_sheet.dart';

class MesScreen extends ConsumerWidget {
  const MesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mes = ref.watch(mesEscolhidoProvider);
    final mesAsync = ref.watch(cashMonthProvider);
    final entradas = ref.watch(cashEntriesProvider);
    final dividas = ref.watch(debtsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mês'),
        actions: [
          const FiSearchAction(),
          IconButton(
            tooltip: 'Trocar de mês',
            icon: const Icon(Icons.calendar_month_outlined),
            onPressed: () => _escolherMes(context, ref, entradas.valueOrNull),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => abrirLancarSheet(context, ref),
        icon: const Icon(Icons.add),
        label: const Text('Lançar'),
      ),
      body: mesAsync.when(
        loading: () => FiSkeleton.tela(
          shape: FiSkeletonShape.metric,
          count: 1,
          label: 'Carregando seu mês',
        ),
        error: (e, _) => FiErrorState(
          error: e,
          action: 'carregar seu mês',
          onRetry: () => ref.invalidate(cashMonthProvider),
        ),
        data: (m) => _Corpo(
          mes: m,
          entradas: entradas.valueOrNull ?? const [],
          dividas: dividas.valueOrNull ?? const [],
          ehMesCorrente: mes == mesCorrente(),
        ),
      ),
    );
  }

  Future<void> _escolherMes(
    BuildContext context,
    WidgetRef ref,
    List<CashEntry>? entradas,
  ) async {
    final meses = <String>{mesCorrente()};
    for (final e in entradas ?? const <CashEntry>[]) {
      meses.add(e.competencia.substring(0, 7));
    }
    final ordenados = meses.toList()..sort((a, b) => b.compareTo(a));
    final atual = ref.read(mesEscolhidoProvider);

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
                    label: nomeDoMes(m),
                    value: m == atual ? 'em leitura' : null,
                    valueColor: m == atual ? fiInk3(context) : null,
                    onTap: () => Navigator.of(context).pop(m),
                  ),
              ],
            ),
          ],
        ),
      ),
    );

    if (escolhido != null) {
      ref.read(mesEscolhidoProvider.notifier).state = escolhido;
    }
  }
}

class _Corpo extends ConsumerWidget {
  const _Corpo({
    required this.mes,
    required this.entradas,
    required this.dividas,
    required this.ehMesCorrente,
  });

  final CashMonth mes;
  final List<CashEntry> entradas;
  final List<Debt> dividas;
  final bool ehMesCorrente;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final semLancamento = entradas.isNotEmpty && entradas.every((e) => e.derived);
    if (entradas.isEmpty || semLancamento) {
      return _MesVazio(onLancar: () => abrirLancarSheet(context, ref));
    }

    final caras = dividas.where((d) => d.debtClass == DebtClass.expensive).toList();
    final v = vereditoDoMes(
      recebido: mes.received,
      comprometido: mes.committed,
      dividaCara: caras.isEmpty ? null : caras.first,
    );

    final doMes = entradas
        .where((e) => e.competencia.startsWith(mes.month))
        .toList()
      ..sort((a, b) => a.competencia.compareTo(b.competencia));

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
          _Veredito(veredito: v, mes: mes, ehMesCorrente: ehMesCorrente),

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
                children: [for (final d in caras) _LinhaDivida(divida: d)],
              ),
            ),

          if (mes.due.isNotEmpty)
            FiSection(
              title: 'A vencer',
              count: mes.due.length,
              child: FiRows(
                children: [
                  for (final conta in mes.due) _LinhaAVencer(conta: conta),
                ],
              ),
            ),

          FiSection(
            title: 'O mês',
            action: doMes.isEmpty
                ? FiButton.secondary(
                    icon: Icons.content_copy_outlined,
                    label:
                        'Repetir ${nomeDoMes(mesAnterior(mes.month)).split(' de ').first}',
                    onPressed: () => abrirMoldeSheet(context, ref),
                  )
                : null,
            child: doMes.isEmpty
                ? FiEmptyLine(
                    'Nada lançado em ${nomeDoMes(mes.month)}. Repetir o mês anterior traz o '
                    'que se repete por natureza, e deixa o gasto variável desmarcado.',
                  )
                : Column(
                    children: [for (final e in doMes) _LinhaDoMes(entry: e)],
                  ),
          ),
        ],
      ),
    );
  }
}

class _Veredito extends StatelessWidget {
  const _Veredito({
    required this.veredito,
    required this.mes,
    required this.ehMesCorrente,
  });

  final VereditoDoMes veredito;
  final CashMonth mes;
  final bool ehMesCorrente;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          veredito.veredito,
          style: fiSerif(FiType.verdict).copyWith(
            color: fiStateColor(veredito.band.state, brightness),
          ),
        ),
        const SizedBox(height: FiSpace.s2),
        Text(
          veredito.razao,
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
          eyebrow: ehMesCorrente
              ? 'Livre agora'
              : 'Sobrou em ${nomeDoMes(mes.month)}',
          figure: formatCurrency(mes.freeNow),
        ),

        const SizedBox(height: FiSpace.s5),
        FiFigures(
          rule: false,
          figures: {
            'ENTROU': formatCurrency(mes.received),
            'SAIU': formatCurrency(mes.paid),
            'COMPROMETIDO': formatCurrency(mes.committed),
          },
        ),

        const SizedBox(height: FiSpace.s6),
        Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
        const SizedBox(height: FiSpace.s4),

        Text(
          mes.hasRange
              ? 'Descontando o que ainda deve sair, a sobra parte de '
                    '${formatCurrency(mes.surplusLow)}.'
              : 'Sem mês fechado ainda não há como estimar o que falta sair, então a sobra é o '
                    'próprio livre.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s3),
        Align(
          alignment: Alignment.centerLeft,
          child: FiButton.secondary(
            label: 'Decidir o que fazer com ela',
            onPressed: () => GoRouter.of(context).go('/sobra'),
          ),
        ),
      ],
    );
  }
}

class _LinhaDivida extends StatelessWidget {
  const _LinhaDivida({required this.divida});

  final Debt divida;

  @override
  Widget build(BuildContext context) {
    final taxa = divida.monthlyRate;
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${divida.description}: ${formatCurrency(divida.balance)}'
            '${taxa == null ? '' : ' a ${formatPercent(taxa)} ao mês'}',
            style: FiType.body.copyWith(color: fiInk1(context)),
          ),
          if (divida.flipRate != null)
            Text(
              'Vira administrável a ${formatPercent(divida.flipRate)} ao mês.',
              style: FiType.caption.copyWith(color: fiInk3(context)),
            ),
        ],
      ),
    );
  }
}

class _LinhaAVencer extends ConsumerWidget {
  const _LinhaAVencer({required this.conta});

  final CashDueEntry conta;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FiDataRow(
      leading: _Dia(dia: diaDe(conta.dueOn)),
      label: conta.description,
      detail: formatCurrency(conta.amount),
      trailing: FiButton.quiet(
        label: 'Marcar paga',
        onPressed: conta.id == null
            ? null
            : () async {
                await ref
                    .read(apiRepositoryProvider)
                    .markCashEntryPaid(conta.id!);
                ref.invalidate(cashMonthProvider);
                ref.invalidate(cashEntriesProvider);
              },
      ),
    );
  }
}

class _Dia extends StatelessWidget {
  const _Dia({required this.dia});

  final String dia;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 24,
      child: Text(
        dia,
        style: FiType.figure.copyWith(color: fiInk3(context)),
      ),
    );
  }
}

class _LinhaDoMes extends ConsumerWidget {
  const _LinhaDoMes({required this.entry});

  final CashEntry entry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final entrada = entry.kind == CashKind.income;
    final cor = fiDirectionColor(entrada ? 1 : -1, Theme.of(context).brightness);

    return ExpansionTile(
      childrenPadding: const EdgeInsets.only(bottom: FiSpace.s3),
      leading: _Dia(dia: diaDe(entry.competencia)),
      title: Text(
        entry.description,
        style: FiType.body.copyWith(color: fiInk1(context)),
      ),
      subtitle: entry.futura || entry.derived
          ? Text(
              entry.derived
                  ? 'do seu razão'
                  : (entrada ? 'a receber' : 'a vencer'),
              style: FiType.caption.copyWith(color: fiInk3(context)),
            )
          : null,
      trailing: Text(
        '${entrada ? '+' : '−'}${formatCurrency(entry.amount)}',
        style: FiType.figure.copyWith(color: cor),
      ),
      children: [
        Row(
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
                onPressed: () => abrirLancarSheet(context, ref, editar: entry),
              ),
          ],
        ),
      ],
    );
  }
}

class _MesVazio extends StatelessWidget {
  const _MesVazio({required this.onLancar});

  final VoidCallback onLancar;

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
            onPressed: onLancar,
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
