import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  final fontes = _dartsDe('lib');

  group('regras de produto no mobile', () {
    test('nenhuma tela julga sem explicar', () {
      const julgamento = [
        'scoreBand',
        'scoreBandFor',
        'fiBandFor',
        'fiDecision',
        'fairPrice',


        'DebtClass.',
      ];
      const explicador = [
        'FiProvenance',
        'HelpTooltip',
        'consensusLabel',
        'dataYearsLabel',
        'trendBasisLabel',
        'dataCompletenessLabel',
        'confidenceLabel',
      ];
      final mudos = <String>[];
      for (final f in fontes.where((f) => f.path.contains('features'))) {
        final fonte = f.readAsStringSync();
        if (_temEscape(fonte, 'explicabilidade')) continue;
        if (!julgamento.any(fonte.contains)) continue;
        if (explicador.any(fonte.contains)) continue;
        mudos.add(_curto(f));
      }

      expect(
        mudos,
        isEmpty,
        reason:
            'estas telas colocam um numero numa faixa nomeada e nao dizem de onde ele veio. '
            'Use FiProvenance (metodo, fonte, momento, limitacao) ou declare o motivo: '
            '// design-exception: explicabilidade — motivo',
      );
    });


    test('nenhuma tela promete o futuro', () {
      final promessas = RegExp(
        r'(retorno|lucro|ganho|rendimento)\s+garantid|garantia\s+de\s+(retorno|lucro|ganho)|'
        r'vai\s+(render|valorizar|subir|dobrar)|certamente\s+(vai|ira)|sem\s+risco',
        caseSensitive: false,
      );
      final negacao = RegExp(
        r'(nao|n[aã]o)\s+h[aá]\s+garantia|'
        r'(nao|n[aã]o)\s+(existe|garante)',
        caseSensitive: false,
      );
      final achados = <String>[];
      for (final f in fontes) {
        for (final linha in f.readAsLinesSync()) {
          if (!promessas.hasMatch(linha)) continue;
          if (negacao.hasMatch(linha)) continue;
          achados.add('${_curto(f)}: ${linha.trim()}');
        }
      }

      expect(
        achados,
        isEmpty,
        reason:
            'preco futuro nao se afirma. Troque por linguagem condicional, ou negue '
            'explicitamente',
      );
    });


    test('projeção só aparece como faixa', () {
      const projetados = ['portfolioValue', 'passiveIncomeMonthly'];

      final semFaixa = <String>[];
      for (final f in fontes.where((f) => f.path.contains('features'))) {
        final fonte = f.readAsStringSync();
        for (final campo in projetados) {
          final piso = fonte.contains('${campo}Low');
          final teto = fonte.contains('${campo}High');
          if (piso == teto) continue;
          semFaixa.add('${_curto(f)}: $campo tem ${piso ? 'piso' : 'teto'} e falta o outro lado');
        }
      }

      expect(
        semFaixa,
        isEmpty,
        reason:
            'mostre piso e teto juntos. A faixa e o numero, nao a tolerancia dele -- e por isso '
            'ela nao mora em tooltip',
      );
    });
  });

  group('regras de acessibilidade no mobile', () {

    test('todo botao de icone tem nome acessivel', () {
      final semNome = <String>[];
      for (final f in fontes) {
        final fonte = f.readAsStringSync();
        final botoes = 'IconButton('.allMatches(fonte).length;
        if (botoes == 0) continue;
        final nomes = 'tooltip:'.allMatches(fonte).length +
            'Semantics('.allMatches(fonte).length;
        if (nomes >= botoes) continue;
        semNome.add('${_curto(f)}: $botoes botões, $nomes nomes');
      }

      expect(
        semNome,
        isEmpty,
        reason: 'adicione tooltip: ao IconButton, ou envolva em Semantics(button: true, label:)',
      );
    });
  });

  group('regras de coerencia no mobile', () {

    test('o papel de veredito sai em serifa', () {
      final semSerifa = <String>[];
      for (final f in fontes) {
        final linhas = f.readAsLinesSync();
        for (var i = 0; i < linhas.length; i++) {
          if (!RegExp(r'FiType\.verdict(Sm)?\b').hasMatch(linhas[i])) continue;

          final janela = linhas.sublist(i, (i + 4).clamp(0, linhas.length)).join(' ');
          if (janela.contains('fiFontSerif') || janela.contains('fiSerif')) continue;
          semSerifa.add('${_curto(f)}:${i + 1}');
        }
      }

      expect(
        semSerifa,
        isEmpty,
        reason:
            'FiType.verdict declara o papel, nao a familia. Aplique fiFontSerif (ou fiSerif) — '
            'sem isso a conclusao sai na fonte que mede, e o principio nao chega a tela',
      );
    });



    test('nenhuma tela fala como IA generica', () {
      final proibido = <RegExp, String>{
        RegExp(r'revolucion[aá]ri', caseSensitive: false): 'marketing generico',
        RegExp(r'simples\s+e\s+poderos', caseSensitive: false): 'marketing generico',
        RegExp(r'tudo\s+em\s+um\s+s[oó]\s+\w+', caseSensitive: false): 'marketing generico',
        RegExp(r'pr[oó]ximo\s+n[ií]vel', caseSensitive: false): 'marketing generico',
        RegExp(r'como\s+posso\s+(te\s+)?ajudar', caseSensitive: false): 'fala de assistente',
        RegExp(r'[eé]\s+importante\s+notar', caseSensitive: false): 'fala de assistente',
        RegExp(
          r'assistente\s+(financeiro|de\s+investimentos)',
          caseSensitive: false,
        ): 'persona de chatbot',
        RegExp(r'parab[eé]ns', caseSensitive: false): 'o produto descreve, nao comemora',
      };

      final emoji = RegExp(
        r'[\u{1F300}-\u{1FAFF}\u{1F000}-\u{1F0FF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}]',
        unicode: true,
      );

      final achados = <String>[];
      for (final f in fontes) {
        final fonte = f.readAsStringSync();
        if (_temEscape(fonte, 'vocabulario')) continue;
        for (final texto in _literaisDe(fonte)) {
          for (final entrada in proibido.entries) {
            final m = entrada.key.firstMatch(texto);
            if (m != null) achados.add('${_curto(f)}: "${m[0]}" -- ${entrada.value}');
          }
          final g = emoji.firstMatch(texto);
          if (g != null) achados.add('${_curto(f)}: ${g[0]} em texto de interface');
        }
      }

      expect(
        achados,
        isEmpty,
        reason:
            'a lista esta em docs/design/AI-TELLS.md. Escape: '
            '// design-exception: vocabulario -- motivo. Achados: ${achados.join(' | ')}',
      );
    });


    test('nenhuma tela usa nome de destino que saiu', () {
      const aposentados = {
        'Hoje': 'o feed vive no Mes',
        'Estrategia': 'dissolveu-se em Sobra e Patrimonio',
        'Carteira': 'o destino chama-se Patrimonio',
        'Configuracoes': 'o destino chama-se Voce',
        'Mercado': 'o destino chama-se Descobrir',
      };

      final achados = <String>[];
      for (final f in fontes) {
        final fonte = f.readAsStringSync();
        if (_temEscape(fonte, 'vocabulario')) continue;

        for (final m in RegExp(r"AppBar\(\s*title:\s*(?:const\s+)?Text\('([^']+)'\)")
            .allMatches(fonte)) {
          final titulo = m[1] ?? '';
          for (final entrada in aposentados.entries) {
            if (!_semAcento(titulo).contains(_semAcento(entrada.key))) continue;
            achados.add('${_curto(f)}: "$titulo" -- ${entrada.value}');
          }
        }
      }

      expect(
        achados,
        isEmpty,
        reason:
            'nome de tela e o conceito, e o destino antigo saiu: docs/design/'
            'INFORMATION-ARCHITECTURE.md. Achados: ${achados.join(' | ')}',
      );
    });

    test('o tipo solto nao cresce', () {
      const teto = 0;

      final soltos = <String>[];
      for (final f in fontes) {
        if (f.path.contains('design_tokens.dart')) continue;
        if (f.path.endsWith('core${Platform.pathSeparator}theme.dart') ||
            f.path.endsWith('core/theme.dart')) {
          continue;
        }
        final linhas = f.readAsLinesSync();
        for (var i = 0; i < linhas.length; i++) {
          if (!RegExp(r'fontSize:\s*[0-9]').hasMatch(linhas[i])) continue;
          soltos.add('${_curto(f)}:${i + 1}');
        }
      }

      expect(
        soltos.length,
        lessThanOrEqualTo(teto),
        reason:
            'tamanho solto reabre a decisao a cada tela. Use os papeis de FiType. O teto e '
            'catraca: ao trocar um solto por papel, baixe o numero neste teste. '
            'Soltos hoje:\n  ${soltos.join('\n  ')}',
      );
    });

    test('a caixa do Material nao volta a crescer', () {

      const teto = 0;

      final achados = <String>[];
      for (final f in fontes) {
        final linhas = f.readAsLinesSync();
        for (var i = 0; i < linhas.length; i++) {
          final linha = linhas[i];
          if (linha.trimLeft().startsWith('//') || linha.trimLeft().startsWith('///')) {
            continue;
          }
          if (!RegExp(r'\b(Card|ListTile|SwitchListTile|CircleAvatar)\(').hasMatch(linha)) {
            continue;
          }
          achados.add('${_curto(f)}:${i + 1}: ${linha.trim()}');
        }
      }

      expect(
        achados.length,
        lessThanOrEqualTo(teto),
        reason:
            'a moldura e o atalho que dispensa pensar em espaco, tipo e fio. Use FiObject '
            '(o que e objeto) ou FiSection + FiRows/FiDataRow. O teto e catraca, e so desce. '
            'Achados:\n  ${achados.join('\n  ')}',
      );
    });

    test('espera tem a forma do que vai chegar, e nao um disco girando', () {

      final achados = <String>[];
      for (final f in fontes) {
        final fonte = f.readAsStringSync();
        if (_temEscape(fonte, 'esqueleto')) continue;

        for (final m in RegExp(r'Center\(\s*child:\s*CircularProgressIndicator\(')
            .allMatches(fonte)) {
          final linha = '\n'.allMatches(fonte.substring(0, m.start)).length + 1;
          achados.add('${_curto(f)}:$linha');
        }
      }

      expect(
        achados,
        isEmpty,
        reason:
            'use FiSkeleton.tela(shape: ..., count: ...): o esqueleto tem a altura do papel que '
            'vai ocupar o lugar, entao a pagina nao salta. Achados: ${achados.join(', ')}',
      );
    });

    test('nenhuma tela escreve cor a mao', () {

      final achados = <String>[];
      for (final f in fontes) {
        if (f.path.contains('design_tokens.dart')) continue;

        final linhas = f.readAsLinesSync();
        for (var i = 0; i < linhas.length; i++) {
          final linha = linhas[i];
          if (linha.trimLeft().startsWith('//')) continue;

          if (RegExp(r'Color\(0x[0-9A-Fa-f]{8}\)').hasMatch(linha)) {
            achados.add('${_curto(f)}:${i + 1}: hexadecimal solto');
          }
          if (RegExp(r'\bColors\.(?!transparent\b)[a-zA-Z]').hasMatch(linha)) {
            achados.add('${_curto(f)}:${i + 1}: paleta do Material');
          }
        }
      }

      expect(
        achados,
        isEmpty,
        reason:
            'a paleta e uma so, e vive em core/design_tokens.dart. Use o papel: fiStateColor, '
            'fiDirectionColor, fiSeriesColor, fiInk1/2/3, fiGround0/1/2, fiHairline. '
            'Achados:\n  ${achados.join('\n  ')}',
      );
    });

    test('a busca global e alcancavel de todo destino de raiz', () {

      const raizes = <String, String>{
        'features/mes/mes_screen.dart': 'Mes',
        'features/sobra/sobra_screen.dart': 'Sobra',
        'features/patrimonio/patrimonio_screen.dart': 'Patrimonio',
        'core/router.dart': 'Descobrir',
        'features/config/config_screen.dart': 'Voce',
      };

      final semBusca = <String>[];
      for (final entrada in raizes.entries) {
        final arquivo = File('lib/${entrada.key}');
        expect(arquivo.existsSync(), isTrue, reason: 'destino sumiu: ${entrada.key}');

        if (!arquivo.readAsStringSync().contains('FiSearchAction')) {
          semBusca.add('${entrada.value} (${entrada.key})');
        }
      }

      expect(
        semBusca,
        isEmpty,
        reason:
            'todo destino de raiz leva a /busca por FiSearchAction. Sem busca: '
            '${semBusca.join(', ')}',
      );
    });

    test('todo destino navegado existe no roteador', () {

      final router = File('lib/core/router.dart').readAsStringSync();

      final declarados = <String>{};
      final pilha = <({int indent, String caminho})>[];
      for (final linha in router.split('\n')) {
        final path = RegExp(r"path:\s*'([^']+)'").firstMatch(linha);
        if (path == null) continue;

        final trecho = path[1]!;
        final indent = linha.length - linha.trimLeft().length;

        while (pilha.isNotEmpty && pilha.last.indent >= indent) {
          pilha.removeLast();
        }

        final completo = trecho.startsWith('/')
            ? trecho
            : '${pilha.isEmpty ? '' : pilha.last.caminho}/$trecho';

        pilha.add((indent: indent, caminho: completo));
        declarados.add(completo);
      }

      expect(
        declarados,
        contains('/mes'),
        reason: 'a leitura do roteador quebrou: nenhum destino conhecido foi encontrado',
      );

      bool existe(String destino) {
        final alvo = destino.split('?').first;
        for (final d in declarados) {
          if (d == alvo) return true;
          if (!d.contains(':')) continue;
          final padrao = RegExp('^${d.replaceAll(RegExp(r':[A-Za-z_]+'), '[^/]+')}\$');
          if (padrao.hasMatch(alvo)) return true;
        }
        return false;
      }

      final quebrados = <String>[];
      for (final f in fontes) {
        if (f.path.endsWith('router.dart')) continue;

        final fonte = f.readAsStringSync();
        for (final m in RegExp(r"\.(?:go|push|replace)\('(/[^']*)'").allMatches(fonte)) {
          final destino = m[1]!;
          if (existe(destino)) continue;
          final linha = '\n'.allMatches(fonte.substring(0, m.start)).length + 1;
          quebrados.add('${_curto(f)}:$linha -> $destino');
        }
      }

      expect(
        quebrados,
        isEmpty,
        reason:
            'destino que o roteador nao declara vira GoException no toque, e so aparece para '
            'quem toca. Achados:\n  ${quebrados.join('\n  ')}',
      );
    });

    test('a falha de leitura sai numa voz so', () {

      final proprios = <String>[];
      for (final f in fontes) {
        if (f.path.contains('error_state.dart')) continue;

        final fonte = f.readAsStringSync();
        for (final m in RegExp(r'class _\w*(?:Error|Falha)\w*\s+extends\s+\w*Widget')
            .allMatches(fonte)) {
          proprios.add('${_curto(f)}: ${m[0]}');
        }
      }

      expect(
        proprios,
        isEmpty,
        reason:
            'use FiErrorState, que ja traduz DioException em frase e oferece "Tentar de novo". '
            'Achados: ${proprios.join(' | ')}',
      );
    });

  });
}

List<File> _dartsDe(String raiz) => Directory(raiz)
    .listSync(recursive: true)
    .whereType<File>()
    .where((f) => f.path.endsWith('.dart'))
    .toList();

String _curto(File f) => f.path.replaceAll(r'\', '/').replaceFirst('lib/', '');


String _semAcento(String texto) {
  const de = 'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC';
  const para = 'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ';
  var saida = texto.toLowerCase();
  for (var i = 0; i < para.length; i++) {
    saida = saida.replaceAll(para[i], de[i].toLowerCase());
  }
  return saida;
}





Iterable<String> _literaisDe(String fonte) =>
    RegExp("'([^'\\\\\n]*)'")
        .allMatches(fonte)
        .map((m) => m[1] ?? '');


bool _temEscape(String fonte, String regra) =>
    RegExp('//\\s*design-exception:\\s*$regra\\s*(?:—|-{1,2})\\s*\\S').hasMatch(fonte);
