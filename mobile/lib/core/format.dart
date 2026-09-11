import 'package:intl/intl.dart';

final _currency = NumberFormat.currency(locale: 'pt_BR', symbol: 'R\$');
final _percent = NumberFormat('##0.00', 'pt_BR');

String formatCurrency(double? value) => _currency.format(value ?? 0);

String formatPercent(double? value) =>
    value == null ? '—' : '${_percent.format(value)}%';

/// Uma razao (0,546) escrita como percentual (54,6%).
///
/// Existe porque duas unidades chegam do backend com cara de percentual e passavam pelo mesmo
/// `formatPercent`: `margin_of_safety` e `dy_12m` sao **razao** -- `(consenso - preco) / consenso`
/// --, enquanto `dividend_yield` do snapshot ja vem em percentual. A margem saia cem vezes menor,
/// e um papel 54,6% abaixo do preco justo aparecia como 0,55%.
String formatRatio(double? ratio) =>
    ratio == null ? '—' : formatPercent(ratio * 100);

/// Quando o dado foi lido, no espelho de `idadeDoPreco` do web.
///
/// Devolve vazio sem carimbo, para a tela nao ter de decidir isso: momento ausente e diferente
/// de momento zero, e "01/01/1970" seria pior que nao dizer nada.
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

/// O carimbo que representa um conjunto: o **mais antigo**.
///
/// Numa lista de trinta preços, dizer a idade do mais novo é prometer frescor que o card de
/// baixo não tem. É o mesmo critério de `opportunity_service.market_data_age_seconds` e do
/// `carimboMaisAntigo` do web.
double? carimboMaisAntigo(Iterable<double?> carimbos) {
  final validos = carimbos.whereType<double>().where((c) => c > 0);
  if (validos.isEmpty) return null;
  return validos.reduce((a, b) => a < b ? a : b);
}
