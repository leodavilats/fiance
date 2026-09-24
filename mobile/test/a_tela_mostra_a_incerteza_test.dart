import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/glossary.dart';
import 'package:fiance/core/models.dart';
import 'package:fiance/core/score_ruler.dart';

void main() {
  group('a faixa diz quanto merece confiança', () {
    test('firme diz que outro insumo a confirma', () {
      expect(bandQualityLabel('firme', 2), contains('confirmada por outro insumo'));
    });

    test('frágil diz que a leitura tem teto de intensidade', () {
      expect(bandQualityLabel('fragil', 1), contains('não passa de abaixo ou acima'));
    });

    test('ampla sem confirmação diz que falta a confirmação', () {
      expect(bandQualityLabel('ampla', 1), contains('sem confirmação'));
    });

    test('a concordância da confirmação tem palavra própria', () {
      expect(agreementLabel('dentro'), contains('confirma'));
      expect(agreementLabel('fora_mais_30'), contains('não confirma'));
    });
  });

  group('silêncio com motivo', () {
    test('cada razão de ausência tem palavra própria', () {
      final ditas = {
        for (final estado in [
          'inaplicavel',
          'sem_dado',
          'lucro_negativo',
          'roe_insuficiente',
          'sem_juro',
          'pouco_distribuido',
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
      'metric': 'growth',
      'condition': 'o crescimento não se confirmar',
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
    expect(glossary['taxa_de_desconto'], contains('Selic média de 10 anos'));
    expect(glossary['preco_teto_pessoal'], contains('não a faixa'));
  });

  test('o diagnóstico por método sobrevive a um campo que falte', () {
    final m = FairMethod.fromJson({'method': 'graham', 'status': 'sem_dado'});

    expect(m.applies, isFalse);
    expect(m.input, '');
  });
}
