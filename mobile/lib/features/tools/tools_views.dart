library;

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/widgets/range.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/compare_metrics.dart';
import '../../core/score_ruler.dart'
    show consensusLabel, dataYearsLabel, trendBasisLabel;
import '../../core/widgets/button.dart';
import '../../core/widgets/measure.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import '../mes/widgets/feed_tiles.dart';

class AnalyzeAssetView extends ConsumerStatefulWidget {
  const AnalyzeAssetView({super.key, this.initialTicker});

  final String? initialTicker;

  @override
  ConsumerState<AnalyzeAssetView> createState() => AnalyzeAssetViewState();
}

class AnalyzeAssetViewState extends ConsumerState<AnalyzeAssetView> {
  final _tickerCtrl = TextEditingController();
  bool _loading = false;
  AssetAnalysis? _result;
  String? _error;

  @override
  void initState() {
    super.initState();
    final ticker = widget.initialTicker;
    if (ticker != null && ticker.isNotEmpty) {
      _tickerCtrl.text = ticker.toUpperCase();
      WidgetsBinding.instance.addPostFrameCallback((_) => _analyze());
    }
  }

  Future<void> _analyze() async {
    final ticker = _tickerCtrl.text.trim().toUpperCase();
    if (ticker.isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref.read(apiRepositoryProvider).analyzeAsset(ticker);
      setState(() => _result = result);
    } catch (e) {
      setState(() {
        _error = e is DioException && e.response?.statusCode == 404
            ? 'Não encontramos $ticker. O fiance cobre ações da B3, FIIs, BDRs e ETFs.'
            : 'Não conseguimos analisar $ticker agora. Pode ser a conexão ou uma '
                  'instabilidade na fonte de cotações.';
        _result = null;
      });
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s3,
        FiLayout.gutter,
        FiLayout.scrollTail,
      ),
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: TextField(
                controller: _tickerCtrl,
                textCapitalization: TextCapitalization.characters,
                decoration: const InputDecoration(
                  labelText: 'Ticker',
                  hintText: 'PETR4, HGLG11, IVVB11…',
                ),
                onSubmitted: (_) => _analyze(),
              ),
            ),
            const SizedBox(width: FiSpace.s2),
            FiButton.primary(
              label: 'Analisar',
              busy: _loading,
              onPressed: _analyze,
            ),
          ],
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: FiSpace.s4),
            child: Text(
              _error!,
              style: FiType.body.copyWith(
                color: fiStateColor(
                  FiState.adverse,
                  Theme.of(context).brightness,
                ),
              ),
            ),
          ),
        if (_loading && _result == null)
          const Padding(
            padding: EdgeInsets.only(top: FiSpace.s6),
            child: FiSkeleton(shape: FiSkeletonShape.verdict, count: 2),
          ),
        if (_result != null) _AssetAnalysis(analysis: _result!),
      ],
    );
  }
}

class _AssetAnalysis extends StatelessWidget {
  const _AssetAnalysis({required this.analysis});

  final AssetAnalysis analysis;

  @override
  Widget build(BuildContext context) {
    final a = analysis;
    final idade = formatIdade(a.asOf);
    final estado = fiVerdictState(a.verdict);
    final margem = a.marginOfSafety;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: FiSpace.s6),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    a.symbol,
                    style: FiType.pageTitle.copyWith(color: fiInk1(context)),
                  ),
                  if (a.name != null)
                    Text(
                      a.name!,
                      style: FiType.body.copyWith(color: fiInk2(context)),
                    ),
                ],
              ),
            ),
            const SizedBox(width: FiSpace.s3),
            FiTag(label: a.label, state: estado),
          ],
        ),

        const SizedBox(height: FiSpace.s4),
        FiHeadline(
          eyebrow: 'Preço',
          figure: formatCurrency(a.price),
          note: idade.isEmpty ? null : 'lido $idade',
        ),

        if (margem != null) ...[
          const SizedBox(height: FiSpace.s5),
          Builder(
            builder: (context) {
              final pct = margem * 100;
              final band = fiBandFor(pct, fiMarginOfSafetyBands);
              return FiMeasure(
                label: 'Margem de segurança',
                value: pct,
                min: fiMarginOfSafetyDomain.min,
                max: fiMarginOfSafetyDomain.max,
                reference: 0,
                readout: formatRatio(margem),
                note: '${band.label} · preço justo ${formatCurrency(a.consensus)}, '
                    '${consensusLabel(a.consensusMethods)}',
                state: band.state,
              );
            },
          ),
        ],

        FiSection(
          title: 'A evidência',
          child: FiRows(
            children: [
              FiDataRow(
                label: 'Preço justo',
                value: formatCurrency(a.consensus),
                note: consensusLabel(a.consensusMethods),
              ),
              FiDataRow(
                label: 'Tendência',
                value: trendLabel(a.trend),
                note: trendBasisLabel(a.trendBasis),
              ),
              FiDataRow(
                label: 'Força relativa (RSI 14)',
                value: a.rsi14?.toStringAsFixed(1) ?? '—',
              ),
              FiDataRow(
                label: 'Dividendos',
                value: formatRatio(a.dividendYield),
                note: dataYearsLabel(a.dataYears),
              ),
            ],
          ),
        ),

        if (a.reasons.isNotEmpty)
          FiSection(
            title: 'Por que esta leitura',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final r in a.reasons)
                  Padding(
                    padding: const EdgeInsets.only(bottom: FiSpace.s3),
                    child: Text(
                      r,
                      style: FiType.body.copyWith(color: fiInk2(context)),
                    ),
                  ),
              ],
            ),
          ),

        const SizedBox(height: FiSpace.s3),
        FiProvenance(
          summary: 'Como chegamos nesta leitura',
          method:
              'O preço justo é o consenso dos métodos aplicáveis ao papel; a margem de '
              'segurança é a distância entre o preço de hoje e esse consenso.',
          source: 'Fundamentos e cotações da BRAPI.',
          asOf: idade.isEmpty ? null : 'Preço lido $idade.',
          limitation:
              'É leitura do sistema sobre dado público, não recomendação. Método com histórico '
              'curto entra no consenso com menos peso, e o número de métodos vem escrito.',
        ),
      ],
    );
  }
}

class _RendaFixaOption {
  String tipo = 'cdb';
  String nome = '';
  double valor = 1000;
  double taxa = 110;
  int prazoMeses = 12;
  String tipoTaxa = 'pos_fixado';
}

class RendaFixaSimulatorView extends ConsumerStatefulWidget {
  const RendaFixaSimulatorView({super.key});

  @override
  ConsumerState<RendaFixaSimulatorView> createState() =>
      RendaFixaSimulatorViewState();
}

class RendaFixaSimulatorViewState
    extends ConsumerState<RendaFixaSimulatorView> {
  final List<_RendaFixaOption> _options = [_RendaFixaOption()];
  List<RendaFixaResult>? _results;
  bool _loading = false;
  String? _error;

  static const _tipos = {
    'cdb': 'CDB',
    'lci': 'LCI',
    'lca': 'LCA',
    'tesouro_selic': 'Tesouro Selic',
    'tesouro_ipca': 'Tesouro IPCA+',
    'tesouro_pre': 'Tesouro Pré',
    'cri': 'CRI',
    'cra': 'CRA',
  };

  Future<void> _compare() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await ref
          .read(apiRepositoryProvider)
          .compareRendaFixa(
            _options
                .map(
                  (o) => {
                    'tipo': o.tipo,
                    'nome': o.nome.isEmpty ? null : o.nome,
                    'valor_investido': o.valor,
                    'taxa': o.taxa,
                    'prazo_meses': o.prazoMeses,
                    'tipo_taxa': o.tipoTaxa,
                    if (o.tipoTaxa == 'pos_fixado') 'percentual_cdi': o.taxa,
                  },
                )
                .toList(),
          );
      setState(() => _results = results);
    } catch (e) {
      setState(() => _error = 'Erro ao comparar: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final rates = ref.watch(_ratesProvider);

    final brightness = Theme.of(context).brightness;

    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s3,
        FiLayout.gutter,
        FiLayout.scrollTail,
      ),
      children: [
        rates.when(
          loading: () => const SizedBox.shrink(),
          error: (_, _) => const SizedBox.shrink(),
          data: (r) => Padding(
            padding: const EdgeInsets.only(bottom: FiSpace.s5),
            child: FiFigures(
              rule: false,
              figures: {
                'CDI': formatPercent(r.cdiAnual),
                'SELIC': formatPercent(r.selicAnual),
                'IPCA': formatPercent(r.ipcaAnual),
              },
            ),
          ),
        ),
        ...List.generate(
          _options.length,
          (i) => _OptionForm(
            option: _options[i],
            ordem: i + 1,
            tipos: _tipos,
            onRemove: _options.length > 1
                ? () => setState(() => _options.removeAt(i))
                : null,
            onChanged: () => setState(() {}),
          ),
        ),
        const SizedBox(height: FiSpace.s2),
        Align(
          alignment: Alignment.centerLeft,
          child: FiButton.quiet(
            label: 'Adicionar outro título',
            icon: Icons.add,
            onPressed: () => setState(() => _options.add(_RendaFixaOption())),
          ),
        ),
        const SizedBox(height: FiSpace.s5),
        FiButton.primary(
          label: 'Comparar depois do IR',
          expand: true,
          busy: _loading,
          onPressed: _compare,
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: FiSpace.s4),
            child: Text(
              _error!,
              style: FiType.body.copyWith(
                color: fiStateColor(FiState.adverse, brightness),
              ),
            ),
          ),
        if (_results != null)
          FiSection(
            title: 'Resultado',
            hint: 'Já descontado o IR de cada título, no prazo informado.',
            child: Column(
              children: [
                for (final r in _results!)
                  Padding(
                    padding: const EdgeInsets.only(bottom: FiSpace.s2),
                    child: FiObject(
                      accent: r.melhorOpcao
                          ? fiStateColor(FiState.favorable, brightness)
                          : null,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  '${_tipos[r.tipo] ?? r.tipo}'
                                  '${r.nome != null ? ' · ${r.nome}' : ''}',
                                  style: FiType.title.copyWith(
                                    color: fiInk1(context),
                                  ),
                                ),
                              ),
                              if (r.melhorOpcao)
                                const FiTag(
                                  label: 'Rende mais',
                                  state: FiState.favorable,
                                ),
                            ],
                          ),
                          const SizedBox(height: FiSpace.s3),
                          FiFigures(
                            rule: false,
                            figures: {
                              'LÍQUIDO': formatCurrency(r.valorLiquido),
                              'TAXA LÍQUIDA': formatPercent(r.taxaLiquidaAa),
                            },
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

final _ratesProvider = FutureProvider.autoDispose<ReferenceRates>((ref) {
  return ref.watch(apiRepositoryProvider).getRendaFixaRates();
});

class _OptionForm extends StatelessWidget {
  const _OptionForm({
    required this.option,
    required this.ordem,
    required this.tipos,
    required this.onChanged,
    this.onRemove,
  });

  final _RendaFixaOption option;
  final int ordem;
  final Map<String, String> tipos;
  final VoidCallback onChanged;
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s3),
      child: FiObject(
        padding: const EdgeInsets.all(FiSpace.s3),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'TÍTULO $ordem',
              style: FiType.eyebrow.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s2),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: option.tipo,
                    decoration: const InputDecoration(
                      labelText: 'Tipo',
                      isDense: true,
                    ),
                    items: tipos.entries
                        .map(
                          (e) => DropdownMenuItem(
                            value: e.key,
                            child: Text(e.value),
                          ),
                        )
                        .toList(),
                    onChanged: (v) {
                      option.tipo = v!;
                      option.tipoTaxa = (v == 'tesouro_ipca')
                          ? 'hibrido'
                          : (v == 'tesouro_pre')
                          ? 'pre_fixado'
                          : 'pos_fixado';
                      onChanged();
                    },
                  ),
                ),
                if (onRemove != null)
                  IconButton(
                    onPressed: onRemove,
                    tooltip: 'Remover o título $ordem da comparação',
                    icon: const Icon(Icons.delete_outline),
                  ),
              ],
            ),
            const SizedBox(height: FiSpace.s2),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    initialValue: option.valor.toStringAsFixed(0),
                    decoration: const InputDecoration(
                      labelText: 'Valor (R\$)',
                      isDense: true,
                    ),
                    keyboardType: TextInputType.number,
                    onChanged: (v) =>
                        option.valor = double.tryParse(v) ?? option.valor,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextFormField(
                    initialValue: option.taxa.toStringAsFixed(0),
                    decoration: InputDecoration(
                      labelText: option.tipoTaxa == 'pos_fixado'
                          ? '% do CDI'
                          : 'Taxa % a.a.',
                      isDense: true,
                    ),
                    keyboardType: TextInputType.number,
                    onChanged: (v) =>
                        option.taxa = double.tryParse(v) ?? option.taxa,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextFormField(
                    initialValue: option.prazoMeses.toString(),
                    decoration: const InputDecoration(
                      labelText: 'Prazo (meses)',
                      isDense: true,
                    ),
                    keyboardType: TextInputType.number,
                    onChanged: (v) => option.prazoMeses =
                        int.tryParse(v) ?? option.prazoMeses,
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

const _maxCompareTickers = 4;

class CompareAssetsView extends ConsumerStatefulWidget {
  const CompareAssetsView({super.key});

  @override
  ConsumerState<CompareAssetsView> createState() => CompareAssetsViewState();
}

class CompareAssetsViewState extends ConsumerState<CompareAssetsView> {
  final _tickerCtrl = TextEditingController();
  final List<String> _tickers = [];
  bool _loading = false;
  CompareResponse? _result;
  String? _error;

  void _addTicker(String ticker) {
    final t = ticker.trim().toUpperCase();
    if (t.isEmpty ||
        _tickers.contains(t) ||
        _tickers.length >= _maxCompareTickers) {
      return;
    }
    setState(() {
      _tickers.add(t);
      _tickerCtrl.clear();
    });
  }

  Future<void> _compare() async {
    if (_tickers.length < 2) {
      setState(() => _error = 'Adicione ao menos 2 ativos para comparar.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref
          .read(apiRepositoryProvider)
          .compareAssets(_tickers);
      setState(() => _result = result);
    } catch (e) {
      setState(() => _error = 'Não foi possível comparar os ativos agora.');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s3,
        FiLayout.gutter,
        FiLayout.scrollTail,
      ),
      children: [
        Text(
          'Compare até $_maxCompareTickers ativos lado a lado.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s3),
        Wrap(
          spacing: FiSpace.s2,
          runSpacing: FiSpace.s2,
          children: _tickers
              .map(
                (t) => Chip(
                  label: Text(t),
                  onDeleted: () => setState(() => _tickers.remove(t)),
                ),
              )
              .toList(),
        ),
        if (_tickers.length < _maxCompareTickers) ...[
          const SizedBox(height: FiSpace.s3),
          TickerAutocompleteField(
            controller: _tickerCtrl,
            labelText: 'Adicionar ticker',
            onSelected: (s) => _addTicker(s.ticker),
          ),
        ],
        const SizedBox(height: FiSpace.s5),
        FiButton.primary(
          label: 'Comparar',
          expand: true,
          busy: _loading,
          onPressed: _compare,
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: FiSpace.s4),
            child: Text(
              _error!,
              style: FiType.body.copyWith(
                color: fiStateColor(
                  FiState.adverse,
                  Theme.of(context).brightness,
                ),
              ),
            ),
          ),
        if (_result != null) ...[
          if (_result!.errors.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: FiSpace.s4),
              child: Text(
                'Não foi possível buscar: ${_result!.errors.join(', ')}',
                style: FiType.caption.copyWith(
                  color: fiStateColor(
                    FiState.attention,
                    Theme.of(context).brightness,
                  ),
                ),
              ),
            ),
          if (_result!.items.isNotEmpty) _CompareTable(items: _result!.items),
        ],
      ],
    );
  }
}

class _CompareDecisions extends StatelessWidget {
  const _CompareDecisions({required this.items});

  final List<AssetAnalysis> items;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'A DECISÃO',
          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
        ),
        const SizedBox(height: FiSpace.s3),
        FiRows(
          children: [
            for (final a in items)
              FiDataRow(
                label: a.symbol,
                detail: '${fiAssetTypeLabel[a.assetType] ?? a.assetType} · margem de '
                    'segurança ${formatRatio(a.marginOfSafety)}',
                note: consensusLabel(a.consensusMethods),
                trailing: FiVerdictChip(verdict: a.verdict, label: a.label),
              ),
          ],
        ),
      ],
    );
  }
}

class _CompareTable extends StatelessWidget {
  const _CompareTable({required this.items});

  final List<AssetAnalysis> items;

  @override
  Widget build(BuildContext context) {
    final groups = ['Valuation', 'Qualidade', 'Risco', 'Proventos'];
    final muted = Theme.of(context).textTheme.bodySmall;

    final rows = <DataRow>[];
    for (final group in groups) {
      final metrics = fiCompareMetrics.where((m) => m.group == group).toList();
      if (metrics.isEmpty) continue;
      rows.add(
        DataRow(
          cells: [
            DataCell(
              Text(
                group.toUpperCase(),
                style: FiType.eyebrow.copyWith(color: fiInk3(context)),
              ),
            ),
            ...items.map((_) => const DataCell(Text(''))),
          ],
        ),
      );
      for (final m in metrics) {
        rows.add(
          DataRow(
            cells: [
              DataCell(Text(m.label)),
              ...items.map((a) {
                final applies = m.appliesTo.contains(a.assetType);
                if (!applies) {
                  return DataCell(
                    Text(
                      'não se aplica a ${fiAssetTypeLabel[a.assetType] ?? a.assetType}',
                      style: muted,
                    ),
                  );
                }
                return DataCell(Text(m.render(a)));
              }),
            ],
          ),
        );
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: FiSpace.s8),
        _CompareDecisions(items: items),
        const SizedBox(height: FiSpace.s8),
        Text(
          'A EVIDÊNCIA',
          style: FiType.eyebrow.copyWith(color: fiInk3(context)),
        ),
        const SizedBox(height: FiSpace.s3),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columns: [
              const DataColumn(label: Text('Indicador')),
              ...items.map((a) => DataColumn(label: Text(a.symbol))),
            ],
            rows: rows,
          ),
        ),
      ],
    );
  }
}

class ContributionSimulatorView extends ConsumerStatefulWidget {
  const ContributionSimulatorView({super.key});

  @override
  ConsumerState<ContributionSimulatorView> createState() =>
      ContributionSimulatorViewState();
}

class ContributionSimulatorViewState
    extends ConsumerState<ContributionSimulatorView> {
  final _contributionCtrl = TextEditingController(text: '500');
  final _monthsCtrl = TextEditingController(text: '60');
  final _growthCtrl = TextEditingController(text: '10');
  final _divGrowthCtrl = TextEditingController(text: '5');
  final _targetCtrl = TextEditingController();
  bool _reinvest = true;
  bool _loading = false;
  PassiveIncomeProjection? _result;

  double? _parseDecimal(String text) =>
      double.tryParse(text.trim().replaceAll(',', '.'));

  Future<void> _simulate() async {
    setState(() => _loading = true);
    try {
      final result = await ref
          .read(apiRepositoryProvider)
          .projectPassiveIncome(
            monthlyContribution: _parseDecimal(_contributionCtrl.text) ?? 0,
            monthsAhead: int.tryParse(_monthsCtrl.text) ?? 60,
            portfolioGrowthRate: (_parseDecimal(_growthCtrl.text) ?? 10) / 100,
            dividendGrowthRate: (_parseDecimal(_divGrowthCtrl.text) ?? 5) / 100,
            reinvestDividends: _reinvest,
            targetMonthlyIncome: _parseDecimal(_targetCtrl.text),
          );
      setState(() => _result = result);
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s3,
        FiLayout.gutter,
        FiLayout.scrollTail,
      ),
      children: [
        Text(
          'Simule um aporte mensal recorrente e veja a evolução da sua carteira e renda passiva.',
          style: FiType.body.copyWith(color: fiInk2(context)),
        ),
        const SizedBox(height: FiSpace.s5),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _contributionCtrl,
                decoration: const InputDecoration(
                  labelText: 'Aporte mensal (R\$)',
                ),
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
              ),
            ),
            const SizedBox(width: FiSpace.s2),
            Expanded(
              child: TextField(
                controller: _monthsCtrl,
                decoration: const InputDecoration(labelText: 'Meses'),
                keyboardType: TextInputType.number,
              ),
            ),
          ],
        ),
        const SizedBox(height: FiSpace.s3),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _growthCtrl,
                decoration: const InputDecoration(
                  labelText: 'Valorização anual (%)',
                ),
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
              ),
            ),
            const SizedBox(width: FiSpace.s2),
            Expanded(
              child: TextField(
                controller: _divGrowthCtrl,
                decoration: const InputDecoration(
                  labelText: 'Crescimento dividendos (%)',
                ),
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: FiSpace.s3),
        TextField(
          controller: _targetCtrl,
          decoration: const InputDecoration(
            labelText: 'Meta de renda passiva/mês (opcional)',
          ),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
        ),
        const SizedBox(height: FiSpace.s2),
        FiDataRow(
          label: 'Reinvestir dividendos',
          detail: 'O provento recebido volta para a carteira no mês seguinte',
          trailing: Switch(
            value: _reinvest,
            onChanged: (v) => setState(() => _reinvest = v),
          ),
        ),
        const SizedBox(height: FiSpace.s5),
        FiButton.primary(
          label: 'Projetar',
          expand: true,
          busy: _loading,
          onPressed: _simulate,
        ),
        if (_result != null) ..._buildResult(_result!),
      ],
    );
  }

  List<Widget> _buildResult(PassiveIncomeProjection r) {
    final last = r.projections.last;

    return [
      FiSection(
        title: 'De onde parte',
        child: FiFigures(
          rule: false,
          figures: {
            'CARTEIRA HOJE': formatCurrency(r.currentPortfolioValue),
            'RENDA PASSIVA HOJE': formatCurrency(r.currentPassiveIncomeMonthly),
          },
        ),
      ),

      FiSection(
        title: 'Onde chega',
        hint: 'A faixa é o número: piso e teto saem dos cenários, e o centro é só um deles.',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            FiRange(
              label: 'Carteira no fim',
              low: last.portfolioValueLow,
              high: last.portfolioValueHigh,
              base: last.portfolioValue,
            ),
            const SizedBox(height: FiSpace.s4),
            FiRange(
              label: 'Renda passiva por mês no fim',
              low: last.passiveIncomeMonthlyLow,
              high: last.passiveIncomeMonthlyHigh,
              base: last.passiveIncomeMonthly,
            ),
          ],
        ),
      ),

      FiSection(
        title: 'Os cenários',
        child: FiRows(
          children: [
            for (final cenario in r.scenarios)
              FiDataRow(
                label: cenario.label,
                value: '${formatCurrency(cenario.finalPassiveIncomeMonthly)}/mês',
                note: cenario.rationale,
              ),
          ],
        ),
      ),

      if (r.target != null) ...[
        const SizedBox(height: FiSpace.s6),
        Text(
          _textoDaMeta(r.target!),
          style: fiSerif(FiType.verdictSm).copyWith(color: fiInk1(context)),
        ),
      ],

      const SizedBox(height: FiSpace.s5),
      Text(
        r.disclaimer.isNotEmpty
            ? r.disclaimer
            : 'Projeção educativa sobre premissas que você escolheu. Não há garantia de '
                  'rentabilidade futura.',
        style: FiType.caption.copyWith(color: fiInk3(context)),
      ),
    ];
  }

  String _textoDaMeta(ProjectionTarget meta) {
    final valor = formatCurrency(meta.monthlyIncome);
    if (meta.reachedInAllScenarios) {
      return 'Meta de $valor/mês: alcançada entre ${meta.earliestMonths} e '
          '${meta.latestMonths} meses. No cenário base, ${meta.expectedMonths} meses.';
    }
    if (meta.expectedMonths != null) {
      return 'Meta de $valor/mês: ${meta.expectedMonths} meses no cenário base, mas não '
          'alcançada no cenário conservador dentro do período simulado.';
    }
    return 'Meta de $valor/mês: não alcançada em nenhum dos três cenários dentro do '
        'período simulado. Aumentar o aporte ou o prazo muda isso; mudar a premissa '
        'de valorização não.';
  }
}
