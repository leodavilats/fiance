import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/score_ruler.dart';

void main() {
  for (final tamanho in [ScoreRulerSize.inline, ScoreRulerSize.list, ScoreRulerSize.card]) {
    testWidgets('a trilha da régua tem altura no tamanho ${tamanho.name}', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: buildAppTheme(Brightness.light),
          home: Scaffold(
            body: SizedBox(width: 300, child: ScoreRuler(score: 78, size: tamanho)),
          ),
        ),
      );

      final faixas = tester.renderObjectList<RenderBox>(
        find.descendant(of: find.byType(ScoreRuler), matching: find.byType(DecoratedBox)),
      );
      expect(faixas, isNotEmpty);
      for (final faixa in faixas) {
        expect(
          faixa.size.height,
          greaterThan(0),
          reason: 'faixa sem filho dentro do Stack encolhia a zero: a régua mostrava só o '
              'marcador, sem a escala que dá sentido a ele',
        );
      }
    });
  }

  test('a nota da margem sai do veredito do servidor, e não de uma régua própria', () {
    expect(
      {
        for (final v in ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL', 'UNKNOWN'])
          v: fiMarginBandForVerdict(v).label,
      },
      {
        'STRONG_BUY': 'Desconto amplo',
        'BUY': 'Algum desconto',
        'HOLD': 'Perto do justo',
        'SELL': 'Acima do justo',
        'STRONG_SELL': 'Acima do justo',
        'UNKNOWN': 'Sem preço justo',
      },
      reason: 'a régua do app começava em 10%, e o servidor em 15%: com 12% a etiqueta dizia '
          '"No preço justo" e a medida, "Algum desconto", na mesma folha',
    );
  });
}
