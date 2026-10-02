import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/features/market/opportunities_tab.dart';

class _Servidor extends Interceptor {
  final buscas = <Object?>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (options.path == '/opportunities') {
      buscas.add(options.queryParameters['search']);
      handler.resolve(
        Response<dynamic>(requestOptions: options, statusCode: 200, data: {'items': []}),
      );
      return;
    }
    if (options.path == '/universe/search') {
      handler.resolve(
        Response<dynamic>(requestOptions: options, statusCode: 200, data: {'items': []}),
      );
      return;
    }
    handler.reject(
      DioException(
        requestOptions: options,
        response: Response<dynamic>(requestOptions: options, statusCode: 404),
        type: DioExceptionType.badResponse,
      ),
    );
  }
}

Future<void> _esperar(WidgetTester tester) async {
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

Future<_Servidor> _montar(WidgetTester tester) async {
  tester.view.physicalSize = const Size(390, 1600) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final servidor = _Servidor();
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiRepositoryProvider.overrideWithValue(
          ApiRepository(Dio()..interceptors.add(servidor)),
        ),
      ],
      child: MaterialApp(
        theme: buildAppTheme(Brightness.light),
        home: const Scaffold(body: OpportunitiesTab()),
      ),
    ),
  );
  await _esperar(tester);
  return servidor;
}

void main() {
  testWidgets('o Enter aplica a busca, e ela vira ficha que se remove', (tester) async {
    final servidor = await _montar(tester);
    expect(find.text('Nenhum ativo na lista agora'), findsOneWidget);

    await tester.enterText(find.byType(TextField), 'XPTO');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await _esperar(tester);

    expect(servidor.buscas.last, 'XPTO', reason: 'o Enter não fazia nada: só a sugestão buscava');
    expect(find.text('Busca: XPTO'), findsOneWidget, reason: 'a busca aplicada tem de aparecer');
    expect(find.text('Filtros: 1'), findsOneWidget, reason: 'a busca conta como recorte');
    expect(
      find.text('Nenhum ativo com esse nome'),
      findsOneWidget,
      reason: 'vazio por causa do nome não pode culpar o yield ou a margem',
    );

    await tester.tap(find.text('Limpar a busca'));
    await _esperar(tester);

    expect(find.text('Busca: XPTO'), findsNothing);
    expect(
      tester.widget<TextField>(find.byType(TextField)).controller!.text,
      isEmpty,
      reason: 'limpar a busca e deixar o texto no campo mostra um filtro que não vale mais',
    );
    expect(servidor.buscas.last, isNull);
  });

  testWidgets('esvaziar o campo tira a busca', (tester) async {
    final servidor = await _montar(tester);

    await tester.enterText(find.byType(TextField), 'ABC');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await _esperar(tester);
    expect(servidor.buscas.last, 'ABC');

    await tester.enterText(find.byType(TextField), '');
    await _esperar(tester);

    expect(
      servidor.buscas.last,
      isNull,
      reason: 'o campo vazio continuava filtrando pela última sugestão tocada',
    );
    expect(find.text('Busca: ABC'), findsNothing);
  });

  testWidgets('a falha da lista tem saída, e não é o vazio', (tester) async {
    tester.view.physicalSize = const Size(390, 1600) * 2;
    tester.view.devicePixelRatio = 2;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(Dio()
          ..interceptors.add(
            InterceptorsWrapper(
              onRequest: (options, handler) => handler.reject(
                DioException(
                  requestOptions: options,
                  response: Response<dynamic>(requestOptions: options, statusCode: 503),
                  type: DioExceptionType.badResponse,
                ),
              ),
            ),
          )))],
        child: MaterialApp(
          theme: buildAppTheme(Brightness.light),
          home: const Scaffold(body: OpportunitiesTab()),
        ),
      ),
    );
    await _esperar(tester);

    expect(find.text('Tentar de novo'), findsOneWidget, reason: 'a falha sem saída prendia a tela');
    expect(find.text('Nenhum ativo na lista agora'), findsNothing);
  });
}
