import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/help_tooltip.dart';
import 'asset_detail_sheet.dart';

class OpportunitiesFilters {
  const OpportunitiesFilters({
    this.search = '',
    this.minDy,
    this.minMos,
    this.category = '',
    this.onlyInteresting = false,
  });

  final String search;
  final double? minDy;
  final double? minMos;
  final String category;
  final bool onlyInteresting;

  OpportunitiesFilters copyWith({
    String? search,
    double? minDy,
    double? minMos,
    String? category,
    bool? onlyInteresting,
  }) {
    return OpportunitiesFilters(
      search: search ?? this.search,
      minDy: minDy ?? this.minDy,
      minMos: minMos ?? this.minMos,
      category: category ?? this.category,
      onlyInteresting: onlyInteresting ?? this.onlyInteresting,
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
          .getOpportunities(search: f.search);
    });

final dipScanResultProvider = FutureProvider.autoDispose<List<DipScanItem>>((
  ref,
) {
  return ref.watch(apiRepositoryProvider).dipScan();
});

final oppModeProvider = StateProvider.autoDispose<bool>(
  (ref) => false,
); // false=Todas, true=Em queda

class OpportunitiesTab extends ConsumerWidget {
  const OpportunitiesTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDipMode = ref.watch(oppModeProvider);

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
          child: SegmentedButton<bool>(
            segments: const [
              ButtonSegment(value: false, label: Text('Todas')),
              ButtonSegment(value: true, label: Text('Em queda')),
            ],
            selected: {isDipMode},
            onSelectionChanged: (s) =>
                ref.read(oppModeProvider.notifier).state = s.first,
          ),
        ),
        Expanded(
          child: isDipMode
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
            separatorBuilder: (_, _) => const SizedBox(height: 6),
            itemBuilder: (context, index) {
              final item = items[index];
              return Card(
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

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              TextField(
                decoration: const InputDecoration(
                  hintText: 'Buscar ticker ou nome...',
                  prefixIcon: Icon(Icons.search),
                  isDense: true,
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (v) =>
                    ref.read(opportunitiesFiltersProvider.notifier).state =
                        filters.copyWith(search: v),
              ),
              const SizedBox(height: 8),
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
                      label: 'Ações INT',
                      value: 'acoes_int',
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
                      label: 'Cripto',
                      value: 'cripto',
                      selected: filters.category,
                      filters: filters,
                    ),
                    const SizedBox(width: 8),
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
          child: RefreshIndicator(
            onRefresh: () async =>
                ref.invalidate(filteredOpportunitiesProvider),
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
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 6),
                  itemBuilder: (context, index) =>
                      _OpportunityCard(opportunity: items[index]),
                );
              },
            ),
          ),
        ),
      ],
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
      child: InkWell(
        onTap: () => showAssetDetailSheet(context, opportunity.ticker),
        child: Padding(
          padding: const EdgeInsets.all(12),
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
