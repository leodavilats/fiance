import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/help_tooltip.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import 'asset_detail_sheet.dart';

const _categoryToAssetType = {
  '': '',
  'acoes_br': 'br_stock',
  'bdrs': 'bdr',
  'fiis': 'fii',
  'etfs': 'etf',
};

class OpportunitiesFilters {
  const OpportunitiesFilters({
    this.search = '',
    this.minDy,
    this.minMos,
    this.category = '',
    this.onlyInteresting = false,
    this.onlyDip = false,
  });

  final String search;
  final double? minDy;
  final double? minMos;
  final String category;
  final bool onlyInteresting;
  final bool onlyDip;

  OpportunitiesFilters copyWith({
    String? search,
    double? minDy,
    double? minMos,
    String? category,
    bool? onlyInteresting,
    bool? onlyDip,
  }) {
    return OpportunitiesFilters(
      search: search ?? this.search,
      minDy: minDy ?? this.minDy,
      minMos: minMos ?? this.minMos,
      category: category ?? this.category,
      onlyInteresting: onlyInteresting ?? this.onlyInteresting,
      onlyDip: onlyDip ?? this.onlyDip,
    );
  }
}

final opportunitiesFiltersProvider =
    StateProvider.autoDispose<OpportunitiesFilters>(
      (ref) => const OpportunitiesFilters(),
    );

final filteredOpportunitiesProvider =
    FutureProvider.autoDispose<List<Opportunity>>((ref) {
      final f = ref.watch(opportunitiesFiltersProvider);
      return ref
          .watch(apiRepositoryProvider)
          .getOpportunities(
            search: f.search,
            assetType: _categoryToAssetType[f.category] ?? '',
            onlyInteresting: f.onlyInteresting,
            minDy: f.minDy,
            minMosPct: f.minMos != null ? f.minMos! * 100 : null,
          );
    });

final dipScanResultProvider = FutureProvider.autoDispose<List<DipScanItem>>((
  ref,
) {
  final f = ref.watch(opportunitiesFiltersProvider);
  return ref
      .watch(apiRepositoryProvider)
      .dipScan(category: f.category.isEmpty ? null : f.category);
});

class OpportunitiesTab extends ConsumerStatefulWidget {
  const OpportunitiesTab({super.key});

  @override
  ConsumerState<OpportunitiesTab> createState() => _OpportunitiesTabState();
}

const _categoryLabels = {
  '': 'Todas',
  'acoes_br': 'Ações BR',
  'bdrs': 'BDRs',
  'fiis': 'FIIs',
  'etfs': 'ETFs',
};

int _activeFilterCount(OpportunitiesFilters f) {
  var count = 0;
  if (f.category.isNotEmpty) count++;
  if (f.onlyDip) count++;
  if (f.onlyInteresting) count++;
  if (f.minDy != null) count++;
  if (f.minMos != null) count++;
  return count;
}

class _OpportunitiesTabState extends ConsumerState<OpportunitiesTab> {
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _openFilters() async {
    final filters = ref.read(opportunitiesFiltersProvider);
    final result = await showModalBottomSheet<OpportunitiesFilters>(
      context: context,
      isScrollControlled: true,
      builder: (context) => _FiltersSheet(initial: filters),
    );
    if (result != null) {
      ref.read(opportunitiesFiltersProvider.notifier).state = result;
    }
  }

  @override
  Widget build(BuildContext context) {
    final filters = ref.watch(opportunitiesFiltersProvider);
    final activeCount = _activeFilterCount(filters);

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: TickerAutocompleteField(
                      controller: _searchCtrl,
                      labelText: 'Buscar ticker ou nome...',
                      onSelected: (s) {
                        ref.read(opportunitiesFiltersProvider.notifier).state =
                            filters.copyWith(search: s.ticker);
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  Badge(
                    label: Text('$activeCount'),
                    isLabelVisible: activeCount > 0,
                    child: IconButton.filledTonal(
                      icon: const Icon(Icons.tune),
                      tooltip: 'Filtros',
                      onPressed: _openFilters,
                    ),
                  ),
                ],
              ),
              if (activeCount > 0) ...[
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      if (filters.category.isNotEmpty)
                        _ActiveFilterChip(
                          label: _categoryLabels[filters.category] ?? filters.category,
                          onDeleted: () =>
                              ref.read(opportunitiesFiltersProvider.notifier).state =
                                  filters.copyWith(category: ''),
                        ),
                      if (filters.onlyDip)
                        _ActiveFilterChip(
                          label: 'Em queda',
                          onDeleted: () =>
                              ref.read(opportunitiesFiltersProvider.notifier).state =
                                  filters.copyWith(onlyDip: false),
                        ),
                      if (filters.onlyInteresting)
                        _ActiveFilterChip(
                          label: 'Destaques',
                          onDeleted: () =>
                              ref.read(opportunitiesFiltersProvider.notifier).state =
                                  filters.copyWith(onlyInteresting: false),
                        ),
                      if (filters.minDy != null)
                        _ActiveFilterChip(
                          label: 'DY ≥ ${filters.minDy!.toStringAsFixed(1)}%',
                          onDeleted: () =>
                              ref.read(opportunitiesFiltersProvider.notifier).state =
                                  OpportunitiesFilters(
                                    search: filters.search,
                                    minMos: filters.minMos,
                                    category: filters.category,
                                    onlyInteresting: filters.onlyInteresting,
                                    onlyDip: filters.onlyDip,
                                  ),
                        ),
                      if (filters.minMos != null)
                        _ActiveFilterChip(
                          label: 'MS ≥ ${(filters.minMos! * 100).toStringAsFixed(0)}%',
                          onDeleted: () =>
                              ref.read(opportunitiesFiltersProvider.notifier).state =
                                  OpportunitiesFilters(
                                    search: filters.search,
                                    minDy: filters.minDy,
                                    category: filters.category,
                                    onlyInteresting: filters.onlyInteresting,
                                    onlyDip: filters.onlyDip,
                                  ),
                        ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 10),
            ],
          ),
        ),
        Expanded(
          child: filters.onlyDip
              ? const _DipScannerView()
              : const _AllOpportunitiesView(),
        ),
      ],
    );
  }
}

class _ActiveFilterChip extends StatelessWidget {
  const _ActiveFilterChip({required this.label, required this.onDeleted});

  final String label;
  final VoidCallback onDeleted;

  @override
  Widget build(BuildContext context) {
    return InputChip(
      label: Text(label, style: const TextStyle(fontSize: 12)),
      onDeleted: onDeleted,
      visualDensity: VisualDensity.compact,
    );
  }
}

class _FiltersSheet extends StatefulWidget {
  const _FiltersSheet({required this.initial});

  final OpportunitiesFilters initial;

  @override
  State<_FiltersSheet> createState() => _FiltersSheetState();
}

class _FiltersSheetState extends State<_FiltersSheet> {
  late String _category = widget.initial.category;
  late bool _onlyDip = widget.initial.onlyDip;
  late bool _onlyInteresting = widget.initial.onlyInteresting;
  late bool _dyEnabled = widget.initial.minDy != null;
  late double _dyValue = widget.initial.minDy ?? 6.0;
  late bool _mosEnabled = widget.initial.minMos != null;
  late double _mosValue = (widget.initial.minMos ?? 0.15) * 100;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 16,
          bottom: 16 + MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Filtros',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                TextButton(
                  onPressed: () => setState(() {
                    _category = '';
                    _onlyDip = false;
                    _onlyInteresting = false;
                    _dyEnabled = false;
                    _mosEnabled = false;
                  }),
                  child: const Text('Limpar'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text('Categoria', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: _categoryLabels.entries
                  .map(
                    (e) => ChoiceChip(
                      label: Text(e.value),
                      selected: _category == e.key,
                      onSelected: (_) => setState(() => _category = e.key),
                    ),
                  )
                  .toList(),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Em queda'),
              subtitle: const Text('Scanner de ativos em queda recente'),
              value: _onlyDip,
              onChanged: (v) => setState(() => _onlyDip = v),
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Somente destaques'),
              value: _onlyInteresting,
              onChanged: _onlyDip ? null : (v) => setState(() => _onlyInteresting = v),
            ),
            const Divider(height: 24),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Dividend yield mínimo'),
              subtitle: _dyEnabled ? Text('${_dyValue.toStringAsFixed(1)}%') : null,
              value: _dyEnabled,
              onChanged: (v) => setState(() => _dyEnabled = v),
            ),
            if (_dyEnabled)
              Slider(
                value: _dyValue,
                min: 0,
                max: 20,
                divisions: 40,
                label: '${_dyValue.toStringAsFixed(1)}%',
                onChanged: (v) => setState(() => _dyValue = v),
              ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Margem de segurança mínima'),
              subtitle: _mosEnabled ? Text('${_mosValue.toStringAsFixed(0)}%') : null,
              value: _mosEnabled,
              onChanged: (v) => setState(() => _mosEnabled = v),
            ),
            if (_mosEnabled)
              Slider(
                value: _mosValue,
                min: -20,
                max: 50,
                divisions: 70,
                label: '${_mosValue.toStringAsFixed(0)}%',
                onChanged: (v) => setState(() => _mosValue = v),
              ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  Navigator.pop(
                    context,
                    OpportunitiesFilters(
                      search: widget.initial.search,
                      category: _category,
                      onlyDip: _onlyDip,
                      onlyInteresting: _onlyDip ? false : _onlyInteresting,
                      minDy: _dyEnabled ? _dyValue : null,
                      minMos: _mosEnabled ? _mosValue / 100 : null,
                    ),
                  );
                },
                child: const Text('Aplicar filtros'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DipScannerView extends ConsumerWidget {
  const _DipScannerView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final result = ref.watch(dipScanResultProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(dipScanResultProvider),
      child: result.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Erro: $err')),
        data: (items) {
          if (items.isEmpty) {
            return ListView(
              children: const [
                Padding(
                  padding: EdgeInsets.all(32),
                  child: Text(
                    'Nenhum ativo em queda encontrado agora',
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: items.length,
            separatorBuilder: (_, _) => const SizedBox(height: 14),
            itemBuilder: (context, index) {
              final item = items[index];
              return Card(
                margin: EdgeInsets.zero,
                elevation: 1.5,
                child: InkWell(
                  onTap: () => showAssetDetailSheet(context, item.symbol),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              item.symbol,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              'score ${item.dipScore.toStringAsFixed(0)}',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Colors.orange,
                              ),
                            ),
                          ],
                        ),
                        if (item.name != null)
                          Text(
                            item.name!,
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 12,
                            ),
                          ),
                        const SizedBox(height: 6),
                        Text(
                          'Queda do topo: ${formatPercent(item.dropFromHighPct)} · MS: ${formatPercent(item.marginOfSafety)}',
                          style: const TextStyle(fontSize: 12),
                        ),
                        if (item.topReason.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(
                              item.topReason,
                              style: const TextStyle(
                                fontSize: 12,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class _AllOpportunitiesView extends ConsumerWidget {
  const _AllOpportunitiesView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filters = ref.watch(opportunitiesFiltersProvider);
    final opportunities = ref.watch(filteredOpportunitiesProvider);

    var items = opportunities.valueOrNull ?? [];
    items = items.where((o) {
      if (filters.minDy != null && (o.dividendYield ?? 0) < filters.minDy!) {
        return false;
      }
      if (filters.minMos != null &&
          (o.marginOfSafety ?? -999) < filters.minMos!) {
        return false;
      }
      return true;
    }).toList();

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(filteredOpportunitiesProvider),
      child: opportunities.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Erro: $err')),
        data: (_) {
          if (items.isEmpty) {
            return ListView(
              children: const [
                Padding(
                  padding: EdgeInsets.all(32),
                  child: Text(
                    'Nenhuma oportunidade encontrada',
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            itemCount: items.length,
            separatorBuilder: (_, _) => const SizedBox(height: 14),
            itemBuilder: (context, index) =>
                _OpportunityCard(opportunity: items[index]),
          );
        },
      ),
    );
  }
}

class _OpportunityCard extends StatelessWidget {
  const _OpportunityCard({required this.opportunity});

  final Opportunity opportunity;

  Color _verdictColor(Brightness brightness) {
    switch (opportunity.verdict) {
      case 'STRONG_BUY':
      case 'BUY':
        return gainColor(brightness);
      case 'STRONG_SELL':
      case 'SELL':
        return lossColor(brightness);
      default:
        return Colors.grey.shade700;
    }
  }

  @override
  Widget build(BuildContext context) {
    final verdictColor = _verdictColor(Theme.of(context).brightness);
    return Card(
      margin: EdgeInsets.zero,
      elevation: 1.5,
      child: InkWell(
        onTap: () => showAssetDetailSheet(context, opportunity.ticker),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          opportunity.ticker,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        if (opportunity.name != null)
                          Text(
                            opportunity.name!,
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 12,
                            ),
                          ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: verdictColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      opportunity.label,
                      style: TextStyle(
                        color: verdictColor,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
              const Divider(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _Stat(
                    label: 'Preço',
                    value: formatCurrency(opportunity.price),
                  ),
                  _Stat(
                    label: 'Preço justo',
                    value: formatCurrency(opportunity.fairPrice),
                  ),
                  _Stat(
                    label: 'MS',
                    value: formatPercent(opportunity.marginOfSafety),
                    glossaryKey: 'ms',
                  ),
                  _Stat(
                    label: 'DY',
                    value: formatPercent(opportunity.dividendYield),
                    glossaryKey: 'dy',
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

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value, this.glossaryKey});

  final String label;
  final String value;
  final String? glossaryKey;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: TextStyle(color: Colors.grey.shade600, fontSize: 11),
            ),
            if (glossaryKey != null) HelpTooltip(termKey: glossaryKey!),
          ],
        ),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
      ],
    );
  }
}
