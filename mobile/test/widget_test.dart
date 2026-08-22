import 'package:fiance/features/auth/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
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
