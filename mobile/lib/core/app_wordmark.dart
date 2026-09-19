import 'package:flutter/material.dart';

import 'theme.dart';

class AppWordmark extends StatelessWidget {
  const AppWordmark({super.key, this.height = 18, this.color});

  final double height;
  final Color? color;

  static const _letterSpacing = 13.0;
  static const _advances = <double>[62, 13, 74, 72, 70, 62];
  static double get _width =>
      _advances.reduce((a, b) => a + b) + (_advances.length - 1) * _letterSpacing;

  @override
  Widget build(BuildContext context) {
    final tinta = color ?? DefaultTextStyle.of(context).style.color ?? fiInk1(context);
    return CustomPaint(
      size: Size(height * _width / 100.0, height),
      painter: _WordmarkPainter(tinta),
    );
  }
}

class _WordmarkPainter extends CustomPainter {
  const _WordmarkPainter(this.color);

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final e = size.height / 100.0;
    final tinta = Paint()
      ..color = color
      ..isAntiAlias = true;

    var x = 0.0;
    for (final letter in _AppWordmarkLetters.todas) {
      canvas.save();
      canvas.translate(x * e, 0);
      canvas.drawPath(letter.path(e), tinta);
      canvas.restore();
      x += letter.advance + AppWordmark._letterSpacing;
    }
  }

  @override
  bool shouldRepaint(_WordmarkPainter old) => old.color != color;
}

class _Letter {
  const _Letter(this.advance, this.path);
  final double advance;
  final Path Function(double scale) path;
}

class _AppWordmarkLetters {
  static final List<_Letter> todas = [f, i, a, n, c, e];

  static Path _poly(double scale, List<Offset> pontos) {
    final p = Path()..moveTo(pontos.first.dx * scale, pontos.first.dy * scale);
    for (final pt in pontos.skip(1)) {
      p.lineTo(pt.dx * scale, pt.dy * scale);
    }
    return p..close();
  }

  static final f = _Letter(62, (k) => _poly(k, const [
        Offset(0, 0), Offset(62, 0), Offset(62, 13), Offset(13, 13),
        Offset(13, 49), Offset(50, 49), Offset(50, 62), Offset(13, 62),
        Offset(13, 100), Offset(0, 100),
      ]));

  static final i = _Letter(13, (k) => _poly(k, const [
        Offset(0, 0), Offset(13, 0), Offset(13, 100), Offset(0, 100),
      ]));

  static final a = _Letter(74, (k) {
    final p = _poly(k, const [
      Offset(29, 0), Offset(45, 0), Offset(74, 100), Offset(59.5, 100),
      Offset(37, 22.4), Offset(14.5, 100), Offset(0, 100),
    ]);
    p.addPath(
      _poly(k, const [
        Offset(29.29, 49), Offset(44.71, 49), Offset(48.48, 62), Offset(25.52, 62),
      ]),
      Offset.zero,
    );
    return p;
  });

  static final n = _Letter(72, (k) => _poly(k, const [
        Offset(0, 0), Offset(13, 0), Offset(59, 76), Offset(59, 0),
        Offset(72, 0), Offset(72, 100), Offset(59, 100), Offset(13, 24),
        Offset(13, 100), Offset(0, 100),
      ]));

  static final c = _Letter(70, (k) {
    return Path()
      ..moveTo(64.4 * k, 22.8 * k)
      ..arcToPoint(
        Offset(64.4 * k, 77.2 * k),
        radius: Radius.elliptical(35 * k, 50 * k),
        largeArc: true,
        clockwise: false,
      )
      ..lineTo(53.4 * k, 70.2 * k)
      ..arcToPoint(
        Offset(53.4 * k, 29.8 * k),
        radius: Radius.elliptical(22 * k, 37 * k),
        largeArc: true,
        clockwise: true,
      )
      ..close();
  });

  static final e = _Letter(62, (k) => _poly(k, const [
        Offset(0, 0), Offset(62, 0), Offset(62, 13), Offset(13, 13),
        Offset(13, 49), Offset(48, 49), Offset(48, 62), Offset(13, 62),
        Offset(13, 87), Offset(62, 87), Offset(62, 100), Offset(0, 100),
      ]));
}
