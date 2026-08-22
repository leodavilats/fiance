import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/widgets/error_state.dart';

class FixedIncomeScreen extends ConsumerWidget {
  const FixedIncomeScreen({super.key});

  Future<void> _openForm(
    BuildContext context,
    WidgetRef ref, {
    FixedIncomePosition? existing,
  }) async {
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: _FixedIncomeForm(existing: existing),
      ),
    );

    if (saved == true) {
      ref.invalidate(fixedIncomeProvider);
      ref.invalidate(dashboardProvider);
    }
  }

  Future<void> _delete(
    BuildContext context,
    WidgetRef ref,
    FixedIncomePosition position,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Remover ${position.nome}?'),
        content: const Text('A aplicação sai da carteira e do histórico de rendimento.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Remover'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      await ref.read(apiRepositoryProvider).deleteFixedIncome(position.id);
      ref.invalidate(fixedIncomeProvider);
      ref.invalidate(dashboardProvider);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(fiErrorMessage(e, action: 'remover esta aplicação'))));
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final listing = ref.watch(fixedIncomeProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Renda Fixa')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openForm(context, ref),
        child: const Icon(Icons.add),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(fixedIncomeProvider),
        child: listing.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar sua renda fixa',
            action: 'carregar suas aplicações',
            onRetry: () => ref.invalidate(fixedIncomeProvider),
          ),
          data: (data) {
            if (data.items.isEmpty) {
              return ListView(
                children: const [
                  Padding(
                    padding: EdgeInsets.all(32),
                    child: Column(
                      children: [
                        Icon(Icons.account_balance_outlined, size: 48),
                        SizedBox(height: 12),
                        Text(
                          'Nenhuma aplicação de renda fixa.\nToque em + para cadastrar '
                          'seu CDB, LCI, Tesouro…',
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
                _TotalsCard(data: data),
                const SizedBox(height: 16),
                for (final item in data.items)
                  _FixedIncomeTile(
                    item: item,
                    onEdit: () => _openForm(context, ref, existing: item),
                    onDelete: () => _delete(context, ref, item),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _TotalsCard extends StatelessWidget {
  const _TotalsCard({required this.data});

  final FixedIncomeList data;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Total aplicado', style: theme.textTheme.labelMedium),
            Text(
              formatCurrency(data.totalInvestido),
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Valor hoje', style: theme.textTheme.labelMedium),
                      Text(formatCurrency(data.totalAtual)),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Rendimento líquido', style: theme.textTheme.labelMedium),
                      Text(
                        '${formatCurrency(data.totalRendimento)} '
                        '(${data.rendimentoPct.toStringAsFixed(2)}%)',
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              'Taxa média ${data.taxaMediaAa.toStringAsFixed(2)}% a.a. · CDI de '
              'referência ${data.cdiReferencia.toStringAsFixed(2)}% '
              '(${data.fonteTaxas == 'bcb' ? 'BCB' : 'estimativa'})',
              style: theme.textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _FixedIncomeTile extends StatelessWidget {
  const _FixedIncomeTile({
    required this.item,
    required this.onEdit,
    required this.onDelete,
  });

  final FixedIncomePosition item;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Opacity(
        opacity: item.oculto ? 0.5 : 1,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(item.nome, style: theme.textTheme.titleMedium),
                        Text(
                          '${rendaFixaTipoLabel(item.tipo)} · '
                          '${item.taxaAnualEfetivaPct.toStringAsFixed(2)}% a.a.'
                          '${item.isentoIr == true ? ' · isento de IR' : ''}',
                          style: theme.textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: onEdit,
                    icon: const Icon(Icons.edit_outlined),
                    tooltip: 'Editar',
                  ),
                  IconButton(
                    onPressed: onDelete,
                    icon: const Icon(Icons.delete_outline),
                    tooltip: 'Remover',
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Aplicado', style: theme.textTheme.labelSmall),
                        Text(formatCurrency(item.valorInvestido)),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Hoje', style: theme.textTheme.labelSmall),
                        Text(formatCurrency(item.valorAtual)),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Rendimento', style: theme.textTheme.labelSmall),
                        Text('+${item.rendimentoPct.toStringAsFixed(2)}%'),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '${liquidezLabel(item.liquidez)}'
                '${item.vencimento != null ? ' · vence em ${item.vencimento}' : ''}',
                style: theme.textTheme.bodySmall,
              ),
              if (item.vencimentoProximo && item.diasParaVencimento != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Row(
                    children: [
                      const Icon(Icons.event_available_outlined, size: 16),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Vence em ${item.diasParaVencimento} dias — planeje a reaplicação.',
                          style: theme.textTheme.bodySmall,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FixedIncomeForm extends ConsumerStatefulWidget {
  const _FixedIncomeForm({this.existing});

  final FixedIncomePosition? existing;

  @override
  ConsumerState<_FixedIncomeForm> createState() => _FixedIncomeFormState();
}

class _FixedIncomeFormState extends ConsumerState<_FixedIncomeForm> {
  late final TextEditingController _nome;
  late final TextEditingController _valor;
  late final TextEditingController _taxa;
  late final TextEditingController _percentualCdi;

  late String _tipo;
  late String _tipoTaxa;
  late String _liquidez;
  late DateTime _dataAplicacao;
  DateTime? _vencimento;
  late bool _oculto;

  bool _saving = false;
  String? _error;

  static const _tipos = [
    'cdb',
    'lci',
    'lca',
    'lc',
    'cri',
    'cra',
    'tesouro_selic',
    'tesouro_ipca',
    'tesouro_pre',
  ];

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    _nome = TextEditingController(text: e?.nome ?? '');
    _valor = TextEditingController(text: e != null ? '${e.valorInvestido}' : '');
    _taxa = TextEditingController(text: e != null ? '${e.taxa}' : '');
    _percentualCdi = TextEditingController(
      text: e?.percentualCdi != null ? '${e!.percentualCdi}' : '',
    );
    _tipo = e?.tipo ?? 'cdb';
    _tipoTaxa = e?.tipoTaxa ?? 'pre_fixado';
    _liquidez = e?.liquidez ?? 'no_vencimento';
    _dataAplicacao = DateTime.tryParse(e?.dataAplicacao ?? '') ?? DateTime.now();
    _vencimento = e?.vencimento != null ? DateTime.tryParse(e!.vencimento!) : null;
    _oculto = e?.oculto ?? false;
  }

  @override
  void dispose() {
    _nome.dispose();
    _valor.dispose();
    _taxa.dispose();
    _percentualCdi.dispose();
    super.dispose();
  }

  String _iso(DateTime date) => date.toIso8601String().substring(0, 10);

  Future<void> _pickDate({required bool vencimento}) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: vencimento ? (_vencimento ?? now) : _dataAplicacao,
      firstDate: DateTime(now.year - 30),
      lastDate: DateTime(now.year + 30),
    );
    if (picked == null) return;
    setState(() {
      if (vencimento) {
        _vencimento = picked;
      } else {
        _dataAplicacao = picked;
      }
    });
  }

  Future<void> _save() async {
    final valor = double.tryParse(_valor.text.replaceAll(',', '.'));
    final taxa = double.tryParse(_taxa.text.replaceAll(',', '.'));

    if (_nome.text.trim().isEmpty || valor == null || valor <= 0 || taxa == null || taxa <= 0) {
      setState(() => _error = 'Preencha nome, valor aplicado e taxa.');
      return;
    }

    final payload = <String, dynamic>{
      'nome': _nome.text.trim(),
      'tipo': _tipo,
      'valor_investido': valor,
      'taxa': taxa,
      'tipo_taxa': _tipoTaxa,
      'percentual_cdi': _tipoTaxa == 'pos_fixado'
          ? double.tryParse(_percentualCdi.text.replaceAll(',', '.'))
          : null,
      'data_aplicacao': _iso(_dataAplicacao),
      'vencimento': _vencimento != null ? _iso(_vencimento!) : null,
      'liquidez': _liquidez,
      'oculto': _oculto,
    };

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      final repo = ref.read(apiRepositoryProvider);
      final existing = widget.existing;
      if (existing != null) {
        await repo.updateFixedIncome(existing.id, payload);
      } else {
        await repo.createFixedIncome(payload);
      }
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        setState(() {
          _saving = false;
          _error = 'Não foi possível salvar: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isPosFixado = _tipoTaxa == 'pos_fixado';

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                widget.existing == null ? 'Nova aplicação' : 'Editar aplicação',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _nome,
                decoration: const InputDecoration(
                  labelText: 'Nome / banco emissor',
                  hintText: 'ex.: CDB Banco Inter 2027',
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _tipo,
                decoration: const InputDecoration(labelText: 'Tipo'),
                items: _tipos
                    .map(
                      (t) => DropdownMenuItem(
                        value: t,
                        child: Text(rendaFixaTipoLabel(t)),
                      ),
                    )
                    .toList(),
                onChanged: (v) => setState(() => _tipo = v ?? _tipo),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _valor,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'Valor aplicado (R\$)'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _tipoTaxa,
                decoration: const InputDecoration(labelText: 'Tipo de taxa'),
                items: const [
                  DropdownMenuItem(value: 'pre_fixado', child: Text('Pré-fixado')),
                  DropdownMenuItem(
                    value: 'pos_fixado',
                    child: Text('Pós-fixado (% do CDI)'),
                  ),
                  DropdownMenuItem(
                    value: 'hibrido',
                    child: Text('Híbrido (IPCA + taxa)'),
                  ),
                ],
                onChanged: (v) => setState(() => _tipoTaxa = v ?? _tipoTaxa),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _taxa,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: isPosFixado
                      ? 'Taxa de referência (% a.a.)'
                      : 'Taxa (% a.a.)',
                ),
              ),
              if (isPosFixado) ...[
                const SizedBox(height: 12),
                TextField(
                  controller: _percentualCdi,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: '% do CDI',
                    hintText: 'ex.: 110',
                  ),
                ),
              ],
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Data de aplicação'),
                subtitle: Text(_iso(_dataAplicacao)),
                trailing: const Icon(Icons.calendar_today_outlined),
                onTap: () => _pickDate(vencimento: false),
              ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Vencimento (opcional)'),
                subtitle: Text(_vencimento != null ? _iso(_vencimento!) : 'sem vencimento'),
                trailing: const Icon(Icons.calendar_today_outlined),
                onTap: () => _pickDate(vencimento: true),
              ),
              DropdownButtonFormField<String>(
                initialValue: _liquidez,
                decoration: const InputDecoration(labelText: 'Liquidez'),
                items: const [
                  DropdownMenuItem(
                    value: 'no_vencimento',
                    child: Text('No vencimento'),
                  ),
                  DropdownMenuItem(value: 'diaria', child: Text('Diária')),
                ],
                onChanged: (v) => setState(() => _liquidez = v ?? _liquidez),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _oculto,
                onChanged: (v) => setState(() => _oculto = v),
                title: const Text('Não somar na carteira'),
                subtitle: const Text('Para reservas mantidas à parte'),
              ),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    _error!,
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                  ),
                ),
              const SizedBox(height: 8),
              FilledButton(
                onPressed: _saving ? null : _save,
                child: Text(_saving ? 'Salvando…' : 'Salvar'),
              ),
              TextButton(
                onPressed: _saving ? null : () => Navigator.pop(context, false),
                child: const Text('Cancelar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
