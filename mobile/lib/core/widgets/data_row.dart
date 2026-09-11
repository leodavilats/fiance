import 'package:flutter/material.dart';

import '../theme.dart';

/// Uma linha de dado: rotulo a esquerda, valor a direita, fio embaixo.
///
/// Com `onTap` a linha inteira e o alvo, com a altura minima de acessibilidade. Sem `onTap` ela
/// e so leitura, e nao finge ser tocavel.
class FiDataRow extends StatelessWidget {
  const FiDataRow({
    super.key,
    required this.label,
    this.value,
    this.valueColor,
    this.detail,
    this.note,
    this.leading,
    this.trailing,
    this.onTap,
    this.emphasis = false,
    this.dense = false,
  });

  final String label;

  /// A cifra ou o estado, alinhado a direita.
  final String? value;

  final Color? valueColor;

  final String? detail;

  /// Ocupa o lugar do valor quando ele nao e texto -- uma regua, um interruptor.
  final Widget? trailing;

  /// Um marcador antes do rotulo: informacao, nunca enfeite.
  final Widget? leading;

  /// Rodape da propria linha, em tinta terciaria.
  final String? note;

  /// A linha que resume o bloco. Sai em peso, nao em caixa.
  final bool emphasis;

  final bool dense;

  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final navegavel = onTap != null;

    final corpo = Padding(
      padding: EdgeInsets.symmetric(vertical: dense ? FiSpace.s2 : FiSpace.s3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (leading != null) ...[
            leading!,
            const SizedBox(width: FiSpace.s3),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: emphasis
                      ? FiType.title
                      : FiType.body.copyWith(color: fiInk1(context)),
                ),
                if (detail != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    detail!,
                    style: FiType.caption.copyWith(color: fiInk2(context)),
                  ),
                ],
                if (note != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    note!,
                    style: FiType.caption.copyWith(color: fiInk3(context)),
                  ),
                ],
              ],
            ),
          ),
          if (value != null || trailing != null) const SizedBox(width: FiSpace.s4),
          // `Flexible`: o valor as vezes e uma frase, e sem ele a linha estoura em 320dp.
          if (value != null)
            Flexible(
              child: Text(
                value!,
                textAlign: TextAlign.end,
                style: (emphasis ? FiType.metricSm : FiType.figure).copyWith(
                  color: valueColor ?? fiInk1(context),
                ),
              ),
            ),
          ?trailing,
          if (navegavel) ...[
            const SizedBox(width: FiSpace.s2),
            Icon(Icons.chevron_right, size: 18, color: fiInk3(context)),
          ],
        ],
      ),
    );

    if (!navegavel) return corpo;

    return Semantics(
      button: true,
      label: value == null ? label : '$label: $value',
      child: InkWell(
        onTap: onTap,
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
          child: corpo,
        ),
      ),
    );
  }
}

/// Uma pilha de linhas separadas por fio, sem caixa em volta.
class FiRows extends StatelessWidget {
  const FiRows({super.key, required this.children, this.divided = true});

  final List<Widget> children;

  final bool divided;

  @override
  Widget build(BuildContext context) {
    if (children.isEmpty) return const SizedBox.shrink();
    if (!divided) {
      return Column(crossAxisAlignment: CrossAxisAlignment.start, children: children);
    }

    final hairline = fiHairline(Theme.of(context).brightness);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var i = 0; i < children.length; i++) ...[
          if (i > 0) Divider(color: hairline, height: 1, thickness: 1),
          children[i],
        ],
      ],
    );
  }
}

/// A unica caixa do sistema, e so para o que e **objeto**: uma posicao, um titulo, uma
/// oportunidade -- o que a pessoa abre, vende ou remove. O resto e `FiSection`.
class FiObject extends StatelessWidget {
  const FiObject({
    super.key,
    required this.child,
    this.onTap,
    this.padding = const EdgeInsets.all(FiSpace.s4),
    this.accent,
    this.semanticsLabel,
  });

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsets padding;

  /// A tinta da aresta esquerda, quando o objeto carrega estado. Nada de fundo tingido: cor de
  /// estado em area grande compete com o proprio numero.
  final Color? accent;

  final String? semanticsLabel;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final borda = fiHairline(brightness);

    final conteudo = Padding(padding: padding, child: child);

    // `IntrinsicHeight` so quando ha aresta: sem ele o `stretch` do `Row` pede altura infinita
    // dentro de uma lista rolavel.
    Widget corpo = DecoratedBox(
      decoration: BoxDecoration(
        color: fiGround1(brightness),
        borderRadius: BorderRadius.circular(FiRadius.md),
        border: Border.all(color: borda),
      ),
      child: accent == null
          ? conteudo
          : IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Container(
                    width: 3,
                    decoration: BoxDecoration(
                      color: accent,
                      borderRadius: const BorderRadius.horizontal(
                        left: Radius.circular(FiRadius.md),
                      ),
                    ),
                  ),
                  Expanded(child: conteudo),
                ],
              ),
            ),
    );

    if (onTap != null) {
      corpo = InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(FiRadius.md),
        child: corpo,
      );
    }

    if (semanticsLabel != null) {
      corpo = Semantics(label: semanticsLabel, container: true, child: corpo);
    }

    return corpo;
  }
}
