import 'package:dio/dio.dart';
import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/format.dart';
import 'package:fiance/core/models.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/score_ruler.dart';
import 'package:fiance/features/market/quick_invest_view.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _analitico = <String, dynamic>{
  'total_cash': 1000.0,
  'cash_source': 'cascade',
  'basis': 'goals',
  'allocated_cash': null,
  'remaining_cash': null,
  'summary': 'Esta ordem cobre 1 ativo e uma fatia em renda fixa.',
  'allocations': [
    {
      'ticker': 'PETR4',
      'name': 'Petrobras',
      'category': 'acoes_br',
      'sector': 'Energia',
      'current_price': 38.0,
      'suggested_quantity': null,
      'suggested_investment': null,
      'rationale': 'score 82',
      'score': 82.0,
      'dividend_yield': 12.0,
    },
  ],
  'fixed_income': {
    'amount': null,
    'reference_monthly_pct': 0.94,
    'reference_source': 'bcb',
    'rationale': 'A alocação-alvo pede renda fixa.',
  },
  'unallocated': [
    {'value': null, 'reason': 'Troco de cota inteira em acoes_br'},
  ],
  'portfolio_balance': {
    'acoes_br': {'value': null, 'percentage': null, 'target': 40.0},
  },
  'affirmation': {
    'level': 2,
    'prescriptive': false,
    'disclaimer': 'Leitura de critérios objetivos.',
  },
};

class _Resposta extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    handler.resolve(
      Response<dynamic>(requestOptions: options, statusCode: 200, data: _analitico),
    );
  }
}

List<String> _textos(WidgetTester tester) => [
  for (final w in tester.widgetList<Text>(find.byType(Text)))
    w.data ?? w.textSpan?.toPlainText() ?? '',
  for (final w in tester.widgetList<RichText>(find.byType(RichText)))
    w.text.toPlainText(),
];

void main() {
  testWidgets('no modo analítico a tela não inventa cifra que a régua retirou', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 2400) * 2;
    tester.view.devicePixelRatio = 2;
    addTearDown(tester.view.reset);

    final dio = Dio()..interceptors.add(_Resposta());
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(dio))],
        child: MaterialApp(
          theme: buildAppTheme(Brightness.light),
          home: const Scaffold(body: QuickInvestView()),
        ),
      ),
    );
    for (var i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 120));
    }

    final textos = _textos(tester);
    final cifras = textos.where((t) => t.contains(r'R$')).toSet();
    expect(
      cifras,
      {formatCurrency(1000.0), formatCurrency(38.0)},
      reason:
          'fora do prescritivo só ficam o caixa que entrou e o preço do ativo; alocado, sobra '
          'e valor sem destino saem nulos, e nulo formatado como moeda vira R\$ 0,00 inventado',
    );
    expect(
      textos.any((t) => t.contains('Troco de cota inteira')),
      isTrue,
      reason: 'o motivo do que não coube é análise e continua na tela',
    );
    expect(
      textos.any((t) => t.contains('fica em caixa')),
      isTrue,
      reason: 'o aviso diz por que a sobra aparece como —',
    );
  });

  testWidgets('o score da alocação sai na régua, e não só como selo', (tester) async {
    tester.view.physicalSize = const Size(390, 2400) * 2;
    tester.view.devicePixelRatio = 2;
    addTearDown(tester.view.reset);

    final dio = Dio()..interceptors.add(_Resposta());
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(dio))],
        child: MaterialApp(
          theme: buildAppTheme(Brightness.light),
          home: const Scaffold(body: QuickInvestView()),
        ),
      ),
    );
    for (var i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 120));
    }

    final reguas = tester.widgetList<ScoreRuler>(find.byType(ScoreRuler)).toList();
    expect(
      reguas.map((r) => r.score),
      [82.0],
      reason: 'o selo dizia a faixa sem o número nem a escala: julgamento sem explicação',
    );
  });

  group('QuickInvestResult', () {
    test('sobrevive ao modo analítico, que retira o valor de ação', () {
      final json = <String, dynamic>{
        'total_cash': 1000.0,
        'allocated_cash': null,
        'remaining_cash': null,
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
        'unallocated': [
          {'value': null, 'reason': 'Troco de cota inteira'},
        ],
        'affirmation': {
          'level': 2,
          'prescriptive': false,
          'disclaimer': 'Leitura de critérios objetivos.',
        },
      };

      final resultado = QuickInvestResult.fromJson(json);

      expect(resultado.allocatedCash, isNull);
      expect(
        resultado.remainingCash,
        isNull,
        reason: 'caixa menos sobra é o alocado: a sobra sai junto com ele',
      );
      expect(resultado.totalCash, 1000.0);
      expect(resultado.unallocated.single.value, isNull);
      expect(resultado.unallocated.single.reason, 'Troco de cota inteira');

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
        'allocated_cash': 174.46,
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
      expect(resultado.hasDestination, isTrue, reason: 'renda fixa e destino');

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

      expect(resultado.hasDestination, isFalse);
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
