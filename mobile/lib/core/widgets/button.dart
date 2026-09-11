import 'package:flutter/material.dart';

import '../theme.dart';

/// O peso de uma acao na tela.
enum FiButtonTone {
  /// A acao principal daquele contexto. Uma por tela, quase sempre.
  primary,

  /// A alternativa declarada: mesmo alvo, mesmo tipo, peso de papel em vez de tinta.
  secondary,

  /// A acao discreta -- leva a algum lugar, ou muda um recorte. Alinha com a coluna de texto.
  quiet,

  /// O que remove ou desfaz. Sai em contorno, nunca preenchida.
  danger,
}

/// O botao do sistema: o alvo e `FiLayout.minTouchTarget` em todos os tons, e o rotulo inteiro
/// e tocavel.
class FiButton extends StatelessWidget {
  const FiButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.tone = FiButtonTone.secondary,
    this.icon,
    this.expand = false,
    this.busy = false,
  });

  const FiButton.primary({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
    this.busy = false,
  }) : tone = FiButtonTone.primary;

  const FiButton.secondary({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
    this.busy = false,
  }) : tone = FiButtonTone.secondary;

  const FiButton.quiet({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
    this.busy = false,
  }) : tone = FiButtonTone.quiet;

  const FiButton.danger({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
    this.busy = false,
  }) : tone = FiButtonTone.danger;

  final String label;
  final VoidCallback? onPressed;
  final FiButtonTone tone;

  /// Um icone antes do rotulo. Nunca no lugar dele.
  final IconData? icon;

  /// Ocupa a largura do bloco.
  final bool expand;

  /// A acao esta em curso. O disco vive aqui dentro, que e onde ele diz algo.
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final acionavel = onPressed != null && !busy;
    final tocar = acionavel ? onPressed : null;

    final filho = _Conteudo(label: label, icon: icon, busy: busy, expand: expand);

    final botao = switch (tone) {
      FiButtonTone.primary => FilledButton(onPressed: tocar, child: filho),
      FiButtonTone.secondary => OutlinedButton(onPressed: tocar, child: filho),
      FiButtonTone.danger => OutlinedButton(
        onPressed: tocar,
        style: OutlinedButton.styleFrom(
          foregroundColor: fiStateColor(FiState.adverse, brightness),
          side: BorderSide(color: fiStateColor(FiState.adverse, brightness)),
        ),
        child: filho,
      ),
      // Sem recuo horizontal: a acao discreta alinha com a coluna de texto que a precede.
      FiButtonTone.quiet => TextButton(
        onPressed: tocar,
        style: TextButton.styleFrom(padding: EdgeInsets.zero),
        child: filho,
      ),
    };

    if (!expand) return botao;
    return SizedBox(width: double.infinity, child: botao);
  }
}

class _Conteudo extends StatelessWidget {
  const _Conteudo({
    required this.label,
    required this.icon,
    required this.busy,
    required this.expand,
  });

  final String label;
  final IconData? icon;
  final bool busy;
  final bool expand;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: expand ? MainAxisSize.max : MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (busy) ...[
          const SizedBox(
            height: 14,
            width: 14,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: FiSpace.s2),
        ] else if (icon != null) ...[
          Icon(icon, size: 18),
          const SizedBox(width: FiSpace.s2),
        ],
        Flexible(child: Text(label, overflow: TextOverflow.ellipsis)),
      ],
    );
  }
}

/// A hierarquia de acoes de um bloco: uma principal, e no maximo uma alternativa. Em 360dp o
/// par empilha em vez de espremer dois rotulos numa linha.
class FiActions extends StatelessWidget {
  const FiActions({super.key, required this.primary, this.secondary});

  final Widget primary;
  final Widget? secondary;

  @override
  Widget build(BuildContext context) {
    final alternativa = secondary;
    if (alternativa == null) {
      return Align(alignment: Alignment.centerLeft, child: primary);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        primary,
        const SizedBox(height: FiSpace.s2),
        alternativa,
      ],
    );
  }
}
