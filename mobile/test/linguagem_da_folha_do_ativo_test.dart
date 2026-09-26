import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/api_repository.dart';
import 'package:fiance/core/format.dart';
import 'package:fiance/core/glossary.dart';
import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/data_row.dart';
import 'package:fiance/core/widgets/measure.dart';
import 'package:fiance/features/market/asset_detail_sheet.dart';

const _siglas = <String, String>{
  'ROE': 'retorno sobre o patrimônio',
  'P/VP': 'valor patrimonial',
  'P/L': 'preço sobre lucro',
  'LPA': 'lucro por ação',
  'VPA': 'valor patrimonial',
  'RSI': 'força relativa',
  'DY': 'dividendos',
  'BDR': 'recibo de ação',
  'ETF': 'fundo',
  'FII': 'fundo',
  'JCP': 'juros sobre capital',
  'Selic': 'juro',
  'IPCA': 'inflação',
  'CDI': 'juro',
};

const _jargao = <String, String>{
  'DCF': 'o método se chama pelo que mede: pelo lucro distribuível',
  'Bazin': 'o método se chama pelo que mede: pelos dividendos',
  'Gordon': 'fórmula não é leitura',
  'payout': 'é a parte do lucro que a empresa distribui',
  'yield': 'é rendimento',
  'insumo': 'é dado',
  'exercício': 'é ano fechado',
  'normaliz': 'é a média',
  'taxa de desconto': 'a tela chama de taxa exigida',
  'costuma vir': 'contexto de preço não prevê o próximo movimento',
};

const _acao = {
  'symbol': 'ITSA4',
  'name': 'Itaúsa PN',
  'asset_type': 'br_stock',
  'sector': 'Financial Services',
  'price': 5.0,
  'as_of': 1790000000.0,
  'fair_price': {
    'fair_low': 6.55,
    'fair_high': 8.33,
    'principal_value': 7.41,
    'margin_of_safety': 0.2366,
    'band_quality': 'ampla',
    'independent_inputs': 2,
    'principal': 'lucros_descontados',
    'dy_12m': 0.1,
    'graham': 13.42,
    'personal_ceiling': 8.33,
    'data_years': 5,
    'methods': [
      {'method': 'dcf', 'input': 'lucro', 'role': 'principal', 'value': 7.41, 'status': 'ok', 'note': ''},
      {'method': 'bazin', 'input': 'dividendo', 'role': 'confirmacao', 'value': 5.22, 'status': 'ok', 'note': '', 'agreement': 'fora_ate_30'},
      {'method': 'vpa', 'input': 'patrimonio', 'role': 'inaplicavel', 'status': 'inaplicavel', 'note': 'vale para fundo imobiliário'},
      {'method': 'graham', 'input': 'lucro_e_patrimonio', 'role': 'indicador', 'value': 13.42, 'status': 'ok', 'note': ''},
    ],
    'premises': {
      'discount_rate': 0.145,
      'rate_base': 'selic_media_10a',
      'selic_pct': 9.5,
      'reference_date': '2026-09-23',
      'growth': 0.075,
      'long_run_growth': 0.045,
      'explicit_years': 5,
      'roe': 0.15,
      'payout': 0.5,
      'distributable': 0.5,
      'eps_normalized': 1.0,
      'earnings_years': 3,
      'value_without_growth': 7.11,
      'growth_creates_value': true,
      'breakeven_discount_rate': 0.1873,
    },
    'indicators': [
      {'kind': 'graham', 'value': 13.42, 'passes': true},
      {'kind': 'preco_teto_pessoal', 'value': 8.33, 'passes': true, 'desired_yield': 0.06},
      {'kind': 'pvp', 'value': 0.9, 'passes': null},
    ],
    'quality_reasons': ['a segunda conta fica fora da faixa, a até 30% dela'],
    'confirmation': {'method': 'bazin', 'value': 5.22, 'agreement': 'fora_ate_30'},
  },
  'technical': {'trend': 'uptrend', 'trend_basis': 'long', 'rsi_14': 74.0},
  'decision': {
    'verdict': 'BUY',
    'label': 'Abaixo do preço justo',
    'basis': 'band',
    'reasons': [
      'O preço está 23,7% abaixo do piso da faixa de preço justo, que vai de R\$ 6,55 a R\$ 8,33.',
      'Vale cerca de R\$ 7,41 pelo lucro que a empresa pode distribuir sem deixar de crescer.',
      'Uma segunda conta, pelos dividendos, dá R\$ 5,22, 20% abaixo do piso: não confirma a faixa.',
      'Qualidade da faixa: a segunda conta fica fora da faixa, a até 30% dela.',
      'Cabe na sua meta de renda: para render os 6% ao ano que você pediu em proventos, o '
          'preço-teto é R\$ 8,33, e o de hoje está abaixo.',
      'Na conta, a taxa exigida — o retorno mínimo para o investimento valer a pena — é de '
          '14,5% ao ano: a Selic média de 10 anos, o juro básico do país, mais 5 pontos. O lucro '
          'cresce 7,5% ao ano por 5 anos — o retorno sobre o patrimônio (ROE) de 15% vezes a '
          'parte do lucro que a empresa retém — e 4,5% depois. A faixa cobre esse cenário e o de '
          'não crescer e distribuir todo o lucro, com 1 ponto de taxa a mais e a menos.',
      'Preço sobre valor patrimonial (P/VP) de 0,90: paga-se menos que o patrimônio que está no '
          'balanço.',
      'O preço vem subindo: a média do preço nos últimos 50 dias está acima da média dos '
          'últimos 200. É contexto de preço, e não muda a leitura de valor.',
      'O preço subiu rápido em pouco tempo: o índice de força relativa (RSI) está em 74, de 0 a '
          '100. É contexto, não leitura de valor.',
    ],
    'falsifiers': [
      {'metric': 'price', 'condition': 'O preço cair para R\$ 4,58 ou menos', 'becomes_label': 'Bem abaixo do preço justo', 'current': 5.0, 'threshold': 4.585, 'kind': 'gatilho'},
      {'metric': 'price', 'condition': 'O preço subir para R\$ 5,57 ou mais', 'becomes_label': 'No preço justo', 'current': 5.0, 'threshold': 5.5675, 'kind': 'gatilho'},
      {
        'metric': 'discount_rate',
        'condition': 'A taxa exigida, o retorno mínimo que a conta pede ao ano, subir de 14,5% '
            'para 18,7%: aí o preço de hoje deixa de ter folga sobre o valor',
        'becomes_label': 'Rever a tese',
        'current': 0.145,
        'threshold': 0.1873,
        'kind': 'premissa',
      },
    ],
  },
};

const _fii = {
  'symbol': 'MXRF11',
  'name': 'Maxi Renda FII',
  'asset_type': 'fii',
  'sector': 'Real Estate',
  'price': 120.0,
  'as_of': 1790000000.0,
  'fair_price': {
    'fair_low': 74.07,
    'fair_high': 86.96,
    'principal_value': 80.0,
    'margin_of_safety': -0.2753,
    'band_quality': 'ampla',
    'independent_inputs': 2,
    'principal': 'dividendos',
    'dy_12m': 0.083,
    'personal_ceiling': 100.0,
    'data_years': 5,
    'methods': [
      {'method': 'bazin', 'input': 'dividendo', 'role': 'principal', 'value': 80.0, 'status': 'ok', 'note': ''},
      {'method': 'vpa', 'input': 'patrimonio', 'role': 'confirmacao', 'value': 100.0, 'status': 'ok', 'note': '', 'agreement': 'fora_ate_30'},
      {'method': 'dcf', 'input': 'lucro', 'role': 'inaplicavel', 'status': 'inaplicavel', 'note': 'vale para ação'},
    ],
    'premises': {
      'fii_yield': 0.125,
      'rate_base': 'selic_media_10a',
      'selic_pct': 9.5,
      'reference_date': '2026-09-23',
      'inflation_target': 0.03,
      'real_rate_floor': 0.03,
      'fii_premium': 0.03,
      'fii_segment': 'papel',
      'dividend_recurring': 10.0,
    },
    'indicators': [
      {'kind': 'preco_teto_pessoal', 'value': 100.0, 'passes': false, 'desired_yield': 0.10},
      {'kind': 'pvp', 'value': 1.2, 'passes': null},
    ],
    'quality_reasons': ['a segunda conta fica fora da faixa, a até 30% dela'],
    'confirmation': {'method': 'vpa', 'value': 100.0, 'agreement': 'fora_ate_30'},
  },
  'technical': {'trend': 'downtrend', 'trend_basis': 'short', 'rsi_14': 22.0},
  'decision': {
    'verdict': 'SELL',
    'label': 'Acima do preço justo',
    'basis': 'band',
    'reasons': [
      'O preço está 38,0% acima do teto da faixa de preço justo, que vai de R\$ 74,07 a '
          'R\$ 86,96.',
      'Vale cerca de R\$ 80,00 pelo que o fundo distribui num ano típico, R\$ 10,00 por cota.',
      'Uma segunda conta, pelo valor patrimonial, o patrimônio do fundo dividido pelas cotas, '
          'dá R\$ 100,00, 15% acima do teto: não confirma a faixa.',
      'Qualidade da faixa: a segunda conta fica fora da faixa, a até 30% dela.',
      'Não cabe na sua meta de renda: para render os 10% ao ano que você pediu em proventos, o '
          'preço-teto é R\$ 100,00, abaixo do de hoje.',
      'Na conta, o rendimento exigido do fundo é de 12,5% ao ano: o juro real de longo prazo, '
          'que é o que sobra acima da inflação (a Selic média de 10 anos, o juro básico do país, '
          'menos a meta de inflação de 3%, com piso de 3%), mais 3% de prêmio pelo risco, mais a '
          'meta de inflação, porque o fundo é de papel: ele vive de dívidas imobiliárias, e o que '
          'distribui já traz a correção pela inflação, sem que o valor emprestado cresça com ela. '
          'A faixa vai de 1 ponto a mais a 1 ponto a menos de rendimento exigido.',
      'Preço sobre valor patrimonial (P/VP) de 1,20: paga-se mais que o patrimônio que está no '
          'balanço.',
      'O preço vem caindo: a média do preço nos últimos 20 dias está abaixo da média dos '
          'últimos 50, com histórico curto. É contexto de preço, e não muda a leitura de valor.',
      'O preço caiu rápido em pouco tempo: o índice de força relativa (RSI) está em 22, de 0 a '
          '100. É contexto, não leitura de valor.',
    ],
    'falsifiers': [
      {'metric': 'price', 'condition': 'O preço cair para R\$ 102,31 ou menos', 'becomes_label': 'No preço justo', 'current': 120.0, 'threshold': 102.31, 'kind': 'gatilho'},
      {'metric': 'price', 'condition': 'O preço subir para R\$ 124,23 ou mais', 'becomes_label': 'Bem acima do preço justo', 'current': 120.0, 'threshold': 124.23, 'kind': 'gatilho'},
    ],
  },
};

class _Api extends Interceptor {
  _Api(this.analise);

  final Map<String, Object?> analise;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final dados = options.path.startsWith('/asset/')
        ? analise
        : {'desired_yield_stock': 0.06, 'desired_yield_fii': 0.10, 'detail_level': 'essencial'};
    handler.resolve(Response<dynamic>(requestOptions: options, statusCode: 200, data: dados));
  }
}

Future<void> _abrirNoEssencial(WidgetTester tester, Map<String, Object?> analise) async {
  tester.view.physicalSize = const Size(390, 7000) * 2;
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);

  final dio = Dio()..interceptors.add(_Api(analise));
  await tester.pumpWidget(
    ProviderScope(
      overrides: [apiRepositoryProvider.overrideWithValue(ApiRepository(dio))],
      child: MaterialApp(
        theme: buildAppTheme(Brightness.light),
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () => showAssetDetailSheet(context, analise['symbol']! as String),
              child: const Text('abrir'),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('abrir'));
  for (var i = 0; i < 10; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

Future<void> _abrirAGaveta(WidgetTester tester) async {
  await tester.tap(_texto('Como chegamos nisso'));
  for (var i = 0; i < 5; i++) {
    await tester.pump(const Duration(milliseconds: 120));
  }
}

Finder _texto(String trecho) => find.byWidgetPredicate(
      (w) => w is Text && (w.data ?? '').toLowerCase().contains(trecho.toLowerCase()),
    );

List<String> _unidades(WidgetTester tester) {
  final linhas = tester.widgetList<FiDataRow>(find.byType(FiDataRow));
  final medidas = tester.widgetList<FiMeasure>(find.byType(FiMeasure));
  final dentro = <Widget>{
    ...tester.widgetList(find.descendant(of: find.byType(FiDataRow), matching: find.byType(Text))),
    ...tester.widgetList(find.descendant(of: find.byType(FiMeasure), matching: find.byType(Text))),
  };
  return [
    for (final l in linhas) [l.label, l.value, l.detail, l.note].whereType<String>().join(' · '),
    for (final m in medidas) [m.label, m.readout, m.note].whereType<String>().join(' · '),
    for (final t in tester.widgetList<Text>(find.byType(Text)))
      if (!dentro.contains(t) && t.data != null) t.data!,
  ];
}

bool _temSigla(String texto, String sigla) =>
    RegExp('(?<![\\w/])${RegExp.escape(sigla)}(?![\\w/])').hasMatch(texto);

void _confereSiglasEJargao(WidgetTester tester, Map<String, Object?> analise, String onde) {
  final unidades = _unidades(tester);
  expect(unidades, isNotEmpty);

  for (final unidade in unidades) {
    if (unidade == analise['name'] || unidade == analise['symbol'] || unidade == 'abrir') {
      continue;
    }
    for (final e in _siglas.entries) {
      if (!_temSigla(unidade, e.key)) continue;
      expect(
        unidade.toLowerCase(),
        contains(e.value.toLowerCase()),
        reason: '$onde: "${e.key}" chega sem "${e.value}" ao lado. Metade do público nunca '
            'investiu, e no Essencial a leitura se entende sem abrir o glossário: "$unidade"',
      );
    }
    for (final e in _jargao.entries) {
      expect(
        unidade.toLowerCase(),
        isNot(contains(e.key.toLowerCase())),
        reason: '$onde: "${e.key}" — ${e.value}: "$unidade"',
      );
    }
  }
}

double _topo(WidgetTester tester, String trecho) => tester.getTopLeft(_texto(trecho).first).dy;

void main() {
  for (final caso in {'ação': _acao, 'fundo imobiliário de papel': _fii}.entries) {
    testWidgets('${caso.key}: no essencial, nenhuma sigla chega sem explicação ao lado, nem '
        'com a gaveta aberta', (tester) async {
      await _abrirNoEssencial(tester, caso.value);
      _confereSiglasEJargao(tester, caso.value, 'gaveta fechada');

      await _abrirAGaveta(tester);
      expect(_texto('Quanto o ativo vale'), findsOneWidget);
      _confereSiglasEJargao(tester, caso.value, 'gaveta aberta');
    });

    testWidgets('${caso.key}: o tipo do ativo sai por extenso no cabeçalho', (tester) async {
      await _abrirNoEssencial(tester, caso.value);

      final tipo = caso.value['asset_type'] == 'fii' ? 'Fundo imobiliário (FII)' : 'Ação';
      expect(_texto(tipo), findsWidgets,
          reason: 'o nome que vem da fonte pode trazer a sigla, como "Maxi Renda FII", e é '
              'nome próprio: quem diz o que o ativo é, por extenso, é o cabeçalho');
    });

    testWidgets('${caso.key}: todo termo técnico que fica na tela abre um verbete que existe',
        (tester) async {
      await _abrirNoEssencial(tester, caso.value);
      await _abrirAGaveta(tester);

      for (final m in tester.widgetList<FiMeasure>(find.byType(FiMeasure))) {
        expect(glossary[m.glossaryKey], isNotNull,
            reason: '"${m.label}" é jargão, e a régua é a primeira coisa que o iniciante lê');
      }
      for (final l in tester.widgetList<FiDataRow>(find.byType(FiDataRow))) {
        if (l.glossaryKey != null) {
          expect(glossary[l.glossaryKey], isNotNull,
              reason: 'verbete que não existe deixa o termo sem toque, em silêncio: '
                  '"${l.glossaryKey}" em "${l.label}"');
        }
        final unidade = [l.label, l.detail, l.note].whereType<String>().join(' ');
        final tecnico = _siglas.keys.any((s) => _temSigla(unidade, s)) ||
            RegExp('taxa exigida|rendimento exigido|faixa de preço justo|critério de graham',
                    caseSensitive: false)
                .hasMatch(l.label);
        if (!tecnico) continue;
        expect(l.glossaryKey, isNotNull,
            reason: 'termo técnico que fica na tela tem verbete ao alcance do dedo: "${l.label}"');
      }
    });
  }

  testWidgets('no essencial, a leitura vem antes da evidência, e a evidência antes do método',
      (tester) async {
    await _abrirNoEssencial(tester, _acao);

    final etiqueta = tester.getTopLeft(find.text('Abaixo do preço justo').first).dy;
    final preco = tester.getTopLeft(find.text('PREÇO')).dy;
    final margem = _topo(tester, 'Margem de segurança');
    final evidencia = _topo(tester, 'O preço está 23,7% abaixo do piso');
    final gaveta = _topo(tester, 'Como chegamos nisso');

    expect(etiqueta, lessThan(margem), reason: 'a etiqueta é a primeira leitura');
    expect(preco, lessThan(margem));
    expect(margem, lessThan(evidencia), reason: 'a margem em palavras vem antes do porquê');
    expect(evidencia, lessThan(gaveta), reason: 'o porquê vem aberto; o método, fechado');

    expect(_texto('Quanto o ativo vale'), findsNothing, reason: 'o método vem fechado');
    expect(_texto('As premissas'), findsNothing);
    expect(_texto('Na conta, a taxa exigida'), findsNothing,
        reason: 'a premissa detalhada é método, e não ocupa uma das três razões abertas');
    expect(_texto('O que derrubaria esta leitura'), findsOneWidget,
        reason: 'veredito vem com o que o derrubaria, em todos os níveis');
    expect(_texto('O que muda a classificação'), findsOneWidget);

    await _abrirAGaveta(tester);
    expect(_texto('Na conta, a taxa exigida'), findsOneWidget,
        reason: 'o nível de detalhe muda o que vem aberto, e nada é escondido');
  });

  testWidgets('a margem de segurança sai em palavras e em reais', (tester) async {
    await _abrirNoEssencial(tester, _acao);

    final margem = tester.widget<FiMeasure>(find.byType(FiMeasure));
    expect(margem.note, contains('${formatCurrency(1.55)} abaixo do piso do preço justo'),
        reason: 'um percentual negativo de margem não diz nada a quem começou agora; a '
            'distância em reais até a borda diz');
    expect(margem.note, contains('confirmada por outro dado'));
  });

  testWidgets('tocar no termo abre o verbete', (tester) async {
    await _abrirNoEssencial(tester, _acao);

    await tester.tap(find.text('Margem de segurança'));
    for (var i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 120));
    }

    expect(find.text(glossary['ms']!), findsOneWidget);
  });
}
