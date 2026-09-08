import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/design_tokens.dart';

/// Contraste da paleta: o **mínimo da WCAG 2.1 AA**, e nada além dele.
///
/// Aqui havia pisos acima da norma — tinta secundária a 8:1, legenda e marca a 6:1. Eram escolha
/// de design, e escolha de design deixou de ter máquina: a paleta é livre. O que não é livre é
/// texto ilegível, então ficam os dois números da norma: **4,5:1 para texto** e **3:1 para
/// limite de controle e forma** (WCAG 1.4.3 e 1.4.11).
///
/// A diferença importa: liberdade de UX/UI é escolher a cor, não é publicar o que não se lê.
double _canal(double v) {
  final c = v / 255;
  return c <= 0.03928 ? c / 12.92 : math.pow((c + 0.055) / 1.055, 2.4).toDouble();
}

double _luminancia(Color cor) {
  final r = _canal((cor.r * 255).roundToDouble());
  final g = _canal((cor.g * 255).roundToDouble());
  final b = _canal((cor.b * 255).roundToDouble());
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

double contraste(Color a, Color b) {
  final la = _luminancia(a);
  final lb = _luminancia(b);
  final maior = math.max(la, lb);
  final menor = math.min(la, lb);
  return (maior + 0.05) / (menor + 0.05);
}

void main() {
  for (final escuro in [true, false]) {
    final tema = escuro ? 'escuro' : 'claro';
    final brightness = escuro ? Brightness.dark : Brightness.light;

    Color ground0() => escuro ? FiColors.darkGround0 : FiColors.lightGround0;
    Color ground1() => escuro ? FiColors.darkGround1 : FiColors.lightGround1;
    Color controlBorder() => escuro ? FiColors.darkControlBorder : FiColors.lightControlBorder;
    Color controlFill() => escuro ? FiColors.darkControlFill : FiColors.lightControlFill;
    Color track() => escuro ? FiColors.darkTrack : FiColors.lightTrack;
    Color brand() => escuro ? FiColors.darkBrand : FiColors.lightBrand;
    Color inkOnBrand() => escuro ? FiColors.darkInkOnBrand : FiColors.lightInkOnBrand;
    Color ink1() => escuro ? FiColors.darkInk1 : FiColors.lightInk1;
    Color ink2() => escuro ? FiColors.darkInk2 : FiColors.lightInk2;
    Color ink3() => escuro ? FiColors.darkInk3 : FiColors.lightInk3;
    Color inkDisabled() => escuro ? FiColors.darkInkDisabled : FiColors.lightInkDisabled;

    group('contraste no tema $tema', () {
      test('o contorno de controle alcança 3:1 contra o chão e a superfície', () {
        expect(
          contraste(controlBorder(), ground0()),
          greaterThanOrEqualTo(3.0),
          reason: 'é o contorno que faz um controle ser um controle (WCAG 1.4.11)',
        );
        expect(contraste(controlBorder(), ground1()), greaterThanOrEqualTo(3.0));
      });

      test('preenchido se distingue de vazio', () {
        expect(
          contraste(brand(), track()),
          greaterThanOrEqualTo(3.0),
          reason: 'é o par que faz barra e deslizador mostrarem onde estão',
        );
      });

      test('o rótulo do botão primário é legível', () {
        expect(contraste(inkOnBrand(), brand()), greaterThanOrEqualTo(4.5));
      });

      test('o rótulo do botão secundário é legível sobre o preenchimento', () {
        expect(contraste(ink1(), controlFill()), greaterThanOrEqualTo(4.5));
      });

      test('controle inerte continua sendo lido', () {
        expect(contraste(inkDisabled(), controlFill()), greaterThanOrEqualTo(3.0));
      });

      test('toda tinta de texto passa dos 4,5:1 da norma', () {
        expect(contraste(ink1(), ground0()), greaterThanOrEqualTo(4.5));
        expect(contraste(ink2(), ground0()), greaterThanOrEqualTo(4.5));
        // Legenda e texto pequeno, e a regra para texto pequeno e a mesma, nao uma mais frouxa.
        expect(contraste(ink3(), ground0()), greaterThanOrEqualTo(4.5));
      });

      test('marca e estados carregam rótulo', () {
        expect(contraste(brand(), ground0()), greaterThanOrEqualTo(4.5));
        for (final estado in [
          FiState.favorable,
          FiState.attention,
          FiState.adverse,
          FiState.indeterminate,
        ]) {
          expect(
            contraste(fiStateColor(estado, brightness), ground0()),
            greaterThanOrEqualTo(4.5),
            reason: 'o estado $estado escreve texto',
          );
        }
      });

      test('a tinta do selo é legível sobre o chão do selo', () {
        for (final estado in [
          FiState.favorable,
          FiState.attention,
          FiState.adverse,
          FiState.indeterminate,
        ]) {
          final superficie = fiStateSurface(estado, brightness);
          expect(
            contraste(fiStateColor(estado, brightness), superficie),
            greaterThanOrEqualTo(5.5),
            reason: 'o rótulo do selo é a própria cor do estado',
          );
          expect(
            contraste(ink1(), superficie),
            greaterThanOrEqualTo(4.5),
            reason: 'o corpo do aviso é escrito em tinta primária',
          );
        }
      });

      test('série de gráfico é forma, e escreve o rótulo do próprio chip', () {
        for (var i = 1; i <= 12; i++) {
          final cor = fiSeriesColor(i, brightness);
          expect(contraste(cor, ground0()), greaterThanOrEqualTo(4.5));
        }
      });
    });
  }
}
