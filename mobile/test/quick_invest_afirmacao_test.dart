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

    test('a fatia de renda fixa e o motivo do troco nao sao descartados', () {
      final resultado = QuickInvestResult.fromJson(<String, dynamic>{
        'total_cash': 271.36,
        'allocated_cash': null,
        'remaining_cash': 96.90,
        'basis': 'goals',
        'summary': 'Esta ordem cobre uma fatia em renda fixa.',
        'allocations': [],
        'fixed_income': {
          'amount': 174.46,
          'reference_monthly_pct': 0.94,
          'reference_source': 'bcb',
          'rationale': 'A alocação-alvo pede renda fixa.',
        },
        'unallocated': [
          {'value': 96.90, 'reason': 'Troco de cota inteira'},
        ],
      });

      expect(
        resultado.fixedIncome?.amount,
        174.46,
        reason:
            'a fatia de renda fixa era o unico destino da ordem, e o `fromJson` a descartava: '
            'o resumo anunciava "uma fatia em renda fixa" e a tela nao mostrava nenhuma',
      );
      expect(resultado.fixedIncome?.referenceSource, 'bcb');
      expect(resultado.temDestino, isTrue, reason: 'renda fixa e destino');

      expect(
        resultado.unallocated.single.reason,
        'Troco de cota inteira',
        reason:
            '`remainingCash` sozinho e um numero sem explicacao -- o backend tem teste para '
            'impedir que ele viaje assim, e o cliente o mostrava sem o motivo',
      );
      expect(resultado.unallocated.single.value, 96.90);
      expect(resultado.basis, 'goals');
    });

    test('sem nenhum destino a ordem diz que nao ha destino', () {
      final resultado = QuickInvestResult.fromJson(<String, dynamic>{
        'total_cash': 80.0,
        'allocated_cash': 0.0,
        'remaining_cash': 80.0,
        'summary': 'Nao encontramos ativo cujo preco caiba neste valor.',
        'allocations': [],
      });

      expect(resultado.temDestino, isFalse);
      expect(resultado.basis, 'goals', reason: 'campo ausente cai no padrao, nao em nulo');
      expect(resultado.fixedIncome, isNull);
      expect(resultado.unallocated, isEmpty);
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
