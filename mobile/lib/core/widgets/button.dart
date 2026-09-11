import 'package:flutter/material.dart';

import '../theme.dart';

enum FiButtonTone {
  primary,

  secondary,

  quiet,

  danger,
}

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

  final IconData? icon;

  final bool expand;

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
