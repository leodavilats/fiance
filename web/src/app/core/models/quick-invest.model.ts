export interface QuickInvestRequest {
  cash_available: number;
  use_current_goals: boolean;
  prioritize_rebalance: boolean;
  min_order_value: number;
}

export interface QuickInvestAllocation {
  ticker: string;
  name: string | null;
  category: string;
  sector: string | null;
  current_price: number;
  suggested_quantity: number;
  suggested_investment: number;
  rationale: string;
  score?: number;
  dividend_yield?: number;
}

export interface QuickInvestResponse {
  total_cash: number;
  allocated_cash: number;
  remaining_cash: number;
  allocations: QuickInvestAllocation[];
  portfolio_balance: Record<string, any>;
  summary: string;
}
