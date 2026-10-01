import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/notifications_service.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/router.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/button.dart';

class _ServidorVazio extends Interceptor {
  final caminhos = <String>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    caminhos.add(options.path);
    if (options.path == '/preferences') {
      handler.resolve(
        Response<dynamic>(
          requestOptions: options,
          statusCode: 200,
          data: {'desired_yield_stock': 0.06, 'desired_yield_fii': 0.10},
        ),
      );
      return;
    }
    handler.reject(
      DioException(
        requestOptions: options,
        response: Response<dynamic>(
          requestOptions: options,
          statusCode: 404,
          data: {'detail': 'sem dado neste teste'},
        ),
        type: DioExceptionType.badResponse,
      ),
    );
  }
}

class _SemNotificacao extends NotificationsService {
  _SemNotificacao(super.repo);

  @override
  Future<void> init() async {}
}

String _ondeEstou() => appRouter.routerDelegate.currentConfiguration.uri.path;

Future<_ServidorVazio> _abrirApp(WidgetTester tester) async {
  tester.view.physicalSize = const Size(390, 844) * 3;
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);

  final servidor = _ServidorVazio();
  final api = ApiRepository(Dio()..interceptors.add(servidor));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiRepositoryProvider.overrideWithValue(api),
        notificationsServiceProvider.overrideWithValue(_SemNotificacao(api)),
      ],
      child: MaterialApp.router(
        theme: buildAppTheme(Brightness.light),
        routerConfig: appRouter,
      ),
    ),
  );
  return servidor;
}

Future<void> _esperar(WidgetTester tester) async {
  for (var i = 0; i < 12; i++) {
    await tester.pump(const Duration(milliseconds: 150));
  }
}

void main() {
  testWidgets('o ciclo do dinheiro percorre os cinco destinos sem quebrar', (tester) async {
    final servidor = await _abrirApp(tester);
    appRouter.go('/mes');
    await _esperar(tester);

    const destinos = {
      'Mês': '/mes',
      'Sobra': '/sobra',
      'Patrimônio': '/patrimonio',
      'Descobrir': '/descobrir',
      'Você': '/voce',
    };
    for (final destino in destinos.entries) {
      await tester.tap(find.descendant(of: find.byType(NavigationBar), matching: find.text(destino.key)));
      await _esperar(tester);

      expect(tester.takeException(), isNull, reason: '${destino.key} quebrou ao abrir');
      expect(_ondeEstou(), startsWith(destino.value));
      await expectLater(
        tester,
        meetsGuideline(labeledTapTargetGuideline),
        reason: 'em ${destino.key}, todo alvo de toque precisa de nome para o leitor de tela',
      );
      await expectLater(
        tester,
        meetsGuideline(iOSTapTargetGuideline),
        reason: 'em ${destino.key}, todo alvo de toque precisa de 44dp',
      );
    }

    expect(
      servidor.caminhos,
      isNotEmpty,
      reason: 'as telas leem do servidor; sem nenhuma chamada, a jornada não exercitou nada',
    );
  });

  testWidgets('com todos os filtros abertos, o aplicar continua ao alcance', (tester) async {
    await _abrirApp(tester);
    tester.view.physicalSize = const Size(360, 640) * 3;
    appRouter.go('/descobrir');
    await _esperar(tester);

    await tester.tap(find.widgetWithText(FiButton, 'Filtros'));
    await _esperar(tester);
    for (final rotulo in ['Dividend yield mínimo', 'Margem de segurança mínima']) {
      final chave = find.bySemanticsLabel(rotulo).last;
      await tester.ensureVisible(chave);
      await tester.tap(chave);
      await _esperar(tester);
    }

    final aplicar = find.widgetWithText(FiButton, 'Aplicar 2 filtros');
    expect(
      aplicar.hitTestable(),
      findsOneWidget,
      reason: 'o botão de aplicar não rola junto: abrir os controles não pode empurrá-lo para fora',
    );
    await tester.tap(aplicar);
    await _esperar(tester);
    expect(find.text('Filtros: 2'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('link salvo de URL antiga continua chegando', (tester) async {
    await _abrirApp(tester);

    const antigas = {
      '/dashboard': '/mes',
      '/hoje': '/mes',
      '/estrategia': '/sobra/desvio',
      '/estrategia/metas': '/voce/objetivos',
      '/carteira': '/patrimonio',
      '/market': '/descobrir',
      '/config': '/voce',
    };
    for (final antiga in antigas.entries) {
      appRouter.go(antiga.key);
      await _esperar(tester);

      expect(_ondeEstou(), antiga.value, reason: 'link salvo é contrato: ${antiga.key}');
      expect(tester.takeException(), isNull);
    }
  });
}
