import {
  AllocationCategory,
  AssetType,
  LegacyPortfolioCategory,
  PortfolioCategory,
  TrendBasis,
  Verdict,
} from './common.model';

export interface PortfolioItem {
  ticker: string;
  quantity: number;
  avg_price: number;
  category?: PortfolioCategory;
}

export interface PortfolioEvaluationRequest {
  items: PortfolioItem[];
}

export interface PortfolioPosition {
  ticker: string;
  name: string | null;
  asset_type: AssetType;
  quantity: number;
  avg_price: number;
  current_price: number | null;
  invested: number;
  current_value: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  fair_price: number | null;
  margin_of_safety: number | null;
  verdict: Verdict;
  label: string;
  /** Proveniência do veredito — antes calculada e descartada. */
  confidence: number;
  data_years: number;
  consensus_methods: number;
  trend_basis: TrendBasis;
  as_of: number | null;
  reasons: string[];
  category: LegacyPortfolioCategory;
  category_resolved: AllocationCategory;
  dividend_yield: number | null;
  sector: string | null;
}

export interface PortfolioEvaluationResponse {
  positions: PortfolioPosition[];
  total_invested: number;
  total_current: number;
  total_pnl: number;
  total_pnl_pct: number;
  disclaimer: string;
}

export interface StoredPortfolioItem {
  ticker: string;
  quantity: number;
  avg_price: number;
  category: LegacyPortfolioCategory;
  updated_at: number | null;
}

export interface PortfolioSnapshot {
  captured_at: number;
  total_invested: number;
  total_current: number;
  total_pnl: number;
  total_pnl_pct: number;
}

export interface PortfolioStateResponse {
  items: StoredPortfolioItem[];
  last_updated: number | null;
  snapshots: PortfolioSnapshot[];
}

export interface SellRequest {
  ticker: string;
  quantity: number;
  sell_price: number;
  sold_at?: number | null;
}

export interface ClosedTrade {
  id: number;
  ticker: string;
  category: string;
  quantity: number;
  avg_price: number;
  sell_price: number;
  gross_profit: number;
  ir_rate: number;
  ir_amount: number;
  net_profit: number;
  sold_at: number;
}

export interface ClosedTradesResponse {
  trades: ClosedTrade[];
  total_realized_pnl: number;
  total_ir_paid: number;
}
