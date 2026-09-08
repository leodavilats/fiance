import 'package:flutter/material.dart';

import '../glossary.dart';
import '../theme.dart';

/// O termo do glossario, num sheet.
///
/// Era um `GestureDetector` sobre um icone de 14px: sem `Semantics`, portanto invisivel para
/// quem usa leitor de tela, e com alvo de toque de 14 contra os 44 que `FiLayout.minTouchTarget`
/// declara no arquivo ao lado. A semantica esta resolvida aqui.
///
/// O alvo ficou em 32, nao em 44: este gatilho vive num `Row` ao lado de um rotulo de 11px, e
/// 44 de altura dobraria a linha inteira. Chegar aos 44 exige repensar aquela linha -- fazer o
/// rotulo todo ser o alvo, em vez de pendurar um icone ao lado dele -- e isso e decisao de
/// layout, nao de acessibilidade. Esta registrado no KNOWN_ISSUES.
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
