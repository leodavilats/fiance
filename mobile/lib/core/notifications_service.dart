import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'api_repository.dart';

const _androidChannel = AndroidNotificationChannel(
  'fianceai_default',
  'fianceAI',
  description: 'Alertas de preço e novas oportunidades',
  importance: Importance.high,
);

/// Inicializa push notifications (Firebase Cloud Messaging) e registra o
/// token do aparelho no backend. Chamado após o login, quando já existe um
/// usuário autenticado para associar o token.
class NotificationsService {
  NotificationsService(this._repo);

  final ApiRepository _repo;
  final _localNotifications = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;
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
    await messaging.requestPermission();

    FirebaseMessaging.onMessage.listen(_showForegroundNotification);

    await _registerToken();
    messaging.onTokenRefresh.listen((_) => _registerToken());
  }

  Future<void> _registerToken() async {
    try {
      final token = await FirebaseMessaging.instance.getToken();
      if (token == null) return;
      await _repo.registerDeviceToken(token: token, platform: 'android');
    } catch (e) {
      // Push é um extra, não deve derrubar o app se falhar (ex.: sem
      // Google Play Services no emulador, ou backend fora do ar).
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
