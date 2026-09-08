import 'cash_models.dart';
import 'product_rules.dart';

/// A leitura do mes. Espelha `web/src/app/core/month-verdict.ts`.
///
/// A banda sai de `fiMonthPressureBands`: nenhum limiar se decide aqui.
class VereditoDoMes {
  const VereditoDoMes({
    required this.band,
    required this.pressao,
    required this.veredito,
    required this.razao,
  });

  final FiScoreBand band;

  /// Quanto do que entrou ja esta comprometido, em %. `null` sem o que dividir.
  final int? pressao;

  final String veredito;
  final String razao;
}

/// Sem entrada lancada a banda e a de leitura ausente: dividir por zero daria "Mes folgado".
///
/// Divida caseira nao muda a banda, so assume a razao.
VereditoDoMes vereditoDoMes({
  required double recebido,
  required double comprometido,
  Debt? dividaCara,
}) {
  if (recebido <= 0) {
    return VereditoDoMes(
      band: fiBandFor(0, fiMonthPressureBands, 0),
      pressao: null,
      veredito: 'Ainda não há entrada lançada neste mês',
      razao: 'Sem o que entrou não há como medir o que está comprometido.',
    );
  }

  final pressao = (comprometido / recebido * 100).round().clamp(0, 100);
  final band = fiBandFor(pressao.toDouble(), fiMonthPressureBands);

  if (dividaCara != null) {
    final taxa = dividaCara.monthlyRate == null
        ? ''
        : ' a ${_semZeroInutil(dividaCara.monthlyRate!)}% ao mês';
    return VereditoDoMes(
      band: band,
      pressao: pressao,
      veredito: band.label,
      razao:
          'O comprometido consome $pressao% do que entrou, e ${dividaCara.description}$taxa '
          'come a sobra antes de qualquer aporte.',
    );
  }

  return VereditoDoMes(
    band: band,
    pressao: pressao,
    veredito: band.label,
    razao: 'O comprometido consome $pressao% do que entrou.',
  );
}

/// `14.9` -> `14,9`; `2.0` -> `2`.
String _semZeroInutil(double v) {
  final texto = v == v.roundToDouble()
      ? v.toStringAsFixed(0)
      : v.toStringAsFixed(2).replaceFirst(RegExp(r'0$'), '');
  return texto.replaceAll('.', ',');
}
