import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'api_repository.dart';

const _androidChannel = AndroidNotificationChannel(
  'fiance_default',
  'fiance',
  description: 'Alertas de preço e novas oportunidades',
  importance: Importance.high,
);

Future<String?> _firebaseToken() => FirebaseMessaging.instance.getToken();

class NotificationsService {
  NotificationsService(this._repo, {Future<String?> Function()? readToken})
    : _readToken = readToken ?? _firebaseToken;

  final ApiRepository _repo;
  final Future<String?> Function() _readToken;
  final _localNotifications = FlutterLocalNotificationsPlugin();
  bool _initialized = false;
  bool _signedOut = false;

  AuthorizationStatus? permissionStatus;
  bool tokenRegistered = false;
  String? lastError;

  Future<void> init() async {
    _signedOut = false;
    if (_initialized) return _registerToken();
    _initialized = true;

    await _localNotifications.initialize(
      const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      ),
    );
    await _localNotifications
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >()
        ?.createNotificationChannel(_androidChannel);

    final messaging = FirebaseMessaging.instance;
    final settings = await messaging.requestPermission();
    permissionStatus = settings.authorizationStatus;

    FirebaseMessaging.onMessage.listen(_showForegroundNotification);

    await _registerToken();
    messaging.onTokenRefresh.listen((_) {
      if (!_signedOut) _registerToken();
    });
  }

  Future<void> unregisterToken() async {
    _signedOut = true;
    try {
      final token = await _readToken();
      if (token == null) return;
      await _repo.unregisterDeviceToken(token);
      tokenRegistered = false;
    } catch (e) {
      lastError = e.toString();
      if (kDebugMode) {
        debugPrint('Falha ao desregistrar token de push: $e');
      }
    }
  }

  Future<void> _registerToken() async {
    try {
      final token = await _readToken();
      if (token == null) return;
      await _repo.registerDeviceToken(token: token, platform: 'android');
      tokenRegistered = true;
      lastError = null;
    } catch (e) {
      tokenRegistered = false;
      lastError = e.toString();
      debugPrint('Falha ao registrar token de notificação: $e');
    }
  }

  void _showForegroundNotification(RemoteMessage message) {
    final notification = message.notification;
    if (notification == null) return;

    _localNotifications.show(
      notification.hashCode,
      notification.title,
      notification.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _androidChannel.id,
          _androidChannel.name,
          channelDescription: _androidChannel.description,
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
    );
  }
}
