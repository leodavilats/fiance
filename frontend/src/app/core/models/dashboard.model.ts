import { PortfolioPosition, PortfolioSnapshot } from './portfolio.model';
import { Opportunity } from './opportunity.model';

export interface Alert {
  severity: 'info' | 'warning' | 'critical';
  kind: 'sell_target' | 'opportunity' | 'concentration';
  title: string;
  detail: string;
  ticker?: string | null;
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
  cash_available: number;

  // Métricas de Renda Passiva
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
  last_updated: number | null;
  disclaimer: string;
}
