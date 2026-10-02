library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/widgets/range.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/compare_metrics.dart';
import '../../core/score_ruler.dart' show confirmationLabel;
import '../../core/widgets/button.dart';
import '../../core/widgets/chip.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';
import '../month/widgets/feed_tiles.dart';
import '../../core/widgets/controls.dart';

class _FixedIncomeOption {
  String kind = 'cdb';
  String name = '';
  double amount = 1000;
  double rate = 110;
  int termMonths = 12;
  String rateKind = 'pos_fixado';
}

String _rateKindFor(String kind) => switch (kind) {
  'tesouro_ipca' => 'hibrido',
  'tesouro_pre' => 'pre_fixado',
  _ => 'pos_fixado',
};

double _defaultRateFor(String rateKind, ReferenceRates? rates) => switch (rateKind) {
  'pre_fixado' => (rates?.cdiAnnual ?? 12).roundToDouble(),
  'hibrido' => 6,
  _ => 100,
};

class FixedIncomeSimulatorView extends ConsumerStatefulWidget {
  const FixedIncomeSimulatorView({super.key});

  @override
  ConsumerState<FixedIncomeSimulatorView> createState() =>
      FixedIncomeSimulatorViewState();
}

class FixedIncomeSimulatorViewState
    extends ConsumerState<FixedIncomeSimulatorView> {
  final _formKey = GlobalKey<FormState>();
  final List<_FixedIncomeOption> _options = [_FixedIncomeOption()];
  List<FixedIncomeResult>? _results;
  bool _loading = false;
  Object? _error;

  static const _kinds = {
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
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await ref
          .read(apiRepositoryProvider)
          .compareFixedIncome(
            _options
                .map(
                  (o) => {
                    'tipo': o.kind,
                    'nome': o.name.isEmpty ? null : o.name,
                    'valor_investido': o.amount,
                    'taxa': o.rate,
                    'prazo_meses': o.termMonths,
                    'tipo_taxa': o.rateKind,
                    if (o.rateKind == 'pos_fixado') 'percentual_cdi': o.rate,
                  },
                )
                .toList(),
          );
      if (!mounted) return;
      setState(() => _results = results);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _results = null;
        _error = e;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _changed() => setState(() => _results = null);

  @override
  Widget build(BuildContext context) {
    final rates = ref.watch(_ratesProvider);

    final brightness = Theme.of(context).brightness;
    final erro = _error;

    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s3,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: [
          rates.when(
            loading: () => const Padding(
              padding: EdgeInsets.only(bottom: FiSpace.s5),
              child: FiSkeleton(shape: FiSkeletonShape.caption),
            ),
            error: (e, _) => Padding(
              padding: const EdgeInsets.only(bottom: FiSpace.s5),
              child: Text(
                fiErrorMessage(e, action: 'ler as taxas de referência'),
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ),
            data: (r) => Padding(
              padding: const EdgeInsets.only(bottom: FiSpace.s5),
              child: FiFigures(
                rule: false,
                figures: {
                  'CDI': formatPercent(r.cdiAnnual),
                  'SELIC': formatPercent(r.selicAnnual),
                  'IPCA': formatPercent(r.ipcaAnnual),
                },
              ),
            ),
          ),
          for (var i = 0; i < _options.length; i++)
            _OptionForm(
              key: ObjectKey(_options[i]),
              option: _options[i],
              index: i + 1,
              kinds: _kinds,
              rates: rates.valueOrNull,
              onRemove: _options.length > 1
                  ? () => setState(() {
                      _options.removeAt(i);
                      _results = null;
                    })
                  : null,
              onChanged: _changed,
            ),
          const SizedBox(height: FiSpace.s2),
          Align(
            alignment: Alignment.centerLeft,
            child: FiButton.quiet(
              label: 'Adicionar outro título',
              icon: Icons.add,
              onPressed: () => setState(() {
                _options.add(_FixedIncomeOption());
                _results = null;
              }),
            ),
          ),
          const SizedBox(height: FiSpace.s5),
          FiButton.primary(
            label: 'Comparar depois do IR',
            expand: true,
            busy: _loading,
            onPressed: _compare,
          ),
          if (erro != null)
            FiErrorState(
              error: erro,
              title: 'A comparação não saiu',
              action: 'comparar os títulos',
              onRetry: _compare,
            ),
          if (_results case final resultados?)
            FiSection(
              title: 'Resultado',
              hint: 'Já descontado o imposto de renda de cada título, no prazo informado.',
              child: Column(
                children: [
                  for (final r in resultados)
                    Padding(
                      padding: const EdgeInsets.only(bottom: FiSpace.s2),
                      child: FiObject(
                        accent: r.bestOption
                            ? fiStateColor(FiState.favorable, brightness)
                            : null,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    '${_kinds[r.kind] ?? r.kind}'
                                    '${r.name != null ? ' · ${r.name}' : ''}',
                                    style: FiType.title.copyWith(
                                      color: fiInk1(context),
                                    ),
                                  ),
                                ),
                                if (r.bestOption)
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
                                'LÍQUIDO': formatCurrency(r.netValue),
                                'TAXA LÍQUIDA': formatPercent(r.netAnnualRate),
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
      ),
    );
  }
}

final _ratesProvider = FutureProvider.autoDispose<ReferenceRates>((ref) {
  return ref.watch(apiRepositoryProvider).getFixedIncomeRates();
});

class _OptionForm extends StatelessWidget {
  const _OptionForm({
    super.key,
    required this.option,
    required this.index,
    required this.kinds,
    required this.onChanged,
    this.rates,
    this.onRemove,
  });

  final _FixedIncomeOption option;
  final int index;
  final Map<String, String> kinds;
  final VoidCallback onChanged;
  final ReferenceRates? rates;
  final VoidCallback? onRemove;

  static const _teclado = TextInputType.numberWithOptions(decimal: true);

  String? _validateAmount(String? v) {
    final valor = parseDecimal(v);
    if (valor == null) return 'Informe o valor, como 1.000 ou 1.500,50';
    if (valor <= 0) return 'O valor precisa ser maior que zero';
    return null;
  }

  String? _validateRate(String? v) {
    final taxa = parseDecimal(v);
    if (taxa == null) return 'Informe a taxa, como 110 ou 12,5';
    if (taxa <= 0) return 'A taxa precisa ser maior que zero';
    if (option.rateKind != 'pos_fixado' && taxa > 100) {
      return 'Taxa ao ano acima de 100%: confira o número';
    }
    return null;
  }

  String? _validateTerm(String? v) {
    final prazo = int.tryParse((v ?? '').trim());
    if (prazo == null || prazo < 1) return 'Prazo em meses inteiros, a partir de 1';
    return null;
  }

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
              'TÍTULO $index',
              style: FiType.eyebrow.copyWith(color: fiInk3(context)),
            ),
            const SizedBox(height: FiSpace.s2),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: option.kind,
                    decoration: const InputDecoration(
                      labelText: 'Tipo',
                      isDense: true,
                    ),
                    items: kinds.entries
                        .map(
                          (e) => DropdownMenuItem(
                            value: e.key,
                            child: Text(e.value),
                          ),
                        )
                        .toList(),
                    onChanged: (v) {
                      if (v == null) return;
                      final novoTipoDeTaxa = _rateKindFor(v);
                      if (novoTipoDeTaxa != option.rateKind) {
                        option.rate = _defaultRateFor(novoTipoDeTaxa, rates);
                      }
                      option.kind = v;
                      option.rateKind = novoTipoDeTaxa;
                      onChanged();
                    },
                  ),
                ),
                if (onRemove != null)
                  IconButton(
                    onPressed: onRemove,
                    tooltip: 'Remover o título $index da comparação',
                    icon: const Icon(Icons.delete_outline),
                  ),
              ],
            ),
            const SizedBox(height: FiSpace.s2),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: TextFormField(
                    initialValue: formatForInput(option.amount),
                    decoration: const InputDecoration(
                      labelText: 'Valor (R\$)',
                      isDense: true,
                      errorMaxLines: 3,
                    ),
                    keyboardType: _teclado,
                    autovalidateMode: AutovalidateMode.onUserInteraction,
                    validator: _validateAmount,
                    onChanged: (v) {
                      final valor = parseDecimal(v);
                      if (valor != null && valor > 0) option.amount = valor;
                      onChanged();
                    },
                  ),
                ),
                const SizedBox(width: FiSpace.s2),
                Expanded(
                  child: TextFormField(
                    key: ValueKey(option.rateKind),
                    initialValue: formatForInput(option.rate),
                    decoration: InputDecoration(
                      labelText: option.rateKind == 'pos_fixado'
                          ? '% do CDI'
                          : 'Taxa % a.a.',
                      isDense: true,
                      errorMaxLines: 3,
                    ),
                    keyboardType: _teclado,
                    autovalidateMode: AutovalidateMode.onUserInteraction,
                    validator: _validateRate,
                    onChanged: (v) {
                      final taxa = parseDecimal(v);
                      if (taxa != null && taxa > 0) option.rate = taxa;
                      onChanged();
                    },
                  ),
                ),
                const SizedBox(width: FiSpace.s2),
                Expanded(
                  child: TextFormField(
                    initialValue: option.termMonths.toString(),
                    decoration: const InputDecoration(
                      labelText: 'Prazo (meses)',
                      isDense: true,
                      errorMaxLines: 3,
                    ),
                    keyboardType: TextInputType.number,
                    autovalidateMode: AutovalidateMode.onUserInteraction,
                    validator: _validateTerm,
                    onChanged: (v) {
                      final prazo = int.tryParse(v.trim());
                      if (prazo != null && prazo >= 1) option.termMonths = prazo;
                      onChanged();
                    },
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
  Object? _error;

  @override
  void dispose() {
    _tickerCtrl.dispose();
    super.dispose();
  }

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
      _result = null;
      _error = null;
    });
  }

  void _removeTicker(String ticker) => setState(() {
    _tickers.remove(ticker);
    _result = null;
    _error = null;
  });

  Future<void> _compare() async {
    if (_tickers.length < 2) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref
          .read(apiRepositoryProvider)
          .compareAssets(List.of(_tickers));
      if (!mounted) return;
      setState(() => _result = result);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _result = null;
        _error = e;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final erro = _error;
    final faltam = 2 - _tickers.length;

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
          children: [
            for (final t in _tickers)
              FiChoiceChip(
                label: t,
                selected: true,
                onSelected: () => _removeTicker(t),
                onRemove: () => _removeTicker(t),
              ),
          ],
        ),
        if (_tickers.length < _maxCompareTickers) ...[
          const SizedBox(height: FiSpace.s3),
          TickerAutocompleteField(
            controller: _tickerCtrl,
            labelText: 'Adicionar ticker',
            onSelected: (s) => _addTicker(s.ticker),
            onSubmitted: _addTicker,
          ),
        ],
        const SizedBox(height: FiSpace.s5),
        FiButton.primary(
          label: 'Comparar',
          expand: true,
          busy: _loading,
          onPressed: faltam > 0 ? null : _compare,
        ),
        if (faltam > 0)
          Padding(
            padding: const EdgeInsets.only(top: FiSpace.s2),
            child: Text(
              faltam == 2
                  ? 'Adicione ao menos 2 ativos para comparar.'
                  : 'Adicione mais 1 ativo para comparar.',
              style: FiType.caption.copyWith(color: fiInk3(context)),
            ),
          ),
        if (erro != null)
          FiErrorState(
            error: erro,
            title: 'A comparação não saiu',
            action: 'comparar os ativos',
            onRetry: _compare,
          ),
        if (_result case final resultado?) ...[
          if (resultado.errors.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: FiSpace.s4),
              child: Text(
                'Não foi possível buscar: ${resultado.errors.join(', ')}',
                style: FiType.caption.copyWith(
                  color: fiStateColor(
                    FiState.attention,
                    Theme.of(context).brightness,
                  ),
                ),
              ),
            ),
          if (resultado.items.isNotEmpty) _CompareTable(items: resultado.items),
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
                note: confirmationLabel(a.independentInputs),
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
  Object? _error;

  @override
  void dispose() {
    _contributionCtrl.dispose();
    _monthsCtrl.dispose();
    _growthCtrl.dispose();
    _divGrowthCtrl.dispose();
    _targetCtrl.dispose();
    super.dispose();
  }

  Future<void> _simulate() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref
          .read(apiRepositoryProvider)
          .projectPassiveIncome(
            monthlyContribution: parseDecimal(_contributionCtrl.text) ?? 0,
            monthsAhead: int.tryParse(_monthsCtrl.text.trim()) ?? 60,
            portfolioGrowthRate: (parseDecimal(_growthCtrl.text) ?? 10) / 100,
            dividendGrowthRate: (parseDecimal(_divGrowthCtrl.text) ?? 5) / 100,
            reinvestDividends: _reinvest,
            targetMonthlyIncome: parseDecimal(_targetCtrl.text),
          );
      if (!mounted) return;
      setState(() => _result = result);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _result = null;
        _error = e;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
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
          trailing: FiSwitch(
            label: 'Reinvestir dividendos',
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
        if (_error case final erro?)
          FiErrorState(
            error: erro,
            title: 'A projeção não saiu',
            action: 'projetar',
            onRetry: _simulate,
          ),
        if (_result case final resultado?) ..._buildResult(resultado),
      ],
    );
  }

  List<Widget> _buildResult(PassiveIncomeProjection r) {
    if (r.projections.isEmpty) {
      return const [
        FiEmptyState(
          title: 'Sem meses para projetar',
          body: 'O período simulado não gerou nenhum mês. Informe ao menos 1 mês e '
              'projete de novo.',
        ),
      ];
    }
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
          _targetText(r.target!),
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

  String _targetText(ProjectionTarget meta) {
    final amount = formatCurrency(meta.monthlyIncome);
    if (meta.reachedInAllScenarios) {
      return 'Meta de $amount/mês: alcançada entre ${meta.earliestMonths} e '
          '${meta.latestMonths} meses. No cenário base, ${meta.expectedMonths} meses.';
    }
    if (meta.expectedMonths != null) {
      return 'Meta de $amount/mês: ${meta.expectedMonths} meses no cenário base, mas não '
          'alcançada no cenário conservador dentro do período simulado.';
    }
    return 'Meta de $amount/mês: não alcançada em nenhum dos três cenários dentro do '
        'período simulado. Aumentar o aporte ou o prazo muda isso; mudar a premissa '
        'de valorização não.';
  }
}
