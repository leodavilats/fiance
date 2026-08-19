import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/sector_translations.dart';
import '../../core/theme.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';

enum _AssetGroupMode { value, category, sector }

final _assetGroupModeProvider = StateProvider.autoDispose<_AssetGroupMode>(
  (ref) => _AssetGroupMode.value,
);

class AssetsScreen extends ConsumerWidget {
  const AssetsScreen({super.key});

  Future<void> _openAddDialog(
    BuildContext context,
    WidgetRef ref,
    List<PortfolioPosition> current,
  ) async {
    final tickerCtrl = TextEditingController();
    final qtyCtrl = TextEditingController();
    final priceCtrl = TextEditingController();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Adicionar ativo'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TickerAutocompleteField(
              controller: tickerCtrl,
              labelText: 'Ticker (ex: PETR4)',
            ),
            const SizedBox(height: 16),
            TextField(
              controller: qtyCtrl,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(labelText: 'Quantidade'),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: priceCtrl,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(labelText: 'Preço médio'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Salvar'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    final ticker = tickerCtrl.text.trim().toUpperCase();
    final quantity = double.tryParse(qtyCtrl.text.replaceAll(',', '.'));
    final avgPrice = double.tryParse(priceCtrl.text.replaceAll(',', '.'));

    if (ticker.isEmpty || quantity == null || avgPrice == null) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Preencha ticker, quantidade e preço corretamente'),
          ),
        );
      }
      return;
    }

    final updated = [
      ...current
          .where((i) => i.ticker != ticker)
          .map(
            (i) => StoredPortfolioItem(
              ticker: i.ticker,
              quantity: i.quantity,
              avgPrice: i.avgPrice,
              category: i.categoryResolved,
            ),
          ),
      StoredPortfolioItem(
        ticker: ticker,
        quantity: quantity,
        avgPrice: avgPrice,
        category: 'auto',
      ),
    ];
    await ref.read(apiRepositoryProvider).savePortfolio(updated);
    ref.invalidate(dashboardProvider);
    ref.invalidate(portfolioProvider);
  }

  Future<void> _delete(WidgetRef ref, String ticker) async {
    await ref.read(apiRepositoryProvider).deletePosition(ticker);
    ref.invalidate(dashboardProvider);
    ref.invalidate(portfolioProvider);
  }

  Future<void> _openSellDialog(
    BuildContext context,
    WidgetRef ref,
    PortfolioPosition position,
  ) async {
    final qtyCtrl = TextEditingController(text: '${position.quantity}');
    final priceCtrl = TextEditingController(
      text: '${position.currentPrice ?? position.avgPrice}',
    );

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Vender ${position.ticker}'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: qtyCtrl,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: InputDecoration(
                labelText: 'Quantidade (máx. ${position.quantity})',
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: priceCtrl,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(labelText: 'Preço de venda'),
            ),
            const SizedBox(height: 8),
            const Text(
              'Lucro/prejuízo, IR e histórico serão calculados automaticamente.',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmar venda'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    final quantity = double.tryParse(qtyCtrl.text.replaceAll(',', '.'));
    final sellPrice = double.tryParse(priceCtrl.text.replaceAll(',', '.'));

    if (quantity == null ||
        quantity <= 0 ||
        quantity > position.quantity ||
        sellPrice == null ||
        sellPrice <= 0) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Quantidade ou preço inválidos')),
        );
      }
      return;
    }

    try {
      final trade = await ref
          .read(apiRepositoryProvider)
          .sellPosition(
            ticker: position.ticker,
            quantity: quantity,
            sellPrice: sellPrice,
          );
      ref.invalidate(dashboardProvider);
      ref.invalidate(portfolioProvider);
      ref.invalidate(closedTradesProvider);
      if (context.mounted) {
        final lucro = trade.netProfit >= 0 ? 'lucro' : 'prejuízo';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Venda registrada: $lucro líquido de '
              '${formatCurrency(trade.netProfit.abs())}'
              '${trade.irAmount > 0 ? ' (IR: ${formatCurrency(trade.irAmount)})' : ''}',
            ),
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Erro ao vender: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Meus Ativos')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openAddDialog(
          context,
          ref,
          dashboard.valueOrNull?.positions ?? [],
        ),
        child: const Icon(Icons.add),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(dashboardProvider),
        child: dashboard.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(child: Text('Erro: $err')),
          data: (data) {
            if (data.positions.isEmpty) {
              return ListView(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      children: [
                        Icon(
                          Icons.inbox_outlined,
                          size: 48,
                          color: Colors.grey.shade400,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Nenhum ativo cadastrado ainda.\nToque em + pra adicionar.',
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ],
              );
            }

            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 88),
              children: [
                _SummaryGrid(summary: data.summary),
                if (data.allocations.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  const _SectionTitle(
                    icon: Icons.donut_small_outlined,
                    title: 'Composição da carteira',
                  ),
                  _CompositionCard(
                    allocations: data.allocations,
                    positions: data.positions,
                  ),
                ],
                const SizedBox(height: 20),
                _SectionTitle(
                  icon: Icons.receipt_long_outlined,
                  title: 'Ativos negociados (${data.positions.length})',
                ),
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: SegmentedButton<_AssetGroupMode>(
                    segments: const [
                      ButtonSegment(
                        value: _AssetGroupMode.value,
                        label: Text('Por valor'),
                      ),
                      ButtonSegment(
                        value: _AssetGroupMode.category,
                        label: Text('Por categoria'),
                      ),
                      ButtonSegment(
                        value: _AssetGroupMode.sector,
                        label: Text('Por setor'),
                      ),
                    ],
                    selected: {ref.watch(_assetGroupModeProvider)},
                    onSelectionChanged: (s) =>
                        ref.read(_assetGroupModeProvider.notifier).state =
                            s.first,
                  ),
                ),
                _GroupedPositionsList(
                  positions: data.positions,
                  mode: ref.watch(_assetGroupModeProvider),
                  onDelete: (ticker) => _delete(ref, ticker),
                  onSell: (p) => _openSellDialog(context, ref, p),
                ),
                const SizedBox(height: 20),
                const _ClosedTradesSection(),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.icon, required this.title});

  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10, left: 4),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Colors.grey.shade700),
          const SizedBox(width: 6),
          Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}

class _SummaryGrid extends StatelessWidget {
  const _SummaryGrid({required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final positive = summary.totalPnl >= 0;
    final brightness = Theme.of(context).brightness;
    final pnlColor = positive ? gainColor(brightness) : lossColor(brightness);

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Resumo geral',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: _StatBlock(
                    label: 'Investido',
                    value: formatCurrency(summary.totalInvested),
                  ),
                ),
                Expanded(
                  child: _StatBlock(
                    label: 'Valor atual',
                    value: formatCurrency(summary.totalCurrent),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: _StatBlock(
                    label: 'Rendimento',
                    value:
                        '${positive ? '+' : ''}${formatCurrency(summary.totalPnl)}',
                    valueColor: pnlColor,
                    caption: formatPercent(summary.totalPnlPct),
                  ),
                ),
                Expanded(
                  child: _StatBlock(
                    label: 'Ativos',
                    value: '${summary.positionsCount}',
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatBlock extends StatelessWidget {
  const _StatBlock({
    required this.label,
    required this.value,
    this.valueColor,
    this.caption,
  });

  final String label;
  final String value;
  final Color? valueColor;
  final String? caption;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            color: Colors.grey.shade600,
            fontSize: 11,
            letterSpacing: 0.2,
          ),
        ),
        const SizedBox(height: 2),
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            Text(
              value,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
                color: valueColor,
              ),
            ),
            if (caption != null) ...[
              const SizedBox(width: 6),
              Text(caption!, style: TextStyle(color: valueColor, fontSize: 12)),
            ],
          ],
        ),
      ],
    );
  }
}

enum _CompositionMode { asset, sector }

const _stockCategories = {'acoes_br', 'acoes_int'};

class _CompositionSlice {
  const _CompositionSlice({
    required this.label,
    required this.value,
    required this.pct,
    required this.color,
    required this.icon,
  });

  final String label;
  final double value;
  final double pct;
  final Color color;
  final IconData? icon;
}

class _CompositionCard extends StatefulWidget {
  const _CompositionCard({required this.allocations, required this.positions});

  final List<CategoryAllocation> allocations;
  final List<PortfolioPosition> positions;

  @override
  State<_CompositionCard> createState() => _CompositionCardState();
}

class _CompositionCardState extends State<_CompositionCard> {
  _CompositionMode _mode = _CompositionMode.asset;

  List<_CompositionSlice> get _byAsset {
    final sorted = [...widget.allocations]
      ..sort((a, b) => b.currentValue.compareTo(a.currentValue));
    return sorted
        .where((a) => a.currentPct > 0)
        .map(
          (a) => _CompositionSlice(
            label: categoryLabel(a.category),
            value: a.currentValue,
            pct: a.currentPct,
            color: categoryColor(a.category),
            icon: categoryIcon(a.category),
          ),
        )
        .toList();
  }

  List<_CompositionSlice> get _bySector {
    final buckets = <String, double>{};
    var totalAcoes = 0.0;
    for (final p in widget.positions) {
      if (!_stockCategories.contains(p.categoryResolved)) continue;
      final valor = p.currentValue ?? p.invested;
      final setor = translateSector(p.sector);
      buckets[setor] = (buckets[setor] ?? 0) + valor;
      totalAcoes += valor;
    }
    if (totalAcoes <= 0) return [];

    final entries = buckets.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return entries
        .map(
          (e) => _CompositionSlice(
            label: e.key,
            value: e.value,
            pct: e.value / totalAcoes * 100,
            color: sectorColor(e.key),
            icon: null,
          ),
        )
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final slices = _mode == _CompositionMode.asset ? _byAsset : _bySector;

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            SegmentedButton<_CompositionMode>(
              segments: const [
                ButtonSegment(
                  value: _CompositionMode.asset,
                  label: Text('Por ativo'),
                ),
                ButtonSegment(
                  value: _CompositionMode.sector,
                  label: Text('Por setor (ações)'),
                ),
              ],
              selected: {_mode},
              onSelectionChanged: (s) => setState(() => _mode = s.first),
            ),
            const SizedBox(height: 16),
            if (slices.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Text(
                  'Nenhuma ação ou BDR avaliada ainda.',
                  style: TextStyle(color: Colors.grey.shade600),
                ),
              )
            else ...[
              SizedBox(
                height: 180,
                child: PieChart(
                  PieChartData(
                    sections: slices
                        .map(
                          (s) => PieChartSectionData(
                            value: s.value,
                            color: s.color,
                            title: '${s.pct.round()}%',
                            radius: 60,
                            titleStyle: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        )
                        .toList(),
                    sectionsSpace: 2,
                    centerSpaceRadius: 36,
                  ),
                ),
              ),
              const SizedBox(height: 14),
              for (var i = 0; i < slices.length; i++) ...[
                if (i > 0) const Divider(height: 1),
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Row(
                    children: [
                      if (slices[i].icon != null) ...[
                        Icon(slices[i].icon, size: 16, color: slices[i].color),
                        const SizedBox(width: 8),
                      ] else ...[
                        Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            color: slices[i].color,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      Expanded(child: Text(slices[i].label)),
                      Text(
                        formatCurrency(slices[i].value),
                        style: TextStyle(
                          color: Colors.grey.shade600,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(width: 8),
                      SizedBox(
                        width: 48,
                        child: Text(
                          formatPercent(slices[i].pct),
                          textAlign: TextAlign.right,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}

class _GroupedPositionsList extends ConsumerWidget {
  const _GroupedPositionsList({
    required this.positions,
    required this.mode,
    required this.onDelete,
    required this.onSell,
  });

  final List<PortfolioPosition> positions;
  final _AssetGroupMode mode;
  final void Function(String ticker) onDelete;
  final void Function(PortfolioPosition position) onSell;

  List<PortfolioPosition> _sortedByValue(List<PortfolioPosition> items) {
    final sorted = [...items];
    sorted.sort(
      (a, b) => (b.currentValue ?? 0).compareTo(a.currentValue ?? 0),
    );
    return sorted;
  }

  Widget _cardsFor(
    BuildContext context,
    WidgetRef ref,
    List<PortfolioPosition> items,
  ) {
    return Column(
      children: _sortedByValue(items)
          .map(
            (p) => _AssetCard(
              position: p,
              onDelete: () => onDelete(p.ticker),
              onSell: () => onSell(p),
            ),
          )
          .toList(),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (mode == _AssetGroupMode.value) {
      return _cardsFor(context, ref, positions);
    }

    final totalValue = positions.fold<double>(
      0,
      (sum, p) => sum + (p.currentValue ?? 0),
    );

    if (mode == _AssetGroupMode.category) {
      final goals = ref.watch(goalsProvider).valueOrNull ?? [];
      final groups = <String, List<PortfolioPosition>>{};
      for (final p in positions) {
        groups.putIfAbsent(p.categoryResolved, () => []).add(p);
      }
      final entries = groups.entries.toList()
        ..sort(
          (a, b) => b.value
              .fold<double>(0, (s, p) => s + (p.currentValue ?? 0))
              .compareTo(
                a.value.fold<double>(0, (s, p) => s + (p.currentValue ?? 0)),
              ),
        );

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: entries.expand((e) {
          final groupValue = e.value.fold<double>(
            0,
            (s, p) => s + (p.currentValue ?? 0),
          );
          final atualPct = totalValue > 0 ? groupValue / totalValue * 100 : 0.0;
          final goal = goals.where((g) => g.category == e.key).firstOrNull;
          return [
            _GroupHeader(
              label: categoryLabel(e.key),
              atualPct: atualPct,
              metaPct: goal?.targetPct,
            ),
            _cardsFor(context, ref, e.value),
            const SizedBox(height: 12),
          ];
        }).toList(),
      );
    }

    final sectorGoals = ref.watch(sectorGoalsProvider).valueOrNull ?? [];
    final groups = <String, List<PortfolioPosition>>{};
    for (final p in positions) {
      final sector = p.sector ?? '—';
      groups.putIfAbsent(sector, () => []).add(p);
    }
    final entries = groups.entries.toList()
      ..sort(
        (a, b) => b.value
            .fold<double>(0, (s, p) => s + (p.currentValue ?? 0))
            .compareTo(
              a.value.fold<double>(0, (s, p) => s + (p.currentValue ?? 0)),
            ),
      );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: entries.expand((e) {
        final groupValue = e.value.fold<double>(
          0,
          (s, p) => s + (p.currentValue ?? 0),
        );
        final atualPct = totalValue > 0 ? groupValue / totalValue * 100 : 0.0;
        final goal = sectorGoals
            .where((g) => g.sector == e.key)
            .firstOrNull;
        return [
          _GroupHeader(
            label: translateSector(e.key == '—' ? null : e.key),
            atualPct: atualPct,
            metaPct: goal?.targetPct,
          ),
          _cardsFor(context, ref, e.value),
          const SizedBox(height: 12),
        ];
      }).toList(),
    );
  }
}

class _GroupHeader extends StatelessWidget {
  const _GroupHeader({
    required this.label,
    required this.atualPct,
    this.metaPct,
  });

  final String label;
  final double atualPct;
  final double? metaPct;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, top: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
          Text(
            metaPct != null
                ? 'atual ${formatPercent(atualPct)} · meta ${formatPercent(metaPct)}'
                : 'atual ${formatPercent(atualPct)}',
            style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _AssetCard extends StatelessWidget {
  const _AssetCard({
    required this.position,
    required this.onDelete,
    required this.onSell,
  });

  final PortfolioPosition position;
  final VoidCallback onDelete;
  final VoidCallback onSell;

  void _showReasons(BuildContext context, PortfolioPosition p) {
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${p.ticker} — ${p.label}',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 12),
            ...p.reasons.map(
              (r) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text('•  $r', style: const TextStyle(height: 1.4)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final p = position;
    final positive = (p.pnl ?? 0) >= 0;
    final brightness = Theme.of(context).brightness;
    final pnlColor = positive ? gainColor(brightness) : lossColor(brightness);

    return Dismissible(
      key: ValueKey(p.ticker),
      direction: DismissDirection.endToStart,
      confirmDismiss: (_) => showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Remover ativo'),
          content: Text('Remover ${p.ticker} da carteira?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar'),
            ),
            FilledButton.tonal(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Remover'),
            ),
          ],
        ),
      ).then((v) => v ?? false),
      onDismissed: (_) => onDelete(),
      background: Container(
        margin: const EdgeInsets.only(bottom: 10),
        decoration: BoxDecoration(
          color: lossColor(Theme.of(context).brightness),
          borderRadius: BorderRadius.circular(12),
        ),
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        child: const Icon(Icons.delete, color: Colors.white),
      ),
      child: Card(
        margin: const EdgeInsets.only(bottom: 10),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              p.ticker,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 6,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: categoryColor(
                                  p.categoryResolved,
                                ).withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(5),
                              ),
                              child: Text(
                                categoryLabel(p.categoryResolved),
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                  color: categoryColor(p.categoryResolved),
                                ),
                              ),
                            ),
                          ],
                        ),
                        if (p.name != null)
                          Padding(
                            padding: const EdgeInsets.only(top: 2),
                            child: Text(
                              p.name!,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontSize: 12,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        formatCurrency(p.currentValue),
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      Text(
                        '${positive ? '+' : ''}${formatPercent(p.pnlPct)}',
                        style: TextStyle(
                          color: pnlColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const Divider(height: 18),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _MiniInfo(label: 'Qtd.', value: '${p.quantity}'),
                  _MiniInfo(label: 'PM', value: formatCurrency(p.avgPrice)),
                  _MiniInfo(
                    label: 'Atual',
                    value: formatCurrency(p.currentPrice),
                  ),
                  _MiniInfo(label: 'DY', value: formatPercent(p.dividendYield)),
                ],
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (p.reasons.isNotEmpty)
                    TextButton.icon(
                      onPressed: () => _showReasons(context, p),
                      icon: const Icon(Icons.info_outline, size: 16),
                      label: const Text('Por quê?'),
                      style: TextButton.styleFrom(
                        padding: EdgeInsets.zero,
                        minimumSize: const Size(0, 32),
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ),
                  const SizedBox(width: 12),
                  TextButton.icon(
                    onPressed: onSell,
                    icon: const Icon(Icons.sell_outlined, size: 16),
                    label: const Text('Vender'),
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(0, 32),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ClosedTradesSection extends ConsumerStatefulWidget {
  const _ClosedTradesSection();

  @override
  ConsumerState<_ClosedTradesSection> createState() =>
      _ClosedTradesSectionState();
}

class _ClosedTradesSectionState extends ConsumerState<_ClosedTradesSection> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final trades = ref.watch(closedTradesProvider);

    return trades.when(
      loading: () => const SizedBox.shrink(),
      error: (_, _) => const SizedBox.shrink(),
      data: (data) {
        if (data.trades.isEmpty) return const SizedBox.shrink();

        final brightness = Theme.of(context).brightness;
        final totalColor = data.totalRealizedPnl >= 0
            ? gainColor(brightness)
            : lossColor(brightness);

        return Card(
          margin: EdgeInsets.zero,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ListTile(
                title: const Text(
                  'Operações encerradas',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: RichText(
                  text: TextSpan(
                    style: DefaultTextStyle.of(context).style.copyWith(
                      color: Colors.grey.shade600,
                      fontSize: 12,
                    ),
                    children: [
                      const TextSpan(text: 'Lucro/prejuízo realizado: '),
                      TextSpan(
                        text: formatCurrency(data.totalRealizedPnl),
                        style: TextStyle(
                          color: totalColor,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      TextSpan(text: ' · IR: ${formatCurrency(data.totalIrPaid)}'),
                    ],
                  ),
                ),
                trailing: Icon(
                  _expanded ? Icons.expand_less : Icons.expand_more,
                ),
                onTap: () => setState(() => _expanded = !_expanded),
              ),
              if (_expanded)
                ...data.trades.map(
                  (t) => Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 6,
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                t.ticker,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              Text(
                                '${t.quantity} un. · venda ${formatCurrency(t.sellPrice)}',
                                style: TextStyle(
                                  color: Colors.grey.shade600,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          '${t.netProfit >= 0 ? '+' : ''}${formatCurrency(t.netProfit)}',
                          style: TextStyle(
                            color: t.netProfit >= 0
                                ? gainColor(brightness)
                                : lossColor(brightness),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 8),
            ],
          ),
        );
      },
    );
  }
}

class _MiniInfo extends StatelessWidget {
  const _MiniInfo({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(color: Colors.grey.shade500, fontSize: 10),
        ),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 12),
        ),
      ],
    );
  }
}
