
import 'package:flutter_test/flutter_test.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import 'package:fiance/core/telemetry.dart';

void main() {
  group('o caminho não entrega o papel', () {
    test('ticker vira marcador', () {
      expect(limparCaminho('/ativo/PETR4'), '/ativo/{id}');
      expect(limparCaminho('/ativo/HGLG11/historico'), '/ativo/{id}/historico');
    });

    test('id numérico e identificador longo também', () {
      expect(limparCaminho('/renda-fixa/4821'), '/renda-fixa/{id}');
      expect(
        limparCaminho('/api/transactions/0f9c1a2b3d4e5f60'),
        '/api/transactions/{id}',
      );
    });

    test('a rota continua reconhecível', () {
      expect(limparCaminho('/carteira/encerradas'), '/carteira/encerradas');
    });

    test('mantém o host e descarta query e âncora', () {
      expect(
        limparCaminho('https://fiance.app/ativo/VALE3?destaque=1#topo'),
        'https://fiance.app/ativo/{id}',
      );
    });
  });

  group('o texto não entrega o valor', () {
    test('redige valor em reais', () {
      expect(limparTexto(r'lucro de R$ 38.400,00'), isNot(contains('38.400')));
    });

    test('redige número citado em erro de validação', () {
      final limpo = limparTexto(
        'Quantidade de venda (300) maior que a carteira (100).',
      );

      expect(limpo, isNot(contains('300')));
      expect(limpo, contains('Quantidade de venda'));
    });

    test('redige segredo em URL', () {
      expect(
        limparTexto('GET /api/quote?token=segredo123'),
        isNot(contains('segredo123')),
      );
    });
  });

  group('quando a telemetria reporta', () {
    test('o DSN embutido aponta para o projeto do mobile', () {
      expect(sentryDsn, contains('ingest.us.sentry.io'));
      expect(sentryDsn.endsWith('/4512039720714240'), isTrue);
    });

    test('em teste, que roda em debug, o app sobe sem telemetria', () async {
      var rodou = false;
      final ligou = await rodarComTelemetria(() async {
        rodou = true;
      });

      expect(ligou, isFalse, reason: 'build de debug nao reporta');
      expect(rodou, isTrue, reason: 'o app roda de qualquer jeito');
    });
  });

  group('o evento inteiro', () {
    SentryEvent construir() => SentryEvent(
      user: SentryUser(id: 'u_123', email: 'alguem@exemplo.com'),
      request: SentryRequest(
        method: 'POST',
        url: 'https://fiance.app/carteira/PETR4',
      ),
      breadcrumbs: [
        Breadcrumb(
          message: 'GET /api/asset/PETR4',
          data: const {'avg_price': 38.4},
        ),
      ],
    );

    test('do usuário sai o identificador e mais nada', () {
      final limpo = limparEvento(construir(), Hint())!;

      expect(limpo.user?.id, 'u_123');
      expect(limpo.user?.email, isNull);
    });

    test('o ticker some da URL do request', () {
      final limpo = limparEvento(construir(), Hint())!;

      expect(limpo.request?.url, 'https://fiance.app/carteira/{id}');
    });

    test('o dado do breadcrumb não sai', () {
      final limpo = limparEvento(construir(), Hint())!;

      expect(limpo.breadcrumbs?.first.data, anyOf(isNull, isEmpty));
    });

    test('a mensagem do evento é redigida como a do breadcrumb', () {
      final evento = SentryEvent(
        message: SentryMessage(
          r'Falha ao lançar venda de R$ 38.400,00',
          template: r'Falha ao lançar venda de R$ %s',
          params: [38400],
        ),
      );

      final limpo = limparEvento(evento, Hint())!;

      expect(
        limpo.message?.formatted,
        isNot(contains('38.400')),
        reason: 'valor em reais na mensagem sai do produto se ninguém redigir',
      );
      expect(
        limpo.message?.params,
        anyOf(isNull, isEmpty),
        reason: 'o parâmetro é o valor cru, e nenhuma redação alcança ele',
      );
    });

    test('o valor da exceção é redigido', () {
      final evento = SentryEvent(
        exceptions: [
          SentryException(
            type: 'StateError',
            value: 'Quantidade de venda (300) maior que a carteira (100).',
          ),
        ],
      );

      final limpo = limparEvento(evento, Hint())!;

      expect(
        limpo.exceptions?.first.value,
        isNot(contains('300')),
        reason: 'número citado em erro é dado de carteira',
      );
      expect(limpo.exceptions?.first.value, contains('Quantidade de venda'));
    });
  });

  group('o ambiente', () {
    test('em teste, que roda em debug, não se diz produção', () {
      expect(
        ambiente,
        'development',
        reason: 'evento de desenvolvimento misturado ao de produção cega o painel',
      );
    });
  });
}
