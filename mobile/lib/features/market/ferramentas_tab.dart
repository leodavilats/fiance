import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/ticker_autocomplete_field.dart';

class FerramentasTab extends StatefulWidget {
  const FerramentasTab({super.key});

  @override
  State<FerramentasTab> createState() => _FerramentasTabState();
}

enum _ToolMode { analisar, rendaFixa, comparar, aportes }

class _FerramentasTabState extends State<FerramentasTab> {
  _ToolMode _mode = _ToolMode.rendaFixa;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
          child: GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            childAspectRatio: 2.4,
            children: [
              _ToolModeCard(
                label: 'Simulador RF',
                icon: Icons.account_balance_outlined,
                selected: _mode == _ToolMode.rendaFixa,
                onSelected: () => setState(() => _mode = _ToolMode.rendaFixa),
              ),
              _ToolModeCard(
                label: 'Analisar',
                icon: Icons.search,
                selected: _mode == _ToolMode.analisar,
                onSelected: () => setState(() => _mode = _ToolMode.analisar),
              ),
              _ToolModeCard(
                label: 'Comparar',
                icon: Icons.compare_arrows,
                selected: _mode == _ToolMode.comparar,
                onSelected: () => setState(() => _mode = _ToolMode.comparar),
              ),
              _ToolModeCard(
                label: 'Aportes',
                icon: Icons.savings_outlined,
                selected: _mode == _ToolMode.aportes,
                onSelected: () => setState(() => _mode = _ToolMode.aportes),
              ),
            ],
          ),
        ),
        Expanded(
          child: switch (_mode) {
            _ToolMode.analisar => const _AnalyzeAssetView(),
            _ToolMode.rendaFixa => const _RendaFixaSimulator(),
            _ToolMode.comparar => const _CompareAssetsView(),
            _ToolMode.aportes => const _ContributionSimulatorView(),
          },
        ),
      ],
    );
  }
}

class _ToolModeCard extends StatelessWidget {
  const _ToolModeCard({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onSelected,
  });

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onSelected;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final borderColor = selected ? scheme.primary : scheme.outlineVariant;
    final bgColor = selected ? scheme.primary.withValues(alpha: 0.14) : scheme.surface;
    final fgColor = selected ? scheme.primary : scheme.onSurface;

    return Material(
      color: bgColor,
      borderRadius: BorderRadius.circular(appRadius),
      child: InkWell(
        borderRadius: BorderRadius.circular(appRadius),
        onTap: onSelected,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(appRadius),
            border: Border.all(color: borderColor, width: selected ? 1.5 : 1),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 20, color: fgColor),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  label,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: fgColor,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AnalyzeAssetView extends ConsumerStatefulWidget {
  const _AnalyzeAssetView();

  @override
  ConsumerState<_AnalyzeAssetView> createState() => _AnalyzeAssetViewState();
}

class _AnalyzeAssetViewState extends ConsumerState<_AnalyzeAssetView> {
  final _tickerCtrl = TextEditingController();
  bool _loading = false;
  AssetAnalysis? _result;
  String? _error;

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
        _error = 'Erro ao analisar $ticker: $e';
        _result = null;
      });
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _tickerCtrl,
                textCapitalization: TextCapitalization.characters,
                decoration: const InputDecoration(
                  labelText: 'Ticker (ex: PETR4, HGLG11, AAPL, BTC)',
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (_) => _analyze(),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: _loading ? null : _analyze,
              child: _loading
                  ? const SizedBox(
                      height: 16,
                      width: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Analisar'),
            ),
          ],
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(_error!, style: TextStyle(color: lossColor(Theme.of(context).brightness))),
          ),
        if (_result != null) _AssetAnalysisCard(analysis: _result!),
      ],
    );
  }
}

class _AssetAnalysisCard extends StatelessWidget {
  const _AssetAnalysisCard({required this.analysis});

  final AssetAnalysis analysis;

  @override
  Widget build(BuildContext context) {
    final a = analysis;
    return Padding(
      padding: const EdgeInsets.only(top: 16),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        a.symbol,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                        ),
                      ),
                      if (a.name != null)
                        Text(
                          a.name!,
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                    ],
                  ),
                  Text(
                    a.label,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              const Divider(height: 20),
              Wrap(
                spacing: 16,
                runSpacing: 8,
                children: [
                  _Stat(label: 'Preço', value: formatCurrency(a.price)),
                  _Stat(
                    label: 'Preço justo',
                    value: formatCurrency(a.consensus),
                  ),
                  _Stat(label: 'MS', value: formatPercent(a.marginOfSafety)),
                  _Stat(
                    label: 'RSI(14)',
                    value: a.rsi14?.toStringAsFixed(1) ?? '—',
                  ),
                  _Stat(label: 'Tendência', value: a.trend),
                ],
              ),
              if (a.reasons.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text(
                  'Por que essa decisão?',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                ...a.reasons.map((r) => Text('• $r')),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
        ),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
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

class _RendaFixaSimulator extends ConsumerStatefulWidget {
  const _RendaFixaSimulator();

  @override
  ConsumerState<_RendaFixaSimulator> createState() =>
      _RendaFixaSimulatorState();
}

class _RendaFixaSimulatorState extends ConsumerState<_RendaFixaSimulator> {
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

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        rates.when(
          loading: () => const SizedBox.shrink(),
          error: (_, _) => const SizedBox.shrink(),
          data: (r) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Wrap(
              spacing: 16,
              children: [
                Text('CDI: ${formatPercent(r.cdiAnual)}'),
                Text('Selic: ${formatPercent(r.selicAnual)}'),
                Text('IPCA: ${formatPercent(r.ipcaAnual)}'),
              ],
            ),
          ),
        ),
        ...List.generate(
          _options.length,
          (i) => _OptionForm(
            option: _options[i],
            tipos: _tipos,
            onRemove: _options.length > 1
                ? () => setState(() => _options.removeAt(i))
                : null,
            onChanged: () => setState(() {}),
          ),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: () => setState(() => _options.add(_RendaFixaOption())),
          icon: const Icon(Icons.add),
          label: const Text('Adicionar opção'),
        ),
        const SizedBox(height: 12),
        FilledButton(
          onPressed: _loading ? null : _compare,
          child: _loading
              ? const SizedBox(
                  height: 16,
                  width: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Comparar'),
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(_error!, style: TextStyle(color: lossColor(Theme.of(context).brightness))),
          ),
        if (_results != null) ...[
          const SizedBox(height: 16),
          ..._results!.map(
            (r) => Card(
              color: r.melhorOpcao
                  ? gainColor(Theme.of(context).brightness).withValues(alpha: 0.12)
                  : null,
              child: ListTile(
                title: Text(
                  '${_tipos[r.tipo] ?? r.tipo} ${r.nome != null ? "· ${r.nome}" : ""}',
                ),
                subtitle: Text(
                  'Líquido: ${formatCurrency(r.valorLiquido)} · Taxa líq: ${formatPercent(r.taxaLiquidaAa)}',
                ),
                trailing: r.melhorOpcao
                    ? Icon(Icons.star, color: gainColor(Theme.of(context).brightness))
                    : null,
              ),
            ),
          ),
        ],
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
    required this.tipos,
    required this.onChanged,
    this.onRemove,
  });

  final _RendaFixaOption option;
  final Map<String, String> tipos;
  final VoidCallback onChanged;
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
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
                    icon: const Icon(Icons.delete_outline),
                  ),
              ],
            ),
            const SizedBox(height: 8),
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

class _CompareAssetsView extends ConsumerStatefulWidget {
  const _CompareAssetsView();

  @override
  ConsumerState<_CompareAssetsView> createState() => _CompareAssetsViewState();
}

class _CompareAssetsViewState extends ConsumerState<_CompareAssetsView> {
  final _tickerCtrl = TextEditingController();
  final List<String> _tickers = [];
  bool _loading = false;
  CompareResponse? _result;
  String? _error;

  void _addTicker(String ticker) {
    final t = ticker.trim().toUpperCase();
    if (t.isEmpty || _tickers.contains(t) || _tickers.length >= _maxCompareTickers) return;
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
      final result = await ref.read(apiRepositoryProvider).compareAssets(_tickers);
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
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Compare até $_maxCompareTickers ativos lado a lado.',
          style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
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
          const SizedBox(height: 8),
          TickerAutocompleteField(
            controller: _tickerCtrl,
            labelText: 'Adicionar ticker',
            onSelected: (s) => _addTicker(s.ticker),
          ),
        ],
        const SizedBox(height: 12),
        FilledButton(
          onPressed: _loading ? null : _compare,
          child: _loading
              ? const SizedBox(
                  height: 16,
                  width: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Comparar'),
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(_error!, style: TextStyle(color: lossColor(Theme.of(context).brightness))),
          ),
        if (_result != null) ...[
          const SizedBox(height: 16),
          if (_result!.errors.isNotEmpty)
            Text(
              'Não foi possível buscar: ${_result!.errors.join(', ')}',
              style: TextStyle(color: warnColor(Theme.of(context).brightness), fontSize: 12),
            ),
          if (_result!.items.isNotEmpty) _CompareTable(items: _result!.items),
        ],
      ],
    );
  }
}

class _CompareTable extends StatelessWidget {
  const _CompareTable({required this.items});

  final List<AssetAnalysis> items;

  @override
  Widget build(BuildContext context) {
    final rows = <(String, String Function(AssetAnalysis))>[
      ('Preço', (a) => formatCurrency(a.price)),
      ('Preço justo', (a) => formatCurrency(a.consensus)),
      ('Margem de segurança', (a) => formatPercent(a.marginOfSafety)),
      ('Decisão', (a) => a.label),
      ('P/L', (a) => a.fundamentals['pe_ratio']?.toStringAsFixed(1) ?? '—'),
      ('P/VP', (a) => a.fundamentals['pb_ratio']?.toStringAsFixed(2) ?? '—'),
      (
        'Dividend Yield',
        (a) => a.fundamentals['dividend_yield'] != null
            ? '${a.fundamentals['dividend_yield']!.toStringAsFixed(1)}%'
            : '—',
      ),
      ('RSI (14)', (a) => a.rsi14?.toStringAsFixed(0) ?? '—'),
      ('Tendência', (a) => a.trend),
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columns: [
          const DataColumn(label: Text('Indicador')),
          ...items.map((a) => DataColumn(label: Text(a.symbol))),
        ],
        rows: rows
            .map(
              (r) => DataRow(
                cells: [
                  DataCell(Text(r.$1)),
                  ...items.map((a) => DataCell(Text(r.$2(a)))),
                ],
              ),
            )
            .toList(),
      ),
    );
  }
}

class _ContributionSimulatorView extends ConsumerStatefulWidget {
  const _ContributionSimulatorView();

  @override
  ConsumerState<_ContributionSimulatorView> createState() =>
      _ContributionSimulatorViewState();
}

class _ContributionSimulatorViewState
    extends ConsumerState<_ContributionSimulatorView> {
  final _contributionCtrl = TextEditingController(text: '500');
  final _monthsCtrl = TextEditingController(text: '60');
  final _growthCtrl = TextEditingController(text: '10');
  final _divGrowthCtrl = TextEditingController(text: '5');
  final _targetCtrl = TextEditingController();
  bool _reinvest = true;
  bool _loading = false;
  PassiveIncomeProjection? _result;

  double? _parseDecimal(String text) => double.tryParse(text.trim().replaceAll(',', '.'));

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
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Simule um aporte mensal recorrente e veja a evolução da sua carteira e renda passiva.',
          style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _contributionCtrl,
                decoration: const InputDecoration(labelText: 'Aporte mensal (R\$)'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _monthsCtrl,
                decoration: const InputDecoration(labelText: 'Meses'),
                keyboardType: TextInputType.number,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _growthCtrl,
                decoration: const InputDecoration(labelText: 'Valorização anual (%)'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _divGrowthCtrl,
                decoration: const InputDecoration(labelText: 'Crescimento dividendos (%)'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _targetCtrl,
          decoration: const InputDecoration(labelText: 'Meta de renda passiva/mês (opcional)'),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
        ),
        CheckboxListTile(
          value: _reinvest,
          onChanged: (v) => setState(() => _reinvest = v ?? true),
          title: const Text('Reinvestir dividendos'),
          contentPadding: EdgeInsets.zero,
          controlAffinity: ListTileControlAffinity.leading,
        ),
        const SizedBox(height: 8),
        FilledButton(
          onPressed: _loading ? null : _simulate,
          child: _loading
              ? const SizedBox(
                  height: 16,
                  width: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Simular'),
        ),
        if (_result != null) ..._buildResult(_result!),
      ],
    );
  }

  List<Widget> _buildResult(PassiveIncomeProjection r) {
    final last = r.projections.last;
    return [
      const SizedBox(height: 16),
      Row(
        children: [
          Expanded(
            child: _Stat(label: 'Carteira hoje', value: formatCurrency(r.currentPortfolioValue)),
          ),
          Expanded(
            child: _Stat(label: 'Carteira no fim', value: formatCurrency(last.portfolioValue)),
          ),
        ],
      ),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(
            child: _Stat(
              label: 'Renda passiva hoje',
              value: formatCurrency(r.currentPassiveIncomeMonthly),
            ),
          ),
          Expanded(
            child: _Stat(
              label: 'Renda passiva no fim',
              value: formatCurrency(last.passiveIncomeMonthly),
            ),
          ),
        ],
      ),
      if (r.targetMonthlyIncome != null) ...[
        const SizedBox(height: 12),
        if (r.monthsToTarget != null)
          Text(
            '🎯 Meta de ${formatCurrency(r.targetMonthlyIncome)}/mês atingida em ${r.monthsToTarget} meses (${r.targetDate}).',
          )
        else
          Text(
            'Meta de ${formatCurrency(r.targetMonthlyIncome)}/mês não atingida no período simulado.',
            style: TextStyle(color: Colors.grey.shade600),
          ),
      ],
      const SizedBox(height: 12),
      Text(
        'Projeção educativa, não é garantia de rentabilidade futura.',
        style: TextStyle(color: Colors.grey.shade500, fontSize: 11),
      ),
    ];
  }
}
