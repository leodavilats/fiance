import 'package:intl/intl.dart';

final _currency = NumberFormat.currency(locale: 'pt_BR', symbol: 'R\$');
final _percent = NumberFormat('##0.00', 'pt_BR');
final _dayFormat = DateFormat('dd/MM/yyyy');
final _quantityFormat = NumberFormat('#,##0.########', 'pt_BR');
final _inputFormat = NumberFormat('0.########', 'pt_BR');
final _numeroDigitado = RegExp(r'^-?[0-9.,]+$');

String formatCurrency(double? value) => _currency.format(value ?? 0);

String formatDecimal(double? value, {int digits = 1}) => value == null
    ? '—'
    : NumberFormat.decimalPatternDigits(locale: 'pt_BR', decimalDigits: digits).format(value);

String formatPercent(double? value, {int? digits}) {
  if (value == null) return '—';
  if (digits == null) return '${_percent.format(value)}%';
  return '${formatDecimal(value, digits: digits)}%';
}

String formatPoints(double? value, {int digits = 1}) =>
    value == null ? '—' : '${formatDecimal(value, digits: digits)} p.p.';

String formatForInput(double? value) => value == null ? '' : _inputFormat.format(value);

double? parseDecimal(String? text) {
  final limpo = (text ?? '').replaceAll(RegExp(r'R\$|%|\s'), '');
  if (limpo.isEmpty || !_numeroDigitado.hasMatch(limpo)) return null;

  if (limpo.contains(',')) {
    if (limpo.indexOf(',') != limpo.lastIndexOf(',')) return null;
    final [inteiro, fracao] = limpo.split(',');
    if (fracao.contains('.')) return null;
    if (inteiro.contains('.') && !_milharValido(inteiro)) return null;
    return double.tryParse('${inteiro.replaceAll('.', '')}.$fracao');
  }

  final partes = limpo.split('.');
  if (partes.length == 2 && partes.last.length != 3) return double.tryParse(limpo);
  if (partes.length > 1 && !_milharValido(limpo)) return null;
  return double.tryParse(limpo.replaceAll('.', ''));
}

bool _milharValido(String inteiro) =>
    RegExp(r'^-?[0-9]{1,3}(\.[0-9]{3})+$').hasMatch(inteiro);

String formatDate(String? isoDate) {
  if (isoDate == null || isoDate.length < 10) return '—';
  final data = DateTime.tryParse(isoDate.substring(0, 10));
  return data == null ? isoDate : _dayFormat.format(data);
}

String formatQuantity(double? value) =>
    value == null ? '—' : _quantityFormat.format(value);

String formatRatio(double? ratio) =>
    ratio == null ? '—' : formatPercent(ratio * 100);

String formatAge(double? epochSegundos) {
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

double? oldestStamp(Iterable<double?> stamps) {
  final validos = stamps.whereType<double>().where((c) => c > 0);
  if (validos.isEmpty) return null;
  return validos.reduce((a, b) => a < b ? a : b);
}
