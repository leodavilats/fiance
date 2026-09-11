import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/data_row.dart';
import '../../../core/widgets/section.dart';

/// A abertura do Patrimonio: o valor de hoje e o que o explica.
class FiCarteiraSummary extends StatelessWidget {
  const FiCarteiraSummary({super.key, required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final positive = summary.totalPnl >= 0;
    final pnlColor = fiDirectionColor(positive ? 1 : -1, brightness);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        FiHeadline(
          eyebrow: 'Valor de hoje',
          figure: formatCurrency(summary.totalCurrent),
          size: FiHeadlineSize.xl,
          support:
              '${positive ? '+' : ''}${formatCurrency(summary.totalPnl)} '
              '(${formatPercent(summary.totalPnlPct)}) sobre o que você aplicou',
          supportColor: pnlColor,
        ),
        const SizedBox(height: FiSpace.s5),
        FiFigures(
          figures: {
            'APLICADO': formatCurrency(summary.totalInvested),
            'PROVENTOS/MÊS': formatCurrency(summary.monthlyDividendsEstimate),
            'ATIVOS': '${summary.positionsCount}',
          },
        ),
      ],
    );
  }
}

class FiFixedIncomeSummary extends StatelessWidget {
  const FiFixedIncomeSummary({super.key, required this.data});

  final FixedIncomeList data;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final vencendo = data.visiveis.where((i) => i.vencimentoProximo).length;

    return FiSection(
      title: 'Renda fixa',
      count: data.visiveis.length,
      child: FiRows(
        children: [
          FiDataRow(
            label: 'Valor de hoje',
            value: formatCurrency(data.totalAtual),
            detail:
                'rendimento de ${formatCurrency(data.totalRendimento)} '
                '(${data.rendimentoPct.toStringAsFixed(2)}%)',
            onTap: () => context.go('/patrimonio/renda-fixa'),
          ),
          if (vencendo > 0)
            FiDataRow(
              label: vencendo == 1
                  ? '1 aplicação vence nos próximos 30 dias'
                  : '$vencendo aplicações vencem nos próximos 30 dias',
              note: 'Planeje a reaplicação antes do vencimento.',
              valueColor: fiStateColor(FiState.attention, brightness),
              onTap: () => context.go('/patrimonio/renda-fixa'),
            ),
        ],
      ),
    );
  }
}
