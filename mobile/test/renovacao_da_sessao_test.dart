import 'dart:async';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_client.dart';
import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/auth_service.dart';
import 'package:fiance/core/providers.dart';

const _storage = FlutterSecureStorage();

Future<HttpServer> _servidor(Future<void> Function(HttpRequest) responder) async {
  final servidor = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
  servidor.listen(responder);
  addTearDown(() => servidor.close(force: true));
  return servidor;
}

String _base(HttpServer s) => 'http://${s.address.host}:${s.port}';

Future<void> _status(HttpRequest r, int status) async {
  r.response.statusCode = status;
  await r.response.close();
}

class _Sessao extends AuthService {
  _Sessao({this.renovar});

  final Future<bool> Function()? renovar;
  var limpou = false;
  var renovacoes = 0;

  @override
  Future<String?> readToken() async => 'acesso';

  @override
  Future<bool> refreshSession() {
    renovacoes++;
    return renovar!();
  }

  @override
  Future<void> clearSession() async => limpou = true;

  @override
  Future<void> signOut({bool allDevices = false}) async => limpou = true;
}

class _Adaptador implements HttpClientAdapter {
  _Adaptador(this.status);

  final List<int> status;
  var chamadas = 0;

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<List<int>>? body, Future<void>? cancel) async {
    final s = status[chamadas.clamp(0, status.length - 1)];
    chamadas++;
    return ResponseBody.fromString('{"id":"u","email":"u@x"}', s, headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    });
  }

  @override
  void close({bool force = false}) {}
}

DioException _semRede() => DioException(
  requestOptions: RequestOptions(path: '/auth/refresh'),
  type: DioExceptionType.connectionError,
);

void main() {
  setUp(() => FlutterSecureStorage.setMockInitialValues({
    'fiance_access_token': 'acesso',
    'fiance_refresh_token': 'renovacao',
  }));

  group('renovação da sessão', () {
    test('refresh recusado encerra a sessão e avisa quem escuta', () async {
      final servidor = await _servidor((r) => _status(r, 401));
      final sessao = AuthService(apiBaseUrl: _base(servidor));
      final avisos = <void>[];
      sessao.sessionEnded.listen(avisos.add);

      final renovou = await sessao.refreshSession();
      await Future<void>.delayed(Duration.zero);

      expect(renovou, isFalse);
      expect(await _storage.read(key: 'fiance_refresh_token'), isNull,
          reason: 'refresh recusado pelo servidor não volta a valer; guardá-lo só repete a recusa');
      expect(avisos, hasLength(1),
          reason: 'sem o aviso, ninguém leva a pessoa ao login e cada tela mostra "sessão expirou"');
    });

    test('refresh sem resposta mantém a sessão e devolve a falha de rede', () async {
      final servidor = await _servidor((r) => _status(r, 503));
      final sessao = AuthService(apiBaseUrl: _base(servidor));
      final avisos = <void>[];
      sessao.sessionEnded.listen(avisos.add);

      await expectLater(sessao.refreshSession(), throwsA(isA<DioException>()));
      await Future<void>.delayed(Duration.zero);

      expect(await _storage.read(key: 'fiance_refresh_token'), 'renovacao',
          reason: 'servidor instável não é sessão vencida: apagar o refresh desloga quem está sem sinal');
      expect(avisos, isEmpty);
    });

    test('dois pedidos simultâneos dividem uma renovação só', () async {
      var posts = 0;
      final servidor = await _servidor((r) async {
        posts++;
        await Future<void>.delayed(const Duration(milliseconds: 50));
        r.response.headers.contentType = ContentType.json;
        r.response.write('{"access_token":"novo","refresh_token":"outro"}');
        await r.response.close();
      });
      final sessao = AuthService(apiBaseUrl: _base(servidor));

      final resultados = await Future.wait([sessao.refreshSession(), sessao.refreshSession()]);

      expect(resultados, [true, true]);
      expect(posts, 1,
          reason: 'o refresh é queimado no uso: o segundo POST com o mesmo token derruba a sessão');
    });

    test('sair conclui mesmo com o servidor sem responder', () async {
      final servidor = await _servidor((_) async {});
      final sessao = AuthService(apiBaseUrl: _base(servidor));

      await sessao.signOut().timeout(const Duration(seconds: 15));

      expect(await _storage.read(key: 'fiance_access_token'), isNull,
          reason: 'a sessão local sai sempre; o logout no servidor é cortesia, não condição');
    });
  });

  group('cliente da API', () {
    test('com o refresh recusado, o 401 chega a quem pediu', () async {
      final sessao = _Sessao(renovar: () async => false);
      final cliente = ApiClient(sessao);
      cliente.dio.httpClientAdapter = _Adaptador([401]);

      final falha = await cliente.dio.get<dynamic>('/dashboard').then<Object?>((_) => null,
          onError: (Object e) => e);

      expect((falha as DioException).response?.statusCode, 401);
      expect(sessao.renovacoes, 1);
    });

    test('com o refresh sem rede, a falha que chega é de conexão', () async {
      final sessao = _Sessao(renovar: () async => throw _semRede());
      final cliente = ApiClient(sessao);
      cliente.dio.httpClientAdapter = _Adaptador([401]);

      final falha = await cliente.dio.get<dynamic>('/dashboard').then<Object?>((_) => null,
          onError: (Object e) => e);

      expect((falha as DioException).type, DioExceptionType.connectionError,
          reason: 'sem rede na renovação a tela deve dizer "sem conexão", não "sessão expirou"');
    });

    test('com o refresh aceito, o pedido é refeito', () async {
      final sessao = _Sessao(renovar: () async => true);
      final cliente = ApiClient(sessao);
      final adaptador = _Adaptador([401, 200]);
      cliente.dio.httpClientAdapter = adaptador;

      final resposta = await cliente.dio.get<dynamic>('/dashboard');

      expect(resposta.statusCode, 200);
      expect(adaptador.chamadas, 2);
    });
  });

  group('abertura do app', () {
    ProviderContainer montar(_Sessao sessao, List<int> status) {
      final dio = Dio(BaseOptions(baseUrl: 'http://x'))..httpClientAdapter = _Adaptador(status);
      final container = ProviderContainer(overrides: [
        authServiceProvider.overrideWithValue(sessao),
        apiRepositoryProvider.overrideWithValue(ApiRepository(dio)),
      ]);
      addTearDown(container.dispose);
      return container;
    }

    test('sem rede, a sessão fica', () async {
      final sessao = _Sessao();
      final container = ProviderContainer(overrides: [
        authServiceProvider.overrideWithValue(sessao),
        apiRepositoryProvider.overrideWithValue(
          ApiRepository(Dio()..interceptors.add(InterceptorsWrapper(
            onRequest: (o, h) => h.reject(DioException(
              requestOptions: o,
              type: DioExceptionType.connectionError,
            )),
          ))),
        ),
      ]);
      addTearDown(container.dispose);

      final estado = await container.read(authStatusProvider.future);

      expect(estado, SessionCheck.unverified);
      expect(sessao.limpou, isFalse,
          reason: 'abrir o app no metrô deslogava a pessoa: falha de rede não é sessão vencida');
    });

    test('servidor fora do ar não desloga', () async {
      final sessao = _Sessao();
      final estado = await montar(sessao, [503]).read(authStatusProvider.future);

      expect(estado, SessionCheck.unverified);
      expect(sessao.limpou, isFalse);
    });

    test('401 depois da renovação recusada leva ao login', () async {
      final sessao = _Sessao();
      final estado = await montar(sessao, [401]).read(authStatusProvider.future);

      expect(estado, SessionCheck.signedOut);
      expect(sessao.limpou, isTrue);
    });

    test('sessão válida entra', () async {
      final sessao = _Sessao();
      final container = montar(sessao, [200]);
      final estado = await container.read(authStatusProvider.future);

      expect(estado, SessionCheck.signedIn);
      expect(container.read(currentUserProvider)?.email, 'u@x');
    });
  });
}
