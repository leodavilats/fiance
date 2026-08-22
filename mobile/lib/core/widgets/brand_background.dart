import 'package:flutter/material.dart';

import '../theme.dart';

class BrandBackground extends StatelessWidget {
  const BrandBackground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      color: isDark ? FiColors.darkGround0 : FiColors.lightGround0,
      child: child,
    );
  }
}
