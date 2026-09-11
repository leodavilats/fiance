import 'package:flutter/material.dart';

import '../theme.dart';

/// A ação que leva a outro lugar, com forma de controle.
///
/// No tema escuro a marca é clara e salta do chão; no claro ela é um azul fechado
/// (`#295D7C`) que, escrito sem mais nada, tem a mesma cara de texto do corpo. Quem olhava
/// "Repetir agosto" e "Decidir o que fazer com ela" não via um controle — via uma frase.
///
/// Cor não é affordance sozinha: a seta é o que diz que aquilo leva a algum lugar, e ela
/// aparece nos dois temas.
class FiNavAction extends StatelessWidget {
  const FiNavAction({super.key, required this.label, required this.onPressed, this.icon});

  final String label;
  final VoidCallback? onPressed;

  /// Um ícone à esquerda, quando a ação tem um objeto próprio (dívida, mês, meta).
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final marca = Theme.of(context).colorScheme.primary;

    return TextButton(
      onPressed: onPressed,
      // Sem recuo horizontal: a acao alinha com a coluna de texto que a precede, e o alvo de
      // toque continua vindo da altura minima do tema.
      style: TextButton.styleFrom(padding: EdgeInsets.zero),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 16, color: marca),
            const SizedBox(width: FiSpace.s1),
          ],
          Flexible(
            child: Text(
              label,
              style: FiType.label.copyWith(color: marca),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Icon(Icons.chevron_right, size: 18, color: marca),
        ],
      ),
    );
  }
}
