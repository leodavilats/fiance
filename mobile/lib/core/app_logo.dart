import 'package:flutter/material.dart';

/// Selo da marca: gradiente verde→ciano com o ícone de tendência de alta.
/// Mesma identidade visual usada no app web (header e tela de login).
class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 44});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(size * 0.24),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF4ADE80), Color(0xFF22D3EE)],
        ),
      ),
      child: Icon(
        Icons.trending_up,
        size: size * 0.56,
        color: const Color(0xFF0B0E14),
      ),
    );
  }
}
