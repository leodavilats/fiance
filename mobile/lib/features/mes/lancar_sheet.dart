import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/cash_models.dart';
import '../../core/labels.dart';
import '../../core/mes.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';

/// Lancar no caixa.
///
/// A forma muda pelo `kind`: entrada nao tem vencimento, e por isso pede um dia so, o do credito.
Future<void> abrirLancarSheet(
  BuildContext context,
  WidgetRef ref, {
  CashEntry? editar,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: _LancarForm(editar: editar),
    ),
  );
}

class _LancarForm extends ConsumerStatefulWidget {
  const _LancarForm({this.editar});

  final CashEntry? editar;

  @override
  ConsumerState<_LancarForm> createState() => _LancarFormState();
}

class _LancarFormState extends ConsumerState<_LancarForm> {
  final _form = GlobalKey<FormState>();
  final _descricao = TextEditingController();
  final _valor = TextEditingController();

  late CashKind _kind;
  late String _categoria;
  late DateTime _dia;

  bool _liquidado = false;

  bool _salvando = false;
  String? _erro;

  @override
  void initState() {
    super.initState();
    final e = widget.editar;
    _kind = e?.kind ?? CashKind.expense;
    _categoria = e?.category ?? cashCategoryKeys(_kind).first;
    _dia = DateTime.tryParse(e?.competencia ?? '') ?? DateTime.now();
    _liquidado = e?.paidOn != null;
    if (e != null) {
      _descricao.text = e.description;
      _valor.text = e.amount.toStringAsFixed(2).replaceAll('.', ',');
    }
  }

  @override
  void dispose() {
    _descricao.dispose();
    _valor.dispose();
    super.dispose();
  }

  void _trocarKind(CashKind k) {
    setState(() {
      _kind = k;
      // A categoria pertence ao vocabulario do kind, e o backend recusa a de outro.
      _categoria = cashCategoryKeys(k).first;
    });
  }

  String get _iso => _dia.toIso8601String().substring(0, 10);

  bool get _entrada => _kind == CashKind.income;

  Future<void> _salvar() async {
    if (!_form.currentState!.validate()) return;

    final valor = double.tryParse(
      _valor.text.replaceAll('.', '').replaceAll(',', '.'),
    );
    if (valor == null) return;

    setState(() {
      _salvando = true;
      _erro = null;
    });

    try {
      final api = ref.read(apiRepositoryProvider);
      final e = widget.editar;
      if (e == null) {
        await api.createCashEntry(
          kind: _kind,
          category: _categoria,
          description: _descricao.text.trim(),
          amount: valor,
          dueOn: _iso,
          paidOn: _liquidado ? _iso : null,
        );
      } else {
        await api.updateCashEntry(
          id: e.id,
          kind: _kind,
          category: _categoria,
          description: _descricao.text.trim(),
          amount: valor,
          dueOn: _iso,
          paidOn: _liquidado ? _iso : null,
        );
      }

      ref.invalidate(cashMonthProvider);
      ref.invalidate(cashEntriesProvider);
      ref.invalidate(surplusProvider);

      if (!mounted) return;
      final mesDoLancamento = _iso.substring(0, 7);
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Lançado em ${nomeDoMes(mesDoLancamento)}'),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _salvando = false;
        _erro = fiErrorMessage(e, action: 'salvar este lançamento');
      });
    }
  }

  Future<void> _apagar() async {
    final e = widget.editar;
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

    setState(() => _salvando = true);
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
        _salvando = false;
        _erro = fiErrorMessage(erro, action: 'apagar este lançamento');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final categorias = cashCategoryKeys(_kind);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Form(
          key: _form,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.editar == null ? 'Lançar no mês' : 'Editar lançamento',
                style: FiType.title,
              ),
              const SizedBox(height: FiSpace.s4),

              SegmentedButton<CashKind>(
                segments: const [
                  ButtonSegment(
                    value: CashKind.expense,
                    label: Text('Saída'),
                    icon: Icon(Icons.arrow_outward),
                  ),
                  ButtonSegment(
                    value: CashKind.income,
                    label: Text('Entrada'),
                    icon: Icon(Icons.south_west),
                  ),
                ],
                selected: {_kind},
                onSelectionChanged: (s) => _trocarKind(s.first),
              ),
              const SizedBox(height: FiSpace.s4),

              TextFormField(
                controller: _descricao,
                decoration: const InputDecoration(labelText: 'Descrição'),
                textCapitalization: TextCapitalization.sentences,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Diga o que é' : null,
              ),
              const SizedBox(height: FiSpace.s3),

              TextFormField(
                controller: _valor,
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
                initialValue: _categoria,
                decoration: const InputDecoration(labelText: 'Categoria'),
                items: [
                  for (final c in categorias)
                    DropdownMenuItem(
                      value: c,
                      child: Text(cashCategoryLabel(_kind, c)),
                    ),
                ],
                onChanged: (v) => setState(() => _categoria = v ?? _categoria),
              ),
              const SizedBox(height: FiSpace.s3),

              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  _entrada
                      ? 'Dia do crédito'
                      : (_liquidado ? 'Dia do pagamento' : 'Vencimento'),
                  style: FiType.label,
                ),
                subtitle: Text(
                  '${diaDe(_iso)}/${_iso.substring(5, 7)}/${_iso.substring(0, 4)}',
                  style: FiType.body,
                ),
                trailing: TextButton(
                  onPressed: () async {
                    final d = await showDatePicker(
                      context: context,
                      initialDate: _dia,
                      firstDate: DateTime(_dia.year - 3),
                      lastDate: DateTime(_dia.year + 3),
                    );
                    if (d != null) setState(() => _dia = d);
                  },
                  child: const Text('Trocar'),
                ),
              ),

              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _liquidado,
                onChanged: (v) => setState(() => _liquidado = v),
                title: Text(_entrada ? 'Já recebi' : 'Já paguei', style: FiType.label),
                subtitle: Text(
                  _liquidado
                      ? 'Entra na competência deste dia.'
                      : 'Conta não paga conta no mês do vencimento, e é o que forma o comprometido.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              ),

              if (_erro != null) ...[
                const SizedBox(height: FiSpace.s3),
                Text(
                  _erro!,
                  style: FiType.body.copyWith(
                    color: fiStateColor(FiState.adverse, Theme.of(context).brightness),
                  ),
                ),
              ],

              const SizedBox(height: FiSpace.s5),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _salvando ? null : _salvar,
                  child: Text(_salvando ? 'Salvando…' : 'Salvar'),
                ),
              ),

              if (widget.editar != null)
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton(
                    onPressed: _salvando ? null : _apagar,
                    child: const Text('Apagar lançamento'),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
