import 'package:intl/intl.dart';

final _currency = NumberFormat.currency(locale: 'pt_BR', symbol: 'R\$');
final _percent = NumberFormat('##0.00', 'pt_BR');

String formatCurrency(double? value) => _currency.format(value ?? 0);

String formatPercent(double? value) =>
    value == null ? '—' : '${_percent.format(value)}%';

String formatRatio(double? ratio) =>
    ratio == null ? '—' : formatPercent(ratio * 100);

String formatIdade(double? epochSegundos) {
  if (epochSegundos == null || epochSegundos <= 0) return '';

  final minutos = DateTime.now()
      .difference(
        DateTime.fromMillisecondsSinceEpoch((epochSegundos * 1000).round()),
      )
      .inMinutes;

  if (minutos < 1) return 'agora';
  if (minutos < 60) return 'há $minutos min';
  if (minutos < 60 * 24) return 'há ${minutos ~/ 60} h';
  return 'em ${DateFormat('dd/MM/yyyy').format(DateTime.fromMillisecondsSinceEpoch((epochSegundos * 1000).round()))}';
}

double? carimboMaisAntigo(Iterable<double?> carimbos) {
  final validos = carimbos.whereType<double>().where((c) => c > 0);
  if (validos.isEmpty) return null;
  return validos.reduce((a, b) => a < b ? a : b);
}
