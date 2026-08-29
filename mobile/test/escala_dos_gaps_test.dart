import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/models.dart';
import 'package:fiance/features/estrategia/estrategia_screen.dart';

AllocationGap _gap({required double atual, required double meta}) {
  return AllocationGap.fromJson({
    'category': 'acoes_br',
    'current_pct': atual,
    'target_pct': meta,
    'gap_pct': meta - atual,
    'current_value': 0.0,
    'target_value': 0.0,
    'gap_value': 0.0,
    'action': 'Comprar',
  });
}

void main() {
  group('escala compartilhada das barras de meta', () {
    test('a maior barra ocupa a régua em vez de se espremer no canto', () {
      final gaps = [
        _gap(atual: 12, meta: 20),
        _gap(atual: 8, meta: 15),
      ];

      final escala = escalaDosGaps(gaps);

      expect(escala, lessThan(100));
      expect(20 / escala, greaterThan(0.5));
    });

    test('a régua é a mesma para todas as linhas, então elas se comparam', () {
      final gaps = [
        _gap(atual: 40, meta: 50),
        _gap(atual: 5, meta: 10),
      ];

      final escala = escalaDosGaps(gaps);

      expect(50 / escala, greaterThan(10 / escala));
      expect(escala, greaterThanOrEqualTo(50));
    });

    test('a escala acomoda o maior valor, atual ou meta', () {
      expect(escalaDosGaps([_gap(atual: 80, meta: 20)]), greaterThanOrEqualTo(80));
      expect(escalaDosGaps([_gap(atual: 20, meta: 80)]), greaterThanOrEqualTo(80));
    });

    test('nunca passa de 100% nem colapsa numa carteira vazia', () {
      expect(escalaDosGaps([_gap(atual: 95, meta: 100)]), lessThanOrEqualTo(100));
      expect(escalaDosGaps([]), 100);
      expect(escalaDosGaps([_gap(atual: 0, meta: 0)]), 100);
    });

    test('meta minúscula ainda tem régua legível', () {
      expect(escalaDosGaps([_gap(atual: 1, meta: 2)]), greaterThanOrEqualTo(10));
    });
  });
}
