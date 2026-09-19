import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/providers.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/features/patrimony/ledger_screen.dart';

void main() {
  testWidgets('a folha de filtros recorta o razão e sabe se desfazer', (tester) async {
    tester.view.physicalSize = const Size(390, 844) * 2;
    tester.view.devicePixelRatio = 2;
    addTearDown(tester.view.reset);

    late WidgetRef ref;

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          theme: buildAppTheme(Brightness.light),
          home: Consumer(
            builder: (context, r, _) {
              ref = r;
              return Scaffold(
                body: Builder(
                  builder: (context) => TextButton(
                    onPressed: () => openLedgerFilterSheet(context),
                    child: const Text('abrir'),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('abrir'));
    await tester.pumpAndSettle();

    expect(
      find.text('Recortar o razão'),
      findsOneWidget,
      reason: 'o recorte virou um botão só, e é esta folha que ele abre',
    );

    await tester.tap(find.text('Este mês'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Compras'));
    await tester.pumpAndSettle();

    expect(
      ref.read(ledgerFilterProvider).activeCount,
      2,
      reason: 'período e tipo contam separado, e é esse número que a barra mostra',
    );

    await tester.ensureVisible(find.text('Limpar o recorte'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Limpar o recorte'));
    await tester.pumpAndSettle();

    expect(
      ref.read(ledgerFilterProvider).isEmpty,
      isTrue,
      reason: 'sem uma saída para o recorte inteiro, a lista some e não volta',
    );

    await tester.ensureVisible(find.text('Ver os lançamentos'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ver os lançamentos'));
    await tester.pumpAndSettle();

    expect(find.text('Recortar o razão'), findsNothing);
  });
}
