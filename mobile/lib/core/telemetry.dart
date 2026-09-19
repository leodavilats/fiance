import 'package:flutter/foundation.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

const String _defaultDsn =
    'https://824f6af34d9c061803a4fe16e9efa86a@o4512039699021824.ingest.us.sentry.io/4512039720714240';

const bool _dsnFromBuild = bool.hasEnvironment('SENTRY_DSN');

const String sentryDsn = String.fromEnvironment(
  'SENTRY_DSN',
  defaultValue: _defaultDsn,
);

const String _declaredEnvironment = String.fromEnvironment('APP_ENV');

final String environment = _declaredEnvironment.isNotEmpty
    ? _declaredEnvironment
    : (kReleaseMode ? 'production' : 'development');

final RegExp _identifierSegment = RegExp(
  r'^(?:[A-Z][A-Z0-9]{3}\d{1,2}|\d+|[0-9a-fA-F-]{16,})$',
);

final RegExp _secretInUrl = RegExp(
  r'\b(token|api_key|apikey|access_token|refresh_token|secret|password|senha)=([^&\s"' r"'" r'>]+)',
  caseSensitive: false,
);

final RegExp _moneyPattern = RegExp(r'R\$\s?-?[\d.,]+');

final RegExp _numberInParentheses = RegExp(r'\((-?\d[\d.,]*)\)');

String redactPath(String url) {
  var prefixo = '';
  var caminho = url;

  final separador = url.indexOf('://');
  if (separador >= 0) {
    final resto = url.substring(separador + 3);
    final barra = resto.indexOf('/');
    if (barra < 0) return url;
    prefixo = url.substring(0, separador + 3) + resto.substring(0, barra);
    caminho = resto.substring(barra);
  }

  final semQuery = caminho.split('?').first.split('#').first;
  final limpo = semQuery
      .split('/')
      .map((parte) => _identifierSegment.hasMatch(parte) ? '{id}' : parte)
      .join('/');

  return prefixo + limpo;
}

String redactText(String texto) {
  return texto
      .replaceAllMapped(_secretInUrl, (m) => '${m[1]}=[redigido]')
      .replaceAll(_moneyPattern, r'R$ [redigido]')
      .replaceAll(_numberInParentheses, '([redigido])');
}

SentryEvent? redactEvent(SentryEvent evento, Hint hint) {
  final user = evento.user;
  final request = evento.request;

  evento.user = user == null ? null : SentryUser(id: user.id);
  evento.request = request == null
      ? null
      : SentryRequest(
          method: request.method,
          url: request.url == null ? null : redactPath(request.url!),
        );
  // ignore: deprecated_member_use
  evento.extra = <String, dynamic>{};

  final mensagem = evento.message;
  if (mensagem != null) {
    evento.message = SentryMessage(
      redactText(mensagem.formatted),
      template: mensagem.template == null ? null : redactText(mensagem.template!),
    );
  }

  for (final excecao in evento.exceptions ?? const <SentryException>[]) {
    final valor = excecao.value;
    if (valor != null) excecao.value = redactText(valor);
  }

  evento.breadcrumbs = evento.breadcrumbs
      ?.map(
        (b) => Breadcrumb(
          message: b.message == null ? null : redactText(b.message!),
          category: b.category,
          level: b.level,
          type: b.type,
          timestamp: b.timestamp,
        ),
      )
      .toList();

  return evento;
}

Future<bool> runWithTelemetry(Future<void> Function() app) async {
  final reporta = (kReleaseMode || _dsnFromBuild) && sentryDsn.trim().isNotEmpty;
  if (!reporta) {
    await app();
    return false;
  }

  try {
    await SentryFlutter.init((options) {
      options.dsn = sentryDsn;
      options.environment = environment;
      options.sendDefaultPii = false;
      options.beforeSend = redactEvent;
    }, appRunner: app);
    return true;
  } catch (erro) {
    debugPrint('Telemetria não pôde ser ligada; o app segue sem ela: $erro');
    await app();
    return false;
  }
}
