import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/format.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/chip.dart';
import 'package:fiance/features/month/inbox_screen.dart';

class _Servidor extends Interceptor {
  _Servidor(this.itens);

  final List<Map<String, Object?>> itens;
  final pedidos = <RequestOptions>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    pedidos.add(options);
    final Object resposta;
    if (options.path == '/inbox/read') {
      resposta = {'unread': 0};
    } else if (options.path == '/inbox/unread') {
      resposta = {'unread': itens.where((i) => i['read_at'] == null).length};
    } else {
      final tipos = options.queryParameters['kind'] as List?;
      final filtrados = tipos == null
          ? itens
          : itens.where((i) => tipos.contains(i['kind'])).toList();
      resposta = {
        'items': filtrados,
        'unread': filtrados.where((i) => i['read_at'] == null).length,
        'next_cursor': null,
        'has_more': false,
      };
    }
    handler.resolve(Response<dynamic>(requestOptions: options, statusCode: 200, data: resposta));
  }
}

double _haHoras(double horas) => DateTime.now().millisecondsSinceEpoch / 1000 - horas * 3600;

double _horasDesdeMeiaNoite() {
  final agora = DateTime.now();
  return agora.difference(DateTime(agora.year, agora.month, agora.day)).inSeconds / 3600;
}

Map<String, Object?> _aviso(int id, String kind, String titulo, double horas, {bool lido = false}) => {
  'id': id,
  'kind': kind,
  'severity': 'warning',
  'title': titulo,
  'detail': 'Detalhe de $titulo.',
  'ticker': kind == 'price_alert' ? 'PETR4' : null,
  'action': kind == 'price_alert' ? 'analyze' : 'fixed_income',
  'action_label': kind == 'price_alert' ? 'Ver PETR4' : 'Ver renda fixa',
  'created_at': _haHoras(horas),
  'read_at': lido ? _haHoras(horas - 1) : null,
};

Future<void> _montar(WidgetTester tester, _Servidor servidor) async {
  tester.view.physicalSize = const Size(390, 1600) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiRepositoryProvider.overrideWithValue(ApiRepository(Dio()..interceptors.add(servidor))),
      ],
      child: MaterialApp.router(
        theme: buildAppTheme(Brightness.light),
        routerConfig: GoRouter(
          routes: [
            GoRoute(path: '/', builder: (_, _) => const InboxScreen()),
            GoRoute(
              path: '/ativo/:ticker',
              builder: (_, s) => Scaffold(body: Text('Folha de ${s.pathParameters['ticker']}')),
            ),
            GoRoute(
              path: '/voce/avisos',
              builder: (_, _) => const Scaffold(body: Text('Preferências')),
            ),
          ],
        ),
      ),
    ),
  );
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

void main() {
  testWidgets('os avisos saem agrupados pela chegada, com o novo marcado', (tester) async {
    await _montar(
      tester,
      _Servidor([
        _aviso(3, 'price_alert', 'PETR4 está abaixo de R\$ 30,00', _horasDesdeMeiaNoite() / 2),
        _aviso(2, 'maturity', 'LCI vence em 20 dias', _horasDesdeMeiaNoite() + 12),
        _aviso(1, 'maturity', 'CDB vence em 5 dias', 24 * 10, lido: true),
      ]),
    );

    final hoje = tester.getTopLeft(find.text('Hoje · 1')).dy;
    final ontem = tester.getTopLeft(find.text('Ontem · 1')).dy;
    final antes = tester.getTopLeft(find.text('Antes · 1')).dy;
    expect(hoje < ontem && ontem < antes, isTrue, reason: 'do mais recente para o mais antigo');
    expect(find.textContaining('Novo · hoje'), findsOneWidget);
    expect(find.textContaining('Novo ·'), findsNWidgets(2), reason: 'o lido não é novo');
    expect(find.byTooltip('Marcar todos como lidos'), findsOneWidget);
  });

  testWidgets('abrir um aviso marca só ele como lido e leva à ação', (tester) async {
    final servidor = _Servidor([_aviso(3, 'price_alert', 'PETR4 está abaixo de R\$ 30,00', 1)]);
    await _montar(tester, servidor);

    await tester.tap(find.text('PETR4 está abaixo de R\$ 30,00'));
    for (var i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 120));
    }

    final leitura = servidor.pedidos.firstWhere((p) => p.path == '/inbox/read');
    expect(leitura.data, {'ids': [3]});
    expect(find.text('Folha de PETR4'), findsOneWidget);
  });

  testWidgets('marcar todos manda a leitura sem lista', (tester) async {
    final servidor = _Servidor([
      _aviso(3, 'price_alert', 'PETR4 está abaixo de R\$ 30,00', 1),
      _aviso(2, 'maturity', 'LCI vence em 20 dias', 2),
    ]);
    await _montar(tester, servidor);

    await tester.tap(find.byTooltip('Marcar todos como lidos'));
    for (var i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 120));
    }

    final leitura = servidor.pedidos.firstWhere((p) => p.path == '/inbox/read');
    expect(leitura.data, <String, Object?>{}, reason: 'sem ids, o servidor marca todos');
  });

  testWidgets('o filtro pede só o tipo escolhido', (tester) async {
    final servidor = _Servidor([
      _aviso(3, 'price_alert', 'PETR4 está abaixo de R\$ 30,00', 1),
      _aviso(2, 'maturity', 'LCI vence em 20 dias', 2),
    ]);
    await _montar(tester, servidor);

    await tester.tap(find.widgetWithText(FiChoiceChip, 'Preços'));
    for (var i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 120));
    }

    expect(servidor.pedidos.last.queryParameters['kind'], ['price_alert']);
    expect(find.text('LCI vence em 20 dias'), findsNothing);
    expect(find.text('PETR4 está abaixo de R\$ 30,00'), findsOneWidget);
  });

  testWidgets('caixa vazia explica o que chega aqui', (tester) async {
    await _montar(tester, _Servidor([]));

    expect(find.text('Nenhum aviso por aqui'), findsOneWidget);
    expect(find.byTooltip('Marcar todos como lidos'), findsNothing);
  });

  test('a hora de chegada fala como gente', () {
    final agora = DateTime(2026, 10, 18, 15);
    expect(formatWhen(DateTime(2026, 10, 18, 9, 5), agora: agora), 'hoje, 09:05');
    expect(formatWhen(DateTime(2026, 10, 17, 22, 0), agora: agora), 'ontem, 22:00');
    expect(formatWhen(DateTime(2026, 9, 2, 8), agora: agora), '02/09');
    expect(formatWhen(DateTime(2025, 12, 30), agora: agora), '30/12/2025');
  });
}
