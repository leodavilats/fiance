import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/button.dart';
import 'package:fiance/core/widgets/controls.dart';
import 'package:fiance/features/patrimony/import_screen.dart';
import 'package:fiance/features/patrimony/reconciliation_screen.dart';

class _Servidor extends Interceptor {
  _Servidor(this.respostas);

  final Map<String, Object? Function(Object? corpo)> respostas;
  final pedidos = <String, Object?>{};

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final chave = '${options.method} ${options.path}';
    pedidos[chave] = options.data;
    final resposta = respostas[chave];
    if (resposta == null) {
      handler.reject(
        DioException(
          requestOptions: options,
          response: Response<dynamic>(requestOptions: options, statusCode: 404),
          type: DioExceptionType.badResponse,
        ),
      );
      return;
    }
    handler.resolve(
      Response<dynamic>(requestOptions: options, statusCode: 200, data: resposta(options.data)),
    );
  }
}

Future<void> _montar(WidgetTester tester, _Servidor servidor, Widget tela) async {
  tester.view.physicalSize = const Size(390, 2400) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiRepositoryProvider.overrideWithValue(
          ApiRepository(Dio()..interceptors.add(servidor)),
        ),
      ],
      child: MaterialApp(theme: buildAppTheme(Brightness.light), home: tela),
    ),
  );
  await _esperar(tester);
}

Future<void> _esperar(WidgetTester tester) async {
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

Map<String, Object?> _linha(int linha, String ativo, {int? duplicada}) => {
  'line': linha,
  'kind': 'buy',
  'symbol': ativo,
  'traded_on': '2026-09-01',
  'quantity': 100,
  'price': 30.5,
  'fees': 0,
  'ratio_from': 1,
  'ratio_to': 1,
  'amount': 0,
  'note': null,
  'duplicate_of': duplicada,
};

FiButton _importar(WidgetTester tester) => tester.widget<FiButton>(
  find.byWidgetPredicate((w) => w is FiButton && w.label.startsWith('Importar ')),
);

void main() {
  group('importação de extrato', () {
    testWidgets('a repetida fica de fora até a pessoa decidir', (tester) async {
      final servidor = _Servidor({
        'POST /transactions/import/preview': (_) => {
          'format': 'lista colada',
          'rows': [_linha(1, 'PETR4'), _linha(2, 'VALE3', duplicada: 7)],
          'issues': <Object>[],
          'ok': true,
          'duplicates': 1,
        },
        'POST /transactions/import': (_) => {
          'imported': 2,
          'skipped_duplicates': 0,
          'ids': [1, 2],
        },
      });
      await _montar(tester, servidor, const ImportScreen());

      await tester.enterText(find.byType(TextField), 'PETR4 100 30,50\nVALE3 100 30,50');
      await tester.pump();
      await tester.tap(find.widgetWithText(FiButton, 'Conferir'));
      await _esperar(tester);

      expect(find.textContaining('1 operação nova e 1 que já existe'), findsOneWidget);
      expect(
        find.widgetWithText(FiButton, 'Importar 1 operação'),
        findsOneWidget,
        reason: 'duplicidade é apresentada para decisão, e a decisão padrão é não gravar de novo',
      );
      expect(tester.widget<FiSwitch>(find.byType(FiSwitch)).value, isFalse);

      await tester.tap(find.byType(Switch));
      await tester.pump();
      expect(find.widgetWithText(FiButton, 'Importar 2 operações'), findsOneWidget);

      await tester.tap(find.widgetWithText(FiButton, 'Importar 2 operações'));
      await _esperar(tester);

      expect(
        servidor.pedidos['POST /transactions/import'],
        {'content': 'PETR4 100 30,50\nVALE3 100 30,50', 'include_duplicates': true},
        reason: 'o que se grava é o mesmo texto que foi conferido, com a escolha da pessoa',
      );
    });

    testWidgets('com linha errada, nada se importa', (tester) async {
      final servidor = _Servidor({
        'POST /transactions/import/preview': (_) => {
          'format': 'lista colada',
          'rows': [_linha(1, 'PETR4')],
          'issues': [
            {
              'line': 2,
              'message': 'Faltou quantidade ou preço.',
              'field': null,
              'raw': 'VALE3 100',
            },
          ],
          'ok': false,
          'duplicates': 0,
        },
      });
      await _montar(tester, servidor, const ImportScreen());

      await tester.enterText(find.byType(TextField), 'PETR4 100 30,50\nVALE3 100');
      await tester.pump();
      await tester.tap(find.widgetWithText(FiButton, 'Conferir'));
      await _esperar(tester);

      expect(find.textContaining('Linha 2: Faltou quantidade ou preço.'), findsOneWidget);
      expect(
        _importar(tester).onPressed,
        isNull,
        reason: 'a importação é tudo ou nada: o erro diz a linha e trava a gravação',
      );
    });

    testWidgets('mudar o texto depois de conferir desfaz a revisão', (tester) async {
      final servidor = _Servidor({
        'POST /transactions/import/preview': (_) => {
          'format': 'lista colada',
          'rows': [_linha(1, 'PETR4')],
          'issues': <Object>[],
          'ok': true,
          'duplicates': 0,
        },
      });
      await _montar(tester, servidor, const ImportScreen());

      await tester.enterText(find.byType(TextField), 'PETR4 100 30,50');
      await tester.pump();
      await tester.tap(find.widgetWithText(FiButton, 'Conferir'));
      await _esperar(tester);
      expect(find.text('Revisão'), findsOneWidget);

      await tester.enterText(find.byType(TextField), 'PETR4 200 30,50');
      await tester.pump();

      expect(
        find.text('Revisão'),
        findsNothing,
        reason: 'gravar um texto que ninguém conferiu é gravar sem prévia',
      );
    });
  });

  group('conferência da carteira com o razão', () {
    Map<String, Object?> conferencia() => {
      'positions': 2,
      'projected': 1,
      'in_sync': false,
      'differences': [
        {
          'ticker': 'ITSA4',
          'reason': 'posicao_sem_razao',
          'stored': {'ticker': 'ITSA4', 'quantity': 50, 'avg_price': 10},
          'projected': null,
        },
        {
          'ticker': 'PETR4',
          'reason': 'quantidade',
          'stored': {'ticker': 'PETR4', 'quantity': 90, 'avg_price': 30},
          'projected': {'symbol': 'PETR4', 'quantity': 100, 'avg_price': 30},
        },
      ],
    };

    testWidgets('refazer avisa o que sai antes de apagar', (tester) async {
      final servidor = _Servidor({
        'GET /transactions/reconciliation': (_) => conferencia(),
        'POST /transactions/rebuild': (_) => {
          'rebuilt': 2,
          'reconciliation': {
            'positions': 1,
            'projected': 1,
            'in_sync': true,
            'differences': <Object>[],
          },
        },
      });
      await _montar(tester, servidor, const ReconciliationScreen());

      expect(find.text('2 diferenças entre a carteira e o razão'), findsOneWidget);
      expect(find.widgetWithText(FiButton, 'Levar 1 posição para o razão'), findsOneWidget);

      await tester.tap(find.widgetWithText(FiButton, 'Refazer a carteira a partir do razão'));
      await tester.pumpAndSettle();

      expect(
        find.textContaining('ITSA4 sai da carteira'),
        findsOneWidget,
        reason: 'reconstruir apaga posição sem lançamento; a pessoa precisa saber qual antes',
      );
      expect(servidor.pedidos.containsKey('POST /transactions/rebuild'), isFalse);

      await tester.tap(find.text('Refazer'));
      await _esperar(tester);

      expect(servidor.pedidos.containsKey('POST /transactions/rebuild'), isTrue);
    });

    testWidgets('levar para o razão chama o backfill', (tester) async {
      final servidor = _Servidor({
        'GET /transactions/reconciliation': (_) => conferencia(),
        'POST /transactions/backfill': (_) => {'seeded': 1},
      });
      await _montar(tester, servidor, const ReconciliationScreen());

      await tester.tap(find.widgetWithText(FiButton, 'Levar 1 posição para o razão'));
      await _esperar(tester);

      expect(servidor.pedidos.containsKey('POST /transactions/backfill'), isTrue);
      expect(find.text('1 posição(ões) levada(s) para o razão.'), findsOneWidget);
    });

    testWidgets('em dia, não oferece o que não precisa', (tester) async {
      final servidor = _Servidor({
        'GET /transactions/reconciliation': (_) => {
          'positions': 3,
          'projected': 3,
          'in_sync': true,
          'differences': <Object>[],
        },
      });
      await _montar(tester, servidor, const ReconciliationScreen());

      expect(find.text('A carteira bate com o razão'), findsOneWidget);
      expect(find.widgetWithText(FiButton, 'Refazer a carteira a partir do razão'), findsNothing);
    });
  });
}
