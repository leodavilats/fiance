import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/cash_models.dart';
import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/month.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/controls.dart';
import '../../core/widgets/feedback.dart';
import 'cash_refresh.dart';

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
  late DateTime _due;
  DateTime? _paid;

  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final e = widget.editing;
    _kind = e?.kind ?? CashKind.expense;
    _category = e?.category ?? cashCategoryKeys(_kind).first;
    _due = DateTime.tryParse(e?.dueOn ?? '') ?? DateTime.now();
    _paid = DateTime.tryParse(e?.paidOn ?? '');
    if (_kind == CashKind.income && _paid != null) _due = _paid!;
    if (e != null) {
      _description.text = e.description;
      _amount.text = formatForInput(e.amount);
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
      if (k == CashKind.income && _paid != null) _paid = _due;
    });
  }

  static String _isoOf(DateTime d) => d.toIso8601String().substring(0, 10);

  static String _shown(String iso) =>
      '${dayOf(iso)}/${iso.substring(5, 7)}/${iso.substring(0, 4)}';

  bool get _income => _kind == CashKind.income;

  bool get _settled => _paid != null;

  String get _dueIso => _isoOf(_due);

  String? get _paidIso => _paid == null ? null : _isoOf(_paid!);

  void _toggleSettled(bool v) {
    setState(() => _paid = v ? (_income ? _due : DateTime.now()) : null);
  }

  Future<void> _pickDate({required bool payment}) async {
    final inicial = payment ? (_paid ?? DateTime.now()) : _due;
    final d = await showDatePicker(
      context: context,
      initialDate: inicial,
      firstDate: DateTime(inicial.year - 3),
      lastDate: DateTime(inicial.year + 3),
    );
    if (d == null) return;
    setState(() {
      if (payment) {
        _paid = d;
      } else {
        _due = d;
        if (_income && _paid != null) _paid = d;
      }
    });
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;

    final valor = parseDecimal(_amount.text);
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
          dueOn: _dueIso,
          paidOn: _paidIso,
        );
      } else {
        await api.updateCashEntry(
          id: e.id,
          kind: _kind,
          category: _category,
          description: _description.text.trim(),
          amount: valor,
          dueOn: _dueIso,
          paidOn: _paidIso,
        );
      }

      invalidateCashReaders(ref.invalidate);

      if (!mounted) return;
      final entryMonth = (_paidIso ?? _dueIso).substring(0, 7);
      fiNotify(
        context,
        e == null ? 'Lançado em ${monthName(entryMonth)}' : 'Lançamento atualizado',
      );
      Navigator.of(context).pop();
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

    final ok = await fiConfirm(
      context,
      title: 'Apagar este lançamento?',
      body: '${e.description} sai do mês, e o livre agora e a sobra mudam junto.',
      confirmLabel: 'Apagar lançamento',
    );
    if (!ok || !mounted) return;

    setState(() {
      _saving = true;
      _error = null;
    });
    final api = ref.read(apiRepositoryProvider);
    final container = ProviderScope.containerOf(context, listen: false);
    try {
      await api.deleteCashEntry(e.id);
      invalidateCashReaders(container.invalidate);
      if (!mounted) return;
      final mensageiro = ScaffoldMessenger.maybeOf(context);
      fiNotify(
        context,
        'Lançamento apagado',
        actionLabel: 'Desfazer',
        onAction: () async {
          try {
            await api.createCashEntry(
              kind: e.kind,
              category: e.category,
              description: e.description,
              amount: e.amount,
              dueOn: e.dueOn,
              paidOn: e.paidOn,
            );
            invalidateCashReaders(container.invalidate);
          } catch (falha) {
            mensageiro?.showSnackBar(
              SnackBar(
                content: Text(fiErrorMessage(falha, action: 'desfazer a exclusão')),
              ),
            );
          }
        },
      );
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
    final paidIso = _paidIso;

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
                  final n = parseDecimal(v);
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
                    label: _income ? 'Dia do crédito' : 'Vencimento',
                    value: _shown(_dueIso),
                    onTap: () => _pickDate(payment: false),
                  ),
                  FiDataRow(
                    label: _income ? 'Já recebi' : 'Já paguei',
                    detail: _settled
                        ? (_income
                              ? 'Entra na competência do dia do crédito.'
                              : 'Entra na competência do dia do pagamento.')
                        : 'Conta não paga conta no mês do vencimento, e é o que forma o '
                              'comprometido.',
                    trailing: FiSwitch(
                      label: _income ? 'Já recebi' : 'Já paguei',
                      value: _settled,
                      onChanged: _toggleSettled,
                    ),
                  ),
                  if (!_income && paidIso != null)
                    FiDataRow(
                      label: 'Dia do pagamento',
                      value: _shown(paidIso),
                      onTap: () => _pickDate(payment: true),
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
