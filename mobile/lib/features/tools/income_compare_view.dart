import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/button.dart';
import '../../core/widgets/data_row.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/measure.dart';
import '../../core/widgets/section.dart';

class IncomeCompareView extends ConsumerStatefulWidget {
  const IncomeCompareView({super.key});

  @override
  ConsumerState<IncomeCompareView> createState() => _IncomeCompareViewState();
}

class _IncomeCompareViewState extends ConsumerState<IncomeCompareView> {
  final _amountCtrl = TextEditingController(text: '10000');
  int _horizonMonths = 12;

  IncomeCompare? _result;
  bool _loading = false;
  Object? _error;

  @override
  void dispose() {
    _amountCtrl.dispose();
    super.dispose();
  }

  Future<void> _compare() async {
    final amount = double.tryParse(_amountCtrl.text.replaceAll(',', '.'));
    if (amount == null || amount <= 0) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final res = await ref
          .read(apiRepositoryProvider)
          .incomeCompare(amount: amount, horizonMonths: _horizonMonths);
      if (mounted) setState(() => _result = res);
    } catch (err) {
      if (mounted) setState(() => _error = err);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ink2 = fiInk2(context);
    final ink3 = fiInk3(context);

    return ListView(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s3,
        FiLayout.gutter,
        FiLayout.scrollTail,
      ),
      children: [
        TextField(
          controller: _amountCtrl,
          decoration: const InputDecoration(
            labelText: 'Valor a comparar (R\$)',
          ),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
        ),
        const SizedBox(height: FiSpace.s3),
        DropdownButtonFormField<int>(
          initialValue: _horizonMonths,
          decoration: const InputDecoration(labelText: 'Prazo'),
          items: const [
            DropdownMenuItem(value: 6, child: Text('6 meses')),
            DropdownMenuItem(value: 12, child: Text('12 meses')),
            DropdownMenuItem(value: 24, child: Text('2 anos')),
            DropdownMenuItem(value: 60, child: Text('5 anos')),
          ],
          onChanged: (v) => setState(() => _horizonMonths = v ?? 12),
        ),
        const SizedBox(height: FiSpace.s5),
        FiButton.primary(
          label: 'Comparar depois do IR',
          expand: true,
          busy: _loading,
          onPressed: _compare,
        ),

        if (_error != null) ...[
          const SizedBox(height: FiSpace.s4),
          FiErrorState(error: _error!, action: 'comparar renda fixa e bolsa'),
        ],

        if (_result != null) ..._buildResult(_result!, ink2, ink3),
      ],
    );
  }

  List<Widget> _buildResult(IncomeCompare r, Color ink2, Color ink3) {
    final todas = [...r.fixedIncome, ...r.assets];
    final maior = todas.isEmpty
        ? r.cdiAnual
        : todas
              .map((o) => o.netIncomeYieldPct)
              .reduce((a, b) => a > b ? a : b);
    final teto = (maior > r.cdiAnual ? maior : r.cdiAnual) * 1.15 + 0.5;

    return [
      const SizedBox(height: FiSpace.s6),
      if (r.verdict.isNotEmpty) ...[
        Text(
          r.verdict,
          style: fiSerif(FiType.verdict).copyWith(color: fiInk1(context)),
        ),
        const SizedBox(height: FiSpace.s2),
      ],
      Text(
        'CDI a ${r.cdiAnual.toStringAsFixed(2)}% ao ano · '
        '${formatCurrency(r.amount)} por ${r.horizonMonths} meses. '
        'A marca em cada régua é o CDI.',
        style: FiType.caption.copyWith(color: ink3),
      ),

      if (r.fixedIncome.isNotEmpty)
        FiSection(
          title: 'Renda fixa',
          child: Column(
            children: [
              for (final o in r.fixedIncome)
                _OptionObject(option: o, cdi: r.cdiAnual, teto: teto),
            ],
          ),
        ),

      if (r.assets.isNotEmpty)
        FiSection(
          title: 'Bolsa',
          child: Column(
            children: [
              for (final o in r.assets)
                _OptionObject(option: o, cdi: r.cdiAnual, teto: teto),
            ],
          ),
        ),

      const SizedBox(height: FiSpace.s6),
      Text(r.disclaimer, style: FiType.caption.copyWith(color: ink3)),
    ];
  }
}

String liquidityLabel(String liquidity) => switch (liquidity) {
  'diaria' => 'Resgate diário',
  'no_vencimento' => 'Só no vencimento',
  'bolsa' => 'Venda em bolsa (D+2)',
  _ => liquidity,
};

class _OptionObject extends StatelessWidget {
  const _OptionObject({
    required this.option,
    required this.cdi,
    required this.teto,
  });

  final IncomeOption option;
  final double cdi;
  final double teto;

  @override
  Widget build(BuildContext context) {
    final o = option;
    final acimaDoCdi = o.netIncomeYieldPct >= cdi;

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            FiMeasure(
              label: o.label,
              value: o.netIncomeYieldPct,
              max: teto,
              reference: cdi,
              readout: '${o.netIncomeYieldPct.toStringAsFixed(2)}% a.a.',
              note: acimaDoCdi
                  ? 'acima do CDI, já descontado o IR'
                  : 'abaixo do CDI, já descontado o IR',
              state: acimaDoCdi ? FiState.favorable : FiState.neutral,
            ),
            const SizedBox(height: FiSpace.s2),
            Text(
              o.incomeBasis,
              style: FiType.body.copyWith(color: fiInk2(context)),
            ),
            const SizedBox(height: FiSpace.s2),
            Text(
              'Renda estimada ${formatCurrency(o.monthlyIncomeEstimate)}/mês · '
              '${liquidityLabel(o.liquidity)}'
              '${o.taxNote.isNotEmpty ? ' · ${o.taxNote}' : ''}',
              style: FiType.caption.copyWith(color: fiInk3(context)),
            ),
            if (o.hasUpside)
              Text(
                'Pode valorizar além da renda — e pode desvalorizar.',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            if (o.riskNote.isNotEmpty)
              Text(
                o.riskNote,
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
          ],
        ),
      ),
    );
  }
}
