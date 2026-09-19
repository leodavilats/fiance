import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/cash_models.dart';
import '../../core/labels.dart';
import '../../core/month.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';

Future<void> openCashEntrySheet(
  BuildContext context,
  WidgetRef ref, {
  CashEntry? editing,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: _CashEntryForm(editing: editing),
    ),
  );
}

class _CashEntryForm extends ConsumerStatefulWidget {
  const _CashEntryForm({this.editing});

  final CashEntry? editing;

  @override
  ConsumerState<_CashEntryForm> createState() => _CashEntryFormState();
}

class _CashEntryFormState extends ConsumerState<_CashEntryForm> {
  final _form = GlobalKey<FormState>();
  final _description = TextEditingController();
  final _amount = TextEditingController();

  late CashKind _kind;
  late String _category;
  late DateTime _dayFormat;

  bool _settled = false;

  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final e = widget.editing;
    _kind = e?.kind ?? CashKind.expense;
    _category = e?.category ?? cashCategoryKeys(_kind).first;
    _dayFormat = DateTime.tryParse(e?.accrualOn ?? '') ?? DateTime.now();
    _settled = e?.paidOn != null;
    if (e != null) {
      _description.text = e.description;
      _amount.text = e.amount.toStringAsFixed(2).replaceAll('.', ',');
    }
  }

  @override
  void dispose() {
    _description.dispose();
    _amount.dispose();
    super.dispose();
  }

  void _changeKind(CashKind k) {
    setState(() {
      _kind = k;
      _category = cashCategoryKeys(k).first;
    });
  }

  String get _iso => _dayFormat.toIso8601String().substring(0, 10);

  bool get _income => _kind == CashKind.income;

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;

    final valor = double.tryParse(
      _amount.text.replaceAll('.', '').replaceAll(',', '.'),
    );
    if (valor == null) return;

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      final api = ref.read(apiRepositoryProvider);
      final e = widget.editing;
      if (e == null) {
        await api.createCashEntry(
          kind: _kind,
          category: _category,
          description: _description.text.trim(),
          amount: valor,
          dueOn: _iso,
          paidOn: _settled ? _iso : null,
        );
      } else {
        await api.updateCashEntry(
          id: e.id,
          kind: _kind,
          category: _category,
          description: _description.text.trim(),
          amount: valor,
          dueOn: _iso,
          paidOn: _settled ? _iso : null,
        );
      }

      ref.invalidate(cashMonthProvider);
      ref.invalidate(cashEntriesProvider);
      ref.invalidate(surplusProvider);

      if (!mounted) return;
      final entryMonth = _iso.substring(0, 7);
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Lançado em ${monthName(entryMonth)}'),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = fiErrorMessage(e, action: 'salvar este lançamento');
      });
    }
  }

  Future<void> _delete() async {
    final e = widget.editing;
    if (e == null) return;

    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Apagar este lançamento?'),
        content: Text(
          '${e.description} sai do mês, e o livre agora e a sobra mudam junto.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Apagar lançamento'),
          ),
        ],
      ),
    );
    if (ok != true) return;

    setState(() => _saving = true);
    try {
      await ref.read(apiRepositoryProvider).deleteCashEntry(e.id);
      ref.invalidate(cashMonthProvider);
      ref.invalidate(cashEntriesProvider);
      ref.invalidate(surplusProvider);
      if (!mounted) return;
      Navigator.of(context).pop();
    } catch (erro) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = fiErrorMessage(erro, action: 'apagar este lançamento');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final categories = cashCategoryKeys(_kind);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          FiSpace.s5,
          0,
          FiSpace.s5,
          FiSpace.s6,
        ),
        child: Form(
          key: _form,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.editing == null ? 'Lançar no mês' : 'Editar lançamento',
                style: FiType.pageTitle.copyWith(color: fiInk1(context)),
              ),
              const SizedBox(height: FiSpace.s5),

              SegmentedButton<CashKind>(
                showSelectedIcon: false,
                segments: const [
                  ButtonSegment(value: CashKind.expense, label: Text('Saída')),
                  ButtonSegment(value: CashKind.income, label: Text('Entrada')),
                ],
                selected: {_kind},
                onSelectionChanged: (s) => _changeKind(s.first),
              ),
              const SizedBox(height: FiSpace.s5),

              TextFormField(
                controller: _description,
                decoration: const InputDecoration(labelText: 'Descrição'),
                textCapitalization: TextCapitalization.sentences,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Diga o que é' : null,
              ),
              const SizedBox(height: FiSpace.s3),

              TextFormField(
                controller: _amount,
                decoration: const InputDecoration(
                  labelText: 'Valor',
                  prefixText: r'R$ ',
                ),
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                validator: (v) {
                  final n = double.tryParse(
                    (v ?? '').replaceAll('.', '').replaceAll(',', '.'),
                  );
                  if (n == null || n <= 0) return 'Um valor positivo';
                  return null;
                },
              ),
              const SizedBox(height: FiSpace.s3),

              DropdownButtonFormField<String>(
                initialValue: _category,
                decoration: const InputDecoration(labelText: 'Categoria'),
                items: [
                  for (final c in categories)
                    DropdownMenuItem(
                      value: c,
                      child: Text(cashCategoryLabel(_kind, c)),
                    ),
                ],
                onChanged: (v) => setState(() => _category = v ?? _category),
              ),
              const SizedBox(height: FiSpace.s3),

              const SizedBox(height: FiSpace.s2),
              FiRows(
                children: [
                  FiDataRow(
                    label: _income
                        ? 'Dia do crédito'
                        : (_settled ? 'Dia do pagamento' : 'Vencimento'),
                    value:
                        '${dayOf(_iso)}/${_iso.substring(5, 7)}/${_iso.substring(0, 4)}',
                    onTap: () async {
                      final d = await showDatePicker(
                        context: context,
                        initialDate: _dayFormat,
                        firstDate: DateTime(_dayFormat.year - 3),
                        lastDate: DateTime(_dayFormat.year + 3),
                      );
                      if (d != null) setState(() => _dayFormat = d);
                    },
                  ),
                  FiDataRow(
                    label: _income ? 'Já recebi' : 'Já paguei',
                    detail: _settled
                        ? 'Entra na competência deste dia.'
                        : 'Conta não paga conta no mês do vencimento, e é o que forma o '
                              'comprometido.',
                    trailing: Switch(
                      value: _settled,
                      onChanged: (v) => setState(() => _settled = v),
                    ),
                  ),
                ],
              ),

              if (_error != null) ...[
                const SizedBox(height: FiSpace.s3),
                Text(
                  _error!,
                  style: FiType.body.copyWith(
                    color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
                  ),
                ),
              ],

              const SizedBox(height: FiSpace.s6),
              FiButton.primary(
                label: widget.editing == null
                    ? 'Lançar'
                    : 'Salvar alterações',
                expand: true,
                busy: _saving,
                onPressed: _save,
              ),

              if (widget.editing != null) ...[
                const SizedBox(height: FiSpace.s2),
                FiButton.danger(
                  label: 'Apagar lançamento',
                  expand: true,
                  onPressed: _saving ? null : _delete,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
