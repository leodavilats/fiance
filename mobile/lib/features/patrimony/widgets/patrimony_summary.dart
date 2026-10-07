import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/section.dart';

class FiPortfolioSummary extends StatelessWidget {
  const FiPortfolioSummary({super.key, required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final positive = summary.totalPnl >= 0;
    final pnlColor = fiDirectionColor(positive ? 1 : -1, brightness);
    final recebido = summary.dividendsReceivedLast12m;

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
            'PROVENTOS EM 12 MESES':
                recebido == null ? '—' : formatCurrency(recebido),
          },
        ),
      ],
    );
  }
}
