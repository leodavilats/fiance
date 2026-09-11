import 'package:flutter/material.dart';

import '../format.dart';
import '../theme.dart';

class FiRange extends StatelessWidget {
  const FiRange({
    super.key,
    required this.low,
    required this.high,
    this.base,
    this.label = '',
    this.hypothesis = '',
  });

  final double low;
  final double high;

  final double? base;

  final String label;

  final String hypothesis;

  @override
  Widget build(BuildContext context) {
    final ink2 = fiInk2(context);
    final ink3 = fiInk3(context);

    return Semantics(
      label: label.isEmpty
          ? 'Entre ${formatCurrency(low)} e ${formatCurrency(high)}'
          : '$label: entre ${formatCurrency(low)} e ${formatCurrency(high)}',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (label.isNotEmpty)
            Text(label, style: FiType.caption.copyWith(color: ink2)),
          Text(
            'entre ${formatCurrency(low)} e ${formatCurrency(high)}',
            style: FiType.metricSm,
          ),
          if (base != null)
            Text(
              'cenário base: ${formatCurrency(base)}',
              style: FiType.caption.copyWith(color: ink3),
            ),
          if (hypothesis.isNotEmpty)
            Text(hypothesis, style: FiType.caption.copyWith(color: ink3)),
        ],
      ),
    );
  }
}
