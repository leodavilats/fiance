import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/glossary.dart';
import 'package:fiance/core/score_ruler.dart';

void main() {
  group('régua de score', () {
    test('faixas seguem os limiares compartilhados', () {
      const dark = Brightness.dark;
      expect(scoreBand(90, dark).text, 'Forte');
      expect(scoreBand(kScoreStrong, dark).text, 'Forte');
      expect(scoreBand(kScoreStrong - 1, dark).text, 'Boa');
      expect(scoreBand(kScoreGood, dark).text, 'Boa');
      expect(scoreBand(kScoreGood - 1, dark).text, 'Neutra');
      expect(scoreBand(kScoreNeutral, dark).text, 'Neutra');
      expect(scoreBand(kScoreNeutral - 1, dark).text, 'Fraca');
    });

    test('glossário cita os mesmos limiares da régua', () {
      expect(scoreGlossary, contains('${kScoreStrong.toInt()}'));
      expect(scoreGlossary, contains('${kScoreGood.toInt()}'));
      expect(scoreGlossary, contains('${kScoreNeutral.toInt()}'));
      expect(scoreGlossary, isNot(contains('70 =')));
      expect(glossary['score'], scoreGlossary);
    });
  });

  group('rótulos de proveniência', () {
    test('base da tendência distingue histórico longo de curto', () {
      expect(trendBasisLabel('long'), contains('200'));
      expect(trendBasisLabel('short'), contains('histórico curto'));
      expect(trendBasisLabel('none'), contains('sem histórico'));
      expect(trendBasisLabel(null), contains('sem histórico'));
    });

    test('anos de dado e consenso usam singular e plural corretos', () {
      expect(dataYearsLabel(0), 'sem histórico de proventos');
      expect(dataYearsLabel(null), 'sem histórico de proventos');
      expect(dataYearsLabel(1), '1 ano de proventos');
      expect(dataYearsLabel(4), '4 anos de proventos');

      expect(consensusLabel(0), 'sem método aplicável');
      expect(consensusLabel(1), '1 método no consenso');
      expect(consensusLabel(3), '3 métodos no consenso');
    });

    test('confiança é apresentada em percentual', () {
      expect(confidenceLabel(0.75), 'confiança 75%');
      expect(confidenceLabel(null), '');
    });
  });
}
