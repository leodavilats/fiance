import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/format.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/labels.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/chip.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/disclosure.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/help_tooltip.dart';
import '../../core/score_ruler.dart'
    show basisLabel, dataYearsLabel, fairBandEdgeLabel, fairBandLabel, fairBandSummary;
import '../../core/widgets/score_ruler.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import '../../core/widgets/error_state.dart';
import 'asset_detail_sheet.dart';
import '../../core/widgets/controls.dart';

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
    bool clearMinDy = false,
    bool clearMinMos = false,
  }) {
    return OpportunitiesFilters(
      search: search ?? this.search,
      minDy: clearMinDy ? null : (minDy ?? this.minDy),
      minMos: clearMinMos ? null : (minMos ?? this.minMos),
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
    StateProvider.autoDispose.family<OpportunitiesFilters, bool>(
      (ref, dip) => OpportunitiesFilters(onlyDip: dip),
    );

final filteredOpportunitiesProvider =
    FutureProvider.autoDispose.family<List<Opportunity>, bool>((ref, escopo) {
      final f = ref.watch(opportunitiesFiltersProvider(escopo));
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

final dipScanResultProvider =
    FutureProvider.autoDispose.family<List<DipScanItem>, bool>((ref, escopo) {
      final categoria = ref.watch(
        opportunitiesFiltersProvider(escopo).select((f) => f.category),
      );
      return ref
          .watch(apiRepositoryProvider)
          .dipScan(category: categoria.isEmpty ? null : categoria);
    });

class OpportunitiesTab extends ConsumerStatefulWidget {
  const OpportunitiesTab({super.key, this.initialOnlyDip = false, this.header});

  final bool initialOnlyDip;

  final Widget? header;

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
  if (f.search.isNotEmpty) count++;
  if (f.category.isNotEmpty) count++;
  if (f.onlyDip) return count + 1;
  if (f.onlyInteresting) count++;
  if (f.minDy != null) count++;
  if (f.minMos != null) count++;
  if (f.trendDay.isNotEmpty) count++;
  if (f.trendYear.isNotEmpty) count++;
  return count;
}

bool _matchesSearch(String search, String symbol, String? name) {
  final termo = search.trim().toLowerCase();
  if (termo.isEmpty) return true;
  return symbol.toLowerCase().contains(termo) ||
      (name ?? '').toLowerCase().contains(termo);
}

class _OpportunitiesTabState extends ConsumerState<OpportunitiesTab> {
  final _searchCtrl = TextEditingController();

  bool get _escopo => widget.initialOnlyDip;

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _setFilters(OpportunitiesFilters f) =>
      ref.read(opportunitiesFiltersProvider(_escopo).notifier).state = f;

  void _applySearch(String text) {
    final termo = text.trim();
    final atual = ref.read(opportunitiesFiltersProvider(_escopo));
    if (atual.search != termo) _setFilters(atual.copyWith(search: termo));
  }

  void _clearSearch() {
    _searchCtrl.clear();
    _applySearch('');
  }

  void _clearAll() {
    _searchCtrl.clear();
    _setFilters(const OpportunitiesFilters());
  }

  Future<void> _openFilters() async {
    final filters = ref.read(opportunitiesFiltersProvider(_escopo));
    final result = await showModalBottomSheet<OpportunitiesFilters>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.9),
      builder: (context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: _FiltersSheet(initial: filters),
      ),
    );
    if (result == null || !mounted) return;
    if (result.search != filters.search) _searchCtrl.text = result.search;
    _setFilters(result);
  }

  @override
  Widget build(BuildContext context) {
    final filters = ref.watch(opportunitiesFiltersProvider(_escopo));
    final activeCount = _activeFilterCount(filters);
    final dip = filters.onlyDip;

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
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: TickerAutocompleteField(
                      controller: _searchCtrl,
                      labelText: 'Buscar ticker ou nome...',
                      fieldHeight: FiSpace.s12,
                      onChanged: (texto) {
                        if (texto.trim().isEmpty) _applySearch('');
                      },
                      onSubmitted: _applySearch,
                      onSelected: (s) => _applySearch(s.ticker),
                    ),
                  ),
                  const SizedBox(width: FiSpace.s2),
                  SizedBox(
                    height: FiSpace.s12,
                    child: FiButton.secondary(
                      label: activeCount > 0 ? 'Filtros: $activeCount' : 'Filtros',
                      icon: Icons.tune,
                      onPressed: _openFilters,
                    ),
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
                      if (filters.search.isNotEmpty)
                        _ActiveFilterChip(
                          label: 'Busca: ${filters.search}',
                          onDeleted: _clearSearch,
                        ),
                      if (filters.category.isNotEmpty)
                        _ActiveFilterChip(
                          label: _categoryLabels[filters.category] ?? filters.category,
                          onDeleted: () => _setFilters(filters.copyWith(category: '')),
                        ),
                      if (dip)
                        _ActiveFilterChip(
                          label: 'Em queda',
                          onDeleted: () => _setFilters(filters.copyWith(onlyDip: false)),
                        ),
                      if (!dip && filters.onlyInteresting)
                        _ActiveFilterChip(
                          label: 'Destaques',
                          onDeleted: () =>
                              _setFilters(filters.copyWith(onlyInteresting: false)),
                        ),
                      if (!dip && filters.trendDay.isNotEmpty)
                        _ActiveFilterChip(
                          label: fiTrendDayLabels[filters.trendDay] ?? filters.trendDay,
                          onDeleted: () => _setFilters(filters.copyWith(trendDay: '')),
                        ),
                      if (!dip && filters.trendYear.isNotEmpty)
                        _ActiveFilterChip(
                          label: fiTrendYearLabels[filters.trendYear] ?? filters.trendYear,
                          onDeleted: () => _setFilters(filters.copyWith(trendYear: '')),
                        ),
                      if (!dip && filters.minDy != null)
                        _ActiveFilterChip(
                          label:
                              'Dividendos ≥ ${formatPercent(filters.minDy, digits: 1)} ao ano',
                          onDeleted: () => _setFilters(filters.copyWith(clearMinDy: true)),
                        ),
                      if (!dip && filters.minMos != null)
                        _ActiveFilterChip(
                          label: 'Margem de segurança ≥ '
                              '${formatPercent(filters.minMos! * 100, digits: 0)}',
                          onDeleted: () => _setFilters(filters.copyWith(clearMinMos: true)),
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
          child: dip
              ? _DipScannerView(
                  escopo: _escopo,
                  header: widget.header,
                  onClearSearch: _clearSearch,
                )
              : _AllOpportunitiesView(
                  escopo: _escopo,
                  header: widget.header,
                  onClearAll: _clearAll,
                ),
        ),
      ],
    );
  }
}

class DiscoverTools extends StatelessWidget {
  const DiscoverTools({super.key});

  static const _ferramentas = [
    ('Quedas', 'Caiu por quê — e os fundamentos seguem de pé?', '/descobrir/quedas'),
    (
      'Comparar ativos',
      'Entre estes ativos, qual está melhor posicionado?',
      '/descobrir/comparar',
    ),
    (
      'Renda fixa',
      'Entre estes títulos, qual rende mais depois do imposto de renda?',
      '/descobrir/renda-fixa',
    ),
    (
      'Renda fixa × bolsa',
      'Com a Selic nesse patamar, vale mais o CDB ou o fundo imobiliário?',
      '/descobrir/renda-fixa-vs-bolsa',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiDisclosure(
        title: 'Ferramentas',
        detail: 'Quedas, comparar ativos, renda fixa e renda fixa × bolsa',
        child: FiRows(
          children: [
            for (final (nome, pergunta, rota) in _ferramentas)
              FiDataRow(
                label: nome,
                detail: pergunta,
                onTap: () => context.go(rota),
              ),
          ],
        ),
      ),
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
  late String _search = widget.initial.search;
  late String _category = widget.initial.category;
  late bool _onlyDip = widget.initial.onlyDip;
  late bool _onlyInteresting = widget.initial.onlyInteresting;
  late bool _dyEnabled = widget.initial.minDy != null;
  late double _dyValue = widget.initial.minDy ?? 6.0;
  late bool _mosEnabled = widget.initial.minMos != null;
  late double _mosValue = (widget.initial.minMos ?? 0.15) * 100;
  late String _trendDay = widget.initial.trendDay;
  late String _trendYear = widget.initial.trendYear;

  OpportunitiesFilters get _result => _onlyDip
      ? OpportunitiesFilters(search: _search, category: _category, onlyDip: true)
      : OpportunitiesFilters(
          search: _search,
          category: _category,
          onlyInteresting: _onlyInteresting,
          minDy: _dyEnabled ? _dyValue : null,
          minMos: _mosEnabled ? _mosValue / 100 : null,
          trendDay: _trendDay,
          trendYear: _trendYear,
        );

  void _clear() => setState(() {
    _search = '';
    _category = '';
    _onlyDip = false;
    _onlyInteresting = false;
    _dyEnabled = false;
    _mosEnabled = false;
    _trendDay = '';
    _trendYear = '';
  });

  @override
  Widget build(BuildContext context) {
    final ativos = _activeFilterCount(_result);

    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(FiLayout.gutter, 0, FiLayout.gutter, FiSpace.s2),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    'Filtros',
                    style: FiType.title.copyWith(color: fiInk1(context)),
                  ),
                ),
                FiButton.quiet(
                  label: 'Limpar tudo',
                  onPressed: ativos == 0 ? null : _clear,
                ),
              ],
            ),
          ),
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                0,
                FiLayout.gutter,
                FiSpace.s5,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _SheetEyebrow('Classe', first: true),
                  Wrap(
                    spacing: FiSpace.s2,
                    runSpacing: FiSpace.s2,
                    children: [
                      for (final e in _categoryLabels.entries)
                        FiChoiceChip(
                          label: e.value,
                          selected: _category == e.key,
                          onSelected: () => setState(() => _category = e.key),
                        ),
                    ],
                  ),

                  const _SheetEyebrow('O que mostrar'),
                  FiRows(
                    children: [
                      FiDataRow(
                        label: 'Em queda',
                        detail: 'Varredura de ativos que caíram do topo recente',
                        trailing: FiSwitch(
                          label: 'Em queda',
                          value: _onlyDip,
                          onChanged: (v) => setState(() => _onlyDip = v),
                        ),
                      ),
                      FiDataRow(
                        label: 'Somente destaques',
                        detail: _onlyDip ? 'Não se aplica à varredura de quedas' : null,
                        trailing: FiSwitch(
                          label: 'Somente destaques',
                          value: _onlyInteresting && !_onlyDip,
                          onChanged: _onlyDip
                              ? null
                              : (v) => setState(() => _onlyInteresting = v),
                        ),
                      ),
                    ],
                  ),

                  if (_onlyDip) ...[
                    const SizedBox(height: FiSpace.s4),
                    Text(
                      'Na varredura de quedas, só a classe e a busca recortam a lista. '
                      'Variação, posição no ano e fundamentos voltam quando ela sai.',
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),
                  ] else ...[
                    const _SheetEyebrow('Variação de hoje'),
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
                      ],
                    ),

                    const _SheetEyebrow('Posição no ano'),
                    Wrap(
                      spacing: FiSpace.s2,
                      runSpacing: FiSpace.s2,
                      children: [
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
                      'Onde o preço está entre a mínima e a máxima de 52 semanas — não é a '
                      'variação acumulada no ano.',
                      style: FiType.caption.copyWith(color: fiInk3(context)),
                    ),

                    const _SheetEyebrow('Fundamentos'),
                    FiDataRow(
                      label: 'Dividendos mínimos ao ano',
                      value: _dyEnabled ? formatPercent(_dyValue) : null,
                      trailing: FiSwitch(
                        label: 'Dividendos mínimos ao ano',
                        value: _dyEnabled,
                        onChanged: (v) => setState(() => _dyEnabled = v),
                      ),
                    ),
                    if (_dyEnabled)
                      FiSlider(
                        label: 'Dividendos mínimos ao ano',
                        value: _dyValue,
                        min: 0,
                        max: 20,
                        divisions: 40,
                        format: formatPercent,
                        onChanged: (v) => setState(() => _dyValue = v),
                      ),
                    FiDataRow(
                      label: 'Margem de segurança mínima',
                      value: _mosEnabled ? formatPercent(_mosValue) : null,
                      trailing: FiSwitch(
                        label: 'Margem de segurança mínima',
                        value: _mosEnabled,
                        onChanged: (v) => setState(() => _mosEnabled = v),
                      ),
                    ),
                    if (_mosEnabled)
                      FiSlider(
                        label: 'Margem de segurança mínima',
                        value: _mosValue,
                        min: -20,
                        max: 50,
                        divisions: 70,
                        format: formatPercent,
                        onChanged: (v) => setState(() => _mosValue = v),
                      ),
                  ],
                ],
              ),
            ),
          ),
          Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
          Padding(
            padding: const EdgeInsets.fromLTRB(
              FiLayout.gutter,
              FiSpace.s3,
              FiLayout.gutter,
              FiSpace.s3,
            ),
            child: FiButton.primary(
              label: switch (ativos) {
                0 => 'Ver todos',
                1 => 'Aplicar 1 filtro',
                _ => 'Aplicar $ativos filtros',
              },
              expand: true,
              onPressed: () => Navigator.pop(context, _result),
            ),
          ),
        ],
      ),
    );
  }
}

class _SheetEyebrow extends StatelessWidget {
  const _SheetEyebrow(this.text, {this.first = false});

  final String text;
  final bool first;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(top: first ? FiSpace.s2 : FiSpace.s6, bottom: FiSpace.s3),
      child: Text(
        text.toUpperCase(),
        style: FiType.eyebrow.copyWith(color: fiInk3(context)),
      ),
    );
  }
}

class _DipScannerView extends ConsumerWidget {
  const _DipScannerView({
    required this.escopo,
    required this.onClearSearch,
    this.header,
  });

  final bool escopo;
  final VoidCallback onClearSearch;
  final Widget? header;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final result = ref.watch(dipScanResultProvider(escopo));
    final busca = ref.watch(opportunitiesFiltersProvider(escopo).select((f) => f.search));
    final cabecalho = header;

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(dipScanResultProvider(escopo)),
      child: result.when(
        loading: () => FiSkeleton.screen(shape: FiSkeletonShape.row, count: 6, label: 'Varrendo o mercado'),
        error: (err, _) => _ScrollableState(
          header: cabecalho,
          child: FiErrorState(
            error: err,
            action: 'varrer o mercado',
            onRetry: () => ref.invalidate(dipScanResultProvider(escopo)),
          ),
        ),
        data: (todos) {
          final items = todos.where((i) => _matchesSearch(busca, i.symbol, i.name)).toList();
          if (todos.isEmpty) {
            return _ScrollableState(
              header: cabecalho,
              child: const FiEmptyState(
                title: 'Nenhum ativo em queda agora',
                body: 'A varredura mostra quem caiu 15% ou mais da máxima de 52 semanas, com a '
                    'mesma leitura de valor do ativo. Nenhum do universo coberto caiu tanto '
                    'neste momento.',
              ),
            );
          }
          if (items.isEmpty) {
            return _ScrollableState(
              header: cabecalho,
              child: FiEmptyState(
                title: 'Nenhum ativo em queda com esse nome',
                body: 'A varredura achou ${todos.length} em queda, e nenhum responde por '
                    '"$busca".',
                action: FiButton.secondary(label: 'Limpar a busca', onPressed: onClearSearch),
              ),
            );
          }
          final idade = formatAge(oldestStamp(items.map((i) => i.asOf)));
          final antes = [
            ?cabecalho,
            if (idade.isNotEmpty)
              Text(
                'A queda filtra; a leitura de valor ordena. Cotações lidas $idade',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
          ];
          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(
              FiLayout.gutter,
              FiSpace.s2,
              FiLayout.gutter,
              FiLayout.scrollTail,
            ),
            itemCount: items.length + antes.length,
            separatorBuilder: (_, _) => const SizedBox(height: FiSpace.s2),
            itemBuilder: (context, index) {
              if (index < antes.length) return antes[index];
              final item = items[index - antes.length];
              final temFaixa = item.fairLow != null && item.fairHigh != null;

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
                        Flexible(
                          child: FiTag(label: item.label, state: fiVerdictState(item.verdict)),
                        ),
                      ],
                    ),
                    const SizedBox(height: FiSpace.s3),
                    Text(
                      [
                        'Caiu ${formatPercent(item.dropFromHighPct)} da máxima de 52 semanas',
                        if (temFaixa)
                          'preço justo de ${fairBandLabel(item.fairLow, item.fairHigh)}',
                      ].join(' · '),
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

class _ScrollableState extends StatelessWidget {
  const _ScrollableState({required this.child, this.header});

  final Widget child;
  final Widget? header;

  @override
  Widget build(BuildContext context) {
    final cabecalho = header;
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        if (cabecalho != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(FiLayout.gutter, FiSpace.s2, FiLayout.gutter, 0),
            child: cabecalho,
          ),
        child,
      ],
    );
  }
}

class _AllOpportunitiesView extends ConsumerWidget {
  const _AllOpportunitiesView({
    required this.escopo,
    required this.onClearAll,
    this.header,
  });

  final bool escopo;
  final VoidCallback onClearAll;
  final Widget? header;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filters = ref.watch(opportunitiesFiltersProvider(escopo));
    final opportunities = ref.watch(filteredOpportunitiesProvider(escopo));
    final cabecalho = header;

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
      onRefresh: () async => ref.invalidate(filteredOpportunitiesProvider(escopo)),
      child: opportunities.when(
        loading: () => FiSkeleton.screen(shape: FiSkeletonShape.row, count: 6, label: 'Varrendo o mercado'),
        error: (err, _) => _ScrollableState(
          header: cabecalho,
          child: FiErrorState(
            error: err,
            action: 'varrer o mercado',
            onRetry: () => ref.invalidate(filteredOpportunitiesProvider(escopo)),
          ),
        ),
        data: (_) {
          if (items.isEmpty) {
            return _ScrollableState(
              header: cabecalho,
              child: _EmptyOpportunities(filters: filters, onClearAll: onClearAll),
            );
          }
          final idade = formatAge(
            oldestStamp(items.map((o) => o.asOf)),
          );
          final antes = [
            ?cabecalho,
            if (idade.isNotEmpty)
              Padding(
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
              ),
          ];
          return ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(
              FiLayout.gutter,
              FiSpace.s2,
              FiLayout.gutter,
              FiLayout.scrollTail,
            ),
            itemCount: items.length + antes.length,
            separatorBuilder: (_, _) => const SizedBox(height: FiSpace.s2),
            itemBuilder: (context, index) {
              if (index < antes.length) return antes[index];
              return FiOpportunityObject(opportunity: items[index - antes.length]);
            },
          );
        },
      ),
    );
  }
}

class _EmptyOpportunities extends StatelessWidget {
  const _EmptyOpportunities({required this.filters, required this.onClearAll});

  final OpportunitiesFilters filters;
  final VoidCallback onClearAll;

  @override
  Widget build(BuildContext context) {
    final busca = filters.search;
    final outros = _activeFilterCount(filters) - (busca.isEmpty ? 0 : 1);
    final limpar = FiButton.secondary(
      label: outros > 0 ? 'Limpar filtros' : 'Limpar a busca',
      onPressed: onClearAll,
    );

    if (busca.isNotEmpty) {
      return FiEmptyState(
        title: 'Nenhum ativo com esse nome',
        body: outros > 0
            ? 'Nada responde por "$busca" com os filtros ligados. Pode ser o nome, ou '
                  'um dos filtros cortando o ativo.'
            : 'Nada no universo coberto responde por "$busca". Confira o ticker, ou '
                  'busque pelo nome da empresa.',
        action: limpar,
      );
    }
    if (outros > 0) {
      return FiEmptyState(
        title: 'Nenhum ativo passa nos filtros',
        body: 'O corte atual não deixou nada passar. Tirar um filtro de cada vez mostra '
            'qual deles esvaziou a lista.',
        action: limpar,
      );
    }
    return const FiEmptyState(
      title: 'Nenhum ativo na lista agora',
      body: 'O universo coberto ainda não tem leitura para mostrar. Puxe para atualizar '
          'em instantes.',
    );
  }
}

class FiOpportunityObject extends StatelessWidget {
  const FiOpportunityObject({super.key, required this.opportunity});

  final Opportunity opportunity;

  @override
  Widget build(BuildContext context) {
    final o = opportunity;
    final temFaixa = o.fairLow != null && o.fairHigh != null;
    final rodape = [
      if (o.basis == 'trend')
        basisLabel(o.basis)
      else if (temFaixa)
        fairBandSummary(o.fairLow, o.fairHigh, o.independentInputs),
      if (o.dataYears > 0) 'Dividendos sobre ${dataYearsLabel(o.dataYears)}',
    ];

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

          if (rodape.isNotEmpty) ...[
            const SizedBox(height: FiSpace.s3),
            Text(
              rodape.join(' · '),
              style: FiType.axis.copyWith(color: fiInk3(context)),
            ),
          ],
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
