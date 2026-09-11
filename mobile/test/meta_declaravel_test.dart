import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Alvo que o produto lê e nenhuma tela escreve.
///
/// `passiveIncomeGoal` era exibido em três lugares — a régua de progresso do patrimônio, a linha
/// do `/voce` e a projeção — e **nenhum** o declarava: `savePreferences` aceitava o campo e todo
/// chamador só repassava o valor que já estava lá, para não apagá-lo. A régua nunca saía do
/// lugar, e a pessoa não tinha onde dizer quanto queria receber.
///
/// A regra é de grafia, não de layout: em algum lugar de `lib/` uma chamada a `savePreferences`
/// tem de passar um valor de meta que não venha de `prefs`.
void main() {
  test('alguma tela declara a meta de renda passiva', () {
    final fontes = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => f.path.endsWith('.dart'));

    final escritores = <String>[];
    for (final f in fontes) {
      if (f.path.contains('api_repository.dart')) continue;

      // Ancorado em `savePreferences(`: `passiveIncomeGoal:` solto tambem aparece no
      // `fromJson` de `models.dart`, que le o campo em vez de escrever.
      for (final m in RegExp(
        r'savePreferences\(\s*passiveIncomeGoal:\s*([^,\n)]+)',
      ).allMatches(f.readAsStringSync())) {
        final valor = (m[1] ?? '').trim();
        // `passiveIncomeGoal: prefs.passiveIncomeGoal` e repasse, nao declaracao.
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
