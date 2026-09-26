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
import '../../core/widgets/controls.dart';

Future<void> openFixedIncomeForm(
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
  }) => openFixedIncomeForm(context, ref, existing: existing);

  Future<void> _delete(
    BuildContext context,
    WidgetRef ref,
    FixedIncomePosition position,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Remover ${position.name}?'),
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
          loading: () => FiSkeleton.screen(shape: FiSkeletonShape.row, count: 5, label: 'Carregando seus títulos'),
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
                _Totals(data: data),
                FiSection(
                  title: 'Aplicações',
                  count: data.items.length,
                  trailing: FiButton.quiet(
                    label: 'Cadastrar',
                    icon: Icons.add,
                    onPressed: () => _openForm(context, ref),
                  ),
                  child: Column(
                    children: [
                      for (final item in data.items)
                        _HoldingObject(
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

class _Totals extends StatelessWidget {
  const _Totals({required this.data});

  final FixedIncomeList data;

  @override
  Widget build(BuildContext context) {
    final fonte = data.ratesOrigin == 'bcb' ? 'BCB' : 'estimativa';
    final rendeu = data.totalReturn >= 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        FiHeadline(
          eyebrow: 'Valor de hoje',
          figure: formatCurrency(data.totalCurrent),
          size: FiHeadlineSize.xl,
          support:
              '${rendeu ? '+' : ''}${formatCurrency(data.totalReturn)} de rendimento '
              'líquido (${formatPercent(data.returnPct)}) sobre o aplicado',
          supportColor: fiDirectionColor(
            rendeu ? 1 : -1,
            Theme.of(context).brightness,
          ),
        ),
        const SizedBox(height: FiSpace.s5),
        FiFigures(
          figures: {
            'APLICADO': formatCurrency(data.totalInvested),
            'TAXA MÉDIA': '${formatPercent(data.averageAnnualRate)} ao ano',
          },
        ),
        const SizedBox(height: FiSpace.s2),
        Text(
          'Contra um CDI de ${formatPercent(data.cdiReference)} ao ano, lido do $fonte.',
          style: FiType.caption.copyWith(color: fiInk3(context)),
        ),
      ],
    );
  }
}

class _HoldingObject extends StatelessWidget {
  const _HoldingObject({
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
    final vencendo = item.maturingSoon && item.daysToMaturity != null;
    final rendeu = item.accruedReturn >= 0;
    final prazo = item.maturity == null
        ? fixedIncomeLiquidityLabel(item.liquidity)
        : 'vence em ${formatDate(item.maturity)}';

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: Opacity(
        opacity: item.hidden ? 0.6 : 1,
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
                      item.name,
                      style: FiType.title.copyWith(color: fiInk1(context)),
                    ),
                  ),
                  const SizedBox(width: FiSpace.s2),
                  FiTag.series(
                    label: fixedIncomeKindLabel(item.kind),
                    color: fiInk2(context),
                  ),
                ],
              ),
              const SizedBox(height: FiSpace.s1),
              Text(
                '${formatPercent(item.effectiveAnnualRatePct)} ao ano'
                '${item.irExempt == true ? ' · isento de IR' : ''} · $prazo',
                style: FiType.caption.copyWith(color: fiInk2(context)),
              ),

              const SizedBox(height: FiSpace.s4),
              FiFigures(
                rule: false,
                figures: {
                  'APLICADO': formatCurrency(item.investedValue),
                  'HOJE': formatCurrency(item.currentValue),
                },
              ),
              const SizedBox(height: FiSpace.s2),
              Text(
                '${rendeu ? '+' : ''}${formatCurrency(item.accruedReturn)} '
                '(${formatPercent(item.returnPct)}) de rendimento',
                style: FiType.caption.copyWith(
                  color: fiDirectionColor(rendeu ? 1 : -1, brightness),
                ),
              ),

              if (vencendo) ...[
                const SizedBox(height: FiSpace.s3),
                Text(
                  'Vence em ${item.daysToMaturity} dias — planeje a reaplicação.',
                  style: FiType.caption.copyWith(
                    color: fiStateColor(FiState.attention, brightness),
                  ),
                ),
              ],
              if (item.hidden) ...[
                const SizedBox(height: FiSpace.s2),
                Text(
                  'Fora do total da carteira, por escolha sua.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ],

              const SizedBox(height: FiSpace.s4),
              Divider(color: Theme.of(context).dividerColor, height: 1, thickness: 1),
              const SizedBox(height: FiSpace.s1),
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
  late final TextEditingController _name;
  late final TextEditingController _amount;
  late final TextEditingController _rate;
  late final TextEditingController _cdiPercent;

  late String _kind;
  late String _rateKind;
  late String _liquidity;
  late DateTime _appliedOn;
  DateTime? _maturity;
  late bool _hidden;

  bool _saving = false;
  String? _error;

  static const _kinds = [
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
    _name = TextEditingController(text: e?.name ?? '');
    _amount = TextEditingController(text: e != null ? '${e.investedValue}' : '');
    _rate = TextEditingController(text: e != null ? '${e.rate}' : '');
    _cdiPercent = TextEditingController(
      text: e?.cdiPercent != null ? '${e!.cdiPercent}' : '',
    );
    _kind = e?.kind ?? 'cdb';
    _rateKind = e?.rateKind ?? 'pre_fixado';
    _liquidity = e?.liquidity ?? 'no_vencimento';
    _appliedOn = DateTime.tryParse(e?.appliedOn ?? '') ?? DateTime.now();
    _maturity = e?.maturity != null ? DateTime.tryParse(e!.maturity!) : null;
    _hidden = e?.hidden ?? false;
  }

  @override
  void dispose() {
    _name.dispose();
    _amount.dispose();
    _rate.dispose();
    _cdiPercent.dispose();
    super.dispose();
  }

  String _iso(DateTime date) => date.toIso8601String().substring(0, 10);

  Future<void> _pickDate({required bool maturity}) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: maturity ? (_maturity ?? now) : _appliedOn,
      firstDate: DateTime(now.year - 30),
      lastDate: DateTime(now.year + 30),
    );
    if (picked == null) return;
    setState(() {
      if (maturity) {
        _maturity = picked;
      } else {
        _appliedOn = picked;
      }
    });
  }

  Future<void> _save() async {
    final valor = double.tryParse(_amount.text.replaceAll(',', '.'));
    final rate = double.tryParse(_rate.text.replaceAll(',', '.'));

    if (_name.text.trim().isEmpty || valor == null || valor <= 0 || rate == null || rate <= 0) {
      setState(() => _error = 'Preencha nome, valor aplicado e taxa.');
      return;
    }

    final payload = <String, dynamic>{
      'nome': _name.text.trim(),
      'tipo': _kind,
      'valor_investido': valor,
      'taxa': rate,
      'tipo_taxa': _rateKind,
      'percentual_cdi': _rateKind == 'pos_fixado'
          ? double.tryParse(_cdiPercent.text.replaceAll(',', '.'))
          : null,
      'data_aplicacao': _iso(_appliedOn),
      'vencimento': _maturity != null ? _iso(_maturity!) : null,
      'liquidez': _liquidity,
      'oculto': _hidden,
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
    final isPosFixado = _rateKind == 'pos_fixado';

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
                controller: _name,
                decoration: const InputDecoration(
                  labelText: 'Nome / banco emissor',
                  hintText: 'ex.: CDB Banco Inter 2027',
                ),
              ),
              const SizedBox(height: FiSpace.s4),
              DropdownButtonFormField<String>(
                initialValue: _kind,
                decoration: const InputDecoration(labelText: 'Tipo'),
                items: _kinds
                    .map(
                      (t) => DropdownMenuItem(
                        value: t,
                        child: Text(fixedIncomeKindLabel(t)),
                      ),
                    )
                    .toList(),
                onChanged: (v) => setState(() => _kind = v ?? _kind),
              ),
              const SizedBox(height: FiSpace.s4),
              TextField(
                controller: _amount,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'Valor aplicado (R\$)'),
              ),
              const SizedBox(height: FiSpace.s4),
              DropdownButtonFormField<String>(
                initialValue: _rateKind,
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
                onChanged: (v) => setState(() => _rateKind = v ?? _rateKind),
              ),
              const SizedBox(height: FiSpace.s4),
              TextField(
                controller: _rate,
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
                  controller: _cdiPercent,
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
                    value: formatDate(_iso(_appliedOn)),
                    onTap: () => _pickDate(maturity: false),
                  ),
                  FiDataRow(
                    label: 'Vencimento',
                    value: _maturity == null
                        ? 'sem vencimento'
                        : formatDate(_iso(_maturity!)),
                    onTap: () => _pickDate(maturity: true),
                  ),
                ],
              ),
              const SizedBox(height: FiSpace.s4),
              DropdownButtonFormField<String>(
                initialValue: _liquidity,
                decoration: const InputDecoration(labelText: 'Liquidez'),
                items: const [
                  DropdownMenuItem(
                    value: 'no_vencimento',
                    child: Text('No vencimento'),
                  ),
                  DropdownMenuItem(value: 'diaria', child: Text('Diária')),
                ],
                onChanged: (v) => setState(() => _liquidity = v ?? _liquidity),
              ),
              const SizedBox(height: FiSpace.s2),
              FiDataRow(
                label: 'Não somar na carteira',
                detail: 'Para reservas mantidas à parte',
                trailing: FiSwitch(
                  label: 'Não somar na carteira',
                  value: _hidden,
                  onChanged: (v) => setState(() => _hidden = v),
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
