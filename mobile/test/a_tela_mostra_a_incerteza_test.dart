import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/glossary.dart';
import 'package:fiance/core/models.dart';
import 'package:fiance/core/score_ruler.dart';

void main() {
  group('a faixa diz com o que se apoia', () {
    test('firme nomeia quantos insumos independentes a sustentam', () {
      expect(bandQualityLabel('firme', 2), contains('2 insumos independentes'));
    });

    test('frágil com um insumo diz que concordar ali não confirma nada', () {
      expect(bandQualityLabel('fragil', 1), contains('não confirma nada'));
    });

    test('ampla diz que a largura vem da discordância', () {
      expect(bandQualityLabel('ampla', 2), contains('discordam'));
    });
  });

  group('silêncio com motivo', () {
    test('cada razão de ausência tem palavra própria', () {
      final ditas = {
        for (final estado in [
          'inaplicavel',
          'sem_dado',
          'lucro_negativo',
          'fora_da_faixa',
        ])
          estado: methodStatusLabel(estado),
      };

      expect(ditas.values.toSet().length, ditas.length, reason: 'são silêncios diferentes');
      expect(ditas['lucro_negativo'], contains('lucro'));
      expect(ditas['sem_dado'], contains('dado'));
    });
  });

  group('premissa não se confunde com gatilho', () {
    Falsifier de(String kind) => Falsifier.fromJson({
      'metric': 'dividend',
      'condition': 'o dividendo cair 40%',
      'becomes_label': 'Rever a tese',
      'current': 6.0,
      'threshold': 3.6,
      'kind': kind,
    });

    test('a premissa se declara', () {
      expect(de('premissa').isPremise, isTrue);
      expect(de('gatilho').isPremise, isFalse);
    });

    test('sem o campo, o que chega é tratado como gatilho', () {
      final antigo = Falsifier.fromJson({'metric': 'price', 'condition': 'x'});

      expect(antigo.isPremise, isFalse, reason: 'cliente velho não inventa refutação');
    });
  });

  test('a confiança sai em palavra, não em casa decimal', () {
    expect(confidenceLabel(0.75), 'confiança alta');
    expect(confidenceLabel(0.45), 'confiança média');
    expect(confidenceLabel(0.2), 'confiança baixa');
    expect(confidenceLabel(0.75), isNot(contains('%')));
  });

  test('os termos novos têm verbete', () {
    expect(glossary['qualidade_da_faixa'], isNotNull);
    expect(glossary['premissa_e_gatilho'], isNotNull);
    expect(glossary['taxa_de_desconto'], contains('Selic'));
  });

  test('o diagnóstico por método sobrevive a um campo que falte', () {
    final m = FairMethod.fromJson({'method': 'graham', 'status': 'sem_dado'});

    expect(m.applies, isFalse);
    expect(m.input, '');
  });
}
