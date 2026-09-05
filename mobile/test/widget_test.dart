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

  testWidgets('Login diz o que o produto é, antes de a pessoa entrar', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: LoginScreen())),
    );
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.textContaining('não consultoria'), findsOneWidget);
    expect(find.textContaining('Não há garantia'), findsOneWidget);
  });

  testWidgets('Login leva ao texto legal antes do consentimento', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      const ProviderScope(child: MaterialApp(home: LoginScreen())),
    );
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('Termos'), findsOneWidget);
    expect(find.text('Política de Privacidade'), findsOneWidget);
  });
}
