import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/inbox_models.dart';
import '../../core/labels.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/chip.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import 'feed_actions.dart';

const fiInboxFilters = <String, ({String label, List<String>? kinds})>{
  'todos': (label: 'Todos', kinds: null),
  'carteira': (
    label: 'Carteira',
    kinds: ['patrimony', 'verdict_change', 'allocation', 'tax'],
  ),
  'precos': (label: 'Preços', kinds: ['price_alert']),
  'renda-fixa': (label: 'Renda fixa', kinds: ['maturity']),
  'oportunidades': (label: 'Oportunidades', kinds: ['new_opportunity', 'digest']),
};

final inboxProvider = FutureProvider.autoDispose.family<InboxPage, String>((ref, filtro) {
  return ref
      .watch(apiRepositoryProvider)
      .getInbox(kinds: fiInboxFilters[filtro]?.kinds);
});

IconData fiInboxIcon(String kind) => switch (kind) {
  'price_alert' => Icons.notifications_active_outlined,
  'maturity' => Icons.event_outlined,
  'allocation' => Icons.pie_chart_outline,
  'verdict_change' => Icons.sell_outlined,
  'patrimony' => Icons.show_chart,
  'tax' => Icons.receipt_long_outlined,
  'new_opportunity' || 'digest' => Icons.explore_outlined,
  _ => Icons.info_outline,
};

String fiInboxGroup(DateTime quando, DateTime agora) {
  final hoje = DateTime(agora.year, agora.month, agora.day);
  final dias = hoje.difference(DateTime(quando.year, quando.month, quando.day)).inDays;
  if (dias <= 0) return 'Hoje';
  if (dias == 1) return 'Ontem';
  if (dias < 7) return 'Nos últimos 7 dias';
  return 'Antes';
}

class InboxScreen extends ConsumerStatefulWidget {
  const InboxScreen({super.key});

  @override
  ConsumerState<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends ConsumerState<InboxScreen> {
  String _filtro = 'todos';
  final List<InboxItem> _mais = [];
  final Set<int> _lidos = {};
  String? _cursor;
  bool _temMais = false;
  bool _carregandoMais = false;
  Object? _erroAoCarregarMais;
  bool _marcando = false;

  void _trocarFiltro(String filtro) {
    if (filtro == _filtro) return;
    setState(() {
      _filtro = filtro;
      _limparPaginas();
    });
  }

  void _limparPaginas() {
    _mais.clear();
    _cursor = null;
    _temMais = false;
    _erroAoCarregarMais = null;
  }

  Future<void> _recarregar() async {
    setState(_limparPaginas);
    ref.invalidate(inboxProvider(_filtro));
    ref.invalidate(inboxUnreadProvider);
    await ref.read(inboxProvider(_filtro).future);
  }

  Future<void> _carregarMais(String cursor) async {
    setState(() {
      _carregandoMais = true;
      _erroAoCarregarMais = null;
    });
    try {
      final pagina = await ref
          .read(apiRepositoryProvider)
          .getInbox(cursor: cursor, kinds: fiInboxFilters[_filtro]?.kinds);
      if (!mounted) return;
      setState(() {
        _mais.addAll(pagina.items);
        _cursor = pagina.nextCursor;
        _temMais = pagina.hasMore;
        _carregandoMais = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _erroAoCarregarMais = e;
        _carregandoMais = false;
      });
    }
  }

  Future<void> _marcarTodos() async {
    setState(() => _marcando = true);
    final ok = await fiAttempt(
      context,
      () => ref.read(apiRepositoryProvider).markInboxRead(),
      action: 'marcar os avisos como lidos',
    );
    if (!mounted) return;
    setState(() => _marcando = false);
    if (!ok) return;
    ref.invalidate(inboxUnreadProvider);
    await _recarregar();
  }

  void _abrir(InboxItem item) {
    if (item.unread) {
      setState(() => _lidos.add(item.id));
      ref
          .read(apiRepositoryProvider)
          .markInboxRead(ids: [item.id])
          .then((_) => ref.invalidate(inboxUnreadProvider), onError: (_) {});
    }
    runFeedAction(context, item.action, item.ticker);
  }

  @override
  Widget build(BuildContext context) {
    final primeira = ref.watch(inboxProvider(_filtro));
    final naoLidos = primeira.valueOrNull?.unread ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Avisos'),
        actions: [
          if (naoLidos > 0)
            IconButton(
              tooltip: 'Marcar todos como lidos',
              icon: const Icon(Icons.done_all),
              onPressed: _marcando ? null : _marcarTodos,
            ),
          IconButton(
            tooltip: 'Escolher o que chega',
            icon: const Icon(Icons.tune),
            onPressed: () => context.push('/voce/avisos'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _recarregar,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(0, FiSpace.s3, 0, FiLayout.scrollTail),
          children: [
            FiChipBar(
              children: [
                for (final filtro in fiInboxFilters.entries)
                  FiChoiceChip(
                    label: filtro.value.label,
                    selected: filtro.key == _filtro,
                    onSelected: () => _trocarFiltro(filtro.key),
                  ),
              ],
            ),
            const SizedBox(height: FiSpace.s3),
            for (final bloco in primeira.when(
              loading: () => [
                const FiSkeleton(shape: FiSkeletonShape.row, count: 6),
              ],
              error: (err, _) => [
                FiErrorState(
                  error: err,
                  action: 'carregar os avisos',
                  onRetry: () => ref.invalidate(inboxProvider(_filtro)),
                ),
              ],
              data: (pagina) => _conteudo(context, pagina),
            ))
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: FiLayout.gutter),
                child: bloco,
              ),
          ],
        ),
      ),
    );
  }

  List<Widget> _conteudo(BuildContext context, InboxPage pagina) {
    final itens = [...pagina.items, ..._mais]
        .map((i) => _lidos.contains(i.id) ? i.markedRead() : i)
        .toList();
    final cursor = _mais.isEmpty ? pagina.nextCursor : _cursor;
    final temMais = _mais.isEmpty ? pagina.hasMore : _temMais;

    if (itens.isEmpty) {
      return [
        _filtro == 'todos'
            ? const FiEmptyState(
                title: 'Nenhum aviso por aqui',
                body: 'Chega aqui quando um alerta de preço dispara, uma aplicação está perto '
                    'de vencer, a carteira sai da meta ou um ativo entra em destaque.',
              )
            : FiEmptyState(
                title: 'Nenhum aviso de ${fiInboxFilters[_filtro]!.label.toLowerCase()}',
                body: 'Os outros tipos de aviso continuam em Todos.',
              ),
      ];
    }

    final agora = DateTime.now();
    final grupos = <String, List<InboxItem>>{};
    for (final item in itens) {
      grupos.putIfAbsent(fiInboxGroup(item.arrivedAt, agora), () => []).add(item);
    }

    return [
      for (final (i, grupo) in grupos.entries.indexed)
        FiSection(
          first: i == 0,
          title: grupo.key,
          count: grupo.value.length,
          child: FiRows(
            children: [
              for (final item in grupo.value)
                _InboxRow(item: item, agora: agora, onTap: () => _abrir(item)),
            ],
          ),
        ),
      if (temMais && cursor != null) ...[
        const SizedBox(height: FiSpace.s4),
        FiButton.secondary(
          label: _carregandoMais ? 'Carregando…' : 'Ver avisos mais antigos',
          busy: _carregandoMais,
          expand: true,
          onPressed: _carregandoMais ? null : () => _carregarMais(cursor),
        ),
      ],
      if (_erroAoCarregarMais != null) ...[
        const SizedBox(height: FiSpace.s2),
        Text(
          fiErrorMessage(_erroAoCarregarMais!, action: 'carregar os avisos mais antigos'),
          style: FiType.caption.copyWith(
            color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
          ),
        ),
      ],
    ];
  }
}

class _InboxRow extends StatelessWidget {
  const _InboxRow({required this.item, required this.agora, required this.onTap});

  final InboxItem item;
  final DateTime agora;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final marca = Theme.of(context).colorScheme.primary;

    return FiDataRow(
      leading: SizedBox(
        width: 28,
        height: 28,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Icon(
              fiInboxIcon(item.kind),
              size: 24,
              color: fiStateColor(fiSeverityState(item.severity), brightness),
            ),
            if (item.unread)
              Positioned(
                right: -2,
                top: -2,
                child: Container(
                  width: 9,
                  height: 9,
                  decoration: BoxDecoration(color: marca, shape: BoxShape.circle),
                ),
              ),
          ],
        ),
      ),
      label: item.title,
      emphasis: item.unread,
      detail: item.detail,
      note: [
        if (item.unread) 'Novo',
        formatWhen(item.arrivedAt, agora: agora),
        ?item.actionLabel,
      ].join(' · '),
      onTap: onTap,
    );
  }
}
