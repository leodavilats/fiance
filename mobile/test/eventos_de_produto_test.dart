import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/product_events.dart';

class _Captura extends Interceptor {
  final corpos = <Object?>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    corpos.add(options.data);
    handler.resolve(Response<dynamic>(requestOptions: options, statusCode: 200, data: {'accepted': 1}));
  }
}

class _Falha extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    handler.reject(DioException(requestOptions: options, type: DioExceptionType.connectionError));
  }
}

void main() {
  test('o evento vai com nome, plataforma e momento, e sem dado de carteira', () async {
    final captura = _Captura();
    final eventos = ProductEvents(ApiRepository(Dio()..interceptors.add(captura)));

    await eventos.track('feed_item_opened', props: {'source': 'analyze'});

    final corpo = captura.corpos.single as Map;
    final evento = (corpo['events'] as List).single as Map;
    expect(evento['name'], 'feed_item_opened');
    expect(evento['props'], {'source': 'analyze'});
    expect(evento['platform'], isNotEmpty);
    expect(evento['occurred_at'], isA<double>());
  });

  test('a falha de rede na telemetria nunca chega à tela', () async {
    final eventos = ProductEvents(ApiRepository(Dio()..interceptors.add(_Falha())));

    await expectLater(eventos.track('session_started'), completes);
  });
}
