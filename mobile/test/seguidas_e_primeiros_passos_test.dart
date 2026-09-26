import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/button.dart';
import 'package:fiance/core/widgets/controls.dart';
import 'package:fiance/core/widgets/tag.dart';
import 'package:fiance/features/config/onboarding_screen.dart';
import 'package:fiance/features/market/buy_sheet.dart';
import 'package:fiance/features/patrimony/followed_screen.dart';

class _Servidor extends Interceptor {
  _Servidor(this.respostas);

  final Map<String, Object? Function(Object? corpo)> respostas;
  final pedidos = <String>[];
  final corpos = <String, Object?>{};

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final chave = '${options.method} ${options.path}';
    pedidos.add(chave);
    corpos[chave] = options.data;
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

Map<String, Object?> _seguida() => {
  'id': 9,
  'ticker': 'PETR4',
  'source': 'opportunities',
  'action': 'comprar',
  'quantity': 100,
  'price': 30.0,
  'followed_on': '2026-08-27',
  'score_at_suggestion': null,
  'verdict_at_suggestion': 'BUY',
  'note': null,
  'entry_id': 42,
  'invested': 3000.0,
  'current_value': 3300.0,
  'pnl': 300.0,
  'pnl_pct': 10.0,
  'days_held': 30,
  'ibov_pct_since': 2.0,
  'beat_ibov': true,
};

class _Comprar extends ConsumerWidget {
  const _Comprar();

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
    body: Center(
      child: FiButton.primary(
        label: 'Abrir compra',
        onPressed: () => openBuySheet(
          context,
          ref,
          ticker: 'PETR4',
          currentPrice: 30,
          verdict: 'BUY',
        ),
      ),
    ),
  );
}

void main() {
  testWidgets('a compra pelo Descobrir é acompanhada a partir do lançamento', (tester) async {
    final servidor = _Servidor({
      'POST /transactions': (_) => {'id': 42},
      'POST /suggestions/followed': (_) => _seguida(),
    });
    await _montar(tester, servidor, const _Comprar());

    await tester.tap(find.text('Abrir compra'));
    await tester.pumpAndSettle();
    expect(
      tester.widget<FiSwitch>(find.byType(FiSwitch)).value,
      isTrue,
      reason: 'comprar pela leitura do produto é seguir a sugestão; desligar é escolha visível',
    );

    await tester.enterText(find.widgetWithText(TextFormField, 'Quantidade'), '100');
    await tester.tap(find.widgetWithText(FiButton, 'Adicionar à carteira'));
    await _esperar(tester);

    expect(servidor.pedidos, containsAllInOrder(['POST /transactions', 'POST /suggestions/followed']));
    expect(
      servidor.corpos['POST /suggestions/followed'],
      {'entry_id': 42, 'source': 'opportunities', 'verdict_at_suggestion': 'BUY'},
      reason: 'quantidade e preço saem do razão: pedir de novo é o que o item 15 proibiu',
    );
  });

  testWidgets('desligado, a compra entra e não é acompanhada', (tester) async {
    final servidor = _Servidor({'POST /transactions': (_) => {'id': 42}});
    await _montar(tester, servidor, const _Comprar());

    await tester.tap(find.text('Abrir compra'));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(Switch));
    await tester.enterText(find.widgetWithText(TextFormField, 'Quantidade'), '100');
    await tester.tap(find.widgetWithText(FiButton, 'Adicionar à carteira'));
    await _esperar(tester);

    expect(servidor.pedidos, isNot(contains('POST /suggestions/followed')));
  });

  testWidgets('as sugestões seguidas mostram o resultado contra o Ibovespa', (tester) async {
    final servidor = _Servidor({
      'GET /suggestions/followed': (_) => {
        'items': [_seguida()],
        'total_invested': 3000.0,
        'total_current_value': 3300.0,
        'total_pnl': 300.0,
        'total_pnl_pct': 10.0,
        'ibov_pct_same_period': 2.0,
        'beat_ibov': true,
        'by_source': [
          {
            'source': 'Oportunidades',
            'count': 1,
            'invested': 3000.0,
            'current_value': 3300.0,
            'pnl': 300.0,
            'pnl_pct': 10.0,
            'ibov_pct': 2.0,
          },
        ],
        'summary': 'A 1 compra que você fez a partir de sugestões está +10,0%.',
        'next_cursor': null,
        'has_more': false,
        'total_count': 1,
      },
    });
    await _montar(tester, servidor, const FollowedScreen());

    expect(find.text('+10,00%'), findsWidgets);
    expect(find.text('Ibovespa no mesmo período: +2,00%'), findsOneWidget);
    expect(find.text('PETR4'), findsOneWidget);
  });

  group('primeiros passos', () {
    Map<String, Object?> estado({required int step, bool goals = false, bool completed = false}) =>
        {
          'step': step,
          'total_steps': 3,
          'completed': completed,
          'onboarded_at': null,
          'positions': step > 2 ? 1 : 0,
          'has_goals': goals,
          'reason': step == 2 ? 'Falta registrar a primeira posição.' : 'Tudo pronto.',
        };

    testWidgets('o passo sai do que a pessoa já fez, e nada trava', (tester) async {
      final servidor = _Servidor({
        'GET /onboarding': (_) => estado(step: 2),
        'POST /onboarding/complete': (_) => estado(step: 2, completed: true),
      });
      await _montar(tester, servidor, const OnboardingScreen());

      final etiquetas = tester.widgetList<FiTag>(find.byType(FiTag)).map((t) => t.label);
      expect(etiquetas, ['Feito', 'Falta', 'Falta']);
      expect(find.widgetWithText(FiButton, 'Importar extrato'), findsOneWidget);
      expect(
        find.widgetWithText(FiButton, 'Pular por agora'),
        findsOneWidget,
        reason: 'nenhum passo é obrigatório',
      );
    });

    testWidgets('com carteira e meta, conclui', (tester) async {
      final servidor = _Servidor({
        'GET /onboarding': (_) => estado(step: 3, goals: true),
      });
      await _montar(tester, servidor, const OnboardingScreen());

      final etiquetas = tester.widgetList<FiTag>(find.byType(FiTag)).map((t) => t.label);
      expect(etiquetas, ['Feito', 'Feito', 'Feito']);
      expect(find.widgetWithText(FiButton, 'Concluir'), findsOneWidget);
    });
  });
}
