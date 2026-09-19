import 'package:fiance/core/cash_models.dart';
import 'package:fiance/core/month.dart';
import 'package:fiance/core/month_verdict.dart';
import 'package:fiance/core/product_rules.dart';
import 'package:flutter_test/flutter_test.dart';

MonthVerdict _leitura({
  double received = 10000,
  double committed = 3000,
  Debt? expensiveDebt,
}) => monthVerdict(
  received: received,
  committed: committed,
  expensiveDebt: expensiveDebt,
);

Debt _divida({double? taxa = 14.9, String descricao = 'Rotativo do cartão'}) =>
    Debt(
      id: 1,
      kind: 'rotativo_cartao',
      description: descricao,
      balance: 5000,
      monthlyRate: taxa,
      debtClass: DebtClass.expensive,
      referenceMonthly: 0.9,
      referenceSource: 'bcb',
      flipRate: 1.4,
    );

void main() {
  group('veredito do mês', () {
    test('sem entrada lançada não há leitura, e a pressão não vira zero', () {
      final v = _leitura(received: 0, committed: 500);
      expect(
        v.pressure,
        isNull,
        reason: 'dividir por zero daria 0% e "Mês folgado" para quem não lançou nada',
      );
      expect(
        v.band.state,
        FiState.indeterminate,
        reason: 'ausência de base é estado indeterminado, não favorável',
      );
    });

    test('a banda sai da régua gerada, e o pior estado é o mês apertado', () {
      expect(_leitura(committed: 9000).band.id, 'tight');
      expect(_leitura(committed: 7000).band.id, 'pressured');
      expect(_leitura(committed: 4000).band.id, 'steady');
      expect(_leitura(committed: 1000).band.id, 'loose');
    });

    test('comprometido acima da renda não estoura a régua', () {
      final v = _leitura(received: 1000, committed: 4000);
      expect(
        v.pressure,
        100,
        reason: 'o domínio para em 100: uma barra que estoura não informa',
      );
      expect(v.band.id, 'tight');
    });

    test('dívida caseira assume a razão sem mudar a banda', () {
      final sem = _leitura(committed: 1000);
      final com = _leitura(committed: 1000, expensiveDebt: _divida());

      expect(
        com.band.id,
        sem.band.id,
        reason: 'a régua mede pressão do mês, e a dívida é outro julgamento',
      );
      expect(
        com.reason,
        contains('Rotativo do cartão'),
        reason: 'um mês folgado com dívida a 14,9% ao mês não é um mês resolvido',
      );
      expect(com.reason, contains('14,9% ao mês'));
    });

    test('dívida sem taxa informada não inventa taxa na frase', () {
      final v = _leitura(
        expensiveDebt: _divida(taxa: null, descricao: 'Consignado'),
      );
      expect(v.reason, contains('Consignado'));
      expect(
        v.reason,
        isNot(contains('null')),
        reason: 'o produto não estima taxa que a pessoa não informou',
      );
      expect(v.reason, isNot(contains('% ao mês')));
    });
  });

  group('o mês como recorte', () {
    test('o nome do mês é o de quem lê, não o do formato', () {
      expect(monthName('2026-09'), 'setembro de 2026');
      expect(monthName('2026-01'), 'janeiro de 2026');
    });

    test('mês malformado volta como veio, em vez de inventar', () {
      expect(monthName('2026'), '2026');
      expect(monthName('2026-99'), '2026-99 de 2026');
    });

    test('o mês anterior atravessa a virada do ano', () {
      expect(previousMonth('2026-01'), '2025-12');
      expect(previousMonth('2026-09'), '2026-08');
    });

    test('o mês corrente sai no formato que o backend espera', () {
      expect(currentMonth(), matches(RegExp(r'^\d{4}-\d{2}$')));
    });

    test('o dia sai da data, e data curta não estoura', () {
      expect(dayOf('2026-09-08'), '08');
      expect(dayOf('2026-09'), '2026-09');
    });
  });
}
