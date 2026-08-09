import { AssetType, Verdict, PortfolioCategory } from './common.model';

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
  reasons: string[];
  category: 'auto' | 'renda' | 'trade';
  category_resolved: 'renda' | 'trade';
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
  category: 'auto' | 'renda' | 'trade';
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
