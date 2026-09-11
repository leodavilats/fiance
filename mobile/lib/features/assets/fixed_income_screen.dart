import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/widgets/tag.dart';
import '../../core/labels.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/widgets/error_state.dart';

Future<void> abrirFormDeRendaFixa(
  BuildContext context,
  WidgetRef ref, {
  FixedIncomePosition? existing,
}) async {
  final saved = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    constraints: BoxConstraints(
      maxHeight: MediaQuery.of(context).size.height * 0.9,
    ),
    builder: (context) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: _FixedIncomeForm(existing: existing),
    ),
  );

  if (saved == true) {
    ref.invalidate(fixedIncomeProvider);
    ref.invalidate(dashboardProvider);
  }
}

class FixedIncomeScreen extends ConsumerWidget {
  const FixedIncomeScreen({super.key});

  Future<void> _openForm(
    BuildContext context,
    WidgetRef ref, {
    FixedIncomePosition? existing,
  }) => abrirFormDeRendaFixa(context, ref, existing: existing);

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
      appBar: AppBar(title: const Text('Renda fixa')),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(fixedIncomeProvider),
        child: listing.when(
          loading: () => FiSkeleton.tela(shape: FiSkeletonShape.row, count: 5, label: 'Carregando seus títulos'),
          error: (err, _) => FiErrorState(
            error: err,
            title: 'Não conseguimos carregar sua renda fixa',
            action: 'carregar suas aplicações',
            onRetry: () => ref.invalidate(fixedIncomeProvider),
          ),
          data: (data) {
            if (data.items.isEmpty) {
              return ListView(
                children: [
                  FiEmptyState(
                    title: 'Nenhuma aplicação de renda fixa',
                    body: 'Renda fixa é classe de primeira ordem aqui: o CDB entra no '
                        'patrimônio, é marcado a mercado e conta na alocação como qualquer '
                        'outra classe.',
                    hint: 'Cadastre o que você já tem — CDB, LCI, LCA, Tesouro.',
                    action: FiButton.primary(
                      label: 'Cadastrar aplicação',
                      icon: Icons.add,
                      onPressed: () => _openForm(context, ref),
                    ),
                  ),
                ],
              );
            }

            return ListView(
              padding: const EdgeInsets.fromLTRB(
                FiLayout.gutter,
                FiSpace.s3,
                FiLayout.gutter,
                FiLayout.scrollTail,
              ),
              children: [
                _Totais(data: data),
                FiSection(
                  title: 'Aplicações',
                  count: data.items.length,
                  action: FiButton.secondary(
                    label: 'Cadastrar aplicação',
                    icon: Icons.add,
                    onPressed: () => _openForm(context, ref),
                  ),
                  child: Column(
                    children: [
                      for (final item in data.items)
                        _AplicacaoObject(
                          item: item,
                          onEdit: () => _openForm(context, ref, existing: item),
                          onDelete: () => _delete(context, ref, item),
                        ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Totais extends StatelessWidget {
  const _Totais({required this.data});

  final FixedIncomeList data;

  @override
  Widget build(BuildContext context) {
    final fonte = data.fonteTaxas == 'bcb' ? 'BCB' : 'estimativa';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        FiHeadline(
          eyebrow: 'Valor de hoje',
          figure: formatCurrency(data.totalAtual),
          size: FiHeadlineSize.xl,
          support:
              '${formatCurrency(data.totalRendimento)} de rendimento líquido '
              '(${data.rendimentoPct.toStringAsFixed(2)}%) sobre o aplicado',
          supportColor: fiDirectionColor(
            data.totalRendimento >= 0 ? 1 : -1,
            Theme.of(context).brightness,
          ),
        ),
        const SizedBox(height: FiSpace.s5),
        FiFigures(
          figures: {
            'APLICADO': formatCurrency(data.totalInvestido),
            'TAXA MÉDIA': '${data.taxaMediaAa.toStringAsFixed(2)}% a.a.',
            'CDI DE REFERÊNCIA': '${data.cdiReferencia.toStringAsFixed(2)}% a.a.',
          },
        ),
        const SizedBox(height: FiSpace.s2),
        Text(
          'CDI lido do $fonte.',
          style: FiType.caption.copyWith(color: fiInk3(context)),
        ),
      ],
    );
  }
}

class _AplicacaoObject extends StatelessWidget {
  const _AplicacaoObject({
    required this.item,
    required this.onEdit,
    required this.onDelete,
  });

  final FixedIncomePosition item;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final vencendo = item.vencimentoProximo && item.diasParaVencimento != null;

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: Opacity(
        opacity: item.oculto ? 0.6 : 1,
        child: FiObject(
          accent: vencendo
              ? fiStateColor(FiState.attention, brightness)
              : null,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      item.nome,
                      style: FiType.title.copyWith(color: fiInk1(context)),
                    ),
                  ),
                  const SizedBox(width: FiSpace.s2),
                  FiTag.serie(
                    label: rendaFixaTipoLabel(item.tipo),
                    color: fiInk2(context),
                  ),
                ],
              ),
              const SizedBox(height: FiSpace.s1),
              Text(
                '${item.taxaAnualEfetivaPct.toStringAsFixed(2)}% a.a.'
                '${item.isentoIr == true ? ' · isento de IR' : ''} · '
                '${liquidezLabel(item.liquidez)}'
                '${item.vencimento != null ? ' · vence em ${item.vencimento}' : ''}',
                style: FiType.caption.copyWith(color: fiInk2(context)),
              ),

              const SizedBox(height: FiSpace.s4),
              FiFigures(
                rule: false,
                figures: {
                  'APLICADO': formatCurrency(item.valorInvestido),
                  'HOJE': formatCurrency(item.valorAtual),
                  'RENDIMENTO': '+${item.rendimentoPct.toStringAsFixed(2)}%',
                },
              ),

              if (vencendo) ...[
                const SizedBox(height: FiSpace.s3),
                Text(
                  'Vence em ${item.diasParaVencimento} dias — planeje a reaplicação.',
                  style: FiType.caption.copyWith(
                    color: fiStateColor(FiState.attention, brightness),
                  ),
                ),
              ],
              if (item.oculto) ...[
                const SizedBox(height: FiSpace.s2),
                Text(
                  'Fora do total da carteira, por escolha sua.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ],

              const SizedBox(height: FiSpace.s3),
              Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
              Row(
                children: [
                  Flexible(
                    child: FiButton.quiet(label: 'Editar', onPressed: onEdit),
                  ),
                  const SizedBox(width: FiSpace.s5),
                  Flexible(
                    child: FiButton.quiet(label: 'Remover', onPressed: onDelete),
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
        padding: const EdgeInsets.all(FiSpace.s5),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                widget.existing == null ? 'Nova aplicação' : 'Editar aplicação',
                style: FiType.pageTitle.copyWith(color: fiInk1(context)),
              ),
              const SizedBox(height: FiSpace.s5),
              TextField(
                controller: _nome,
                decoration: const InputDecoration(
                  labelText: 'Nome / banco emissor',
                  hintText: 'ex.: CDB Banco Inter 2027',
                ),
              ),
              const SizedBox(height: FiSpace.s4),
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
              const SizedBox(height: FiSpace.s4),
              TextField(
                controller: _valor,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'Valor aplicado (R\$)'),
              ),
              const SizedBox(height: FiSpace.s4),
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
              const SizedBox(height: FiSpace.s4),
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
                const SizedBox(height: FiSpace.s4),
                TextField(
                  controller: _percentualCdi,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: '% do CDI',
                    hintText: 'ex.: 110',
                  ),
                ),
              ],
              const SizedBox(height: FiSpace.s4),
              FiRows(
                children: [
                  FiDataRow(
                    label: 'Data de aplicação',
                    value: _iso(_dataAplicacao),
                    onTap: () => _pickDate(vencimento: false),
                  ),
                  FiDataRow(
                    label: 'Vencimento',
                    value: _vencimento != null ? _iso(_vencimento!) : 'sem vencimento',
                    onTap: () => _pickDate(vencimento: true),
                  ),
                ],
              ),
              const SizedBox(height: FiSpace.s4),
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
              const SizedBox(height: FiSpace.s2),
              FiDataRow(
                label: 'Não somar na carteira',
                detail: 'Para reservas mantidas à parte',
                trailing: Switch(
                  value: _oculto,
                  onChanged: (v) => setState(() => _oculto = v),
                ),
              ),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: FiSpace.s2),
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
              const SizedBox(height: FiSpace.s4),
              FiButton.primary(
                label: 'Salvar aplicação',
                expand: true,
                busy: _saving,
                onPressed: _save,
              ),
              const SizedBox(height: FiSpace.s2),
              FiButton.quiet(
                label: 'Cancelar',
                onPressed: _saving ? null : () => Navigator.pop(context, false),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
