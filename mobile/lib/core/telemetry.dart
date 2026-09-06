import 'package:flutter/foundation.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

const String _dsnPadrao =
    'https://824f6af34d9c061803a4fe16e9efa86a@o4512039699021824.ingest.us.sentry.io/4512039720714240';

const bool _dsnVeioDoBuild = bool.hasEnvironment('SENTRY_DSN');

const String sentryDsn = String.fromEnvironment(
  'SENTRY_DSN',
  defaultValue: _dsnPadrao,
);

const String ambiente = String.fromEnvironment(
  'APP_ENV',
  defaultValue: 'development',
);

final RegExp _segmentoIdentificador = RegExp(
  r'^(?:[A-Z][A-Z0-9]{3}\d{1,2}|\d+|[0-9a-fA-F-]{16,})$',
);

final RegExp _sigiloNaUrl = RegExp(
  r'\b(token|api_key|apikey|access_token|refresh_token|secret|password|senha)=([^&\s"' r"'" r'>]+)',
  caseSensitive: false,
);

final RegExp _dinheiro = RegExp(r'R\$\s?-?[\d.,]+');

final RegExp _numeroEntreParenteses = RegExp(r'\((-?\d[\d.,]*)\)');

String limparCaminho(String url) {
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
      .map((parte) => _segmentoIdentificador.hasMatch(parte) ? '{id}' : parte)
      .join('/');

  return prefixo + limpo;
}

String limparTexto(String texto) {
  return texto
      .replaceAllMapped(_sigiloNaUrl, (m) => '${m[1]}=[redigido]')
      .replaceAll(_dinheiro, r'R$ [redigido]')
      .replaceAll(_numeroEntreParenteses, '([redigido])');
}

SentryEvent? limparEvento(SentryEvent evento, Hint hint) {
  final request = evento.request;

  return evento.copyWith(
    user: evento.user == null ? null : SentryUser(id: evento.user!.id),
    request: request == null
        ? null
        : SentryRequest(
            method: request.method,
            url: request.url == null ? null : limparCaminho(request.url!),
          ),
    // ignore: deprecated_member_use
    extra: const <String, dynamic>{},
    breadcrumbs: evento.breadcrumbs
        ?.map(
          (b) => Breadcrumb(
            message: b.message == null ? null : limparTexto(b.message!),
            category: b.category,
            level: b.level,
            type: b.type,
            timestamp: b.timestamp,
          ),
        )
        .toList(),
  );
}

Future<bool> rodarComTelemetria(Future<void> Function() app) async {
  final reporta = (kReleaseMode || _dsnVeioDoBuild) && sentryDsn.trim().isNotEmpty;
  if (!reporta) {
    await app();
    return false;
  }

  try {
    await SentryFlutter.init((options) {
      options.dsn = sentryDsn;
      options.environment = ambiente;
      options.sendDefaultPii = false;
      options.beforeSend = limparEvento;
    }, appRunner: app);
    return true;
  } catch (erro) {
    debugPrint('Telemetria não pôde ser ligada; o app segue sem ela: $erro');
    await app();
    return false;
  }
}
