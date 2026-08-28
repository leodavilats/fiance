import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';

class AppUser {
  AppUser({
    required this.id,
    required this.email,
    required this.name,
    required this.picture,
  });

  final String id;
  final String email;
  final String name;
  final String picture;

  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
    id: json['id'] as String,
    email: json['email'] as String,
    name: json['name'] as String? ?? '',
    picture: json['picture'] as String? ?? '',
  );
}

class AuthService {
  AuthService({String apiBaseUrl = 'http://localhost:8000/api'})
    : _dio = Dio(BaseOptions(baseUrl: apiBaseUrl)),
      _googleSignIn = GoogleSignIn(
        scopes: ['email', 'profile'],
        serverClientId:
            '113865070204-6lkq31ahsk3ihgshrecggp6l1kiu93tc.apps.googleusercontent.com',
      );

  final Dio _dio;
  final GoogleSignIn _googleSignIn;
  final _storage = const FlutterSecureStorage();

  static const _tokenKey = 'fiance_access_token';
  static const _refreshKey = 'fiance_refresh_token';

  Future<bool>? _refreshInFlight;

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  /// Sessão viva é ter refresh: o acesso expira em uma hora e vencer não é
  /// estar deslogado — é ter que renovar.
  Future<bool> isLoggedIn() async =>
      (await readRefreshToken()) != null || (await readToken()) != null;

  Future<AppUser> signInWithGoogle() async {
    final account = await _googleSignIn.signIn();
    if (account == null) {
      throw Exception('Login cancelado');
    }

    final googleAuth = await account.authentication;
    final idToken = googleAuth.idToken;
    if (idToken == null) {
      throw Exception('Não foi possível obter o token do Google');
    }

    final response = await _dio.post(
      '/auth/google',
      data: {'id_token': idToken},
    );
    await _storeTokens(response.data as Map<String, dynamic>);

    return AppUser.fromJson(response.data['user'] as Map<String, dynamic>);
  }

  /// Troca o refresh por um par novo.
  ///
  /// O servidor rotaciona e queima o refresh usado, então a chamada é
  /// compartilhada: duas requisições que levam 401 ao mesmo tempo não podem
  /// disparar dois refreshes — o segundo apresentaria um token já queimado e
  /// derrubaria a sessão inteira.
  Future<bool> refreshSession() {
    final pending = _refreshInFlight;
    if (pending != null) return pending;

    final future = _doRefresh().whenComplete(() {
      _refreshInFlight = null;
    });
    _refreshInFlight = future;
    return future;
  }

  Future<bool> _doRefresh() async {
    final refresh = await readRefreshToken();
    if (refresh == null) return false;

    try {
      final response = await _dio.post(
        '/auth/refresh',
        data: {'refresh_token': refresh},
      );
      await _storeTokens(response.data as Map<String, dynamic>);
      return true;
    } on DioException {
      return false;
    }
  }

  Future<void> _storeTokens(Map<String, dynamic> data) async {
    await _storage.write(
      key: _tokenKey,
      value: data['access_token'] as String,
    );
    final refresh = data['refresh_token'] as String?;
    if (refresh != null) {
      await _storage.write(key: _refreshKey, value: refresh);
    }
  }

  /// Encerra no servidor antes de limpar o dispositivo: sem isso o token
  /// seguiria válido até expirar, e sair seria só apagar a chave local.
  Future<void> signOut({bool allDevices = false}) async {
    final token = await readToken();
    if (token != null) {
      try {
        await _dio.post(
          '/auth/logout',
          data: {
            'refresh_token': await readRefreshToken(),
            'all_devices': allDevices,
          },
          options: Options(headers: {'Authorization': 'Bearer $token'}),
        );
      } on DioException {
        // Servidor indisponível não pode impedir a saída local.
      }
    }

    await _googleSignIn.signOut();
    await clearSession();
  }

  Future<void> clearSession() async {
    _refreshInFlight = null;
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _refreshKey);
  }
}
