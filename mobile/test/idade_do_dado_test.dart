import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/format.dart';
import 'package:fiance/core/models.dart';

void main() {
  group('a idade de um conjunto de preços', () {
    test('é a do carimbo mais antigo', () {
      expect(carimboMaisAntigo([300.0, 100.0, 200.0]), 100.0);
    });

    test('ignora ausência sem virar zero', () {
      expect(carimboMaisAntigo([null, 500.0, 0.0]), 500.0);
      expect(
        carimboMaisAntigo([null, null]),
        isNull,
        reason: 'sem carimbo a tela cala — 01/01/1970 seria pior que não dizer nada',
      );
      expect(carimboMaisAntigo(const <double?>[]), isNull);
    });
  });

  group('o carimbo do preço chega ao modelo', () {
    test('`as_of` é declarado, senão fromJson o descarta em silêncio', () {
      final posicao = PortfolioPosition.fromJson({
        'ticker': 'PETR4',
        'quantity': 100,
        'avg_price': 30.0,
        'invested': 3000.0,
        'as_of': 1757419200.0,
      });

      expect(
        posicao.asOf,
        1757419200.0,
        reason: 'o backend manda as_of em toda posição, e este modelo não o declarava',
      );
      expect(formatIdade(posicao.asOf), isNotEmpty);
    });

    test('resposta sem o campo não quebra', () {
      final posicao = PortfolioPosition.fromJson({
        'ticker': 'PETR4',
        'quantity': 100,
        'avg_price': 30.0,
        'invested': 3000.0,
      });

      expect(posicao.asOf, isNull);
      expect(formatIdade(posicao.asOf), isEmpty);
    });
  });
}
