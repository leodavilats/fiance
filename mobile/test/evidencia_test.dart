import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/widgets/evidence.dart';

void main() {
  const razoes = [
    'O preço está 20% abaixo do piso da faixa.',
    'Vale cerca de R\$ 12 pelo lucro distribuível.',
    'Pelos dividendos, R\$ 11: dentro da faixa.',
    'Qualidade da faixa: firme.',
  ];

  testWidgets('a evidência mostra os três primeiros motivos sem abrir nada', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: FiEvidence(reasons: razoes))),
    );

    expect(find.text(razoes[0]), findsOneWidget);
    expect(find.text(razoes[2]), findsOneWidget);
    expect(
      find.text(razoes[3]),
      findsNothing,
      reason: 'nível 2 é o porquê em poucas linhas; o resto fica no método, mais abaixo',
    );
  });

  test('o resto da leitura começa onde a evidência para', () {
    expect(FiEvidence.rest(razoes), [razoes[3]]);
    expect(FiEvidence.rest(razoes.take(2).toList()), isEmpty);
  });

  testWidgets('sem motivo, a evidência não desenha nada', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: FiEvidence(reasons: []))));

    expect(find.byType(Text), findsNothing);
  });
}
