import 'labels.dart';
import 'models.dart';
import 'format.dart';

const fiCompareAcoes = {'br_stock', 'bdr'};
const fiCompareComPatrimonio = {'br_stock', 'bdr', 'fii'};
const fiCompareTodas = {'br_stock', 'bdr', 'fii', 'etf'};

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
    fiCompareTodas,
    (a) => formatCurrency(a.price),
  ),
  FiCompareMetric(
    'Preço justo (consenso)',
    'Valuation',
    fiCompareTodas,
    (a) => formatCurrency(a.consensus),
  ),
  FiCompareMetric(
    'P/L',
    'Valuation',
    fiCompareAcoes,
    (a) => a.fundamentals['pe_ratio']?.toStringAsFixed(1) ?? '—',
  ),
  FiCompareMetric(
    'P/VP',
    'Valuation',
    fiCompareComPatrimonio,
    (a) => a.fundamentals['pb_ratio']?.toStringAsFixed(2) ?? '—',
  ),
  FiCompareMetric(
    'ROE',
    'Qualidade',
    fiCompareAcoes,
    (a) => _fmtPct(a.fundamentals['roe']),
  ),
  FiCompareMetric(
    'Margem líquida',
    'Qualidade',
    fiCompareAcoes,
    (a) => _fmtPct(a.fundamentals['profit_margin']),
  ),
  FiCompareMetric(
    'Dívida / Patrimônio',
    'Risco',
    fiCompareAcoes,
    (a) => _fmtPct(a.fundamentals['debt_to_equity']),
  ),
  FiCompareMetric(
    'RSI (14)',
    'Risco',
    fiCompareTodas,
    (a) => a.rsi14?.toStringAsFixed(0) ?? '—',
  ),
  FiCompareMetric('Tendência', 'Risco', fiCompareTodas, (a) => trendLabel(a.trend)),
  FiCompareMetric(
    'Dividend Yield',
    'Proventos',
    fiCompareTodas,
    (a) => _fmtPct(a.fundamentals['dividend_yield']),
  ),
];
