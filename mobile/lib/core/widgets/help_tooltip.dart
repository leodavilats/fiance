import 'package:flutter/material.dart';

import '../glossary.dart';
import '../theme.dart';

/// O termo do glossario, num sheet.
///
/// O alvo e 32, e nao os 44 de `FiLayout.minTouchTarget`: ele vive num `Row` de rotulo de 11px,
/// e 44 dobraria a linha. Chegar aos 44 exige repensar a linha -- esta no KNOWN_ISSUES.
class HelpTooltip extends StatelessWidget {
  const HelpTooltip({super.key, required this.termKey});

  final String termKey;

  static const double _alvo = 32;

  @override
  Widget build(BuildContext context) {
    final text = glossary[termKey];
    if (text == null) return const SizedBox.shrink();

    return Semantics(
      button: true,
      label: 'O que é isto? Abre a explicação do termo.',
      child: InkWell(
        borderRadius: BorderRadius.circular(FiRadius.pill),
        onTap: () => showModalBottomSheet<void>(
          context: context,
          showDragHandle: true,
          builder: (context) => SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
              child: Text(
                text,
                style: FiType.body.copyWith(color: fiInk2(context)),
              ),
            ),
          ),
        ),
        child: SizedBox(
          width: _alvo,
          height: _alvo,
          child: Center(
            child: Icon(
              Icons.help_outline,
              size: 16,
              color: fiInk3(context),
            ),
          ),
        ),
      ),
    );
  }
}
