import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/main.dart';

void main() {
  testWidgets('App inicia na tela de login', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: FianceApp()));
    await tester.pumpAndSettle();

    expect(find.text('fiance'), findsOneWidget);
    expect(find.text('Entrar com Google'), findsOneWidget);
  });
}
