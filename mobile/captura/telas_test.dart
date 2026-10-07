import 'dart:io';
import 'dart:ui' as ui;

import 'package:dio/dio.dart';
import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/router.dart';
import 'package:fiance/core/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../test/fixtures/rede_dublada.dart';

const _tela = Size(390, 1400);

final _saida = Directory('../build/revisao/telas');
final _fontes = Directory('../build/revisao/.fontes');


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
      'Sem as fontes em ${_fontes.path}. Rode `python tool/revisar_telas.py`, que as baixa antes '
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


Future<void> _capturar(WidgetTester tester, String subpasta, String nome) async {
  final boundary =
      tester.firstRenderObject(find.byType(RepaintBoundary)) as RenderRepaintBoundary;

  ByteData? bytes;
  await tester.runAsync(() async {
    final imagem = await boundary.toImage(pixelRatio: 2);
    bytes = await imagem.toByteData(format: ui.ImageByteFormat.png);
    imagem.dispose();
  });

  if (bytes == null) fail('não foi possível codificar $nome');

  final pasta = Directory('${_saida.path}/$subpasta');
  pasta.createSync(recursive: true);
  File('${pasta.path}/$nome.png').writeAsBytesSync(bytes!.buffer.asUint8List());
}

Future<void> _montar(
  WidgetTester tester,
  String rota, {
  required Brightness brilho,
  Estado estado = Estado.conteudo,
}) async {
  tester.view.physicalSize = _tela * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final dio = Dio()..interceptors.add(RedeDublada(estado));

  final roteador = GoRouter(initialLocation: rota, routes: appRouter.configuration.routes);

  await tester.pumpWidget(
    RepaintBoundary(
      child: ProviderScope(
        overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(dio))],
        child: MaterialApp.router(
          debugShowCheckedModeBanner: false,
          theme: buildAppTheme(Brightness.light),
          darkTheme: buildAppTheme(Brightness.dark),
          themeMode: brilho == Brightness.dark ? ThemeMode.dark : ThemeMode.light,
          routerConfig: roteador,
        ),
      ),
    ),
  );

  // Cada Future do Riverpod resolve num ciclo; telas com providers aninhados precisam de mais
  // de um. pumpAndSettle nao serve: o esqueleto de carregamento anima para sempre.
  for (var i = 0; i < 8; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }

  // O google_fonts lanca a cada peso que nao esta nos assets, e o plugin de notificacao nao tem
  // implementacao de plataforma sob flutter test. As duas sao ruido do ambiente: consumidas, o
  // teste segue e a imagem sai. Qualquer outra excecao continua derrubando o teste.
  while (true) {
    final excecao = tester.takeException();
    if (excecao == null) break;
    final texto = excecao.toString();
    if (texto.contains('allowRuntimeFetching')) continue;
    if (texto.contains('LateInitializationError')) continue;
    throw excecao as Object;
  }
}

void main() {
  setUpAll(_carregarFontes);


  for (final screen in telasDoApp.entries) {
    for (final estado in Estado.values) {
      for (final brilho in const [Brightness.light, Brightness.dark]) {
        final tema = brilho == Brightness.light ? 'claro' : 'escuro';

        testWidgets('${screen.key} - ${estado.name} - $tema', (tester) async {
          await _montar(tester, screen.value, brilho: brilho, estado: estado);
          await _capturar(tester, estado.name, '${screen.key}-$tema');
        });
      }
    }
  }
}
