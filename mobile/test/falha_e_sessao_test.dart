import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/auth_service.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/data_row.dart';
import 'package:fiance/core/widgets/error_state.dart';
import 'package:fiance/core/widgets/range.dart';
import 'package:fiance/core/widgets/score_ruler.dart';
import 'package:fiance/features/auth/login_screen.dart';

DioException _status(int status, {Object? data}) => DioException(
  requestOptions: RequestOptions(),
  response: Response<dynamic>(requestOptions: RequestOptions(), statusCode: status, data: data),
  type: DioExceptionType.badResponse,
);

class _Login extends AuthService {
  _Login(this.falha);

  final Object falha;

  @override
  Future<AppUser> signInWithGoogle() async => throw falha;
}

Future<void> _montar(WidgetTester tester, Widget filho) => tester.pumpWidget(
  ProviderScope(
    child: MaterialApp(
      theme: buildAppTheme(Brightness.light),
      home: Scaffold(body: filho),
    ),
  ),
);

Future<void> _entrar(WidgetTester tester, Object falha) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [authServiceProvider.overrideWithValue(_Login(falha))],
      child: MaterialApp(theme: buildAppTheme(Brightness.light), home: const LoginScreen()),
    ),
  );
  await tester.tap(find.text('Continuar com Google'));
  await tester.pump();
  await tester.pump();
}

void main() {
  group('fiErrorMessage', () {
    test('403 é falta de permissão, não sessão vencida', () {
      final mensagem = fiErrorMessage(_status(403), action: 'abrir a manutenção');

      expect(mensagem, isNot(contains('sessão')),
          reason: 'o backend usa 403 para rota de operador; mandar entrar de novo não resolve');
      expect(mensagem, contains('permissão'));
    });

    test('402 nomeia o limite do plano', () {
      final mensagem = fiErrorMessage(_status(402, data: {
        'detail': {'reason': 'Você usou 3 de 3 ativos do plano free.', 'limit_reached': true},
      }));

      expect(mensagem, contains('limite do seu plano'));
      expect(mensagem, contains('3 de 3'));
      expect(mensagem, isNot(contains('conexão')),
          reason: 'limite de plano não é rede caída; a pessoa tentaria de novo para sempre');
    });
  });

  group('FiErrorState', () {
    testWidgets('sessão expirada oferece entrar de novo, e não tentar de novo', (tester) async {
      await _montar(tester, FiErrorState(error: _status(401), onRetry: () {}));

      expect(find.text('Entrar de novo'), findsOneWidget);
      expect(find.text('Tentar de novo'), findsNothing,
          reason: 'repetir o pedido com a sessão vencida só devolve o mesmo 401');
    });

    testWidgets('falha comum segue oferecendo tentar de novo', (tester) async {
      await _montar(tester, FiErrorState(error: _status(503), onRetry: () {}));

      expect(find.text('Tentar de novo'), findsOneWidget);
      expect(find.text('Entrar de novo'), findsNothing);
    });
  });

  group('login', () {
    testWidgets('cancelar o seletor do Google não é erro', (tester) async {
      await _entrar(tester, const SignInCancelled());

      expect(find.textContaining('Não conseguimos'), findsNothing);
      expect(find.textContaining('Falha'), findsNothing,
          reason: 'quem fechou o seletor desistiu; pintar isso de vermelho é acusar a pessoa');
    });

    testWidgets('falha de rede no login sai em frase, sem a exceção crua', (tester) async {
      await _entrar(
        tester,
        DioException(requestOptions: RequestOptions(), type: DioExceptionType.connectionError),
      );

      expect(find.textContaining('Sem conexão'), findsOneWidget);
      expect(find.textContaining('DioException'), findsNothing);
    });
  });

  group('leitor de tela', () {
    testWidgets('linha navegável fala o detalhe e a nota uma vez só', (tester) async {
      final semantica = tester.ensureSemantics();
      await _montar(
        tester,
        FiDataRow(
          label: 'Reserva de emergência',
          value: '6 meses',
          detail: 'Medida contra o gasto fixo',
          note: 'Coberta pela liquidez diária',
          onTap: () {},
        ),
      );

      expect(
        find.bySemanticsLabel(
          'Reserva de emergência: 6 meses. Medida contra o gasto fixo. Coberta pela liquidez diária',
        ),
        findsOneWidget,
      );
      expect(find.bySemanticsLabel('Medida contra o gasto fixo'), findsNothing,
          reason: 'o texto filho repetia o que o rótulo composto já disse');
      semantica.dispose();
    });

    testWidgets('a faixa e a régua não leem o número duas vezes', (tester) async {
      final semantica = tester.ensureSemantics();
      await _montar(
        tester,
        const Column(
          children: [
            FiRange(label: 'Preço justo', low: 10, high: 20, base: 15),
            SizedBox(width: 300, child: ScoreRuler(score: 78)),
          ],
        ),
      );

      expect(find.bySemanticsLabel(RegExp(r'^entre ')), findsNothing,
          reason: 'o Text "entre ..." era lido de novo depois do rótulo da faixa');
      expect(find.bySemanticsLabel(RegExp(r'cenário base')), findsOneWidget);
      expect(find.bySemanticsLabel('78'), findsNothing);
      semantica.dispose();
    });
  });
}
