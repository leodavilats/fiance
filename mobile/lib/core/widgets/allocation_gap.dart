import 'package:flutter/material.dart';

import '../theme.dart';
import 'measure.dart';

/// Sem meta declarada nao ha julgamento: o estado e indeterminado, e a linha diz isso.
class FiAllocationGap extends StatelessWidget {
  const FiAllocationGap({
    super.key,
    required this.label,
    required this.currentPct,
    this.targetPct,
    this.barColor,
    this.trailing,
  });

  final String label;
  final double currentPct;
  final double? targetPct;
  final Color? barColor;

  final String? trailing;

  @override
  Widget build(BuildContext context) {
    final alvo = targetPct;
    final temAlvo = alvo != null;
    final delta = temAlvo ? currentPct - alvo : 0.0;
    final band = fiBandFor(delta.abs(), fiAllocationGapBands, temAlvo ? 1 : 0);

    final partes = <String>[
      ?trailing,
      if (temAlvo)
        'meta ${alvo.toStringAsFixed(0)}%'
      else
        'sem meta declarada',
      if (temAlvo && delta.abs() >= 1)
        '${delta.abs().toStringAsFixed(1)} p.p. ${delta > 0 ? 'acima' : 'abaixo'}'
      else if (temAlvo)
        'na meta',
    ];

    return FiMeasure(
      label: label,
      value: currentPct,
      reference: temAlvo ? alvo : null,
      readout: '${currentPct.toStringAsFixed(1)}%',
      note: partes.join(' · '),
      state: band.state,
      fillColor: barColor ?? fiInk3(context),
      semantics: temAlvo
          ? '$label: ${currentPct.toStringAsFixed(1)}% da carteira contra meta de '
                '${alvo.toStringAsFixed(1)}% — ${delta.abs().toStringAsFixed(1)} pontos '
                'percentuais ${delta > 0 ? 'acima' : 'abaixo'}, ${band.label.toLowerCase()}'
          : '$label: ${currentPct.toStringAsFixed(1)}% da carteira, sem meta definida',
    );
  }
}
