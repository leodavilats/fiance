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

  group('o número digitado é lido em português, e o ponto do teclado não multiplica', () {
    test('vírgula é decimal e ponto é milhar', () {
      expect(parseDecimal('1.234,56'), 1234.56);
      expect(parseDecimal('12,5'), 12.5);
      expect(parseDecimal('R\$ 1.500,00'), 1500);
    });

    test('ponto sozinho com uma ou duas casas é decimal', () {
      expect(
        parseDecimal('12.50'),
        12.5,
        reason: 'o teclado numérico do Android só oferece ponto; ler "12.50" como 1250 '
            'gravava cem vezes o valor digitado',
      );
      expect(parseDecimal('1500.5'), 1500.5);
    });

    test('ponto com três casas é milhar, como em pt-BR', () {
      expect(parseDecimal('1.000'), 1000);
      expect(parseDecimal('1.000.000'), 1000000);
    });

    test('o que não é número volta nulo, em vez de virar outro número', () {
      expect(parseDecimal('abc'), isNull);
      expect(parseDecimal(''), isNull);
      expect(parseDecimal('1,2,3'), isNull);
      expect(parseDecimal('12.34.5'), isNull);
      expect(parseDecimal('1.5,00'), isNull);
    });

    test('o valor salvo volta ao campo no formato que o campo lê', () {
      expect(formatForInput(1234.5), '1234,5');
      expect(parseDecimal(formatForInput(1234.5)), 1234.5);
      expect(formatForInput(100), '100');
    });
  });

  group('percentual e ponto percentual saem com vírgula', () {
    test('formatPercent aceita casas, e o padrão não muda', () {
      expect(formatPercent(33.04, digits: 1), '33,0%');
      expect(formatPercent(14.9), '14,90%');
    });

    test('formatPoints escreve p.p. em português', () {
      expect(formatPoints(8.66), '8,7 p.p.');
    });
  });
}
