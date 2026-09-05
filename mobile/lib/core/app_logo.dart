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
      child: Center(
        child: CustomPaint(
          size: Size.square(size * 0.58),
          painter: _MarcaPainter(
            eixo: onBrand,
            chao: Color.lerp(onBrand, brand, 0.35)!,
          ),
        ),
      ),
    );
  }
}

class _MarcaPainter extends CustomPainter {
  const _MarcaPainter({required this.eixo, required this.chao});

  final Color eixo;
  final Color chao;

  static const _eixo = <Offset>[
    Offset(6, 6), Offset(76, 6), Offset(76, 19), Offset(19, 19),
    Offset(19, 41), Offset(56, 41), Offset(56, 54), Offset(19, 54),
    Offset(19, 79), Offset(6, 79),
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final e = size.width / 100.0;
    final tinta = Paint()..color = eixo..isAntiAlias = true;

    final haste = Path()..moveTo(_eixo.first.dx * e, _eixo.first.dy * e);
    for (final p in _eixo.skip(1)) {
      haste.lineTo(p.dx * e, p.dy * e);
    }
    haste.close();
    canvas.drawPath(haste, tinta);

    canvas.drawRRect(
      RRect.fromLTRBR(83 * e, 6 * e, 96 * e, 19 * e, Radius.circular(3 * e)),
      tinta,
    );
    canvas.drawRRect(
      RRect.fromLTRBR(0, 87 * e, 100 * e, 95 * e, Radius.circular(4 * e)),
      Paint()..color = chao..isAntiAlias = true,
    );
  }

  @override
  bool shouldRepaint(_MarcaPainter old) => old.eixo != eixo || old.chao != chao;
}
