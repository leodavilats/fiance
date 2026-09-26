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

  group('sem preço justo se declara', () {
    test('a ausência tem nome, e não vira leitura de tendência', () {
      expect(consensusLabel(0), 'sem preço justo');
      expect(glossary['sem_preco_justo'], contains('em vez de ler compra ou venda'));
    });

    test('faixa não precisa de aviso, porque é o normal', () {
      expect(basisLabel('band'), '');
    });
  });

  group('taxa de cache vencido', () {
    test('diz de quando é a leitura', () {
      final duasHorasAtras =
          DateTime.now().subtract(const Duration(hours: 2)).millisecondsSinceEpoch / 1000;
      final nota = staleRateNote({
        'rate_source': 'bcb_cache_vencido',
        'rates_as_of': duasHorasAtras,
      });

      expect(nota, contains('há 2 h'));
      expect(nota, contains('BCB fora do ar'));
    });

    test('taxa fresca não ganha nota', () {
      expect(staleRateNote({'rate_source': 'bcb', 'rates_as_of': 1790000000.0}), '');
      expect(staleRateNote(const {}), '');
    });
  });

  test('o glossário explica a faixa e de onde ela vem', () {
    expect(glossary['faixa_de_preco_justo'], contains('premissa pessimista'));
    expect(glossary['consenso'], contains('faixa'));
    expect(glossary['graham'], contains('não preço justo'));
  });
}
