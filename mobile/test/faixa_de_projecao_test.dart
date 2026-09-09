import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/widgets/range.dart';

Future<void> _montar(WidgetTester tester, Widget filho) async {
  await tester.pumpWidget(
    MaterialApp(home: Scaffold(body: Center(child: filho))),
  );
}

void main() {
  group('faixa de projeção', () {
    testWidgets('o número projetado sai como faixa, nunca sozinho', (tester) async {
      await _montar(
        tester,
        const FiRange(label: 'Carteira no fim', low: 120000, high: 190000),
      );

      expect(find.textContaining('entre'), findsOneWidget);
      expect(find.textContaining('120.000'), findsOneWidget);
      expect(find.textContaining('190.000'), findsOneWidget);
    });

    testWidgets('o cenário base é legenda sob a faixa, e não o lugar dela', (tester) async {
      await _montar(
        tester,
        const FiRange(
          label: 'Carteira no fim',
          low: 120000,
          high: 190000,
          base: 150000,
        ),
      );

      expect(
        find.textContaining('cenário base'),
        findsOneWidget,
        reason: 'o web mostrava o cenário base e o mobile não — a mesma projeção contava '
            'duas histórias',
      );
      expect(find.textContaining('150.000'), findsOneWidget);
    });

    testWidgets('sem cenário base a legenda some, em vez de sair zerada', (tester) async {
      await _montar(tester, const FiRange(low: 10, high: 20));

      expect(find.textContaining('cenário base'), findsNothing);
    });

    testWidgets('a faixa inteira é anunciada de uma vez ao leitor de tela', (tester) async {
      await _montar(
        tester,
        const FiRange(label: 'Renda passiva/mês no fim', low: 1200, high: 1900),
      );

      final semantics = tester.getSemantics(find.byType(FiRange));
      expect(semantics.label, contains('Renda passiva/mês no fim'));
      expect(
        semantics.label,
        contains('entre'),
        reason: 'piso e teto lidos separados perdem que são as pontas de uma faixa só',
      );
    });
  });
}
