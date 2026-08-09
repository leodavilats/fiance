import 'package:intl/intl.dart';

final _currency = NumberFormat.currency(locale: 'pt_BR', symbol: 'R\$');
final _percent = NumberFormat('##0.00', 'pt_BR');

String formatCurrency(double? value) => _currency.format(value ?? 0);

String formatPercent(double? value) =>
    value == null ? '—' : '${_percent.format(value)}%';
