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
  }) : destructive = false;

  const FiButton.primary({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
    this.busy = false,
  }) : tone = FiButtonTone.primary,
       destructive = false;

  const FiButton.secondary({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
    this.busy = false,
  }) : tone = FiButtonTone.secondary,
       destructive = false;

  const FiButton.quiet({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
    this.busy = false,
    this.destructive = false,
  }) : tone = FiButtonTone.quiet;

  const FiButton.danger({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
    this.busy = false,
  }) : tone = FiButtonTone.danger,
       destructive = true;

  final String label;
  final VoidCallback? onPressed;
  final FiButtonTone tone;

  final IconData? icon;

  final bool expand;

  final bool busy;

  final bool destructive;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final acionavel = onPressed != null && !busy;
    final tocar = acionavel ? onPressed : null;
    final adverso = fiStateColor(FiState.adverse, brightness);

    final filho = _Content(label: label, icon: icon, busy: busy, expand: expand);

    final botao = switch (tone) {
      FiButtonTone.primary => FilledButton(onPressed: tocar, child: filho),
      FiButtonTone.secondary => OutlinedButton(onPressed: tocar, child: filho),
      FiButtonTone.danger => OutlinedButton(
        onPressed: tocar,
        style: OutlinedButton.styleFrom(foregroundColor: adverso).copyWith(
          side: WidgetStateProperty.resolveWith(
            (estados) => BorderSide(
              color: estados.contains(WidgetState.disabled)
                  ? Theme.of(context).colorScheme.outlineVariant
                  : adverso,
            ),
          ),
        ),
        child: filho,
      ),
      FiButtonTone.quiet => TextButton(
        onPressed: tocar,
        style: TextButton.styleFrom(
          padding: EdgeInsets.zero,
          foregroundColor: destructive ? adverso : null,
        ),
        child: filho,
      ),
    };

    if (!expand) return botao;
    return SizedBox(width: double.infinity, child: botao);
  }
}

class _Content extends StatelessWidget {
  const _Content({
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
