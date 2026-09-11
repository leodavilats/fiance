import 'package:flutter/material.dart';

import '../theme.dart';

/// O selo de estado: veredito, severidade, classe.
class FiTag extends StatelessWidget {
  const FiTag({super.key, required this.label, this.state = FiState.neutral, this.color});

  const FiTag.serie({super.key, required this.label, required Color this.color})
    : state = FiState.neutral;

  final String label;
  final FiState state;

  /// A tinta de identidade -- a cor da categoria ou da serie. O selo entao e contorno e texto:
  /// identidade nao e julgamento, e nao merece area colorida.
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final identidade = color;

    final tinta = identidade ?? fiStateColor(state, brightness);
    final fundo = identidade == null ? fiStateSurface(state, brightness) : null;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: FiSpace.s2, vertical: 2),
      decoration: BoxDecoration(
        color: fundo,
        border: identidade == null ? null : Border.all(color: tinta.withValues(alpha: 0.55)),
        borderRadius: BorderRadius.circular(FiRadius.sm),
      ),
      child: Text(
        label,
        style: FiType.eyebrow.copyWith(color: tinta, letterSpacing: 0.6),
      ),
    );
  }
}
