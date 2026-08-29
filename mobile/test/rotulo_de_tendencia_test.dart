import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/labels.dart';

void main() {
  group('rótulo de tendência', () {
    test('as três direções têm nome em português', () {
      expect(trendLabel('uptrend'), '↗ Alta');
      expect(trendLabel('downtrend'), '↘ Baixa');
      expect(trendLabel('sideways'), '→ Lateral');
    });

    test('nenhum valor cru do backend vaza para a tela', () {
      for (final valor in ['uptrend', 'downtrend', 'sideways', 'unknown', '']) {
        expect(trendLabel(valor), isNot(contains(valor.isEmpty ? 'zzz' : valor)));
      }
    });

    test('sem histórico não vira uma quarta direção', () {
      expect(trendLabel('unknown'), 'sem histórico suficiente');
      expect(trendLabel(null), 'sem histórico suficiente');
      expect(trendLabel('qualquer coisa'), 'sem histórico suficiente');
    });
  });
}
