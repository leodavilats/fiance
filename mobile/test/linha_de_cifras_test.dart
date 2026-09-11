import 'package:fiance/core/models.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/features/market/opportunities_tab.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// A linha de cifras de uma oportunidade, medida em vez de conferida no olho.
///
/// As quatro colunas saíam em três alturas: o rótulo com verbete descia porque o alvo de 44dp
/// era só dele, "PREÇO JUSTO" quebrava em duas linhas, e a base do número existia em duas
/// colunas e faltava nas outras duas.
void main() {
  Opportunity amostra() => Opportunity.fromJson(const {
    'ticker': 'ARRI11',
    'name': 'Fundo de Investimento Imobiliario Atrio Reit Recebiveis',
    'price': 4.55,
    'fair_price': 10.03,
    'margin_of_safety': 0.5464,
    'dividend_yield': 20.66,
    'score': 100.0,
    'verdict': 'BUY',
    'label': 'Comprar',
    'consensus_methods': 1,
    'data_years': 5,
    'data_completeness': 1.0,
  });

  Future<void> montar(WidgetTester tester, double largura) async {
    tester.view.physicalSize = Size(largura, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          theme: buildAppTheme(Brightness.dark),
          home: Scaffold(
            body: ListView(
              padding: const EdgeInsets.all(FiLayout.gutter),
              children: [FiOpportunityObject(opportunity: amostra())],
            ),
          ),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 300));
  }

  /// O topo de cada rotulo, por texto exato -- "DY" tambem aparece dentro da legenda de base.
  Set<double> toposExatos(WidgetTester tester, List<String> textos) => {
    for (final texto in textos) tester.getTopLeft(find.text(texto)).dy,
  };

  Set<double> toposParciais(WidgetTester tester, List<String> trechos) => {
    for (final trecho in trechos)
      tester.getTopLeft(find.textContaining(trecho)).dy,
  };

  for (final largura in [320.0, 390.0]) {
    testWidgets('as cifras compartilham a linha de base em ${largura.toInt()}dp', (
      tester,
    ) async {
      await montar(tester, largura);

      expect(
        toposExatos(tester, ['PREÇO', 'JUSTO', 'MARGEM', 'DY']).length,
        1,
        reason: 'os quatro rótulos começam na mesma altura',
      );
      expect(
        toposParciais(tester, ['4,55', '10,03', '54,64%', '20,66%']).length,
        1,
        reason: 'as quatro cifras começam na mesma altura',
      );
      expect(
        tester.takeException(),
        isNull,
        reason: 'nada estoura em ${largura.toInt()}dp',
      );
    });
  }

  testWidgets('a margem de segurança é razão, e sai em percentual', (tester) async {
    await montar(tester, 390);

    expect(
      find.text('54,64%'),
      findsOneWidget,
      reason:
          '`margin_of_safety` chega como razão — 0,5464 se lê 54,64%. Passava pelo mesmo '
          '`formatPercent` do dividend yield, que já vem em percentual, e saía como 0,55%',
    );
  });

  testWidgets('a base de cada número continua na tela', (tester) async {
    await montar(tester, 390);

    expect(find.textContaining('1 método no consenso'), findsOneWidget);
    expect(find.textContaining('5 anos de proventos'), findsOneWidget);
  });
}
