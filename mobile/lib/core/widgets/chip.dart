import 'package:flutter/material.dart';

import '../theme.dart';

class FiChoiceChip extends StatelessWidget {
  const FiChoiceChip({
    super.key,
    required this.label,
    required this.selected,
    required this.onSelected,
    this.onRemove,
  });

  final String label;
  final bool selected;
  final VoidCallback onSelected;

  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    final marca = Theme.of(context).colorScheme.primary;

    final tinta = selected ? marca : fiInk2(context);
    final borda = selected ? marca : fiHairline(brightness);

    return Semantics(
      button: true,
      selected: selected,
      label: label,
      onTap: onSelected,
      child: ExcludeSemantics(
        child: Material(
          color: selected
              ? marca.withValues(alpha: 0.10)
              : fiGround1(brightness),
          borderRadius: BorderRadius.circular(FiRadius.pill),
          child: InkWell(
            onTap: onSelected,
            borderRadius: BorderRadius.circular(FiRadius.pill),
            child: Container(
              constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(FiRadius.pill),
                border: Border.all(color: borda),
              ),
              padding: const EdgeInsets.symmetric(
                horizontal: FiSpace.s3,
                vertical: FiSpace.s2,
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(label, style: FiType.caption.copyWith(color: tinta)),
                  if (onRemove != null) ...[
                    const SizedBox(width: FiSpace.s1),
                    Icon(Icons.close, size: 14, color: tinta),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
