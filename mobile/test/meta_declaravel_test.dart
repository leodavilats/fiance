import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('alguma tela declara a meta de renda passiva', () {
    final fontes = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => f.path.endsWith('.dart'));

    final escritores = <String>[];
    for (final f in fontes) {
      if (f.path.contains('api_repository.dart')) continue;

      for (final m in RegExp(
        r'savePreferences\(\s*passiveIncomeGoal:\s*([^,\n)]+)',
      ).allMatches(f.readAsStringSync())) {
        final valor = (m[1] ?? '').trim();
        if (valor.startsWith('prefs.')) continue;
        escritores.add('${f.path.replaceAll(r'\', '/')}: $valor');
      }
    }

    expect(
      escritores,
      isNotEmpty,
      reason:
          'nenhuma tela escreve a meta de renda passiva, e o produto a mostra em três. '
          'O alvo tem de ser declarável onde ele é lido — hoje em '
          'features/config/objetivos_screen.dart',
    );
  });
}
