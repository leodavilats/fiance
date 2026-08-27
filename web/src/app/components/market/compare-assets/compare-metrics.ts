import { AssetAnalysis, AssetType } from '../../../core';

export type MetricDirection = 'higher' | 'lower' | null;

export type MetricFormat = 'money' | 'pct' | 'ratio' | 'plain';

export interface CompareMetric {
  readonly id: string;
  readonly label: string;
  readonly group: string;
  readonly direction: MetricDirection;
  readonly format: MetricFormat;
  readonly appliesTo: readonly AssetType[];
  readonly value: (item: AssetAnalysis) => number | null;
}

const ACOES: readonly AssetType[] = ['br_stock', 'bdr'];
const COM_PATRIMONIO: readonly AssetType[] = ['br_stock', 'bdr', 'fii'];
const TODAS: readonly AssetType[] = ['br_stock', 'bdr', 'fii', 'etf'];

export const COMPARE_METRICS: readonly CompareMetric[] = [
  {
    id: 'price',
    label: 'Preço',
    group: 'Valuation',
    direction: null,
    format: 'money',
    appliesTo: TODAS,
    value: i => i.price,
  },
  {
    id: 'fair',
    label: 'Preço justo (consenso)',
    group: 'Valuation',
    direction: null,
    format: 'money',
    appliesTo: TODAS,
    value: i => i.fair_price.consensus,
  },
  {
    id: 'pe',
    label: 'P/L',
    group: 'Valuation',
    direction: 'lower',
    format: 'ratio',
    appliesTo: ACOES,
    value: i => i.fundamentals.pe_ratio ?? null,
  },
  {
    id: 'pb',
    label: 'P/VP',
    group: 'Valuation',
    direction: 'lower',
    format: 'ratio',
    appliesTo: COM_PATRIMONIO,
    value: i => i.fundamentals.pb_ratio ?? null,
  },

  {
    id: 'roe',
    label: 'ROE',
    group: 'Qualidade',
    direction: 'higher',
    format: 'pct',
    appliesTo: ACOES,
    value: i => i.fundamentals.roe ?? null,
  },
  {
    id: 'margin',
    label: 'Margem líquida',
    group: 'Qualidade',
    direction: 'higher',
    format: 'pct',
    appliesTo: ACOES,
    value: i => i.fundamentals.profit_margin ?? null,
  },
  {
    id: 'growth',
    label: 'Crescimento de receita',
    group: 'Qualidade',
    direction: 'higher',
    format: 'pct',
    appliesTo: ACOES,
    value: i => i.fundamentals.revenue_growth ?? null,
  },

  {
    id: 'debt',
    label: 'Dívida / Patrimônio',
    group: 'Risco e tendência',
    direction: 'lower',
    format: 'pct',
    appliesTo: ACOES,
    value: i => i.fundamentals.debt_to_equity ?? null,
  },
  {
    id: 'rsi',
    label: 'RSI (14)',
    group: 'Risco e tendência',
    direction: null,
    format: 'plain',
    appliesTo: TODAS,
    value: i => i.technical.rsi_14,
  },
  {
    id: 'from-high',
    label: 'Distância do topo de 52 semanas',
    group: 'Risco e tendência',
    direction: null,
    format: 'pct',
    appliesTo: TODAS,
    value: i => i.technical.distance_from_52w_high_pct,
  },

  {
    id: 'dy12',
    label: 'DY (12 meses)',
    group: 'Proventos',
    direction: 'higher',
    format: 'pct',
    appliesTo: TODAS,
    value: i => (i.fair_price.dy_12m == null ? null : i.fair_price.dy_12m * 100),
  },
  {
    id: 'dy5',
    label: 'DY médio (5 anos)',
    group: 'Proventos',
    direction: 'higher',
    format: 'pct',
    appliesTo: TODAS,
    value: i => (i.fair_price.dy_5y == null ? null : i.fair_price.dy_5y * 100),
  },
];

export const COMPARE_GROUPS: readonly string[] = [
  'Valuation',
  'Qualidade',
  'Risco e tendência',
  'Proventos',
];

export const ASSET_TYPE_LABEL: Readonly<Record<AssetType, string>> = {
  br_stock: 'ação BR',
  bdr: 'BDR',
  fii: 'FII',
  etf: 'ETF',
  renda_fixa: 'renda fixa',
};
