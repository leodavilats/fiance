import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/cash_models.dart';
import '../../core/widgets/skeleton.dart';
import '../../core/format.dart';
import '../../core/labels.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/vocabulary.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/provenance.dart';
import '../../core/widgets/section.dart';
import '../../core/widgets/tag.dart';

class DebtsScreen extends ConsumerWidget {
  const DebtsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final debts = ref.watch(debtsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Dívidas')),
      body: debts.when(
        loading: () => FiSkeleton.screen(
          shape: FiSkeletonShape.row,
          count: 4,
          label: 'Carregando suas dívidas',
        ),
        error: (e, _) => FiErrorState(
          error: e,
          action: 'carregar suas dívidas',
          onRetry: () => ref.invalidate(debtsProvider),
        ),
        data: (lista) => lista.isEmpty
            ? _NoDebt(onRegister: () => _openDebtForm(context, ref))
            : _DebtList(
                debts: lista,
                onRegister: () => _openDebtForm(context, ref),
              ),
      ),
    );
  }

  Future<void> _openDebtForm(BuildContext context, WidgetRef ref) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: const _DebtForm(),
      ),
    );
  }
}

class _DebtList extends ConsumerWidget {
  const _DebtList({required this.debts, required this.onRegister});

  final List<Debt> debts;
  final VoidCallback onRegister;

  static const _classLabel = {
    DebtClass.expensive: 'Caseira',
    DebtClass.manageable: 'Administrável',
    DebtClass.noRate: 'Sem taxa informada',
  };

  static FiState _state(DebtClass c) => switch (c) {
    DebtClass.expensive => FiState.adverse,
    DebtClass.manageable => FiState.neutral,
    DebtClass.noRate => FiState.indeterminate,
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final caras = debts.where((d) => d.debtClass == DebtClass.expensive);
    final referencia = debts
        .map((d) => d.referenceMonthly)
        .firstWhere((r) => r != null, orElse: () => null);

    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(debtsProvider),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(
          FiLayout.gutter,
          FiSpace.s2,
          FiLayout.gutter,
          FiLayout.scrollTail,
        ),
        children: [
          Text(
            caras.isEmpty
                ? 'Nenhuma dívida sua custa mais do que sua carteira rende.'
                : 'Você tem ${caras.length} '
                      '${caras.length == 1 ? 'dívida que custa' : 'dívidas que custam'} mais do '
                      'que sua carteira rende.',
            style: fiSerif(FiType.verdict).copyWith(
              color: fiStateColor(
                caras.isEmpty ? FiState.favorable : FiState.adverse,
                Theme.of(context).brightness,
              ),
            ),
          ),

          FiProvenance(
            summary: 'Como classificamos',
            method:
                'Compara a taxa mensal de cada dívida com o que sua carteira rende ao mês. '
                'Acima disso, pagar a dívida rende mais que investir.',
            source: referencia == null
                ? 'Sem taxa informada em nenhuma dívida, não há o que comparar.'
                : 'Referência: ${formatPercent(referencia)} ao mês, de '
                      '${debts.first.referenceSource == 'bcb' ? 'CDI do BCB' : debts.first.referenceSource}.',
            limitation:
                'Dívida sem taxa informada fica sem classe: o produto não estima taxa de '
                'rotativo, que varia por banco e por dia.',
          ),

          FiSection(
            title: 'Suas dívidas',
            count: debts.length,
            action: FiButton.secondary(
              label: 'Cadastrar dívida',
              icon: Icons.add,
              onPressed: onRegister,
            ),
            child: Column(
              children: [
                for (final d in debts)
                  _DebtRow(
                    debt: d,
                    label: _classLabel[d.debtClass] ?? '',
                    state: _state(d.debtClass),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DebtRow extends ConsumerWidget {
  const _DebtRow({
    required this.debt,
    required this.label,
    required this.state,
  });

  final Debt debt;
  final String label;
  final FiState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ExpansionTile(
      title: Row(
        children: [
          Expanded(
            child: Text(
              debt.description,
              style: FiType.body.copyWith(color: fiInk1(context)),
            ),
          ),
          const SizedBox(width: FiSpace.s2),
          FiTag(label: label, state: state),
        ],
      ),
      subtitle: Text(
        debtKindLabel(debt.kind),
        style: FiType.caption.copyWith(color: fiInk3(context)),
      ),
      trailing: Text(
        formatCurrency(debt.balance),
        style: FiType.figure.copyWith(color: fiInk1(context)),
      ),
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: FiSpace.s3),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                debt.monthlyRate == null
                    ? 'Taxa não informada, então não há classe.'
                    : 'Custa ${formatPercent(debt.monthlyRate)} ao mês.',
                style: FiType.body.copyWith(color: fiInk2(context)),
              ),
              if (debt.flipRate != null)
                Text(
                  'Vira administrável a ${formatPercent(debt.flipRate)} ao mês.',
                  style: FiType.caption.copyWith(color: fiInk3(context)),
                ),
              const SizedBox(height: FiSpace.s2),
              Align(
                alignment: Alignment.centerLeft,
                child: FiButton.secondary(
                  label: 'Marcar como quitada',
                  onPressed: debt.id == null
                      ? null
                      : () => _payOff(context, ref, debt),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _payOff(BuildContext context, WidgetRef ref, Debt d) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Quitar esta dívida?'),
        content: Text(
          '${d.description} sai da sua ordem de sobra, e o veredito do mês passa a não '
          'contá-la.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Quitar dívida'),
          ),
        ],
      ),
    );
    if (ok != true) return;

    await ref.read(apiRepositoryProvider).settleDebt(d.id!);
    ref.invalidate(debtsProvider);
    ref.invalidate(surplusProvider);
    ref.invalidate(cashMonthProvider);
  }
}

class _DebtForm extends ConsumerStatefulWidget {
  const _DebtForm();

  @override
  ConsumerState<_DebtForm> createState() => _DebtFormState();
}

class _DebtFormState extends ConsumerState<_DebtForm> {
  final _form = GlobalKey<FormState>();
  final _description = TextEditingController();
  final _balance = TextEditingController();
  final _rate = TextEditingController();

  String _kind = fiDebtKinds.keys.first;
  bool _saving = false;
  Object? _error;

  @override
  void dispose() {
    _description.dispose();
    _balance.dispose();
    _rate.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;

    final saldo = double.tryParse(
      _balance.text.replaceAll('.', '').replaceAll(',', '.'),
    );
    if (saldo == null) return;

    final rateText = _rate.text.trim();
    final taxa = rateText.isEmpty
        ? null
        : double.tryParse(rateText.replaceAll(',', '.'));

    setState(() => _saving = true);
    try {
      await ref.read(apiRepositoryProvider).createDebt(
        kind: _kind,
        description: _description.text.trim(),
        balance: saldo,
        monthlyRate: taxa,
      );
      ref.invalidate(debtsProvider);
      ref.invalidate(surplusProvider);
      ref.invalidate(cashMonthProvider);

      if (!mounted) return;
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = e;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Form(
          key: _form,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Cadastrar dívida', style: FiType.title),
              const SizedBox(height: FiSpace.s4),

              TextFormField(
                controller: _description,
                decoration: const InputDecoration(labelText: 'Descrição'),
                textCapitalization: TextCapitalization.sentences,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Diga o que é' : null,
              ),
              const SizedBox(height: FiSpace.s3),

              DropdownButtonFormField<String>(
                initialValue: _kind,
                decoration: const InputDecoration(labelText: 'Tipo'),
                items: [
                  for (final e in fiDebtKinds.entries)
                    DropdownMenuItem(value: e.key, child: Text(e.value)),
                ],
                onChanged: (v) => setState(() => _kind = v ?? _kind),
              ),
              const SizedBox(height: FiSpace.s3),

              TextFormField(
                controller: _balance,
                decoration: const InputDecoration(
                  labelText: 'Saldo devedor',
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

              TextFormField(
                controller: _rate,
                decoration: const InputDecoration(
                  labelText: 'Taxa mensal (opcional)',
                  suffixText: '% ao mês',
                  helperText:
                      'Sem a taxa não há classe: o produto não estima taxa de rotativo.',
                  helperMaxLines: 2,
                ),
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
              ),

              if (_error != null) ...[
                const SizedBox(height: FiSpace.s3),
                Text(
                  fiErrorMessage(_error!, action: 'cadastrar esta dívida'),
                  style: FiType.body.copyWith(
                    color: fiStateColor(
                      FiState.adverse,
                      Theme.of(context).brightness,
                    ),
                  ),
                ),
              ],

              const SizedBox(height: FiSpace.s5),
              FiButton.primary(
                label: 'Cadastrar dívida',
                expand: true,
                busy: _saving,
                onPressed: _save,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NoDebt extends StatelessWidget {
  const _NoDebt({required this.onRegister});

  final VoidCallback onRegister;

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        FiEmptyState(
          title: 'Você não tem dívida cadastrada',
          body: 'A ordem da sobra começa pela dívida que custa mais do que sua carteira '
              'rende. Sem cadastrar, ela não entra na conta — e é a que decide se aportar '
              'faz sentido.',
          hint: 'A taxa mensal é opcional, mas sem ela não há classe: o produto não estima '
              'taxa de rotativo.',
          action: FiButton.primary(
            label: 'Cadastrar dívida',
            icon: Icons.add,
            onPressed: onRegister,
          ),
        ),
      ],
    );
  }
}
