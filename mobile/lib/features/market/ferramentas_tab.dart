import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';

class FerramentasTab extends StatefulWidget {
  const FerramentasTab({super.key});

  @override
  State<FerramentasTab> createState() => _FerramentasTabState();
}

class _FerramentasTabState extends State<FerramentasTab> {
  bool _showRendaFixa = false;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: SegmentedButton<bool>(
            segments: const [
              ButtonSegment(value: false, label: Text('Analisar ativo')),
              ButtonSegment(value: true, label: Text('Simulador RF')),
            ],
            selected: {_showRendaFixa},
            onSelectionChanged: (s) => setState(() => _showRendaFixa = s.first),
          ),
        ),
        Expanded(child: _showRendaFixa ? const _RendaFixaSimulator() : const _AnalyzeAssetView()),
      ],
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
                  ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Analisar'),
            ),
          ],
        ),
        if (_error != null)
          Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
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
                      Text(a.symbol, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                      if (a.name != null) Text(a.name!, style: TextStyle(color: Colors.grey.shade600)),
                    ],
                  ),
                  Text(a.label, style: const TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              const Divider(height: 20),
              Wrap(
                spacing: 16,
                runSpacing: 8,
                children: [
                  _Stat(label: 'Preço', value: formatCurrency(a.price)),
                  _Stat(label: 'Preço justo', value: formatCurrency(a.consensus)),
                  _Stat(label: 'MS', value: formatPercent(a.marginOfSafety)),
                  _Stat(label: 'RSI(14)', value: a.rsi14?.toStringAsFixed(1) ?? '—'),
                  _Stat(label: 'Tendência', value: a.trend),
                ],
              ),
              if (a.reasons.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text('Por que essa decisão?', style: TextStyle(fontWeight: FontWeight.bold)),
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
        Text(label, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}

class _RendaFixaOption {
  _RendaFixaOption({
    this.tipo = 'cdb',
    this.nome = '',
    this.valor = 1000,
    this.taxa = 110,
    this.prazoMeses = 12,
    this.tipoTaxa = 'pos_fixado',
  });

  String tipo;
  String nome;
  double valor;
  double taxa;
  int prazoMeses;
  String tipoTaxa;
}

class _RendaFixaSimulator extends ConsumerStatefulWidget {
  const _RendaFixaSimulator();

  @override
  ConsumerState<_RendaFixaSimulator> createState() => _RendaFixaSimulatorState();
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
      final results = await ref.read(apiRepositoryProvider).compareRendaFixa(_options
          .map((o) => {
                'tipo': o.tipo,
                'nome': o.nome.isEmpty ? null : o.nome,
                'valor_investido': o.valor,
                'taxa': o.taxa,
                'prazo_meses': o.prazoMeses,
                'tipo_taxa': o.tipoTaxa,
                if (o.tipoTaxa == 'pos_fixado') 'percentual_cdi': o.taxa,
              })
          .toList());
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
        ...List.generate(_options.length, (i) => _OptionForm(
              option: _options[i],
              tipos: _tipos,
              onRemove: _options.length > 1 ? () => setState(() => _options.removeAt(i)) : null,
              onChanged: () => setState(() {}),
            )),
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
              ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('Comparar'),
        ),
        if (_error != null)
          Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
        if (_results != null) ...[
          const SizedBox(height: 16),
          ..._results!.map((r) => Card(
                color: r.melhorOpcao ? Colors.green.shade50 : null,
                child: ListTile(
                  title: Text('${_tipos[r.tipo] ?? r.tipo} ${r.nome != null ? "· ${r.nome}" : ""}'),
                  subtitle: Text('Líquido: ${formatCurrency(r.valorLiquido)} · Taxa líq: ${formatPercent(r.taxaLiquidaAa)}'),
                  trailing: r.melhorOpcao ? const Icon(Icons.star, color: Colors.green) : null,
                ),
              )),
        ],
      ],
    );
  }
}

final _ratesProvider = FutureProvider.autoDispose<ReferenceRates>((ref) {
  return ref.watch(apiRepositoryProvider).getRendaFixaRates();
});

class _OptionForm extends StatelessWidget {
  const _OptionForm({required this.option, required this.tipos, required this.onChanged, this.onRemove});

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
                    decoration: const InputDecoration(labelText: 'Tipo', isDense: true),
                    items: tipos.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))).toList(),
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
                  IconButton(onPressed: onRemove, icon: const Icon(Icons.delete_outline)),
              ],
            ),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    initialValue: option.valor.toStringAsFixed(0),
                    decoration: const InputDecoration(labelText: 'Valor (R\$)', isDense: true),
                    keyboardType: TextInputType.number,
                    onChanged: (v) => option.valor = double.tryParse(v) ?? option.valor,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextFormField(
                    initialValue: option.taxa.toStringAsFixed(0),
                    decoration: InputDecoration(
                      labelText: option.tipoTaxa == 'pos_fixado' ? '% do CDI' : 'Taxa % a.a.',
                      isDense: true,
                    ),
                    keyboardType: TextInputType.number,
                    onChanged: (v) => option.taxa = double.tryParse(v) ?? option.taxa,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextFormField(
                    initialValue: option.prazoMeses.toString(),
                    decoration: const InputDecoration(labelText: 'Prazo (meses)', isDense: true),
                    keyboardType: TextInputType.number,
                    onChanged: (v) => option.prazoMeses = int.tryParse(v) ?? option.prazoMeses,
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
