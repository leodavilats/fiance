import 'labels.dart';
import 'models.dart';
import 'format.dart';

const fiCompareStocks = {'br_stock', 'bdr'};
const fiCompareWithPatrimony = {'br_stock', 'bdr', 'fii'};
const fiCompareAll = {'br_stock', 'bdr', 'fii', 'etf'};

const fiAssetTypeLabel = {
  'br_stock': 'ação BR',
  'bdr': 'BDR',
  'fii': 'FII',
  'etf': 'ETF',
  'renda_fixa': 'renda fixa',
};

class FiCompareMetric {
  const FiCompareMetric(this.label, this.group, this.appliesTo, this.render);

  final String label;
  final String group;
  final Set<String> appliesTo;
  final String Function(AssetAnalysis) render;
}

String _fmtPct(double? v) => v == null ? '—' : '${v.toStringAsFixed(1)}%';

final fiCompareMetrics = <FiCompareMetric>[
  FiCompareMetric(
    'Preço',
    'Valuation',
    fiCompareAll,
    (a) => formatCurrency(a.price),
  ),
  FiCompareMetric(
    'Preço justo (consenso)',
    'Valuation',
    fiCompareAll,
    (a) => formatCurrency(a.consensus),
  ),
  FiCompareMetric(
    'P/L',
    'Valuation',
    fiCompareStocks,
    (a) => a.fundamentals['pe_ratio']?.toStringAsFixed(1) ?? '—',
  ),
  FiCompareMetric(
    'P/VP',
    'Valuation',
    fiCompareWithPatrimony,
    (a) => a.fundamentals['pb_ratio']?.toStringAsFixed(2) ?? '—',
  ),
  FiCompareMetric(
    'ROE',
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
    'Risco',
    fiCompareStocks,
    (a) => _fmtPct(a.fundamentals['debt_to_equity']),
  ),
  FiCompareMetric(
    'RSI (14)',
    'Risco',
    fiCompareAll,
    (a) => a.rsi14?.toStringAsFixed(0) ?? '—',
  ),
  FiCompareMetric('Tendência', 'Risco', fiCompareAll, (a) => trendLabel(a.trend)),
  FiCompareMetric(
    'Dividend Yield',
    'Proventos',
    fiCompareAll,
    (a) => _fmtPct(a.fundamentals['dividend_yield']),
  ),
];
