import 'dart:io';
import 'dart:ui' as ui;

import 'package:dio/dio.dart';
import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/features/assets/fixed_income_screen.dart';
import 'package:fiance/features/auth/login_screen.dart';
import 'package:fiance/features/config/config_screen.dart';
import 'package:fiance/features/config/objetivos_screen.dart';
import 'package:fiance/features/mes/atividade_screen.dart';
import 'package:fiance/features/mes/dividas_screen.dart';
import 'package:fiance/features/mes/mes_screen.dart';
import 'package:fiance/features/patrimonio/patrimonio_screen.dart';
import 'package:fiance/features/patrimonio/proventos_screen.dart';
import 'package:fiance/features/patrimonio/razao_screen.dart';
import 'package:fiance/features/sobra/desvio_screen.dart';
import 'package:fiance/features/sobra/sobra_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:google_fonts/google_fonts.dart';

const _tela = Size(390, 1400);

final _saida = Directory('build/catalogo/telas');
final _fontes = Directory('build/fontes');

enum Estado { conteudo, carregando, falha, vazio }

void _ignorarFonteAusente() {
  final anterior = FlutterError.onError;
  FlutterError.onError = (detalhes) {
    final texto = detalhes.exception.toString();
    if (texto.contains('allowRuntimeFetching is false')) return;
    anterior?.call(detalhes);
  };
}

Future<void> _carregarIcones() async {
  final arquivo = File('${_fontes.path}/MaterialIcons-Regular.otf');
  if (!arquivo.existsSync()) return;

  final carga = FontLoader('MaterialIcons')
    ..addFont(Future.value(arquivo.readAsBytesSync().buffer.asByteData()));
  await carga.load();
}

Future<void> _carregarFontes() async {
  GoogleFonts.config.allowRuntimeFetching = false;
  _ignorarFonteAusente();
  await _carregarIcones();

  if (!_fontes.existsSync()) {
    fail(
      'Sem as fontes em ${_fontes.path}. Rode `python tool/capturar_telas.py`, que as baixa antes '
      'de chamar este teste — sem elas o Flutter desenha caixas no lugar do texto, e a imagem '
      'engana quem for avaliá-la.',
    );
  }

  const arquivos = {
    'IBMPlexSans': 'IBMPlexSans-Regular.ttf',
    'SourceSerif4': 'SourceSerif4-Regular.ttf',
  };

  for (final fonte in arquivos.entries) {
    final arquivo = File('${_fontes.path}/${fonte.value}');
    if (!arquivo.existsSync()) fail('fonte ausente: ${arquivo.path}');

    final bytes = arquivo.readAsBytesSync().buffer.asByteData();

    for (final variante in const [
      'regular',
      'italic',
      '100',
      '200',
      '300',
      '500',
      '600',
      '700',
      '800',
      '900',
    ]) {
      final carga = FontLoader('${fonte.key}_$variante')
        ..addFont(Future.value(bytes));
      await carga.load();
    }
  }
}

class _RedeDublada extends Interceptor {
  _RedeDublada(this.estado);

  final Estado estado;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (estado == Estado.carregando) return;

    if (estado == Estado.falha) {
      handler.reject(
        DioException(
          requestOptions: options,
          response: Response<dynamic>(requestOptions: options, statusCode: 503),
          type: DioExceptionType.badResponse,
        ),
      );
      return;
    }

    handler.resolve(
      Response<dynamic>(
        requestOptions: options,
        statusCode: 200,
        data: _resposta(options.path, estado),
      ),
    );
  }
}

dynamic _resposta(String caminho, Estado estado) {
  final vazio = estado == Estado.vazio;

  if (caminho.contains('/preferences')) {
    return {
      'risk_profile': 'moderate',
      'passive_income_goal': vazio ? null : 5000.0,
      'preferred_categories': <String>[],
      'preferred_sectors': <String>[],
      'excluded_tickers': <String>[],
      'density': 'comfortable',
      'desired_yield_stock': 0.06,
      'desired_yield_fii': 0.10,
    };
  }

  if (caminho.contains('/auth/me')) {
    return {'id': 'demo', 'name': 'Maria', 'email': 'maria@exemplo.com'};
  }

  return vazio ? _vazio() : _cheio(caminho);
}

Map<String, dynamic> _vazio() => {
  'items': <dynamic>[],
  'count': 0,
  'entries': <dynamic>[],
  'positions': <dynamic>[],
  'allocations': <dynamic>[],
  'snapshots': <dynamic>[],
  'steps': <dynamic>[],
  'goals': <dynamic>[],
  'suggestions': <dynamic>[],
  'debts': <dynamic>[],
  'months': <dynamic>[],
  'by_month': <dynamic>[],
  'by_ticker': <dynamic>[],
  'allocation_gaps': <dynamic>[],
};

Map<String, dynamic> _cheio(String caminho) {
  final base = _vazio();

  if (caminho.contains('/transactions')) {
    return {
      ...base,
      'items': [
        {
          'id': 1,
          'kind': 'buy',
          'symbol': 'PETR4',
          'traded_on': '2026-08-14',
          'quantity': 200.0,
          'price': 38.42,
          'fees': 4.9,
        },
        {
          'id': 2,
          'kind': 'sell',
          'symbol': 'VALE3',
          'traded_on': '2026-07-30',
          'quantity': 50.0,
          'price': 61.10,
          'fees': 4.9,
        },
        {
          'id': 3,
          'kind': 'split',
          'symbol': 'WEGE3',
          'traded_on': '2026-06-12',
          'ratio_from': 1.0,
          'ratio_to': 2.0,
        },
      ],
      'count': 3,
    };
  }

  if (caminho.contains('/dividends/pending')) {
    return {
      'items': [
        {
          'ticker': 'BBAS3',
          'paid_at': '2026-09-05',
          'amount': 142.80,
          'quantity_at_date': 300.0,
          'rate_per_share': 0.476,
          'kind': 'jcp',
          'caveats': ['A quantidade usada é a de hoje, não a da data do crédito.'],
          'quantity_is_current': true,
        },
      ],
      'count': 1,
      'note': 'Sugestões do calendário cruzadas com a sua carteira.',
    };
  }

  if (caminho.contains('/dividends')) {
    return {
      ...base,
      'items': [
        {
          'id': 1,
          'ticker': 'PETR4',
          'paid_at': '2026-08-20',
          'amount': 318.40,
          'kind': 'dividendo',
        },
        {
          'id': 2,
          'ticker': 'MXRF11',
          'paid_at': '2026-08-15',
          'amount': 96.10,
          'kind': 'rendimento',
        },
      ],
      'total_received': 4820.50,
      'received_this_month': 414.50,
      'received_last_12m': 4120.00,
      'monthly_average_12m': 343.33,
      'total_count': 2,
      'by_ticker': [
        {'ticker': 'PETR4', 'total': 2480.0, 'count': 8},
        {'ticker': 'MXRF11', 'total': 1152.0, 'count': 12},
      ],
    };
  }

  return base;
}

Future<void> _capturar(WidgetTester tester, String nome) async {
  final boundary =
      tester.firstRenderObject(find.byType(RepaintBoundary)) as RenderRepaintBoundary;

  ByteData? bytes;
  await tester.runAsync(() async {
    final imagem = await boundary.toImage(pixelRatio: 2);
    bytes = await imagem.toByteData(format: ui.ImageByteFormat.png);
    imagem.dispose();
  });

  if (bytes == null) fail('não foi possível codificar $nome');

  _saida.createSync(recursive: true);
  File('${_saida.path}/$nome.png').writeAsBytesSync(bytes!.buffer.asUint8List());
}

Future<void> _montar(
  WidgetTester tester,
  Widget tela, {
  required Brightness brilho,
  Estado estado = Estado.conteudo,
}) async {
  tester.view.physicalSize = _tela * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final dio = Dio()..interceptors.add(_RedeDublada(estado));

  await tester.pumpWidget(
    RepaintBoundary(
      child: ProviderScope(
        overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(dio))],
        child: MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: buildAppTheme(Brightness.light),
          darkTheme: buildAppTheme(Brightness.dark),
          themeMode: brilho == Brightness.dark ? ThemeMode.dark : ThemeMode.light,
          home: tela,
        ),
      ),
    ),
  );

  // Cada Future do Riverpod resolve num ciclo; telas com providers aninhados precisam de mais
  // de um. pumpAndSettle nao serve: o esqueleto de carregamento anima para sempre.
  for (var i = 0; i < 8; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

void main() {
  setUpAll(_carregarFontes);

  final telas = <String, Widget Function()>{
    'login': () => const LoginScreen(),
    'mes': () => const MesScreen(),
    'mes-atividade': () => const AtividadeScreen(),
    'mes-dividas': () => const DividasScreen(),
    'sobra': () => const SobraScreen(),
    'sobra-desvio': () => const DesvioScreen(),
    'patrimonio': () => const PatrimonioScreen(),
    'patrimonio-renda-fixa': () => const FixedIncomeScreen(),
    'patrimonio-razao': () => const RazaoScreen(),
    'patrimonio-proventos': () => const ProventosScreen(),
    'voce': () => const ConfigScreen(),
    'voce-objetivos': () => const ObjetivosScreen(),
  };

  for (final tela in telas.entries) {
    for (final brilho in const [Brightness.light, Brightness.dark]) {
      final sufixo = brilho == Brightness.light ? 'claro' : 'escuro';

      testWidgets('${tela.key} - $sufixo', (tester) async {
        await _montar(tester, tela.value(), brilho: brilho);
        await _capturar(tester, '${tela.key}-$sufixo');
      });
    }
  }

  for (final estado in const [Estado.carregando, Estado.falha, Estado.vazio]) {
    testWidgets('razao - ${estado.name}', (tester) async {
      await _montar(tester, const RazaoScreen(), brilho: Brightness.light, estado: estado);
      await _capturar(tester, 'estado-razao-${estado.name}');
    });
  }
}
