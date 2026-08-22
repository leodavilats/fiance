import { PortfolioPosition, PortfolioSnapshot } from './portfolio.model';
import { Opportunity } from './opportunity.model';
import { ActionKind } from './whats-new.model';

export interface Alert {
  severity: 'info' | 'warning' | 'critical';
  kind: 'sell_target' | 'opportunity' | 'concentration' | 'rebalance';
  title: string;
  detail: string;
  ticker?: string | null;
  count: number;
  tickers: string[];
  action: ActionKind | null;
  action_label: string | null;
}

export interface DataFreshness {
  rates_source: string;
  market_data_age_seconds: number | null;
  market_data_stale: boolean;
  quotes_ttl_seconds: number;
}

export interface PortfolioHealth {
  score: number;
  concentration_score: number;
  sector_concentration_score: number;
  diversification_score: number;
  risk_score: number;
  top_position_ticker: string | null;
  top_position_pct: number | null;
  top_sector: string | null;
  top_sector_pct: number | null;
  warnings: string[];
}

export interface CategoryAllocation {
  category: string;
  current_value: number;
  current_pct: number;
  target_pct: number | null;
  delta_pct: number | null;
  delta_value: number | null;
}

export interface DashboardSummary {
  total_invested: number;
  total_current: number;
  total_pnl: number;
  total_pnl_pct: number;

  monthly_dividends_estimate: number;
  yearly_dividends_estimate: number;
  portfolio_yield: number | null;
  passive_income_goal?: number | null;
  passive_income_progress?: number | null;

  positions_count: number;
}

export interface DashboardResponse {
  summary: DashboardSummary;
  positions: PortfolioPosition[];
  top_buys: Opportunity[];
  top_sells: PortfolioPosition[];
  alerts: Alert[];
  allocations: CategoryAllocation[];
  snapshots: PortfolioSnapshot[];
  health: PortfolioHealth | null;
  freshness: DataFreshness | null;
  last_updated: number | null;
  disclaimer: string;
}
