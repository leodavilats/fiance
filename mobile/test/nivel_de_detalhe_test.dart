import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/models.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/features/market/asset_detail_sheet.dart';

const _analise = {
  'symbol': 'PETR4',
  'name': 'Petrobras PN',
  'asset_type': 'br_stock',
  'price': 38.0,
  'as_of': 1790000000.0,
  'fair_price': {
    'fair_low': 35.0,
    'fair_high': 45.0,
    'principal_value': 40.0,
    'margin_of_safety': 0.0,
    'band_quality': 'firme',
    'independent_inputs': 2,
    'principal': 'lucros_descontados',
    'methods': [
      {'method': 'dcf', 'input': 'lucro', 'role': 'principal', 'status': 'ok', 'note': '', 'value': 40.0},
      {'method': 'vpa', 'input': 'patrimonio', 'role': 'inaplicavel', 'status': 'inaplicavel', 'note': 'vale para FII'},
    ],
    'premises': {'discount_rate': 0.145, 'growth': 0.05, 'reference_date': '2026-09-25', 'selic_pct': 9.48, 'rate_base': 'selic_media_10a'},
  },
  'technical': {'trend': 'uptrend', 'rsi_14': 50.0},
  'decision': {
    'verdict': 'HOLD',
    'label': 'No preço justo',
    'basis': 'band',
    'reasons': ['Primeira razão.', 'Segunda razão.', 'Terceira razão.', 'Quarta razão.'],
  },
};

const _preferencias = {'desired_yield_stock': 0.06, 'desired_yield_fii': 0.10};

class _Api extends Interceptor {
  _Api(this.nivel);

  final String nivel;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final dados = options.path.startsWith('/asset/')
        ? _analise
        : {..._preferencias, 'detail_level': nivel};
    handler.resolve(Response<dynamic>(requestOptions: options, statusCode: 200, data: dados));
  }
}

Future<void> _abrir(WidgetTester tester, String nivel) async {
  tester.view.physicalSize = const Size(390, 2400) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final dio = Dio()..interceptors.add(_Api(nivel));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(dio))],
      child: MaterialApp(
        theme: buildAppTheme(Brightness.light),
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () => showAssetDetailSheet(context, 'PETR4'),
              child: const Text('abrir'),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('abrir'));
  for (var i = 0; i < 10; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

Finder _texto(String trecho) => find.byWidgetPredicate(
      (w) => w is Text && (w.data ?? '').toLowerCase().contains(trecho.toLowerCase()),
    );

void main() {
  test('sem escolha declarada, o nível é completo', () {
    expect(Preferences.fromJson(_preferencias).detailLevel, 'completo');
    expect(
      Preferences.fromJson({..._preferencias, 'detail_level': 'avancado'}).detailLevel,
      'avancado',
    );
  });

  testWidgets('no essencial, o método vem numa gaveta fechada, e o porquê fica aberto', (tester) async {
    await _abrir(tester, 'essencial');

    expect(_texto('Como chegamos nisso'), findsOneWidget);
    expect(_texto('Quanto o ativo vale'), findsNothing, reason: 'nada é escondido: vem fechado');
    expect(_texto('Primeira razão.'), findsOneWidget);
  });

  testWidgets('no completo, as seções de método vêm abertas', (tester) async {
    await _abrir(tester, 'completo');

    expect(_texto('Quanto o ativo vale'), findsOneWidget);
    expect(_texto('Como chegamos nisso'), findsNothing);
    expect(_texto('Os métodos e os insumos'), findsNothing);
  });

  testWidgets('no avançado, os métodos e os insumos do cálculo aparecem', (tester) async {
    await _abrir(tester, 'avancado');

    await tester.scrollUntilVisible(
      _texto('Data de referência do cálculo'),
      300,
      scrollable: find.byType(Scrollable).last,
    );
    expect(_texto('Os métodos e os insumos'), findsOneWidget);
    expect(_texto('Data de referência do cálculo'), findsOneWidget);
  });
}
