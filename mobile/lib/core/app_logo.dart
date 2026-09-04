import 'package:flutter/material.dart';

import 'design_tokens.dart';

class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 44});

  final double size;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final brand = dark ? FiColors.darkBrand : FiColors.lightBrand;
    final onBrand = dark ? FiColors.darkInkOnBrand : FiColors.lightInkOnBrand;

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(FiRadius.md),
        color: brand,
      ),
      child: Icon(Icons.trending_up, size: size * 0.56, color: onBrand),
    );
  }
}
