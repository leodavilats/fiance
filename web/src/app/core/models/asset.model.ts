import { AssetType, TrendBasis, Verdict } from './common.model';

export interface PricePoint {
  date: string;
  close: number;
}

export interface FairPriceBlock {
  bazin: number | null;
  graham: number | null;
  dcf: number | null;
  consensus: number | null;
  margin_of_safety: number | null;
  avg_dividend_5y: number | null;
  dy_12m: number | null;
  dy_5y: number | null;
  data_years: number;
  desired_yield_used: number;
  pvp: number | null;
  consensus_methods: number;
  details: Record<string, number | null>;
}

export interface TechnicalBlock {
  sma_50: number | null;
  sma_200: number | null;
  rsi_14: number | null;
  trend: string;
  trend_basis: TrendBasis;
  last_price: number | null;
  distance_from_52w_high_pct: number | null;
  distance_from_52w_low_pct: number | null;
}

export interface Falsifier {
  metric: string;
  condition: string;
  becomes: Verdict | string;
  becomes_label: string;
  current: number;
  threshold: number;
  unit: string;
}

export interface DecisionBlock {
  verdict: Verdict;
  label: string;
  confidence: number;
  reasons: string[];
  falsifiers: Falsifier[];
}

export interface AssetFundamentals {
  market_cap: number | null;
  pe_ratio: number | null;
  pb_ratio: number | null;
  eps: number | null;
  book_value: number | null;
  roe: number | null;
  dividend_yield: number | null;
  debt_to_equity: number | null;
  profit_margin: number | null;
  revenue_growth: number | null;
  fifty_two_week_high: number | null;
  fifty_two_week_low: number | null;
}

export interface AssetAnalysis {
  symbol: string;
  asset_type: AssetType;
  name: string | null;
  sector: string | null;
  currency: string | null;
  price: number | null;
  fundamentals: Partial<AssetFundamentals>;
  fair_price: FairPriceBlock;
  technical: TechnicalBlock;
  decision: DecisionBlock;

  price_history: PricePoint[];
}

export interface CompareResponse {
  items: AssetAnalysis[];
  errors: string[];
}
