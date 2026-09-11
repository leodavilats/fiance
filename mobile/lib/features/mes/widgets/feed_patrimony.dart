import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/models.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/measure.dart';
import '../../../core/widgets/provenance.dart';
import '../../../core/widgets/section.dart';

class FiPatrimonyBlock extends StatelessWidget {
  const FiPatrimonyBlock({super.key, required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final positive = summary.totalPnl >= 0;
    final pnlColor = fiDirectionColor(positive ? 1 : -1, brightness);
    final meta = summary.passiveIncomeGoal;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        FiHeadline(
          eyebrow: 'Patrimônio total',
          figure: formatCurrency(summary.totalCurrent),
          size: FiHeadlineSize.xl,
          support:
              '${positive ? '+' : ''}${formatCurrency(summary.totalPnl)} '
              '(${formatPercent(summary.totalPnlPct)}) · '
              '${summary.positionsCount} posições',
          supportColor: pnlColor,
        ),
        const SizedBox(height: FiSpace.s5),
        FiFigures(
          figures: {
            'INVESTIDO': formatCurrency(summary.totalInvested),
            'PROVENTOS/MÊS': formatCurrency(summary.monthlyDividendsEstimate),
          },
        ),
        if (meta != null) ...[
          const SizedBox(height: FiSpace.s5),
          FiMeasure(
            label: 'Meta de renda passiva',
            value: (summary.passiveIncomeProgress ?? 0).clamp(0, 1) * 100,
            readout: '${formatCurrency(meta)}/mês',
            reference: 100,
            note:
                '${((summary.passiveIncomeProgress ?? 0) * 100).toStringAsFixed(0)}% do alvo, '
                'com ${formatCurrency(summary.monthlyDividendsEstimate)} por mês hoje',
            state: fiBandFor(
              (summary.passiveIncomeProgress ?? 0) * 100,
              fiGoalProgressBands,
              1,
            ).state,
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
      ],
    );
  }
}

String fiCompactCurrency(double value) {
  final abs = value.abs();
  if (abs >= 1000000) return 'R\$ ${(value / 1000000).toStringAsFixed(1)}M';
  if (abs >= 1000) return 'R\$ ${(value / 1000).toStringAsFixed(0)}k';
  return formatCurrency(value);
}

/// Quando o dado foi lido, e de onde vem a referência.
///
/// Momento é nível 1, e não nota de rodapé: um preço de anteontem muda a decisão.
class FiFreshnessLine extends StatelessWidget {
  const FiFreshnessLine({super.key, required this.freshness});

  final DataFreshness freshness;

  @override
  Widget build(BuildContext context) {
    final atrasado = freshness.marketDataStale;

    return Padding(
      padding: const EdgeInsets.only(top: FiSpace.s3),
      child: Text(
        '${freshness.label} · ${freshness.ratesLabel}',
        style: FiType.caption.copyWith(
          color: atrasado
              ? fiStateColor(FiState.attention, Theme.of(context).brightness)
              : fiInk3(context),
        ),
      ),
    );
  }
}
