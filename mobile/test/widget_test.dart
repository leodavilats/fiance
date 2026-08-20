import 'package:fiance/features/auth/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  // Montar a app inteira arrasta o splash, que dispara `authStatusProvider`
  // (leitura de secure storage + delay de 1,1 s) e um indicador em animação
  // contínua: o teste que fazia isso ficava pendurado em pumpAndSettle e
  // falhava por timeout. Testar a tela isolada é determinístico.
  testWidgets('Tela de login oferece entrada com Google', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: LoginScreen())),
    );
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('Continuar com Google'), findsOneWidget);
  });

  testWidgets('Login mostra o disclaimer educativo', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: LoginScreen())),
    );
    await tester.pump(const Duration(milliseconds: 300));

    expect(
      find.textContaining('Não constitui recomendação formal'),
      findsOneWidget,
    );
  });
}
