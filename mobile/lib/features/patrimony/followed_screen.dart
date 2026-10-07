import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/ledger_models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/feedback.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';

String _compras(int n) => n == 1 ? '1 compra' : '$n compras';

String _signed(double? pct) => pct == null ? '—' : '${pct > 0 ? '+' : ''}${formatPercent(pct)}';

class FollowedScreen extends ConsumerWidget {
  const FollowedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final seguidas = ref.watch(followedSuggestionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Sugestões seguidas')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(followedSuggestionsProvider),
        child: seguidas.when(
          loading: () => FiSkeleton.screen(
            shape: FiSkeletonShape.row,
            count: 5,
            label: 'Apurando o resultado das sugestões seguidas',
          ),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos apurar as sugestões seguidas',
            action: 'apurar as sugestões seguidas',
            onRetry: () => ref.invalidate(followedSuggestionsProvider),
          ),
          data: (data) {
            if (data.items.isEmpty) {
              return ListView(
                children: [
                  FiEmptyState(
                    title: 'Nenhuma compra acompanhada',
                    body: data.summary,
                    hint: 'Ao comprar pelo Descobrir, deixe ligado "Acompanhar o resultado": a '
                        'compra entra aqui a partir do razão, sem digitar nada de novo.',
                    action: FiButton.primary(
                      label: 'Ver o Descobrir',
                      onPressed: () => context.go('/descobrir'),
                    ),
                  ),
                ],
              );
            }
            return _Outcome(data: data);
          },
        ),
      ),
    );
  }
}

class _Outcome extends StatelessWidget {
  const _Outcome({required this.data});

  final FollowedSuggestions data;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final ibov = data.ibovPctSamePeriod;
    final apurado = data.totalInvested > 0;

    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s3,
        FiLayout.gutter,
        FiSpace.s8,
      ),
      children: [
        FiHeadline(
          eyebrow: 'Resultado do que você seguiu',
          figure: apurado ? _signed(data.totalPnlPct) : '—',
          size: FiHeadlineSize.xl,
          support: apurado
              ? '${data.totalPnl >= 0 ? '+' : ''}${formatCurrency(data.totalPnl)} sobre '
                    '${formatCurrency(data.totalInvested)} investidos'
              : null,
          supportColor: fiDirectionColor(data.totalPnl, brightness),
          note: ibov == null ? null : 'Ibovespa no mesmo período: ${_signed(ibov)}',
        ),
        if (!apurado) ...[
          const SizedBox(height: FiSpace.s3),
          Text(data.summary, style: FiType.body.copyWith(color: fiInk2(context))),
        ],
        const SizedBox(height: FiSpace.s2),
        const FiProvenance(
          summary: 'Como o resultado é apurado',
          method: 'Cada compra vale pela quantidade e pelo preço lançados no razão, e o valor '
              'de hoje pela cotação atual. O Ibovespa é medido do dia da compra mais antiga até '
              'hoje.',
          source: 'Seus lançamentos; cotação e Ibovespa da BRAPI.',
          limitation: 'Não entram proventos nem custos. Compra sem cotação agora fica fora do '
              'total, e compra apagada do razão sai daqui.',
        ),
        if (data.bySource.length > 1)
          FiSection(
            title: 'Por origem da sugestão',
            child: FiRows(
              children: [
                for (final g in data.bySource)
                  FiDataRow(
                    label: g.source,
                    value: _signed(g.pnlPct),
                    valueColor: fiDirectionColor(g.pnlPct, brightness),
                    detail: g.ibovPct == null
                        ? _compras(g.count)
                        : '${_compras(g.count)} · Ibovespa ${_signed(g.ibovPct)}',
                  ),
              ],
            ),
          ),
        FiSection(
          title: 'Compras',
          count: data.totalCount,
          child: Column(
            children: [
              for (final item in data.items) _FollowedObject(key: ValueKey(item.id), item: item),
            ],
          ),
        ),
        if (data.hasMore && data.nextCursor != null)
          _MoreFollowed(key: ObjectKey(data), cursor: data.nextCursor!),
      ],
    );
  }
}

class _FollowedObject extends ConsumerStatefulWidget {
  const _FollowedObject({super.key, required this.item});

  final FollowedSuggestion item;

  @override
  ConsumerState<_FollowedObject> createState() => _FollowedObjectState();
}

class _FollowedObjectState extends ConsumerState<_FollowedObject> {
  bool _stopping = false;

  Future<void> _stop() async {
    final item = widget.item;
    final confirmado = await fiConfirm(
      context,
      title: 'Deixar de acompanhar ${item.ticker}?',
      body: 'A compra continua no razão e na carteira. Só deixa de contar no resultado das '
          'sugestões seguidas.',
      confirmLabel: 'Deixar de acompanhar',
    );
    if (!confirmado || !mounted) return;

    setState(() => _stopping = true);
    final ok = await fiAttempt(
      context,
      () => ref.read(apiRepositoryProvider).deleteFollowedSuggestion(item.id),
      action: 'deixar de acompanhar esta compra',
      success: '${item.ticker} saiu do resultado. A compra continua no razão.',
    );
    if (ok) ref.invalidate(followedSuggestionsProvider);
    if (mounted) setState(() => _stopping = false);
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    final brightness = Theme.of(context).brightness;
    final pnl = item.pnlPct;

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(item.ticker, style: FiType.title.copyWith(color: fiInk1(context))),
                ),
                if (item.action == 'vender')
                  FiTag.series(label: 'Venda', color: fiInk2(context)),
                IconButton(
                  onPressed: _stopping ? null : _stop,
                  icon: const Icon(Icons.visibility_off_outlined),
                  tooltip: 'Deixar de acompanhar',
                  iconSize: 20,
                ),
              ],
            ),
            FiRows(
              children: [
                FiDataRow(
                  label: 'Data',
                  value: formatDate(item.followedOn),
                  detail: item.daysHeld == 1 ? 'há 1 dia' : 'há ${item.daysHeld} dias',
                ),
                FiDataRow(
                  label: 'Investido',
                  value: formatCurrency(item.invested),
                  detail: '${formatQuantity(item.quantity)} × ${formatCurrency(item.price)}',
                ),
                FiDataRow(
                  label: 'Hoje',
                  value: item.currentValue == null ? '—' : formatCurrency(item.currentValue),
                  detail: item.currentValue == null ? 'Sem cotação agora' : null,
                ),
                FiDataRow(
                  label: 'Resultado',
                  value: _signed(pnl),
                  valueColor: pnl == null ? null : fiDirectionColor(pnl, brightness),
                  detail: item.ibovPctSince == null
                      ? null
                      : 'Ibovespa no período: ${_signed(item.ibovPctSince)}',
                ),
                if (item.scoreAtSuggestion != null)
                  FiDataRow(
                    label: 'Score quando comprou',
                    glossaryKey: 'score',
                    value: formatDecimal(item.scoreAtSuggestion, digits: 0),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MoreFollowed extends ConsumerStatefulWidget {
  const _MoreFollowed({super.key, required this.cursor});

  final String cursor;

  @override
  ConsumerState<_MoreFollowed> createState() => _MoreFollowedState();
}

class _MoreFollowedState extends ConsumerState<_MoreFollowed> {
  final List<FollowedSuggestion> _extras = [];
  String? _cursor;
  bool _loading = false;
  Object? _error;

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final page = await ref
          .read(apiRepositoryProvider)
          .getFollowedSuggestions(cursor: _cursor ?? widget.cursor);
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
        for (final item in _extras) _FollowedObject(key: ValueKey(item.id), item: item),
        if (_error != null)
          Text(
            fiErrorMessage(_error!, action: 'carregar as compras anteriores'),
            style: FiType.caption.copyWith(
              color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
            ),
          ),
        const SizedBox(height: FiSpace.s2),
        if (temMais)
          FiButton.secondary(
            label: _loading ? 'Carregando…' : 'Carregar as anteriores',
            busy: _loading,
            onPressed: _loading ? null : _load,
          ),
      ],
    );
  }
}
