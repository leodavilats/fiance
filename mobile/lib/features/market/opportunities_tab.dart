import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/labels.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/chip.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/help_tooltip.dart';
import '../../core/score_ruler.dart'
    show basisLabel, dataYearsLabel, fairBandEdgeLabel, fairBandSummary;
import '../../core/widgets/score_ruler.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import '../../core/widgets/error_state.dart';
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
    this.trendDay = '',
    this.trendYear = '',
  });

  final String search;
  final double? minDy;
  final double? minMos;
  final String category;
  final bool onlyInteresting;
  final bool onlyDip;

  final String trendDay;
  final String trendYear;

  OpportunitiesFilters copyWith({
    String? search,
    double? minDy,
    double? minMos,
    String? category,
    bool? onlyInteresting,
    bool? onlyDip,
    String? trendDay,
    String? trendYear,
  }) {
    return OpportunitiesFilters(
      search: search ?? this.search,
      minDy: minDy ?? this.minDy,
      minMos: minMos ?? this.minMos,
      category: category ?? this.category,
      onlyInteresting: onlyInteresting ?? this.onlyInteresting,
      onlyDip: onlyDip ?? this.onlyDip,
      trendDay: trendDay ?? this.trendDay,
      trendYear: trendYear ?? this.trendYear,
    );
  }
}

const fiTrendDayLabels = {'up': 'Subindo hoje', 'down': 'Caindo hoje'};

const fiTrendYearLabels = {
  'up': 'Na parte alta do ano',
  'down': 'Na parte baixa do ano',
};

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
            trendDay: f.trendDay,
            trendYear: f.trendYear,
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
  const OpportunitiesTab({super.key, this.initialOnlyDip = false});

  final bool initialOnlyDip;

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
  if (f.trendDay.isNotEmpty) count++;
  if (f.trendYear.isNotEmpty) count++;
  return count;
}

class _OpportunitiesTabState extends ConsumerState<OpportunitiesTab> {
  final _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final current = ref.read(opportunitiesFiltersProvider);
      if (current.onlyDip != widget.initialOnlyDip) {
        ref.read(opportunitiesFiltersProvider.notifier).state = current.copyWith(
          onlyDip: widget.initialOnlyDip,
        );
      }
    });
  }

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
          padding: const EdgeInsets.fromLTRB(
            FiLayout.gutter,
            FiSpace.s3,
            FiLayout.gutter,
            0,
          ),
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
                  const SizedBox(width: FiSpace.s2),
                  FiButton.secondary(
                    label: activeCount > 0 ? 'Filtros: $activeCount' : 'Filtros',
                    icon: Icons.tune,
                    onPressed: _openFilters,
                  ),
                ],
              ),
              if (activeCount > 0) ...[
                const SizedBox(height: FiSpace.s3),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Wrap(
                    spacing: FiSpace.s2,
                    runSpacing: FiSpace.s2,
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
                      if (filters.trendDay.isNotEmpty)
                        _ActiveFilterChip(
                          label: fiTrendDayLabels[filters.trendDay] ?? filters.trendDay,
                          onDeleted: () =>
                              ref.read(opportunitiesFiltersProvider.notifier).state =
                                  filters.copyWith(trendDay: ''),
                        ),
                      if (filters.trendYear.isNotEmpty)
                        _ActiveFilterChip(
                          label: fiTrendYearLabels[filters.trendYear] ?? filters.trendYear,
                          onDeleted: () =>
                              ref.read(opportunitiesFiltersProvider.notifier).state =
                                  filters.copyWith(trendYear: ''),
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
              const SizedBox(height: FiSpace.s3),
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
    return FiChoiceChip(
      label: label,
      selected: true,
      onSelected: onDeleted,
      onRemove: onDeleted,
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
  late String _trendDay = widget.initial.trendDay;
  late String _trendYear = widget.initial.trendYear;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: FiSpace.s5,
          right: FiSpace.s5,
          top: FiSpace.s5,
          bottom: FiSpace.s5 + MediaQuery.of(context).viewInsets.bottom,
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
                  style: FiType.title,
                ),
                FiButton.quiet(
                  label: 'Limpar tudo',
                  onPressed: () => setState(() {
                    _category = '';
                    _onlyDip = false;
                    _onlyInteresting = false;
                    _dyEnabled = false;
                    _mosEnabled = false;
                    _trendDay = '';
                    _trendYear = '';
                  }),
                ),
              ],
            ),
            const SizedBox(height: FiSpace.s5),
            Text(
              'CATEGORIA',
              style: FiType.eyebrow.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            Wrap(
              spacing: FiSpace.s2,
              runSpacing: FiSpace.s2,
              children: _categoryLabels.entries
                  .map(
                    (e) => FiChoiceChip(
                      label: e.value,
                      selected: _category == e.key,
                      onSelected: () => setState(() => _category = e.key),
                    ),
                  )
                  .toList(),
            ),
            const SizedBox(height: FiSpace.s5),
            Text(
              'DIREÇÃO DO PREÇO',
              style: FiType.eyebrow.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s3),
            Wrap(
              spacing: FiSpace.s2,
              runSpacing: FiSpace.s2,
              children: [
                for (final e in fiTrendDayLabels.entries)
                  FiChoiceChip(
                    label: e.value,
                    selected: _trendDay == e.key,
                    onSelected: () => setState(
                      () => _trendDay = _trendDay == e.key ? '' : e.key,
                    ),
                  ),
                for (final e in fiTrendYearLabels.entries)
                  FiChoiceChip(
                    label: e.value,
                    selected: _trendYear == e.key,
                    onSelected: () => setState(
                      () => _trendYear = _trendYear == e.key ? '' : e.key,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: FiSpace.s2),
            Text(
              'Hoje é a variação do pregão. O ano é onde o preço está entre a mínima e a '
              'máxima de 52 semanas — não é a variação acumulada no ano.',
              style: FiType.caption.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s5),
            FiRows(
              children: [
                FiDataRow(
                  label: 'Em queda',
                  detail: 'Varredura de ativos que caíram do topo recente',
                  trailing: Switch(
                    value: _onlyDip,
                    onChanged: (v) => setState(() => _onlyDip = v),
                  ),
                ),
                FiDataRow(
                  label: 'Somente destaques',
                  detail: _onlyDip ? 'Não se aplica à varredura de quedas' : null,
                  trailing: Switch(
                    value: _onlyInteresting,
                    onChanged: _onlyDip
                        ? null
                        : (v) => setState(() => _onlyInteresting = v),
                  ),
                ),
                FiDataRow(
                  label: 'Dividend yield mínimo',
                  value: _dyEnabled ? '${_dyValue.toStringAsFixed(1)}%' : null,
                  trailing: Switch(
                    value: _dyEnabled,
                    onChanged: (v) => setState(() => _dyEnabled = v),
                  ),
                ),
              ],
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
            FiDataRow(
              label: 'Margem de segurança mínima',
              value: _mosEnabled ? '${_mosValue.toStringAsFixed(0)}%' : null,
              trailing: Switch(
                value: _mosEnabled,
                onChanged: (v) => setState(() => _mosEnabled = v),
              ),
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
            const SizedBox(height: FiSpace.s6),
            FiButton.primary(
              label: 'Aplicar filtros',
              expand: true,
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
                    trendDay: _trendDay,
                    trendYear: _trendYear,
                  ),
                );
              },
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
        loading: () => FiSkeleton.screen(shape: FiSkeletonShape.row, count: 6, label: 'Varrendo o mercado'),
        error: (err, _) => FiErrorState(error: err, action: 'varrer o mercado'),
        data: (items) {
          if (items.isEmpty) {
            return ListView(
              children: const [
                FiEmptyState(
                  title: 'Nenhum ativo em queda agora',
                  body: 'A varredura procura papéis que caíram do topo recente e ainda têm '
                      'fundamento. Nenhum do universo coberto atende ao corte neste momento.',
                ),
              ],
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(
              FiLayout.gutter,
              FiSpace.s2,
              FiLayout.gutter,
              FiLayout.scrollTail,
            ),
            itemCount: items.length,
            separatorBuilder: (_, _) => const SizedBox(height: FiSpace.s2),
            itemBuilder: (context, index) {
              final item = items[index];
              final band = fiBandFor(item.dipScore, fiDipScoreBands);

              return FiObject(
                onTap: () => showAssetDetailSheet(context, item.symbol),
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
                              Text(
                                item.symbol,
                                style: FiType.ticker.copyWith(color: fiInk1(context)),
                              ),
                              if (item.name != null)
                                Text(
                                  item.name!,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: FiType.caption.copyWith(color: fiInk2(context)),
                                ),
                            ],
                          ),
                        ),
                        const SizedBox(width: FiSpace.s3),
                        FiTag(label: band.label, state: band.state),
                      ],
                    ),
                    const SizedBox(height: FiSpace.s3),
                    Text(
                      'Caiu ${formatPercent(item.dropFromHighPct)} do topo · '
                      'margem de segurança ${formatRatio(item.marginOfSafety)}',
                      style: FiType.caption.copyWith(color: fiInk2(context)),
                    ),
                    if (item.topReason.isNotEmpty) ...[
                      const SizedBox(height: FiSpace.s1),
                      Text(
                        item.topReason,
                        style: FiType.caption.copyWith(color: fiInk3(context)),
                      ),
                    ],
                  ],
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
        loading: () => FiSkeleton.screen(shape: FiSkeletonShape.row, count: 6, label: 'Varrendo o mercado'),
        error: (err, _) => FiErrorState(error: err, action: 'varrer o mercado'),
        data: (_) {
          if (items.isEmpty) {
            return ListView(
              children: [
                FiEmptyState(
                  title: 'Nenhuma oportunidade com estes filtros',
                  body: 'O corte atual não deixou nada passar. Afrouxar o yield mínimo ou a '
                      'margem de segurança costuma ser o que devolve resultado.',
                  action: FiButton.secondary(
                    label: 'Limpar filtros',
                    onPressed: () =>
                        ref.read(opportunitiesFiltersProvider.notifier).state =
                            OpportunitiesFilters(search: filters.search),
                  ),
                ),
              ],
            );
          }
          final idade = formatAge(
            oldestStamp(items.map((o) => o.asOf)),
          );
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(
              FiLayout.gutter,
              FiSpace.s2,
              FiLayout.gutter,
              FiLayout.scrollTail,
            ),
            itemCount: items.length + (idade.isEmpty ? 0 : 1),
            separatorBuilder: (_, _) => const SizedBox(height: FiSpace.s2),
            itemBuilder: (context, index) {
              if (idade.isNotEmpty && index == 0) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: FiSpace.s2),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Expanded(child: FiRankingProfile()),
                      const SizedBox(width: FiSpace.s3),
                      Flexible(
                        child: Text(
                          'Cotações lidas $idade',
                          textAlign: TextAlign.end,
                          style: FiType.caption.copyWith(color: fiInk3(context)),
                        ),
                      ),
                    ],
                  ),
                );
              }
              return FiOpportunityObject(
                opportunity: items[idade.isEmpty ? index : index - 1],
              );
            },
          );
        },
      ),
    );
  }
}

class FiOpportunityObject extends StatelessWidget {
  const FiOpportunityObject({super.key, required this.opportunity});

  final Opportunity opportunity;

  @override
  Widget build(BuildContext context) {
    final o = opportunity;

    return FiObject(
      onTap: () => showAssetDetailSheet(context, o.ticker),
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
                    Text(
                      o.ticker,
                      style: FiType.ticker.copyWith(color: fiInk1(context)),
                    ),
                    if (o.name != null)
                      Text(
                        o.name!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: FiType.caption.copyWith(color: fiInk2(context)),
                      ),
                  ],
                ),
              ),
              const SizedBox(width: FiSpace.s3),
              Flexible(child: FiTag(label: o.label, state: fiVerdictState(o.verdict))),
            ],
          ),

          const SizedBox(height: FiSpace.s4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _Figure(label: 'PREÇO', value: formatCurrency(o.price)),
              ),
              Expanded(
                child: _Figure(
                  label: 'JUSTO',
                  value: fairBandEdgeLabel(o.price, o.fairLow, o.fairHigh),
                  glossaryKey: 'faixa_de_preco_justo',
                ),
              ),
              Expanded(
                child: _Figure(
                  label: 'MARGEM',
                  value: formatRatio(o.marginOfSafety),
                  glossaryKey: 'ms',
                ),
              ),
              Expanded(
                child: _Figure(
                  label: 'DY',
                  value: formatPercent(o.dividendYield),
                  glossaryKey: 'dy',
                ),
              ),
            ],
          ),

          const SizedBox(height: FiSpace.s4),
          ScoreRuler(
            score: o.score,
            dataCompleteness: o.dataCompleteness,
            size: ScoreRulerSize.list,
            subject: 'Score de ${o.ticker}',
          ),

          if (o.changePercentDay != null || o.distanceFrom52wHighPct != null) ...[
            const SizedBox(height: FiSpace.s3),
            _Direction(opportunity: o),
          ],

          const SizedBox(height: FiSpace.s3),
          Text(
            [
              if (o.basis == 'trend')
                basisLabel(o.basis)
              else
                fairBandSummary(o.fairLow, o.fairHigh, o.independentInputs),
              if (o.dataYears > 0) 'DY sobre ${dataYearsLabel(o.dataYears)}',
            ].join(' · '),
            style: FiType.axis.copyWith(color: fiInk3(context)),
          ),
        ],
      ),
    );
  }
}

class _Direction extends StatelessWidget {
  const _Direction({required this.opportunity});

  final Opportunity opportunity;

  @override
  Widget build(BuildContext context) {
    final o = opportunity;
    final brightness = Theme.of(context).brightness;
    final dia = o.changePercentDay;
    final doTopo = o.distanceFrom52wHighPct;

    return Row(
      children: [
        if (dia != null) ...[
          Text(
            'hoje ${dia >= 0 ? '+' : ''}${formatPercent(dia)}',
            style: FiType.axis.copyWith(
              color: fiDirectionColor(dia >= 0 ? 1 : -1, brightness),
            ),
          ),
          const SizedBox(width: FiSpace.s3),
        ],
        if (doTopo != null)
          Flexible(
            child: Text(
              doTopo.abs() < 0.5
                  ? 'na máxima de 52 semanas'
                  : '${formatPercent(doTopo.abs())} abaixo da máxima de 52 semanas',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: FiType.axis.copyWith(color: fiInk3(context)),
            ),
          ),
      ],
    );
  }
}

class _Figure extends StatelessWidget {
  const _Figure({required this.label, required this.value, this.glossaryKey});

  final String label;
  final String value;
  final String? glossaryKey;

  @override
  Widget build(BuildContext context) {
    final chave = glossaryKey;

    final figure = Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Text(
        value,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: FiType.figure.copyWith(color: fiInk1(context)),
      ),
    );

    if (chave == null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: FiType.eyebrow.copyWith(color: fiInk3(context)),
          ),
          figure,
        ],
      );
    }

    return HelpTooltip(termKey: chave, label: label, child: figure);
  }
}

class FiRankingProfile extends ConsumerWidget {
  const FiRankingProfile({super.key});

  static const _labels = {
    'conservative': 'conservador',
    'moderate': 'moderado',
    'aggressive': 'arrojado',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prefs = ref.watch(preferencesProvider);

    return prefs.maybeWhen(
      data: (p) {
        final rotulo = _labels[p.riskProfile] ?? p.riskProfile;
        return HelpTooltip(
          termKey: 'perfil_de_risco',
          label: 'perfil $rotulo',
          child: Text(
            'Ordenado pelo seu perfil $rotulo. O carimbo é o do preço mais antigo da lista.',
            style: FiType.caption.copyWith(color: fiInk3(context)),
          ),
        );
      },
      orElse: () => const SizedBox.shrink(),
    );
  }
}
