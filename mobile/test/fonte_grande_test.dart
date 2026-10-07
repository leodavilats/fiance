import 'package:dio/dio.dart';
import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/notifications_service.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/router.dart';
import 'package:fiance/core/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'fixtures/rede_dublada.dart';

class _SemNotificacao extends NotificationsService {
  _SemNotificacao(super.repo);

  @override
  Future<void> init() async {}
}

void main() {
  for (final tela in telasDoApp.entries) {
    testWidgets('${tela.key} cabe em 320dp com letra larga', (tester) async {
      tester.view.physicalSize = const Size(320, 2400) * 2;
      tester.view.devicePixelRatio = 2;
      addTearDown(tester.view.reset);

      final api = ApiRepository(Dio()..interceptors.add(RedeDublada(Estado.conteudo)));
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiRepositoryProvider.overrideWithValue(api),
            notificationsServiceProvider.overrideWithValue(_SemNotificacao(api)),
          ],
          child: MaterialApp.router(
            theme: buildAppTheme(Brightness.light),
            routerConfig: GoRouter(
              initialLocation: tela.value,
              routes: appRouter.configuration.routes,
            ),
          ),
        ),
      );
      for (var i = 0; i < 8; i++) {
        await tester.pump(const Duration(milliseconds: 120));
      }

      final estouros = <String>[];
      while (true) {
        final excecao = tester.takeException();
        if (excecao == null) break;
        final texto = excecao.toString();
        if (texto.contains('allowRuntimeFetching')) continue;
        estouros.add(texto.split('\n').first);
      }
      expect(
        estouros,
        isEmpty,
        reason: '${tela.value} estoura em tela estreita: com a fonte do sistema grande, quem '
            'usa o app perde o fim da linha',
      );
    });
  }
}
