import 'cash_models.dart';
import 'product_rules.dart';

class MonthVerdict {
  const MonthVerdict({
    required this.band,
    required this.pressure,
    required this.verdict,
    required this.reason,
  });

  final FiScoreBand band;

  final int? pressure;

  final String verdict;
  final String reason;
}

MonthVerdict monthVerdict({
  required double received,
  required double committed,
  Debt? expensiveDebt,
}) {
  if (received <= 0) {
    return MonthVerdict(
      band: fiBandFor(0, fiMonthPressureBands, 0),
      pressure: null,
      verdict: 'Ainda não há entrada lançada neste mês',
      reason: 'Sem o que entrou não há como medir o que está comprometido.',
    );
  }

  final pressure = (committed / received * 100).round().clamp(0, 100);
  final band = fiBandFor(pressure.toDouble(), fiMonthPressureBands);

  if (expensiveDebt != null) {
    final taxa = expensiveDebt.monthlyRate == null
        ? ''
        : ' a ${_trimTrailingZero(expensiveDebt.monthlyRate!)}% ao mês';
    return MonthVerdict(
      band: band,
      pressure: pressure,
      verdict: band.label,
      reason:
          'O comprometido consome $pressure% do que entrou, e ${expensiveDebt.description}$taxa '
          'come a sobra antes de qualquer aporte.',
    );
  }

  return MonthVerdict(
    band: band,
    pressure: pressure,
    verdict: band.label,
    reason: 'O comprometido consome $pressure% do que entrou.',
  );
}

String _trimTrailingZero(double v) {
  final texto = v == v.roundToDouble()
      ? v.toStringAsFixed(0)
      : v.toStringAsFixed(2).replaceFirst(RegExp(r'0$'), '');
  return texto.replaceAll('.', ',');
}
