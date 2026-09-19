import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/button.dart';
import 'package:fiance/features/config/delete_account_screen.dart';

class _Politica extends Interceptor {
  _Politica(this.chamadas);

  final List<String> chamadas;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    chamadas.add('${options.method} ${options.path}');

    handler.resolve(
      Response<dynamic>(
        requestOptions: options,
        statusCode: 200,
        data: {
          'sla_days': 30,
          'removes': ['transactions', 'cash_entries', 'positions'],
          'note': 'Backups e réplicas ainda guardam o dado até serem rotacionados.',
          'confirmation_phrase': 'EXCLUIR',
        },
      ),
    );
  }
}

Future<void> _montar(WidgetTester tester, List<String> chamadas) async {
  tester.view.physicalSize = const Size(390, 1200) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final dio = Dio()..interceptors.add(_Politica(chamadas));

  await tester.pumpWidget(
    ProviderScope(
      overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(dio))],
      child: MaterialApp(
        theme: buildAppTheme(Brightness.light),
        home: const DeleteAccountScreen(),
      ),
    ),
  );
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

FiButton _botao(WidgetTester tester) =>
    tester.widget<FiButton>(find.widgetWithText(FiButton, 'Excluir minha conta'));

void main() {
  testWidgets('a exclusão só se arma com a frase digitada', (tester) async {
    final chamadas = <String>[];
    await _montar(tester, chamadas);

    expect(
      _botao(tester).onPressed,
      isNull,
      reason: 'sem a frase, o botão que apaga a conta inteira não pode estar armado',
    );

    await tester.enterText(find.byType(TextField), 'excluo');
    await tester.pump();
    expect(
      _botao(tester).onPressed,
      isNull,
      reason: 'frase parecida não é a frase: só a confirmação exata arma o botão',
    );

    await tester.enterText(find.byType(TextField), 'excluir');
    await tester.pump();
    expect(
      _botao(tester).onPressed,
      isNotNull,
      reason: 'a frase é conferida sem caixa, senão o teclado do aparelho decide pelo usuário',
    );

    expect(
      chamadas.where((c) => c.startsWith('DELETE')),
      isEmpty,
      reason: 'nada pode ser apagado antes do toque no botão',
    );
  });

  testWidgets('a tela diz o que sai, na palavra do produto', (tester) async {
    await _montar(tester, <String>[]);

    expect(
      find.textContaining('livro-razão'),
      findsOneWidget,
      reason:
          'a lista vem do backend para não descolar dele, e é traduzida para não pedir que '
          'alguém reconheça o nome de uma tabela antes de apagar a própria conta',
    );
    expect(
      find.textContaining('30 dias'),
      findsWidgets,
      reason: 'o prazo de backup é o que separa "apagado" de "apagado em todo lugar"',
    );
  });
}
