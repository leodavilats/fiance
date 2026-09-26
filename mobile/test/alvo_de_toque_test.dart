import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/theme.dart';
import 'package:fiance/core/widgets/button.dart';
import 'package:fiance/core/widgets/chip.dart';
import 'package:fiance/core/widgets/data_row.dart';
import 'package:fiance/core/widgets/disclosure.dart';
import 'package:fiance/core/widgets/help_tooltip.dart';
import 'package:fiance/core/widgets/provenance.dart';
import 'package:fiance/core/widgets/segments.dart';

Future<void> _montar(WidgetTester tester, Widget filho) => tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(Brightness.light),
        home: Scaffold(
          body: SingleChildScrollView(
            child: Padding(padding: const EdgeInsets.all(24), child: filho),
          ),
        ),
      ),
    );

void main() {
  final componentes = <String, Widget>{
    'FiButton.primary': FiButton.primary(label: 'Salvar', onPressed: () {}),
    'FiButton.secondary': FiButton.secondary(label: 'Voltar', onPressed: () {}),
    'FiButton.quiet': FiButton.quiet(label: 'Pular', onPressed: () {}),
    'FiChoiceChip': Wrap(
      children: [FiChoiceChip(label: 'FIIs', selected: false, onSelected: () {})],
    ),
    'FiDataRow com toque': FiDataRow(label: 'PETR4', value: 'R\$ 38,00', onTap: () {}),
    'FiDisclosure': const FiDisclosure(title: 'Ver os números', child: Text('x')),
    'FiGroupDisclosure': const FiGroupDisclosure(label: 'Ações', count: 3, child: Text('x')),
    'FiSegments': FiSegments<int>(
      selected: 0,
      options: const {0: 'Mês', 1: 'Ano'},
      onSelect: (_) {},
    ),
    'HelpTooltip': const HelpTooltip(termKey: 'score', label: 'Score'),
    'FiProvenance': const FiProvenance(method: 'Lucro distribuível descontado'),
  };

  for (final entrada in componentes.entries) {
    testWidgets('${entrada.key} tem alvo de toque de 44dp', (tester) async {
      final semantica = tester.ensureSemantics();
      await _montar(tester, entrada.value);

      expect(
        find.semantics.byAction(SemanticsAction.tap),
        findsWidgets,
        reason: 'sem ação de toque na semântica, a diretriz de alvo nem enxerga o controle, e o '
            'leitor de tela não consegue apertá-lo',
      );
      await expectLater(
        tester,
        meetsGuideline(iOSTapTargetGuideline),
        reason: 'dedo não é cursor: abaixo de 44dp o toque erra o alvo, e quem tem tremor ou '
            'usa o celular andando não acerta',
      );
      semantica.dispose();
    });
  }

  testWidgets('o chip se ativa pelo leitor de tela', (tester) async {
    final semantica = tester.ensureSemantics();
    var tocado = false;
    await _montar(
      tester,
      FiChoiceChip(label: 'FIIs', selected: false, onSelected: () => tocado = true),
    );

    expect(
      tester.getSemantics(find.byType(FiChoiceChip)),
      matchesSemantics(
        label: 'FIIs',
        isButton: true,
        hasSelectedState: true,
        hasTapAction: true,
      ),
      reason: 'o chip cobria o InkWell com ExcludeSemantics e ficava sem ação: um leitor de tela '
          'anunciava o botão e não conseguia apertá-lo, e a diretriz de alvo nem o enxergava',
    );
    expect(tester.getSize(find.byType(FiChoiceChip)).height, greaterThanOrEqualTo(44));

    tester.semantics.tap(find.semantics.byLabel('FIIs'));
    expect(tocado, isTrue);
    semantica.dispose();
  });
}
