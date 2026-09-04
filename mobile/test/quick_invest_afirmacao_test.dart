import 'package:fiance/core/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('QuickInvestResult', () {
    test('sobrevive ao modo analítico, que retira o valor de ação', () {
      final json = <String, dynamic>{
        'total_cash': 1000.0,
        'allocated_cash': null,
        'remaining_cash': 1000.0,
        'summary': 'Estratégia Quick Invest: 1 ativo selecionado.',
        'allocations': [
          {
            'ticker': 'PETR4',
            'name': 'Petrobras',
            'category': 'acoes_br',
            'sector': 'Energia',
            'current_price': 38.0,
            'suggested_quantity': null,
            'suggested_investment': null,
            'rationale': 'Score alto | MS 31%',
            'score': 82.0,
            'dividend_yield': 12.0,
          },
        ],
        'affirmation': {
          'level': 2,
          'prescriptive': false,
          'disclaimer': 'Leitura de critérios objetivos.',
        },
      };

      final resultado = QuickInvestResult.fromJson(json);

      expect(resultado.allocatedCash, isNull);
      expect(resultado.remainingCash, 1000.0);

      final alocacao = resultado.allocations.single;
      expect(alocacao.suggestedQuantity, isNull);
      expect(alocacao.suggestedInvestment, isNull);

      expect(alocacao.ticker, 'PETR4');
      expect(alocacao.score, 82.0);
      expect(alocacao.rationale, isNotEmpty);

      expect(resultado.affirmation?.prescriptive, isFalse);
      expect(resultado.affirmation?.disclaimer, isNotEmpty);
    });

    test('no modo prescritivo os números chegam inteiros', () {
      final resultado = QuickInvestResult.fromJson(<String, dynamic>{
        'total_cash': 1000.0,
        'allocated_cash': 950.0,
        'remaining_cash': 50.0,
        'summary': 'ok',
        'allocations': [
          {
            'ticker': 'PETR4',
            'name': 'Petrobras',
            'category': 'acoes_br',
            'sector': 'Energia',
            'current_price': 38.0,
            'suggested_quantity': 25,
            'suggested_investment': 950.0,
            'rationale': 'Score alto',
            'score': 82.0,
            'dividend_yield': 12.0,
          },
        ],
      });

      expect(resultado.allocatedCash, 950.0);
      expect(resultado.allocations.single.suggestedQuantity, 25);
      expect(resultado.allocations.single.suggestedInvestment, 950.0);
    });
  });
}
