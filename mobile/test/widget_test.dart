import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fianceai/main.dart';

void main() {
  testWidgets('App inicia na tela de login', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: FianceAIApp()));
    await tester.pumpAndSettle();

    expect(find.text('fianceAI'), findsOneWidget);
    expect(find.text('Entrar com Google'), findsOneWidget);
  });
}
