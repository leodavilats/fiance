import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/design_tokens.dart';
import '../../core/format.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../core/theme.dart';
import '../../core/widgets/error_state.dart';

/// Renda fixa × bolsa: os dois lados da conta na mesma tela.
///
/// O produto tinha o comparador de títulos e o de ativos como universos
/// separados, e a pergunta que as pessoas fazem atravessa os dois: "com a Selic
/// nesse patamar, vale mais o CDB ou o FII?".
///
/// A tabela não iguala as duas colunas. O rendimento de um CDB é contratado; o
/// de um FII é o dividend yield dos últimos doze meses, que é medição do
/// passado e não promessa. Por isso a base de cada número aparece embaixo dele,
/// e a coluna de bolsa diz quando há valorização possível — que é o que a renda
/// fixa não tem e o que não cabe no mesmo percentual.
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
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final ink2 = isDark ? FiColors.darkInk2 : FiColors.lightInk2;
    final ink3 = isDark ? FiColors.darkInk3 : FiColors.lightInk3;

    return ListView(
      padding: const EdgeInsets.all(FiSpace.s4),
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
        const SizedBox(height: FiSpace.s4),
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

        if (_error != null) ...[
          const SizedBox(height: FiSpace.s4),
          FiErrorState(error: _error!, action: 'comparar renda fixa e bolsa'),
        ],

        if (_result != null) ..._buildResult(_result!, ink2, ink3),
      ],
    );
  }

  List<Widget> _buildResult(IncomeCompare r, Color ink2, Color ink3) {
    return [
      const SizedBox(height: FiSpace.s5),
      if (r.verdict.isNotEmpty) ...[
        Text(
          r.verdict,
          style: FiType.verdict.copyWith(fontFamily: fiFontSerif),
        ),
        const SizedBox(height: FiSpace.s2),
      ],
      Text(
        'CDI a ${r.cdiAnual.toStringAsFixed(2)}% ao ano · '
        '${formatCurrency(r.amount)} por ${r.horizonMonths} meses',
        style: FiType.caption.copyWith(color: ink3),
      ),

      if (r.fixedIncome.isNotEmpty) ...[
        const SizedBox(height: FiSpace.s5),
        Text('RENDA FIXA', style: FiType.eyebrow.copyWith(color: ink3)),
        const SizedBox(height: FiSpace.s2),
        ...r.fixedIncome.map(
          (o) => _OptionRow(option: o, ink2: ink2, ink3: ink3),
        ),
      ],

      if (r.assets.isNotEmpty) ...[
        const SizedBox(height: FiSpace.s5),
        Text('BOLSA', style: FiType.eyebrow.copyWith(color: ink3)),
        const SizedBox(height: FiSpace.s2),
        ...r.assets.map((o) => _OptionRow(option: o, ink2: ink2, ink3: ink3)),
      ],

      const SizedBox(height: FiSpace.s5),
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

class _OptionRow extends StatelessWidget {
  const _OptionRow({
    required this.option,
    required this.ink2,
    required this.ink3,
  });

  final IncomeOption option;
  final Color ink2;
  final Color ink3;

  @override
  Widget build(BuildContext context) {
    final hairline = Theme.of(context).brightness == Brightness.dark
        ? FiColors.darkHairline
        : FiColors.lightHairline;

    return Container(
      margin: const EdgeInsets.only(bottom: FiSpace.s2),
      padding: const EdgeInsets.all(FiSpace.s3),
      decoration: BoxDecoration(
        border: Border.all(color: hairline),
        borderRadius: BorderRadius.circular(FiRadius.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(option.label, style: FiType.body)),
              Text(
                '${option.netIncomeYieldPct.toStringAsFixed(2)}% a.a.',
                style: FiType.body.copyWith(fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: FiSpace.s1),
          // De onde o número veio, sempre colado nele: rendimento contratado e
          // dividend yield medido não são a mesma espécie de número.
          Text(option.incomeBasis, style: FiType.caption.copyWith(color: ink2)),
          const SizedBox(height: FiSpace.s1),
          Text(
            '${liquidityLabel(option.liquidity)}'
            '${option.taxNote.isNotEmpty ? ' · ${option.taxNote}' : ''}',
            style: FiType.caption.copyWith(color: ink3),
          ),
          Text(
            'Renda estimada: ${formatCurrency(option.monthlyIncomeEstimate)}/mês',
            style: FiType.caption.copyWith(color: ink3),
          ),
          if (option.hasUpside)
            // A renda fixa não tem isso, e é a diferença que o percentual
            // sozinho esconde.
            Text(
              'Pode valorizar além da renda — e pode desvalorizar.',
              style: FiType.caption.copyWith(color: ink3),
            ),
          if (option.riskNote.isNotEmpty)
            Text(option.riskNote, style: FiType.caption.copyWith(color: ink3)),
        ],
      ),
    );
  }
}
