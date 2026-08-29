import 'package:fiance/core/models.dart';
import 'package:fiance/features/tools/income_compare_view.dart';
import 'package:flutter_test/flutter_test.dart';

/// O payload é copiado do que `IncomeCompareResponse` emite de verdade, com as
/// chaves e os nulos que o backend manda. Um fixture inventado testaria o
/// parser contra a memória de quem o escreveu, que é justamente onde o campo
/// errado passa.
Map<String, dynamic> payload() => {
  'amount': 10000.0,
  'horizon_months': 12,
  'cdi_anual': 14.4,
  'ipca_anual': 4.5,
  'rates_source': 'BCB SGS',
  'fixed_income': [
    {
      'kind': 'renda_fixa',
      'label': 'CDB 110% CDI',
      'ticker': null,
      'net_income_yield_pct': 11.2,
      'income_basis': 'taxa contratada',
      'upside_pct': null,
      'has_upside': false,
      'liquidity': 'no_vencimento',
      'tax_note': 'IR de 17,5% no resgate',
      'risk_note': '',
      'monthly_income_estimate': 93.33,
      'score': null,
      'data_completeness': null,
    },
  ],
  'assets': [
    {
      'kind': 'fii',
      'label': 'HGLG11',
      'ticker': 'HGLG11',
      'net_income_yield_pct': 9.1,
      'income_basis': 'dividend yield dos últimos 12 meses',
      'upside_pct': 12.0,
      'has_upside': true,
      'liquidity': 'bolsa',
      'tax_note': 'Rendimento isento',
      'risk_note': 'Cota oscila',
      'monthly_income_estimate': 75.83,
      'score': 72.0,
      'data_completeness': 0.9,
    },
  ],
  'best_income_option': null,
  'verdict': 'Hoje a renda fixa paga mais renda que o FII comparado.',
  'disclaimer': 'Conteúdo educativo.',
};

void main() {
  group('leitura do payload', () {
    test('as duas colunas chegam separadas', () {
      final r = IncomeCompare.fromJson(payload());

      expect(r.fixedIncome, hasLength(1));
      expect(r.assets, hasLength(1));
    });

    test('a base do número viaja junto do número', () {
      final r = IncomeCompare.fromJson(payload());

      expect(r.fixedIncome.first.incomeBasis, contains('contratada'));
      expect(r.assets.first.incomeBasis, contains('12 meses'));
    });

    test('só a bolsa declara valorização possível', () {
      final r = IncomeCompare.fromJson(payload());

      expect(r.fixedIncome.first.hasUpside, isFalse);
      expect(r.assets.first.hasUpside, isTrue);
    });

    test('a ressalva não é opcional', () {
      final r = IncomeCompare.fromJson(payload());

      expect(r.disclaimer, isNotEmpty);
    });

    test('sem melhor opção o campo é nulo e não estoura', () {
      expect(IncomeCompare.fromJson(payload()).bestIncomeOption, isNull);
    });
  });

  group('resiliência a resposta incompleta', () {
    test('listas ausentes viram listas vazias', () {
      final r = IncomeCompare.fromJson({
        'amount': 1000.0,
        'horizon_months': 12,
        'cdi_anual': 14.4,
      });

      expect(r.fixedIncome, isEmpty);
      expect(r.assets, isEmpty);
    });

    test('ticker nulo é aceito — renda fixa não tem ticker', () {
      final r = IncomeCompare.fromJson(payload());

      expect(r.fixedIncome.first.ticker, isNull);
      expect(r.assets.first.ticker, 'HGLG11');
    });
  });

  group('rótulos de liquidez', () {
    test('cada forma de sair do investimento tem nome próprio', () {
      expect(liquidityLabel('diaria'), 'Resgate diário');
      expect(liquidityLabel('no_vencimento'), 'Só no vencimento');
      expect(liquidityLabel('bolsa'), 'Venda em bolsa (D+2)');
    });

    test('valor desconhecido aparece cru em vez de sumir', () {
      expect(liquidityLabel('resgate_em_d30'), 'resgate_em_d30');
    });
  });
}
