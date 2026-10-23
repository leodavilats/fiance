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

    final remover = onRemove;

    return Semantics(
      button: true,
      selected: remover == null ? selected : null,
      label: remover == null ? label : 'Remover filtro $label',
      onTap: remover ?? onSelected,
      child: ExcludeSemantics(
        child: Material(
          color: selected
              ? marca.withValues(alpha: 0.10)
              : fiGround1(brightness),
          borderRadius: BorderRadius.circular(FiRadius.pill),
          child: InkWell(
            onTap: remover ?? onSelected,
            borderRadius: BorderRadius.circular(FiRadius.pill),
            child: Container(
              constraints: const BoxConstraints(minHeight: FiLayout.minTouchTarget),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(FiRadius.pill),
                border: Border.all(color: borda),
              ),
              padding: const EdgeInsets.symmetric(
                horizontal: FiSpace.s3,
                vertical: FiSpace.s2,
              ),
              child: Align(
                widthFactor: 1,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Flexible(
                      child: Text(
                        label,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: FiType.caption.copyWith(color: tinta),
                      ),
                    ),
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
      ),
    );
  }
}

class FiChipBar extends StatelessWidget {
  const FiChipBar({
    super.key,
    required this.children,
    this.padding = const EdgeInsets.symmetric(horizontal: FiLayout.gutter),
  });

  final List<Widget> children;

  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: padding,
      child: Row(
        children: [
          for (var i = 0; i < children.length; i++) ...[
            if (i > 0) const SizedBox(width: FiSpace.s2),
            children[i],
          ],
        ],
      ),
    );
  }
}
