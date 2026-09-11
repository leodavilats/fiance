import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/labels.dart';
import '../../../core/models.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/data_row.dart';
import '../../../core/widgets/nav_action.dart';
import '../../../core/widgets/tag.dart';
import '../feed_actions.dart';
import '../../../core/score_ruler.dart';

/// Um item do feed: o que mudou, e o que fazer com isso. O estado vive na aresta do objeto.
class FiInsightTile extends StatelessWidget {
  const FiInsightTile({
    super.key,
    required this.state,
    required this.title,
    required this.detail,
    this.actionLabel,
    this.onAction,
  });

  final FiState state;
  final String title;
  final String detail;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final rotulo = actionLabel;

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        accent: fiStateColor(state, Theme.of(context).brightness),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: FiType.title.copyWith(color: fiInk1(context))),
            const SizedBox(height: FiSpace.s1),
            Text(detail, style: FiType.body.copyWith(color: fiInk2(context))),
            if (rotulo != null) ...[
              const SizedBox(height: FiSpace.s2),
              Align(
                alignment: Alignment.centerLeft,
                child: FiNavAction(label: rotulo, onPressed: onAction),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class FiAlertTile extends StatelessWidget {
  const FiAlertTile({super.key, required this.alert});

  final PortfolioAlert alert;

  @override
  Widget build(BuildContext context) {
    return FiInsightTile(
      state: fiSeverityState(alert.severity),
      title: alert.count > 1 ? '${alert.title} (${alert.count})' : alert.title,
      detail: alert.detail,
      actionLabel: alert.actionLabel,
      onAction: () => runHojeAction(context, alert.action, alert.ticker),
    );
  }
}

class FiWhatsNewTile extends StatelessWidget {
  const FiWhatsNewTile({super.key, required this.item});

  final WhatsNewItem item;

  @override
  Widget build(BuildContext context) {
    return FiInsightTile(
      state: fiSeverityState(item.severity),
      title: item.title,
      detail: item.detail,
      actionLabel: item.actionLabel,
      onAction: () => runHojeAction(context, item.action, item.ticker),
    );
  }
}

class FiVerdictChip extends StatelessWidget {
  const FiVerdictChip({super.key, required this.verdict, required this.label});

  final String verdict;
  final String label;

  @override
  Widget build(BuildContext context) {
    return FiTag(label: label, state: fiVerdictState(verdict));
  }
}

class FiOpportunityTile extends StatelessWidget {
  const FiOpportunityTile({super.key, required this.opportunity, this.onTap});

  final Opportunity opportunity;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final o = opportunity;
    // Rotulo e estado saem da mesma regua: o rotulo do score com a cor do veredito seriam
    // duas reguas no mesmo selo.
    final band = fiScoreBandFor(o.score, o.dataCompleteness);

    return Padding(
      padding: const EdgeInsets.only(bottom: FiSpace.s2),
      child: FiObject(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        o.ticker,
                        style: FiType.ticker.copyWith(color: fiInk1(context)),
                      ),
                      if (o.name != null)
                        Text(
                          o.name!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: FiType.caption.copyWith(color: fiInk2(context)),
                        ),
                    ],
                  ),
                ),
                const SizedBox(width: FiSpace.s3),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      formatCurrency(o.price),
                      style: FiType.metricSm.copyWith(color: fiInk1(context)),
                    ),
                    Text(
                      'DY ${formatPercent(o.dividendYield)}',
                      style: FiType.caption.copyWith(color: fiInk2(context)),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: FiSpace.s3),
            Row(
              children: [
                FiTag(label: band.label, state: band.state),
                const SizedBox(width: FiSpace.s2),
                Expanded(
                  child: Text(
                    '${dataYearsLabel(o.dataYears)} · ${consensusLabel(o.consensusMethods)}',
                    style: FiType.caption.copyWith(color: fiInk3(context)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
