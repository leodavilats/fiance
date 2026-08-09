import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';

class AppUser {
  AppUser({required this.id, required this.email, required this.name, required this.picture});

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

/// Autenticação via Google Sign-In + troca do id_token por um JWT de sessão
/// próprio, emitido pelo backend (POST /api/auth/google).
class AuthService {
  AuthService({String apiBaseUrl = 'http://localhost:8000/api'})
      : _dio = Dio(BaseOptions(baseUrl: apiBaseUrl)),
        _googleSignIn = GoogleSignIn(
          scopes: ['email', 'profile'],
          // Client ID do tipo Web do mesmo projeto GCP — necessário para o
          // plugin devolver um idToken no Android (o client ID Android por
          // si só não gera idToken). O backend valida o aud contra este ID.
          serverClientId:
              '226171385204-fgrdfsrqimsfc95dotuet2ru4e7eunhc.apps.googleusercontent.com',
        );

  final Dio _dio;
  final GoogleSignIn _googleSignIn;
  final _storage = const FlutterSecureStorage();

  static const _tokenKey = 'fianceai_access_token';

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<bool> isLoggedIn() async => (await readToken()) != null;

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

    final response = await _dio.post('/auth/google', data: {'id_token': idToken});
    final accessToken = response.data['access_token'] as String;
    await _storage.write(key: _tokenKey, value: accessToken);

    return AppUser.fromJson(response.data['user'] as Map<String, dynamic>);
  }

  Future<void> signOut() async {
    await _googleSignIn.signOut();
    await _storage.delete(key: _tokenKey);
  }
}
