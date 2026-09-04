import 'package:fiance/core/models.dart';
import 'package:fiance/features/hoje/widgets/hoje_tiles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const rotuloLongo = 'Ver sugestões de ajuste';

  Future<void> montar(WidgetTester tester, Widget filho) async {
    tester.view.physicalSize = const Size(360, 720);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      MaterialApp(home: Scaffold(body: ListView(children: [filho]))),
    );
  }

  testWidgets('a ação fica abaixo do texto, na mesma coluna do título', (
    tester,
  ) async {
    await montar(
      tester,
      const FiInsightTile(
        icon: Icons.balance_outlined,
        color: Colors.blue,
        title: 'FIIs abaixo da meta',
        detail: 'Sua exposição está 7,0 pontos percentuais abaixo do objetivo.',
        actionLabel: rotuloLongo,
      ),
    );

    final titulo = tester.getRect(find.text('FIIs abaixo da meta'));
    final acao = tester.getRect(find.text('$rotuloLongo →'));

    expect(acao.left, titulo.left);
    expect(acao.top, greaterThan(titulo.bottom));
  });

  testWidgets('o título ocupa a linha inteira, sem disputar com o botão', (
    tester,
  ) async {
    await montar(
      tester,
      const FiInsightTile(
        icon: Icons.balance_outlined,
        color: Colors.blue,
        title: 'Um título comprido o bastante para encostar na margem direita',
        detail: 'Detalhe.',
        actionLabel: rotuloLongo,
      ),
    );

    final titulo = tester.getSize(
      find.text('Um título comprido o bastante para encostar na margem direita'),
    );

    expect(titulo.width, greaterThan(280));
  });

  testWidgets('sem rótulo de ação, não sobra botão nem espaço', (tester) async {
    await montar(
      tester,
      FiWhatsNewTile(
        item: WhatsNewItem.fromJson(const {
          'kind': 'patrimony',
          'severity': 'info',
          'title': 'Patrimônio estável',
          'detail': 'Nada relevante mudou.',
        }),
      ),
    );

    expect(find.byType(TextButton), findsNothing);
  });
}
