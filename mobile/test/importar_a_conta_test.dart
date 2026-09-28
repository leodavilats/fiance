import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/button.dart';
import 'package:fiance/features/config/import_account_screen.dart';

const _arquivo = <String, dynamic>{
  'format_version': 1,
  'exported_at': 1790000000.0,
  'user': {'email': 'maria@exemplo.com'},
  'data': <String, dynamic>{},
};

class _Servidor extends Interceptor {
  _Servidor(this.previa);

  final Map<String, dynamic> previa;
  final pedidos = <String, Object?>{};

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    pedidos['${options.method} ${options.path}'] = options.data;
    handler.resolve(
      Response<dynamic>(
        requestOptions: options,
        statusCode: 200,
        data: options.path.endsWith('/preview') ? previa : {'imported': <String, int>{}},
      ),
    );
  }
}

Future<_Servidor> _montar(WidgetTester tester, Map<String, dynamic> previa) async {
  tester.view.physicalSize = const Size(390, 2000) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final servidor = _Servidor(previa);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiRepositoryProvider.overrideWithValue(
          ApiRepository(Dio()..interceptors.add(servidor)),
        ),
        accountFileReaderProvider.overrideWithValue(() async => _arquivo),
      ],
      child: MaterialApp.router(
        theme: buildAppTheme(Brightness.light),
        routerConfig: GoRouter(
          initialLocation: '/voce/conta/importar',
          routes: [
            GoRoute(
              path: '/voce/conta/importar',
              builder: (context, state) => const ImportAccountScreen(),
            ),
            GoRoute(
              path: '/patrimonio',
              builder: (context, state) => const Scaffold(body: Text('Patrimônio')),
            ),
          ],
        ),
      ),
    ),
  );
  await tester.tap(find.widgetWithText(FiButton, 'Escolher o arquivo'));
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
  return servidor;
}

FiButton _importar(WidgetTester tester) =>
    tester.widget<FiButton>(find.widgetWithText(FiButton, 'Importar'));

Map<String, dynamic> _previa({
  List<String> blockers = const [],
  List<Map<String, dynamic>> issues = const [],
}) => {
  'format_version': 1,
  'exported_at': 1790000000.0,
  'source_email': 'maria@exemplo.com',
  'sections': [
    {'section': 'transactions', 'label': 'Lançamentos do razão', 'count': 12},
    {'section': 'cash_entries', 'label': 'Lançamentos do mês', 'count': 30},
  ],
  'left_out': [
    {'section': 'device_tokens', 'label': 'aparelhos cadastrados para notificação'},
  ],
  'issues': issues,
  'blockers': blockers,
  'ok': blockers.isEmpty && issues.isEmpty,
};

void main() {
  testWidgets('o arquivo é conferido antes, e só então se importa', (tester) async {
    final servidor = await _montar(tester, _previa());

    expect(
      servidor.pedidos['POST /account/import/preview'],
      {'export': _arquivo},
      reason: 'a prévia vem do servidor, que é quem valida o arquivo',
    );
    expect(find.text('Lançamentos do razão'), findsOneWidget);
    expect(find.textContaining('aparelhos cadastrados para notificação'), findsOneWidget);
    expect(servidor.pedidos.containsKey('POST /account/import'), isFalse);

    await tester.tap(find.widgetWithText(FiButton, 'Importar'));
    for (var i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 120));
    }

    expect(servidor.pedidos['POST /account/import'], {'export': _arquivo});
    expect(find.text('Patrimônio'), findsOneWidget, reason: 'depois de importar, a carteira');
  });

  testWidgets('conta com dados não importa, e diz o que já existe', (tester) async {
    await _montar(tester, _previa(blockers: ['lançamentos do mês']));

    expect(find.textContaining('Esta conta já tem lançamentos do mês'), findsOneWidget);
    expect(
      _importar(tester).onPressed,
      isNull,
      reason: 'somar o arquivo ao que já existe duplicaria a carteira',
    );
  });

  testWidgets('item com problema aparece com o lugar, e trava a gravação', (tester) async {
    await _montar(
      tester,
      _previa(
        issues: [
          {
            'section': 'cash_entries',
            'label': 'Lançamentos do mês',
            'index': 3,
            'message': 'Valor negativo não é lançamento',
          },
        ],
      ),
    );

    expect(
      find.text('Lançamentos do mês, item 3: Valor negativo não é lançamento'),
      findsOneWidget,
    );
    expect(_importar(tester).onPressed, isNull);
  });
}
