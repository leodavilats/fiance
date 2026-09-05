import 'package:flutter/material.dart';

class AppWordmark extends StatelessWidget {
  const AppWordmark({super.key, this.height = 18, this.color});

  final double height;
  final Color? color;

  static const _entreletra = 13.0;
  static const _avancos = <double>[62, 13, 74, 72, 70, 62];
  static double get _largura =>
      _avancos.reduce((a, b) => a + b) + (_avancos.length - 1) * _entreletra;

  @override
  Widget build(BuildContext context) {
    final tinta = color ?? DefaultTextStyle.of(context).style.color ?? Colors.black;
    return CustomPaint(
      size: Size(height * _largura / 100.0, height),
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
    for (final letra in _AppWordmarkLetras.todas) {
      canvas.save();
      canvas.translate(x * e, 0);
      canvas.drawPath(letra.path(e), tinta);
      canvas.restore();
      x += letra.avanco + AppWordmark._entreletra;
    }
  }

  @override
  bool shouldRepaint(_WordmarkPainter old) => old.color != color;
}

class _Letra {
  const _Letra(this.avanco, this.path);
  final double avanco;
  final Path Function(double escala) path;
}

/// Cada `_Letra.path` reproduz literalmente o atributo `d` do SVG de
/// referência — polígono por polígono, arco por arco — na mesma caixa 0..100.
class _AppWordmarkLetras {
  static final List<_Letra> todas = [f, i, a, n, c, e];

  static Path _poly(double escala, List<Offset> pontos) {
    final p = Path()..moveTo(pontos.first.dx * escala, pontos.first.dy * escala);
    for (final pt in pontos.skip(1)) {
      p.lineTo(pt.dx * escala, pt.dy * escala);
    }
    return p..close();
  }

  static final f = _Letra(62, (k) => _poly(k, const [
        Offset(0, 0), Offset(62, 0), Offset(62, 13), Offset(13, 13),
        Offset(13, 49), Offset(50, 49), Offset(50, 62), Offset(13, 62),
        Offset(13, 100), Offset(0, 100),
      ]));

  static final i = _Letra(13, (k) => _poly(k, const [
        Offset(0, 0), Offset(13, 0), Offset(13, 100), Offset(0, 100),
      ]));

  static final a = _Letra(74, (k) {
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

  static final n = _Letra(72, (k) => _poly(k, const [
        Offset(0, 0), Offset(13, 0), Offset(59, 76), Offset(59, 0),
        Offset(72, 0), Offset(72, 100), Offset(59, 100), Offset(13, 24),
        Offset(13, 100), Offset(0, 100),
      ]));

  // Única letra com arco: "M64.4 22.8 A35 50 0 1 0 64.4 77.2
  // L53.4 70.2 A22 37 0 1 1 53.4 29.8 Z" — dois arcos elípticos concêntricos
  // ligados por dois segmentos retos. `Path.arcToPoint` recebe os mesmos
  // parâmetros do comando SVG `A` (rx, ry, rotação, arco-grande, sentido).
  static final c = _Letra(70, (k) {
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

  static final e = _Letra(62, (k) => _poly(k, const [
        Offset(0, 0), Offset(62, 0), Offset(62, 13), Offset(13, 13),
        Offset(13, 49), Offset(48, 49), Offset(48, 62), Offset(13, 62),
        Offset(13, 87), Offset(62, 87), Offset(62, 100), Offset(0, 100),
      ]));
}
