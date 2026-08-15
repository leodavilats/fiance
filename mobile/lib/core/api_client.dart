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
      ),
    );
  }

  final AuthService _authService;
  late final Dio dio;
}
