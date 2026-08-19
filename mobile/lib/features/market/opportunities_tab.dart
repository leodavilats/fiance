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

class _OpportunitiesTabState extends ConsumerState<OpportunitiesTab> {
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final filters = ref.watch(opportunitiesFiltersProvider);

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 8, 0),
          child: Column(
            children: [
              TickerAutocompleteField(
                controller: _searchCtrl,
                labelText: 'Buscar ticker ou nome...',
                onSelected: (s) {
                  ref.read(opportunitiesFiltersProvider.notifier).state =
                      filters.copyWith(search: s.ticker);
                },
              ),
              const SizedBox(height: 10),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _CategoryChip(
                      label: 'Todas',
                      value: '',
                      selected: filters.category,
                      filters: filters,
                    ),
                    _CategoryChip(
                      label: 'Ações BR',
                      value: 'acoes_br',
                      selected: filters.category,
                      filters: filters,
                    ),
                    _CategoryChip(
                      label: 'BDRs',
                      value: 'bdrs',
                      selected: filters.category,
                      filters: filters,
                    ),
                    _CategoryChip(
                      label: 'FIIs',
                      value: 'fiis',
                      selected: filters.category,
                      filters: filters,
                    ),
                    _CategoryChip(
                      label: 'ETFs',
                      value: 'etfs',
                      selected: filters.category,
                      filters: filters,
                    ),
                    const SizedBox(width: 8),
                    Container(width: 1, height: 20, color: Theme.of(context).dividerColor),
                    const SizedBox(width: 8),
                    FilterChip(
                      avatar: Icon(
                        Icons.trending_down,
                        size: 16,
                        color: filters.onlyDip
                            ? Theme.of(context).colorScheme.primary
                            : null,
                      ),
                      label: const Text('Em queda'),
                      selected: filters.onlyDip,
                      onSelected: (v) =>
                          ref
                              .read(opportunitiesFiltersProvider.notifier)
                              .state = filters.copyWith(
                            onlyDip: v,
                          ),
                    ),
                    const SizedBox(width: 6),
                    if (!filters.onlyDip)
                      FilterChip(
                        label: const Text('Destaques'),
                        selected: filters.onlyInteresting,
                        onSelected: (v) =>
                            ref
                                .read(opportunitiesFiltersProvider.notifier)
                                .state = filters.copyWith(
                              onlyInteresting: v,
                            ),
                      ),
                  ],
                ),
              ),
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

class _CategoryChip extends ConsumerWidget {
  const _CategoryChip({
    required this.label,
    required this.value,
    required this.selected,
    required this.filters,
  });

  final String label;
  final String value;
  final String selected;
  final OpportunitiesFilters filters;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: ChoiceChip(
        label: Text(label),
        selected: selected == value,
        onSelected: (_) =>
            ref.read(opportunitiesFiltersProvider.notifier).state = filters
                .copyWith(category: value),
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
