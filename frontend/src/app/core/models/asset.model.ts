import { AssetType, Verdict } from './common.model';

export interface FairPriceBlock {
  bazin: number | null;
  graham: number | null;
  consensus: number | null;
  margin_of_safety: number | null;
  avg_dividend_5y: number | null;
  dy_12m: number | null;
  dy_5y: number | null;
  data_years: number;
  desired_yield_used: number;
  pvp: number | null;
  details: Record<string, number | null>;
}

export interface TechnicalBlock {
  sma_50: number | null;
  sma_200: number | null;
  rsi_14: number | null;
  trend: string;
  last_price: number | null;
  distance_from_52w_high_pct: number | null;
  distance_from_52w_low_pct: number | null;
}

export interface DecisionBlock {
  verdict: Verdict;
  label: string;
  confidence: number;
  reasons: string[];
}

export interface AssetAnalysis {
  symbol: string;
  asset_type: AssetType;
  name: string | null;
  sector: string | null;
  currency: string | null;
  price: number | null;
  fundamentals: Record<string, number | null>;
  fair_price: FairPriceBlock;
  technical: TechnicalBlock;
  decision: DecisionBlock;
}
