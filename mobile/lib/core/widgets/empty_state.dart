import 'package:flutter/material.dart';

import '../theme.dart';
import 'button.dart';

/// Ausencia de dado, numa voz so.
///
/// E o par de `FiErrorState`, e a separacao entre os dois e invariante: "nao conseguimos ler" e
/// "voce ainda nao tem nada" sao estados diferentes, e nunca compartilham a mesma tela.
class FiEmptyState extends StatelessWidget {
  const FiEmptyState({
    super.key,
    required this.title,
    required this.body,
    this.hint,
    this.action,
    this.secondary,
  });

  /// A frase que nomeia a ausencia. Descreve o estado, nao cobra a pessoa.
  final String title;

  /// Por que isto importa, e o que destrava.
  final String body;

  /// Uma instrucao concreta.
  final String? hint;

  final Widget? action;
  final Widget? secondary;

  @override
  Widget build(BuildContext context) {
    final acao = action;

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        FiLayout.gutter,
        FiSpace.s8,
        FiLayout.gutter,
        FiSpace.s6,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: fiSerif(FiType.verdict).copyWith(color: fiInk1(context)),
          ),
          const SizedBox(height: FiSpace.s3),
          Text(body, style: FiType.body.copyWith(color: fiInk2(context))),
          if (hint != null) ...[
            const SizedBox(height: FiSpace.s2),
            Text(hint!, style: FiType.caption.copyWith(color: fiInk3(context))),
          ],
          if (acao != null) ...[
            const SizedBox(height: FiSpace.s6),
            FiActions(primary: acao, secondary: secondary),
          ],
        ],
      ),
    );
  }
}

/// A ausencia dentro de uma secao: a linha que diz por que nao ha nada ali, e nada mais.
class FiEmptyLine extends StatelessWidget {
  const FiEmptyLine(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: FiSpace.s2),
      child: Text(text, style: FiType.body.copyWith(color: fiInk2(context))),
    );
  }
}
