import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/models.dart';
import 'package:fiance/features/surplus/allocation_drift_screen.dart';

AllocationGap _gap({required double current, required double meta}) {
  return AllocationGap.fromJson({
    'category': 'acoes_br',
    'current_pct': current,
    'target_pct': meta,
    'gap_pct': meta - current,
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
        _gap(current: 12, meta: 20),
        _gap(current: 8, meta: 15),
      ];

      final scale = gapScale(gaps);

      expect(scale, lessThan(100));
      expect(20 / scale, greaterThan(0.5));
    });

    test('a régua é a mesma para todas as linhas, então elas se comparam', () {
      final gaps = [
        _gap(current: 40, meta: 50),
        _gap(current: 5, meta: 10),
      ];

      final scale = gapScale(gaps);

      expect(50 / scale, greaterThan(10 / scale));
      expect(scale, greaterThanOrEqualTo(50));
    });

    test('a escala acomoda o maior valor, atual ou meta', () {
      expect(gapScale([_gap(current: 80, meta: 20)]), greaterThanOrEqualTo(80));
      expect(gapScale([_gap(current: 20, meta: 80)]), greaterThanOrEqualTo(80));
    });

    test('nunca passa de 100% nem colapsa numa carteira vazia', () {
      expect(gapScale([_gap(current: 95, meta: 100)]), lessThanOrEqualTo(100));
      expect(gapScale([]), 100);
      expect(gapScale([_gap(current: 0, meta: 0)]), 100);
    });

    test('meta minúscula ainda tem régua legível', () {
      expect(gapScale([_gap(current: 1, meta: 2)]), greaterThanOrEqualTo(10));
    });
  });
}
