import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/format.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/allocation_gap.dart';
import 'package:fiance/core/widgets/button.dart';
import 'package:fiance/core/widgets/measure.dart';
import 'package:fiance/features/patrimony/ledger_screen.dart';
import 'package:fiance/features/patrimony/patrimony_screen.dart';

class _Servidor extends Interceptor {
  _Servidor(this.respostas);

  final Map<String, Object? Function(RequestOptions pedido)> respostas;
  final pedidos = <String>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final chave = '${options.method} ${options.path}';
    pedidos.add(chave);
    final resposta = respostas[chave];
    if (resposta == null) {
      handler.reject(
        DioException(
          requestOptions: options,
          response: Response<dynamic>(requestOptions: options, statusCode: 404),
          type: DioExceptionType.badResponse,
        ),
      );
      return;
    }
    final corpo = resposta(options);
    if (corpo is int) {
      handler.reject(
        DioException(
          requestOptions: options,
          response: Response<dynamic>(requestOptions: options, statusCode: corpo),
          type: DioExceptionType.badResponse,
        ),
      );
      return;
    }
    handler.resolve(Response<dynamic>(requestOptions: options, statusCode: 200, data: corpo));
  }
}

Future<void> _montar(WidgetTester tester, _Servidor servidor, Widget tela) async {
  tester.view.physicalSize = const Size(390, 3200) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiRepositoryProvider.overrideWithValue(ApiRepository(Dio()..interceptors.add(servidor))),
      ],
      child: MaterialApp(theme: buildAppTheme(Brightness.light), home: tela),
    ),
  );
  await _esperar(tester);
}

Future<void> _esperar(WidgetTester tester) async {
  for (var i = 0; i < 8; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

Map<String, Object?> _posicao(
  String ticker, {
  String categoria = 'acoes_br',
  String? nome,
  double quantidade = 100,
  double valor = 3000,
}) => {
  'ticker': ticker,
  'name': nome,
  'asset_type': categoria == 'renda_fixa' ? 'renda_fixa' : 'br_stock',
  'quantity': quantidade,
  'avg_price': 25.0,
  'current_price': valor / quantidade,
  'invested': 2500.0,
  'current_value': valor,
  'pnl': valor - 2500,
  'pnl_pct': 20.0,
  'verdict': 'HOLD',
  'label': '',
  'category_resolved': categoria,
  'category': categoria,
};

Map<String, Object?> _painel() => {
  'summary': {
    'total_invested': 5000.0,
    'total_current': 13000.0,
    'total_pnl': 8000.0,
    'total_pnl_pct': 160.0,
    'monthly_dividends_estimate': 0.0,
    'positions_count': 2,
  },
  'positions': [
    _posicao('PETR4'),
    _posicao('RF-12', categoria: 'renda_fixa', nome: 'CDB Inter 2027', quantidade: 1, valor: 10000),
  ],
  'allocations': [
    {'category': 'acoes_br', 'current_value': 3000.0, 'current_pct': 23.1},
    {'category': 'renda_fixa', 'current_value': 10000.0, 'current_pct': 76.9},
  ],
  'top_buys': <Object>[],
  'top_sells': <Object>[],
  'alerts': <Object>[],
};

Map<String, Object?> _lancamento(int id, String ativo, String dia) => {
  'id': id,
  'kind': 'buy',
  'symbol': ativo,
  'traded_on': dia,
  'quantity': 200,
  'price': 38.42,
  'fees': 4.9,
};

void main() {
  group('patrimônio', () {
    testWidgets('a aplicação de renda fixa não entra entre os ativos negociados', (tester) async {
      final servidor = _Servidor({'GET /dashboard': (_) => _painel()});
      await _montar(tester, servidor, const PatrimonyScreen());

      expect(find.text('Ativos negociados · 1'), findsOneWidget,
          reason: 'a aplicação já tem a seção dela; contar aqui duplica o patrimônio');
      expect(find.text('RF-12'), findsNothing,
          reason: 'RF-<id> é identificador interno, não ticker que a pessoa reconheça');
      expect(find.text('CDB Inter 2027'), findsOneWidget,
          reason: 'na composição por ativo, a aplicação aparece pelo nome');
      expect(find.text('1.0 un.'), findsNothing);
      expect(find.textContaining('100 un.'), findsOneWidget);
    });

    testWidgets('remover pede confirmação e só some quando o servidor grava', (tester) async {
      var falhar = true;
      final servidor = _Servidor({
        'GET /dashboard': (_) => _painel(),
        'DELETE /portfolio/position/PETR4': (_) => falhar ? 500 : {'items': <Object>[]},
      });
      await _montar(tester, servidor, const PatrimonyScreen());

      await tester.tap(find.widgetWithText(FiButton, 'Remover'));
      await _esperar(tester);
      expect(servidor.pedidos, isNot(contains('DELETE /portfolio/position/PETR4')),
          reason: 'remover é destrutivo: nada sai antes da confirmação');

      await tester.tap(find.widgetWithText(FiButton, 'Remover').last);
      await _esperar(tester);
      expect(servidor.pedidos, contains('DELETE /portfolio/position/PETR4'));
      expect(find.textContaining('O serviço está instável'), findsOneWidget,
          reason: 'a falha da escrita precisa chegar à pessoa, e não sumir num onDismissed');
      expect(find.textContaining('100 un.'), findsOneWidget,
          reason: 'a posição continua na lista quando o servidor recusa');

      falhar = false;
      await tester.tap(find.widgetWithText(FiButton, 'Remover'));
      await _esperar(tester);
      await tester.tap(find.widgetWithText(FiButton, 'Remover').last);
      await _esperar(tester);
      expect(find.text('PETR4 saiu da carteira.'), findsOneWidget);
    });

    testWidgets('vender mais do que tem fica no diálogo, com o motivo', (tester) async {
      final servidor = _Servidor({'GET /dashboard': (_) => _painel()});
      await _montar(tester, servidor, const PatrimonyScreen());

      await tester.tap(find.widgetWithText(FiButton, 'Vender'));
      await _esperar(tester);

      expect(find.text('Quantidade (máx. 100)'), findsOneWidget,
          reason: 'o limite sai do formatador, não do toString do double');
      final quantidade = find.byType(TextFormField).first;
      expect(tester.widget<TextFormField>(quantidade).controller!.text, '100');

      await tester.enterText(quantidade, '150');
      await tester.tap(find.widgetWithText(FiButton, 'Confirmar venda'));
      await _esperar(tester);

      expect(find.text('Você tem 100 un. — não dá para vender mais que isso'), findsOneWidget);
      expect(find.text('Vender PETR4'), findsOneWidget, reason: 'o diálogo continua aberto');
      expect(servidor.pedidos, isNot(contains('POST /portfolio/sell')));
    });

    testWidgets('adicionar um ticker que já existe avisa que substitui', (tester) async {
      final servidor = _Servidor({
        'GET /dashboard': (_) => _painel(),
        'GET /universe/search': (_) => {'items': <Object>[]},
      });
      await _montar(tester, servidor, const PatrimonyScreen());

      await tester.tap(find.widgetWithText(FiButton, 'Adicionar ativo'));
      await _esperar(tester);
      await tester.tap(find.text('Ativo negociado'));
      await _esperar(tester);

      await tester.enterText(find.byType(TextField).first, 'PETR4');
      await _esperar(tester);

      expect(find.textContaining('Você já tem 100 un. de PETR4'), findsOneWidget,
          reason: 'declarar posição substitui a quantidade; quem queria somar precisa saber');
      expect(find.widgetWithText(FiButton, 'Registrar compra no razão'), findsOneWidget);
      expect(find.widgetWithText(FiButton, 'Substituir posição'), findsOneWidget);
    });

    testWidgets('a projeção tem caminho a partir do patrimônio', (tester) async {
      final servidor = _Servidor({'GET /dashboard': (_) => _painel()});
      await _montar(tester, servidor, const PatrimonyScreen());

      expect(find.text('Projeção — aportando assim, onde eu chego?'), findsOneWidget);
    });
  });

  group('livro-razão', () {
    testWidgets('apagar um lançamento carregado depois tira ele da lista', (tester) async {
      var apagado = false;
      final servidor = _Servidor({
        'GET /transactions': (pedido) => pedido.queryParameters['cursor'] == null
            ? {
                'items': [_lancamento(2, 'PETR4', '2026-09-12')],
                'count': 2,
                'has_more': true,
                'next_cursor': 'c1',
              }
            : {
                'items': [if (!apagado) _lancamento(1, 'VALE3', '2025-03-04')],
                'count': 2,
                'has_more': false,
              },
        'DELETE /transactions/1': (_) {
          apagado = true;
          return null;
        },
      });
      await _montar(tester, servidor, const LedgerScreen());

      expect(find.text('PETR4 · Compra'), findsOneWidget);
      expect(find.text('200 × ${formatCurrency(38.42)}'), findsOneWidget,
          reason: 'a linha compacta diz quanto e a que preço numa linha só');

      await tester.tap(find.widgetWithText(FiButton, 'Carregar os anteriores'));
      await _esperar(tester);
      expect(find.text('VALE3 · Compra'), findsOneWidget);

      await tester.tap(find.text('VALE3 · Compra'));
      await _esperar(tester);
      await tester.tap(find.widgetWithText(FiButton, 'Apagar lançamento'));
      await _esperar(tester);
      await tester.tap(find.widgetWithText(FiButton, 'Apagar'));
      await _esperar(tester);

      expect(servidor.pedidos, contains('DELETE /transactions/1'));
      expect(find.text('VALE3 · Compra'), findsNothing,
          reason: 'o lançamento apagado não pode continuar na página carregada à parte');
    });
  });

  testWidgets('a distância da meta sai em português', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(Brightness.light),
        home: const Scaffold(
          body: FiAllocationGap(label: 'FIIs', currentPct: 33, targetPct: 24.3),
        ),
      ),
    );

    final medida = tester.widget<FiMeasure>(find.byType(FiMeasure));
    expect(medida.readout, '33,0%');
    expect(medida.note, contains('8,7 p.p. acima'));
    expect(medida.semantics, isNot(contains('33.0')),
        reason: 'o leitor de tela lê o mesmo número que a tela mostra');

    final rotulo = tester.getRect(find.text('FIIs'));
    final leitura = tester.getRect(find.text('33,0%'));
    final linha = tester.getRect(find.byType(FiMeasure));
    expect(leitura.right, closeTo(linha.right, 1),
        reason: 'o percentual encosta na margem direita, alinhado com o rótulo');
    expect(leitura.left, greaterThan(rotulo.right));
  });
}
