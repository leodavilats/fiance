import 'package:flutter/material.dart';

import '../glossary.dart';

// Toque em vez de hover, pois é a interação natural em touch.
class HelpTooltip extends StatelessWidget {
  const HelpTooltip({super.key, required this.termKey});

  final String termKey;

  @override
  Widget build(BuildContext context) {
    final text = glossary[termKey];
    if (text == null) return const SizedBox.shrink();

    return GestureDetector(
      onTap: () => showModalBottomSheet(
        context: context,
        showDragHandle: true,
        builder: (context) => Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
          child: Text(text, style: const TextStyle(fontSize: 14, height: 1.4)),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.only(left: 4),
        child: Icon(
          Icons.help_outline,
          size: 14,
          color: Theme.of(context).colorScheme.outline,
        ),
      ),
    );
  }
}
