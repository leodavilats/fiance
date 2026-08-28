import 'package:dio/dio.dart';

import 'auth_service.dart';

const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://fiance.up.railway.app/api',
);

class ApiClient {
  ApiClient(this._authService) {
    dio = Dio(BaseOptions(baseUrl: apiBaseUrl));
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _authService.readToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          // O acesso vale uma hora. Um 401 aqui quase sempre é token vencido,
          // não sessão encerrada — renovar uma vez e repetir evita mandar o
          // usuário para o login no meio de uma navegação.
          if (error.response?.statusCode != 401 || _isAuthRoute(error)) {
            return handler.next(error);
          }

          final renewed = await _authService.refreshSession();
          if (!renewed) {
            return handler.next(error);
          }

          final token = await _authService.readToken();
          if (token == null) {
            return handler.next(error);
          }

          try {
            final request = error.requestOptions;
            request.headers['Authorization'] = 'Bearer $token';
            handler.resolve(await dio.fetch<dynamic>(request));
          } on DioException catch (retryError) {
            handler.next(retryError);
          }
        },
      ),
    );
  }

  static bool _isAuthRoute(DioException error) {
    final path = error.requestOptions.path;
    return path.contains('/auth/refresh') || path.contains('/auth/google');
  }

  final AuthService _authService;
  late final Dio dio;
}
