import 'package:flutter/material.dart';

import '../theme.dart';

class BrandBackground extends StatelessWidget {
  const BrandBackground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final glow1 = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final glow2 = isDark ? AppColors.darkAccent2 : AppColors.lightAccent2;

    return Container(
      color: bg,
      child: Stack(
        fit: StackFit.expand,
        children: [
          Positioned(
            top: -120,
            right: -80,
            child: _Glow(color: glow2, size: 280),
          ),
          Positioned(
            bottom: -140,
            left: -100,
            child: _Glow(color: glow1, size: 320),
          ),
          child,
        ],
      ),
    );
  }
}

class _Glow extends StatelessWidget {
  const _Glow({required this.color, required this.size});

  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(
          colors: [color.withValues(alpha: 0.16), color.withValues(alpha: 0.0)],
        ),
      ),
    );
  }
}
