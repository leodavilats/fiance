import 'dart:io';

import 'package:fiance/core/design_tokens.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

String _hex(Color cor) =>
    '#${(cor.toARGB32() & 0xFFFFFF).toRadixString(16).padLeft(6, '0').toUpperCase()}';

String _corDaAbertura(String pasta) {
  final xml = File('android/app/src/main/res/$pasta/splash.xml').readAsStringSync();
  return RegExp(r'<color name="chao">(#[0-9A-Fa-f]{6})</color>').firstMatch(xml)!.group(1)!.toUpperCase();
}

void main() {
  test('a abertura do Android tem o chão do app, nos dois temas', () {
    expect(
      _corDaAbertura('values'),
      _hex(FiColors.lightGround0),
      reason: 'a abertura branca piscava antes do app, que tem chão creme',
    );
    expect(
      _corDaAbertura('values-night'),
      _hex(FiColors.darkGround0),
      reason: 'no tema escuro, a abertura branca piscava antes do app escuro',
    );
  });
}
