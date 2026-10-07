import 'package:flutter/material.dart';

import '../format.dart';
import '../theme.dart';
import 'measure.dart';

class FiAllocationGap extends StatelessWidget {
  const FiAllocationGap({
    super.key,
    required this.label,
    required this.currentPct,
    this.targetPct,
    this.barColor,
    this.trailing,
    this.judged = true,
  });

  final String label;
  final double currentPct;
  final double? targetPct;
  final Color? barColor;

  final String? trailing;

  final bool judged;

  @override
  Widget build(BuildContext context) {
    final alvo = targetPct;
    final temAlvo = alvo != null;
    final delta = temAlvo ? currentPct - alvo : 0.0;
    final band = fiBandFor(delta.abs(), fiAllocationGapBands, temAlvo ? 1 : 0);

    final partes = <String>[
      ?trailing,
      if (temAlvo)
        'meta ${formatPercent(alvo, digits: 0)}'
      else if (judged)
        'sem meta declarada',
      if (temAlvo && band.id != 'on-target')
        '${formatPoints(delta.abs())} ${delta > 0 ? 'acima' : 'abaixo'}'
      else if (temAlvo)
        'na meta',
    ];

    return FiMeasure(
      label: label,
      value: currentPct,
      reference: temAlvo ? alvo : null,
      readout: formatPercent(currentPct, digits: 1),
      note: partes.isEmpty ? null : partes.join(' · '),
      state: band.state,
      fillColor: barColor ?? fiInk3(context),
      semantics: temAlvo
          ? '$label: ${formatPercent(currentPct, digits: 1)} da carteira contra meta de '
                '${formatPercent(alvo, digits: 1)} — ${formatDecimal(delta.abs())} pontos '
                'percentuais ${delta > 0 ? 'acima' : 'abaixo'}, ${band.label.toLowerCase()}'
          : '$label: ${formatPercent(currentPct, digits: 1)} da carteira'
                '${judged ? ', sem meta definida' : ''}',
    );
  }
}
