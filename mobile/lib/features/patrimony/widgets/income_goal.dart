import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/measure.dart';
import '../../../core/widgets/provenance.dart';

class FiIncomeGoalBlock extends StatelessWidget {
  const FiIncomeGoalBlock({super.key, required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final meta = summary.passiveIncomeGoal;
    if (meta == null) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        FiMeasure(
          label: 'Meta de renda passiva',
          value: (summary.passiveIncomeProgress ?? 0).clamp(0, 100),
          readout: '${formatCurrency(meta)}/mês',
          reference: 100,
          note:
              '${formatPercent(summary.passiveIncomeProgress ?? 0, digits: 0)} do alvo, '
              'com ${formatCurrency(summary.monthlyDividendsEstimate)} por mês estimados',
          state: fiBandFor(summary.passiveIncomeProgress ?? 0, fiGoalProgressBands, 1).state,
        ),
        FiProvenance(
          summary: 'Como lemos o progresso da meta',
          method:
              'Os proventos estimados dos próximos doze meses, divididos pela meta mensal '
              'que você declarou. A faixa nomeada vem da régua de progresso do sistema.',
          source: 'Suas posições e o histórico de proventos de cada papel.',
          limitation:
              'É estimativa de provento, não promessa: corte de dividendo do emissor muda o '
              'número sem aviso.',
        ),
      ],
    );
  }
}
