import 'package:flutter/material.dart';

import '../theme.dart';

/// O recorte de uma seção: rótulos curtos separados por ponto médio.
///
/// Recorte não é ação: ele muda **o que** se lê, e por isso tem peso de legenda. O alvo de toque
/// continua sendo o da norma, porque a área clicável não é a tinta.
class FiSegments<T> extends StatelessWidget {
  const FiSegments({
    super.key,
    required this.selected,
    required this.options,
    required this.onSelect,
    this.semanticsPrefix = 'Mostrar',
  });

  final T selected;

  final Map<T, String> options;

  final ValueChanged<T> onSelect;

  final String semanticsPrefix;

  @override
  Widget build(BuildContext context) {
    final entradas = options.entries.toList();

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (var i = 0; i < entradas.length; i++) ...[
          if (i > 0)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: FiSpace.s1),
              child: Text(
                '·',
                style: FiType.caption.copyWith(color: fiInk3(context)),
              ),
            ),
          _Opcao(
            label: entradas[i].value,
            selecionado: entradas[i].key == selected,
            semanticsLabel: '$semanticsPrefix ${entradas[i].value}',
            onTap: () => onSelect(entradas[i].key),
          ),
        ],
      ],
    );
  }
}

class _Opcao extends StatelessWidget {
  const _Opcao({
    required this.label,
    required this.selecionado,
    required this.semanticsLabel,
    required this.onTap,
  });

  final String label;
  final bool selecionado;
  final String semanticsLabel;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      selected: selecionado,
      label: semanticsLabel,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(FiRadius.sm),
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: FiSpace.s2),
            child: Center(
              widthFactor: 1,
              child: Text(
                label,
                style: FiType.caption.copyWith(
                  color: selecionado ? fiInk1(context) : fiInk3(context),
                  fontWeight: selecionado ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
