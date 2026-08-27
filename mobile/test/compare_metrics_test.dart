import 'package:flutter_test/flutter_test.dart';
import 'package:fiance/core/compare_metrics.dart';

void main() {
  FiCompareMetric metric(String label) =>
      fiCompareMetrics.firstWhere((m) => m.label == label);

  group('semântica por classe de ativo', () {
    test('P/L e ROE não se aplicam a FII nem a ETF', () {
      for (final label in ['P/L', 'ROE']) {
        final m = metric(label);
        expect(m.appliesTo.contains('fii'), isFalse, reason: '$label em FII');
        expect(m.appliesTo.contains('etf'), isFalse, reason: '$label em ETF');
        expect(m.appliesTo.contains('br_stock'), isTrue);
      }
    });

    test('P/VP se aplica a FII, porque FII tem patrimônio', () {
      expect(metric('P/VP').appliesTo.contains('fii'), isTrue);
      expect(metric('P/VP').appliesTo.contains('etf'), isFalse);
    });

    test('preço, DY e RSI valem para toda classe de renda variável', () {
      for (final label in ['Preço', 'Dividend Yield', 'RSI (14)']) {
        expect(
          metric(label).appliesTo,
          containsAll(<String>['br_stock', 'bdr', 'fii', 'etf']),
          reason: label,
        );
      }
    });

    test('toda classe suportada tem rótulo legível', () {
      for (final type in ['br_stock', 'bdr', 'fii', 'etf', 'renda_fixa']) {
        expect(fiAssetTypeLabel[type], isNotNull, reason: type);
      }
    });

    test('nenhum indicador é declarado sem classe em que valha', () {
      for (final m in fiCompareMetrics) {
        expect(m.appliesTo, isNotEmpty, reason: m.label);
      }
    });
  });
}
