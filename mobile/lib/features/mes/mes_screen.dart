import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/cash_models.dart';
import '../../core/format.dart';
import '../../core/mes.dart';
import '../../core/month_verdict.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/labels.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import 'lancar_sheet.dart';
import 'molde_sheet.dart';

/// O Mes: "o que aconteceu com meu dinheiro?"
///
/// Mesma hierarquia do web -- veredito, evidencia, atencao, a vencer, o mes -- em forma nativa.
/// O que muda de proposito: a linha do tempo e **lista com disclosure**, nao tabela, porque uma
/// tabela de cinco colunas em 360dp e um scroll horizontal que esconde a coluna que decide.
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
        loading: () => const Center(child: CircularProgressIndicator()),
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

  /// Os meses que a pessoa tem, mais o corrente. Nada de faixa inventada.
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
          children: [
            for (final m in ordenados)
              ListTile(
                title: Text(nomeDoMes(m)),
                trailing: m == atual ? const Icon(Icons.check) : null,
                onTap: () => Navigator.of(context).pop(m),
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
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 88),
        children: [
          _Veredito(veredito: v, mes: mes, ehMesCorrente: ehMesCorrente),

          if (caras.isNotEmpty)
            FiSection(
              title: 'Exige atenção',
              count: caras.length,
              trailing: TextButton(
                onPressed: () => GoRouter.of(context).go('/mes/dividas'),
                child: const Text('Ver dívidas'),
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
              child: Column(
                children: [
                  for (final conta in mes.due) _LinhaAVencer(conta: conta),
                ],
              ),
            ),

          FiSection(
            title: 'O mês',
            trailing: TextButton(
              onPressed: () => abrirMoldeSheet(context, ref),
              child: Text('Repetir ${nomeDoMes(mesAnterior(mes.month)).split(' de ').first}'),
            ),
            child: Column(
              children: [
                if (doMes.isEmpty)
                  Text(
                    'Nada lançado em ${nomeDoMes(mes.month)}.',
                    style: FiType.body.copyWith(color: fiInk2(context)),
                  ),
                for (final e in doMes) _LinhaDoMes(entry: e),
              ],
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
        // A resposta da tela vem antes da cifra que a sustenta.
        Text(
          veredito.veredito,
          style: FiType.verdict.copyWith(
            fontFamily: fiFontSerif,
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
        Text(
          ehMesCorrente ? 'LIVRE AGORA' : 'SOBROU EM ${nomeDoMes(mes.month).toUpperCase()}',
          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
        ),
        const SizedBox(height: FiSpace.s1),
        Text(formatCurrency(mes.freeNow), style: FiType.moneyLg),

        const SizedBox(height: FiSpace.s5),
        FiFigures(
          figures: {
            'ENTROU': formatCurrency(mes.received),
            'SAIU': formatCurrency(mes.paid),
            'COMPROMETIDO': formatCurrency(mes.committed),
          },
        ),

        const SizedBox(height: FiSpace.s5),
        Divider(color: Theme.of(context).dividerColor, height: 1),
        const SizedBox(height: FiSpace.s4),

        // Fato e projecao sao numeros diferentes, e a diferenca entre eles *e* a estimativa.
        Text(
          mes.hasRange
              ? 'Descontando o que ainda deve sair, a sobra parte de '
                    '${formatCurrency(mes.surplusLow)}.'
              : 'Sem mês fechado ainda não há como estimar o que falta sair, então a sobra é o '
                    'próprio livre.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s2),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton(
            onPressed: () => GoRouter.of(context).go('/sobra'),
            child: const Text('Decidir o que fazer com ela'),
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
            style: FiType.body,
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
    return ListTile(
      contentPadding: EdgeInsets.zero,
      dense: true,
      leading: SizedBox(
        width: 28,
        child: Text(diaDe(conta.dueOn), style: FiType.metricSm),
      ),
      title: Text(conta.description, style: FiType.body),
      subtitle: Text(formatCurrency(conta.amount), style: FiType.caption),
      trailing: TextButton(
        onPressed: conta.id == null
            ? null
            : () async {
                await ref
                    .read(apiRepositoryProvider)
                    .markCashEntryPaid(conta.id!);
                ref.invalidate(cashMonthProvider);
                ref.invalidate(cashEntriesProvider);
              },
        child: const Text('Paga'),
      ),
    );
  }
}

/// Linha da linha do tempo, com disclosure em vez de coluna.
class _LinhaDoMes extends ConsumerWidget {
  const _LinhaDoMes({required this.entry});

  final CashEntry entry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final entrada = entry.kind == CashKind.income;
    final cor = fiDirectionColor(entrada ? 1 : -1, Theme.of(context).brightness);

    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      childrenPadding: const EdgeInsets.only(bottom: FiSpace.s3),
      shape: const Border(),
      collapsedShape: const Border(),
      leading: SizedBox(
        width: 28,
        child: Text(diaDe(entry.competencia), style: FiType.metricSm),
      ),
      title: Text(entry.description, style: FiType.body),
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
        style: FiType.metricSm.copyWith(color: cor),
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
              TextButton(
                onPressed: () => abrirLancarSheet(context, ref, editar: entry),
                child: const Text('Editar'),
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
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Seu mês ainda não tem nada lançado',
          style: FiType.verdict.copyWith(fontFamily: fiFontSerif),
        ),
        const SizedBox(height: FiSpace.s3),
        Text(
          'Comece pelo que se repete: o dia e o valor que você recebe, e os dois ou três '
          'maiores gastos fixos. Com isso a sobra do mês já sai, e ela é o que decide o '
          'próximo aporte.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s5),
        FilledButton.icon(
          onPressed: onLancar,
          icon: const Icon(Icons.add),
          label: const Text('Lançar o primeiro mês'),
        ),
        const SizedBox(height: FiSpace.s3),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton(
            onPressed: () => GoRouter.of(context).go('/mes/dividas'),
            child: const Text('Cadastrar uma dívida'),
          ),
        ),
      ],
    );
  }
}
