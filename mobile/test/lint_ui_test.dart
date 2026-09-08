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
     * corpos para a mesma coisa em telas vizinhas. Aqui ela esta viva -- 49 linhas em 15 tamanhos
     * distintos, incluindo 11px e 9px, contra 83 usos de papel.
     *
     * `core/design_tokens.dart` e `core/theme.dart` ficam de fora: sao a camada de design, e e
     * ali que tamanho se declara. O resto e tela.
     *
     * Por isso esta regra e CATRACA, no padrao de `SEM_MODELO_HOJE` no backend: nao conserta
     * hoje, nao deixa crescer, e o teto so desce. Consertar de verdade exige recalibrar a escala
     * para 360dp -- `body` em 16 para `caption` deixar de ser o corpo do aplicativo -- e isso
     * pede uma passagem visual em aparelho, nao substituicao mecanica. Esta no KNOWN_ISSUES.
     */
    test('o tipo solto nao cresce', () {
      const teto = 49;

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

/// A forma unica de escapar, igual a do web: a regra pelo nome, e o motivo escrito.
bool _temEscape(String fonte, String regra) =>
    RegExp('//\\s*design-exception:\\s*$regra\\s*(?:—|-{1,2})\\s*\\S').hasMatch(fonte);
