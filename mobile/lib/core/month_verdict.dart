import 'cash_models.dart';
import 'format.dart';
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

  final bruto = (committed / received * 100).round();
  final pressure = bruto.clamp(0, 100);
  final band = fiBandFor(pressure.toDouble(), fiMonthPressureBands);
  final frase = bruto > 100
      ? 'O comprometido passa do que entrou: equivale a '
            '${formatDecimal(bruto.toDouble(), digits: 0)}% da entrada.'
      : 'O comprometido consome $pressure% do que entrou.';

  if (expensiveDebt != null) {
    final taxa = expensiveDebt.monthlyRate == null
        ? ''
        : ', que custa ${_trimTrailingZero(expensiveDebt.monthlyRate!)}% ao mês';
    return MonthVerdict(
      band: band,
      pressure: pressure,
      verdict: band.label,
      reason:
          '$frase A sobra, porém, vai antes para ${expensiveDebt.description}$taxa.',
    );
  }

  return MonthVerdict(
    band: band,
    pressure: pressure,
    verdict: band.label,
    reason: frase,
  );
}

String _trimTrailingZero(double v) => v == v.roundToDouble()
    ? formatDecimal(v, digits: 0)
    : formatDecimal(v, digits: 2).replaceFirst(RegExp(r'0$'), '');
