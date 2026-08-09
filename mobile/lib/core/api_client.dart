import 'package:dio/dio.dart';

import 'auth_service.dart';

/// URL base da API FastAPI.
///
/// Aponta por padrão para o backend em produção (Railway). Para testar
/// contra um backend local, rode com:
///   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api   (emulador Android)
///   flutter run --dart-define=API_BASE_URL=http://localhost:8000/api  (iOS simulator / web)
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://fianceai-production.up.railway.app/api',
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
      ),
    );
  }

  final AuthService _authService;
  late final Dio dio;
}
