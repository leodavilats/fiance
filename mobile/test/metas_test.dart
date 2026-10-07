import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/button.dart';
import 'package:fiance/features/config/goals_screen.dart';

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

class _LeitorDoPasso extends ConsumerWidget {
  const _LeitorDoPasso();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(onboardingProvider);
    ref.watch(surplusProvider);
    ref.watch(rebalanceSuggestionsProvider);
    ref.watch(quickInvestProvider);
    return const SizedBox(height: 1);
  }
}

Future<void> _esperar(WidgetTester tester) async {
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

Future<void> _montar(WidgetTester tester, _Servidor servidor) async {
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
      child: MaterialApp(
        theme: buildAppTheme(Brightness.light),
        home: const Scaffold(
          body: Column(children: [_LeitorDoPasso(), GoalsSection()]),
        ),
      ),
    ),
  );
  await _esperar(tester);
}

List<Map<String, Object?>> _metas(List<double> pcts, {required bool declared}) => [
  for (final (i, c) in ['acoes_br', 'fiis', 'renda_fixa'].indexed)
    {'category': c, 'target_pct': pcts[i], 'declared': declared},
];

FiButton _salvar(WidgetTester tester) =>
    tester.widget<FiButton>(find.widgetWithText(FiButton, 'Salvar metas'));

Map<String, Object? Function(Object?)> _onboarding() => {
  'GET /onboarding': (_) => {
    'step': 3,
    'total_steps': 3,
    'completed': false,
    'onboarded_at': null,
    'positions': 1,
    'has_goals': false,
    'reason': 'Falta definir a primeira meta de alocação.',
  },
};

void main() {
  testWidgets('a divisão de partida pode ser salva sem mexer em nada', (tester) async {
    final servidor = _Servidor({
      ..._onboarding(),
      'GET /goals': (_) => _metas([50, 30, 20], declared: false),
      'PUT /goals': (_) => _metas([50, 30, 20], declared: true),
    });
    await _montar(tester, servidor);

    expect(
      _salvar(tester).onPressed,
      isNotNull,
      reason: 'quem concorda com o ponto de partida precisa conseguir declará-lo sem arrastar '
          'um controle de propósito',
    );

    await tester.tap(find.widgetWithText(FiButton, 'Salvar metas'));
    await _esperar(tester);

    final corpo = servidor.corpos['PUT /goals'] as Map<String, dynamic>;
    expect((corpo['goals'] as List).length, 3, reason: 'salva a divisão que veio do servidor');
    expect(
      servidor.pedidos.where((p) => p == 'GET /onboarding').length,
      2,
      reason: 'salvar a meta muda o passo 3: Primeiros passos tem de ler de novo',
    );
    for (final leitura in ['GET /surplus', 'GET /rebalance-suggestions', 'POST /quick-invest']) {
      expect(
        servidor.pedidos.where((p) => p == leitura).length,
        2,
        reason: 'a Sobra e o desvio seguem montados no shell: sem ler de novo, continuam '
            'dizendo que não há meta ($leitura)',
      );
    }
  });

  testWidgets('declarada e sem mudança, não há o que salvar', (tester) async {
    final servidor = _Servidor({
      ..._onboarding(),
      'GET /goals': (_) => _metas([50, 30, 20], declared: true),
    });
    await _montar(tester, servidor);

    expect(_salvar(tester).onPressed, isNull, reason: 'nada mudou desde a última gravação');
  });

  testWidgets('soma acima de 100% diz quanto passou, e não quanto falta', (tester) async {
    final servidor = _Servidor({
      ..._onboarding(),
      'GET /goals': (_) => _metas([60, 40, 20], declared: true),
    });
    await _montar(tester, servidor);

    expect(find.textContaining('Passou 20 pontos de 100%'), findsOneWidget);
    expect(
      find.textContaining('Faltam'),
      findsNothing,
      reason: 'com 120%, "faltam 20" manda a pessoa somar mais',
    );
  });
}
