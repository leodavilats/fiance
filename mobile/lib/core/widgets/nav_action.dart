import 'package:flutter/material.dart';

import '../theme.dart';

class FiNavAction extends StatelessWidget {
  const FiNavAction({super.key, required this.label, required this.onPressed, this.icon});

  final String label;
  final VoidCallback? onPressed;

  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final marca = Theme.of(context).colorScheme.primary;

    return TextButton(
      onPressed: onPressed,
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
              style: FiType.action.copyWith(color: marca),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Icon(Icons.chevron_right, size: 18, color: marca),
        ],
      ),
    );
  }
}
