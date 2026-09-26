import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/format.dart';
import 'package:fiance/core/widgets/controls.dart';

void main() {
  testWidgets('o interruptor diz o nome do que liga', (tester) async {
    final semantica = tester.ensureSemantics();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FiSwitch(label: 'Tema escuro', value: true, onChanged: (_) {}),
        ),
      ),
    );

    expect(
      tester.getSemantics(find.byType(FiSwitch)),
      matchesSemantics(
        label: 'Tema escuro',
        hasToggledState: true,
        isToggled: true,
        hasEnabledState: true,
        isEnabled: true,
        isFocusable: true,
        hasTapAction: true,
        hasFocusAction: true,
      ),
      reason: 'o Switch solto no fim da linha era anunciado como "ligado", sem dizer o quê',
    );
    semantica.dispose();
  });

  testWidgets('o controle deslizante fala o número em português', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FiSlider(
            label: 'Dividend yield mínimo',
            value: 5.5,
            min: 0,
            max: 20,
            format: formatPercent,
            onChanged: (_) {},
          ),
        ),
      ),
    );

    final slider = tester.widget<Slider>(find.byType(Slider));
    expect(
      slider.semanticFormatterCallback!(5.5),
      'Dividend yield mínimo: 5,50%',
      reason: 'o rótulo antigo era 5.5%, com ponto: número em português é do formatador',
    );
    expect(slider.label, '5,50%');
  });
}
