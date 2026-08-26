import 'package:flutter/material.dart';

import 'design_tokens.dart';

/// O selo da marca: chapa sólida na cor de marca, sem gradiente.
///
/// A versão anterior mantinha o gradiente verde→ciano da paleta antiga, que o
/// web já havia abandonado — o mesmo produto tinha duas marcas. Verde continua
/// significando "favorável" no sistema, então usá-lo como identidade fazia a
/// marca competir com o estado (§10).
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
