import 'package:flutter_test/flutter_test.dart';
import 'package:fiance/core/format.dart';

void main() {
  group('formatadores não dependem de locale não inicializado', () {
    test('formatDate devolve a data em pt-BR sem initializeDateFormatting', () {
      expect(
        formatDate('2026-09-13'),
        '13/09/2026',
        reason: 'DateFormat com locale explícito exige initializeDateFormatting, que o '
            'aplicativo nunca chama — e a exceção só aparece na tela que formata data.',
      );
    });

    test('formatDate aceita carimbo com hora e devolve só o dia', () {
      expect(formatDate('2026-01-05T13:45:00Z'), '05/01/2026');
    });

    test('formatDate sem data não inventa data', () {
      expect(formatDate(null), '—');
      expect(formatDate(''), '—');
    });

    test('formatQuantity escreve número em português', () {
      expect(formatQuantity(1500), '1.500');
      expect(formatQuantity(10.5), '10,5');
    });

    test('formatCurrency escreve real em português', () {
      expect(formatCurrency(120000), contains('120.000'));
    });
  });
}
