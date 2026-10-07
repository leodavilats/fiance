import 'labels.dart';
import 'models.dart';
import 'format.dart';
import 'score_ruler.dart' show fairBandLabel;

const fiCompareStocks = {'br_stock', 'bdr'};
const fiCompareWithPatrimony = {'br_stock', 'bdr', 'fii'};
const fiCompareAll = {'br_stock', 'bdr', 'fii', 'etf'};

const fiAssetTypeLabel = {
  'br_stock': 'ação',
  'bdr': 'recibo de ação estrangeira (BDR)',
  'fii': 'fundo imobiliário (FII)',
  'etf': 'fundo de índice (ETF)',
  'renda_fixa': 'renda fixa',
};

class FiCompareMetric {
  const FiCompareMetric(this.label, this.group, this.appliesTo, this.render);

  final String label;
  final String group;
  final Set<String> appliesTo;
  final String Function(AssetAnalysis) render;
}

String _fmtPct(double? v) => formatPercent(v, digits: 1);

final fiCompareMetrics = <FiCompareMetric>[
  FiCompareMetric(
    'Preço',
    'Preço e valor',
    fiCompareAll,
    (a) => formatCurrency(a.price),
  ),
  FiCompareMetric(
    'Faixa de preço justo',
    'Preço e valor',
    fiCompareAll,
    (a) => fairBandLabel(a.fairLow, a.fairHigh),
  ),
  FiCompareMetric(
    'Preço sobre lucro (P/L)',
    'Preço e valor',
    fiCompareStocks,
    (a) => formatDecimal(a.fundamentals['pe_ratio']),
  ),
  FiCompareMetric(
    'Preço sobre valor patrimonial (P/VP)',
    'Preço e valor',
    fiCompareWithPatrimony,
    (a) => formatDecimal(a.fundamentals['pb_ratio'], digits: 2),
  ),
  FiCompareMetric(
    'Retorno sobre o patrimônio (ROE)',
    'Qualidade',
    fiCompareStocks,
    (a) => _fmtPct(a.fundamentals['roe']),
  ),
  FiCompareMetric(
    'Margem líquida',
    'Qualidade',
    fiCompareStocks,
    (a) => _fmtPct(a.fundamentals['profit_margin']),
  ),
  FiCompareMetric(
    'Dívida / Patrimônio',
    'Dívida',
    fiCompareStocks,
    (a) => _fmtPct(a.fundamentals['debt_to_equity']),
  ),
  FiCompareMetric(
    'Força relativa (RSI, 0 a 100)',
    'O que o preço vem fazendo',
    fiCompareAll,
    (a) => formatDecimal(a.rsi14, digits: 0),
  ),
  FiCompareMetric(
    'Tendência',
    'O que o preço vem fazendo',
    fiCompareAll,
    (a) => trendLabel(a.trend),
  ),
  FiCompareMetric(
    'Dividendos ao ano (DY)',
    'Proventos',
    fiCompareAll,
    (a) => _fmtPct(a.fundamentals['dividend_yield']),
  ),
];
