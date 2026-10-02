import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
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

class SignInCancelled implements Exception {
  const SignInCancelled();
}

class AuthService {
  AuthService({String apiBaseUrl = 'http://localhost:8000/api/v1'})
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

  final _sessionEnded = StreamController<void>.broadcast();

  Stream<void> get sessionEnded => _sessionEnded.stream;

  static const _logoutTimeout = Duration(seconds: 5);

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  Future<bool> isLoggedIn() async =>
      (await readRefreshToken()) != null || (await readToken()) != null;

  Future<AppUser> signInWithGoogle() async {
    final GoogleSignInAccount? account;
    try {
      account = await _googleSignIn.signIn();
    } on PlatformException catch (e) {
      if (e.code == GoogleSignIn.kSignInCanceledError) throw const SignInCancelled();
      rethrow;
    }
    if (account == null) {
      throw const SignInCancelled();
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
    if (refresh == null) {
      await _endSession();
      return false;
    }

    try {
      final response = await _dio.post(
        '/auth/refresh',
        data: {'refresh_token': refresh},
      );
      await _storeTokens(response.data as Map<String, dynamic>);
      return true;
    } on DioException catch (e) {
      if (!_refreshRejected(e)) rethrow;
      await _endSession();
      return false;
    }
  }

  static bool _refreshRejected(DioException e) =>
      const {400, 401, 403, 422}.contains(e.response?.statusCode);

  Future<void> _endSession() async {
    await clearSession();
    _sessionEnded.add(null);
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

  Future<void> signOut({bool allDevices = false}) async {
    try {
      final token = await readToken();
      if (token != null) {
        await _dio
            .post(
              '/auth/logout',
              data: {
                'refresh_token': await readRefreshToken(),
                'all_devices': allDevices,
              },
              options: Options(headers: {'Authorization': 'Bearer $token'}),
            )
            .timeout(_logoutTimeout);
      }
    } catch (_) {}

    try {
      await _googleSignIn.signOut().timeout(_logoutTimeout);
    } catch (_) {}
    await clearSession();
  }

  Future<void> clearSession() async {
    _refreshInFlight = null;
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _refreshKey);
  }
}
