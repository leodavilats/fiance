import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/glossary.dart';
import 'package:fiance/core/format.dart';
import 'package:fiance/core/score_ruler.dart';

void main() {
  group('a faixa é lida como faixa', () {
    test('piso e teto diferentes saem como intervalo', () {
      expect(fairBandLabel(12.94, 23.77), '${formatCurrency(12.94)} a ${formatCurrency(23.77)}');
    });

    test('método único sai como número, e não como intervalo de zero', () {
      expect(fairBandLabel(10.0, 10.0), formatCurrency(10.0));
    });

    test('sem método não se inventa faixa', () {
      expect(fairBandLabel(null, null), '—');
    });
  });

  group('a borda mostrada é a que a margem mede', () {
    test('abaixo da faixa, a referência é o piso', () {
      expect(fairBandEdgeLabel(41.91, 60.32, 146.03), formatCurrency(60.32));
    });

    test('acima da faixa, a referência é o teto', () {
      expect(fairBandEdgeLabel(51.78, 12.94, 23.77), formatCurrency(23.77));
    });

    test('dentro da faixa não há borda a favor nem contra', () {
      expect(fairBandEdgeLabel(20.0, 10.0, 30.0), 'na faixa');
    });
  });

  group('leitura sem preço justo se declara', () {
    test('tendência vem nomeada', () {
      expect(basisLabel('trend'), contains('tendência'));
      expect(basisLabel('trend'), contains('sem preço justo'));
    });

    test('faixa não precisa de aviso, porque é o normal', () {
      expect(basisLabel('band'), '');
    });
  });

  test('o glossário explica a faixa e a leitura de tendência', () {
    expect(glossary['faixa_de_preco_justo'], isNotNull);
    expect(glossary['leitura_de_tendencia'], isNotNull);
    expect(glossary['consenso'], contains('faixa'));
  });
}
