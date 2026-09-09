import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// As regras de produto e acessibilidade do `npm run lint:ui`, agora no Dart.
///
/// O `lint:ui` tem 22 regras e nenhuma rodava aqui. O efeito era medivel e sempre na mesma
/// direcao: todo principio do produto era cobrado por uma maquina que so rodava no web, e no
/// mobile ele simplesmente nao embarcava. Proveniencia em julgamento: 15 pontos no web, zero
/// aqui. Serifa carregando conclusao: 20 contra 3. Tamanho de tipo escrito solto: zero no web,
/// porque uma regra reprova, e 49 aqui, porque nenhuma rodava.
///
/// Vive como teste, e nao como script proprio, porque `flutter test` ja e o comando do CI: uma
/// regra que exige mudar a esteira para rodar e uma regra que nao roda.
void main() {
  final fontes = _dartsDe('lib');

  group('regras de produto no mobile', () {
    /*
     * Julgamento renderizado exige como conferir a conta.
     *
     * O sinal de julgamento e estreito de proposito: `scoreBand`/`scoreBandFor`/`fiBandFor` sao
     * o sistema colocando um numero numa faixa nomeada, `fiDecision` e o veredito, e `fairPrice`
     * e preco justo. `fiStateColor` NAO entra: a tela de login usa estado para erro, e erro nao
     * e julgamento sobre dinheiro.
     *
     * O explicador aceita o vocabulario que este codigo ja tem: `FiProvenance`, `HelpTooltip`,
     * e as funcoes de proveniencia de `core/score_ruler.dart` (`consensusLabel` diz quantos
     * metodos entraram, `dataYearsLabel` diz a profundidade do historico). Mencionar em prosa
     * nao conta, igual no web.
     */
    test('nenhuma tela julga sem explicar', () {
      const julgamento = [
        'scoreBand',
        'scoreBandFor',
        'fiBandFor',
        'fiDecision',
        'fairPrice',
        // A classe da divida e julgamento do sistema sobre o custo dela -- "caseira" contra
        // "administravel" -- e sai de comparar a taxa com o que a carteira rende.
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

    /*
     * O produto nao sabe o futuro, e diz isso. Mesma lista do web: a negacao explicita passa,
     * a afirmacao nao. "nao ha garantia de retorno" e a frase certa; "retorno garantido" e a
     * errada.
     */
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

    /*
     * Projecao sai como faixa, nunca numero unico.
     *
     * `_low`/`_high` sao campos obrigatorios de `PassiveIncomeMonth` no backend justamente para
     * que nao exista caminho em que o numero saia sozinho: um valor unico a cinco anos empresta
     * precisao de centavo a uma pilha de premissas, e e em cima dele que a pessoa decide quanto
     * poupar.
     *
     * A regra e sobre PROJECAO, e o escopo e o mesmo do `lint:ui` do web: `portfolioValue` e
     * `passiveIncomeMonthly`, que sao os numeros a anos de distancia. Duas coisas ficam fora, e
     * por motivos diferentes:
     *
     * * **meta** (`passiveIncomeGoal`) e alvo declarado pela pessoa, e alvo nao tem faixa;
     * * **piso de sobra** (`surplusLow`) aparece sozinho no Mes de proposito, porque a frase o
     *   nomeia como piso -- "a sobra parte de X". A faixa inteira vive na Sobra, onde e o
     *   assunto. Escrever a regra larga demais reprovaria essa frase, que esta certa; o teste
     *   pegou exatamente isso na primeira vez que rodou.
     */
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
    /*
     * Botao de icone sem nome acessivel anuncia so "botao", e a pessoa tem que adivinhar se
     * aquilo apaga a posicao ou fecha o modal. No Flutter o `tooltip:` do IconButton ja produz
     * o rotulo semantico, e por isso ele conta.
     */
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
    /*
     * Serifa decide, sans mede. O papel `verdict` existe para carregar conclusao, e conclusao
     * se le em serifa -- mas declarar o papel nao aplica a familia: `FiType.verdict` sozinho sai
     * em Inter, porque a familia do tema e sans. Quem usa o papel aplica `fiFontSerif` ou
     * `fiSerif`, e e isso que se cobra.
     */
    test('o papel de veredito sai em serifa', () {
      final semSerifa = <String>[];
      for (final f in fontes) {
        final linhas = f.readAsLinesSync();
        for (var i = 0; i < linhas.length; i++) {
          if (!RegExp(r'FiType\.verdict(Sm)?\b').hasMatch(linhas[i])) continue;
          // A familia pode vir no `.copyWith(` da linha seguinte.
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

    /*
     * Tipografia fora da escala de papeis.
     *
     * `fontSize:` solto e o `text-sm` do Flutter, e a doenca e a mesma que o web ja curou: dois
     * corpos para a mesma coisa em telas vizinhas.
     *
     * `core/design_tokens.dart` e `core/theme.dart` ficam de fora: sao a camada de design, e e
     * ali que tamanho se declara. O resto e tela.
     *
     * A escala ja foi recalibrada para 360dp, e com ela os 15 tamanhos que tinham papel
     * equivalente foram trocados. O que resta e legenda de grafico abaixo de 11px, que nao tem
     * papel porque a escala tem piso -- e por isso a regra segue CATRACA, no padrao de
     * `SEM_MODELO_HOJE`: nao conserta hoje, nao deixa crescer, e o teto so desce.
     */
    /*
     * A parte mecanica de docs/design/AI-TELLS.md.
     *
     * Aquele documento se declara nao-checavel por maquina, e para composicao e redacao isso e
     * verdade. A lista de vocabulario proibido nao e: sao frases literais. E foi aqui que ela
     * custou -- `login_screen` e `splash_screen`, as duas primeiras telas do aplicativo, abriam
     * com "tudo em um so assistente": o "tudo em um so lugar" de marketing generico e a persona
     * de assistente conversacional, numa frase de dez palavras.
     *
     * Emoji tambem entra, incluindo os dingbats que o web usava para carregar estado. Estado e
     * papel de cor (`fiStateColor`), nao glifo.
     *
     * Seta fica de fora de proposito: e a informacao no rotulo de tendencia lateral.
     */
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

    /*
     * Nome de destino que o produto nao tem mais.
     *
     * A PARIDADE exige que conceito, nome e hierarquia sejam iguais nas duas plataformas -- valor
     * de cor e composicao sao livres, nome nao e. E o nome divergia em quatro telas: a barra do
     * `/voce` dizia "Configuracoes", a de `/sobra/desvio` dizia "Estrategia" (um destino removido),
     * `/voce/objetivos` dizia "Minhas metas" e a renda fixa vinha com F maiusculo.
     *
     * "Hoje", "Carteira" e "Mercado" entram na lista pelo mesmo motivo: eram destinos, sairam, e
     * a rota antiga continua viva como redirect -- o que faz o nome antigo ser facil de reescrever
     * sem perceber.
     */
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
            'nome de tela e paridade de conceito, e nao de aparencia: docs/design/PARIDADE.md. '
            'Achados: ${achados.join(' | ')}',
      );
    });

    test('o tipo solto nao cresce', () {
      const teto = 36;

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
  });
}

List<File> _dartsDe(String raiz) => Directory(raiz)
    .listSync(recursive: true)
    .whereType<File>()
    .where((f) => f.path.endsWith('.dart'))
    .toList();

String _curto(File f) => f.path.replaceAll(r'\', '/').replaceFirst('lib/', '');

/// Compara nome sem depender de acento, que e onde a grafia divergiu na pratica.
String _semAcento(String texto) {
  const de = 'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC';
  const para = 'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ';
  var saida = texto.toLowerCase();
  for (var i = 0; i < para.length; i++) {
    saida = saida.replaceAll(para[i], de[i].toLowerCase());
  }
  return saida;
}

/// Os literais de string do arquivo -- o que de fato vai para a tela.
///
/// Varrer o fonte inteiro pegaria comentario e nome de simbolo, e a regra passaria a
/// reprovar a propria justificativa de por que uma frase e proibida.
Iterable<String> _literaisDe(String fonte) =>
    RegExp("'([^'\\\\\n]*)'")
        .allMatches(fonte)
        .map((m) => m[1] ?? '');

/// A forma unica de escapar, igual a do web: a regra pelo nome, e o motivo escrito.
bool _temEscape(String fonte, String regra) =>
    RegExp('//\\s*design-exception:\\s*$regra\\s*(?:—|-{1,2})\\s*\\S').hasMatch(fonte);
