import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/auth_service.dart';
import 'package:fiance/core/notifications_service.dart';
import 'package:fiance/core/providers.dart';

const _token = 'fAparelho:APA91bXy_-9Xy_-9Xy_-9Xy_-9Xy_-9Xy_-9';

class _Servidor extends Interceptor {
  _Servidor(this.chamadas, {this.status = 204});

  final List<String> chamadas;
  final int status;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    chamadas.add('${options.method} ${options.path} ${options.queryParameters['token']}');
    final resposta = Response<dynamic>(requestOptions: options, statusCode: status);
    if (status >= 400) {
      handler.reject(DioException.badResponse(
        statusCode: status,
        requestOptions: options,
        response: resposta,
      ));
      return;
    }
    handler.resolve(resposta);
  }
}

class _Sessao extends AuthService {
  _Sessao(this.chamadas);

  final List<String> chamadas;

  @override
  Future<void> signOut({bool allDevices = false}) async {
    chamadas.add('signOut');
  }
}

ProviderContainer _montar(List<String> chamadas, {int status = 204}) {
  final repo = ApiRepository(Dio()..interceptors.add(_Servidor(chamadas, status: status)));
  final container = ProviderContainer(
    overrides: [
      authServiceProvider.overrideWithValue(_Sessao(chamadas)),
      apiRepositoryProvider.overrideWithValue(repo),
      notificationsServiceProvider.overrideWithValue(
        NotificationsService(repo, readToken: () async => _token),
      ),
    ],
  );
  addTearDown(container.dispose);
  return container;
}

void main() {
  test('sair da conta apaga o token do aparelho antes de encerrar a sessão', () async {
    final chamadas = <String>[];
    final container = _montar(chamadas);

    await container.read(signOutProvider)();

    expect(
      chamadas,
      ['DELETE /notifications/register-token $_token', 'signOut'],
      reason:
          'o DELETE precisa da sessão viva; depois dela, o aparelho seguiria recebendo '
          'aviso da carteira de quem saiu',
    );
  });

  test('falha ao apagar o token não prende ninguém na conta', () async {
    final chamadas = <String>[];
    final container = _montar(chamadas, status: 500);

    await container.read(signOutProvider)();

    expect(
      chamadas.last,
      'signOut',
      reason: 'sair é sempre possível; o token órfão é trocado no próximo login do aparelho',
    );
  });

  test('sair da conta limpa o usuário corrente', () async {
    final container = _montar(<String>[]);
    container.read(currentUserProvider.notifier).state = AppUser(
      id: 'u',
      email: 'u@x',
      name: 'U',
      picture: '',
    );

    await container.read(signOutProvider)();

    expect(container.read(currentUserProvider), isNull);
  });
}
