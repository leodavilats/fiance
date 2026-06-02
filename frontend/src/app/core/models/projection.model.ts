export interface PassiveIncomeMonth {
  month: string;
  portfolio_value: number;
  passive_income_monthly: number;
  passive_income_yearly: number;
  dividend_yield_avg: number;
}

export interface PassiveIncomeProjectionRequest {
  monthly_contribution: number;
  target_monthly_income?: number;
  dividend_growth_rate: number;
  portfolio_growth_rate: number;
  reinvest_dividends: boolean;
  months_ahead: number;
}

export interface PassiveIncomeProjectionResponse {
  current_passive_income_monthly: number;
  current_passive_income_yearly: number;
  current_portfolio_value: number;
  current_dividend_yield_avg: number;

  projections: PassiveIncomeMonth[];

  target_monthly_income?: number;
  months_to_target?: number;
  target_date?: string;

  assumptions: Record<string, any>;
}

export interface SectorAllocation {
  sector: string;
  target_percentage: number;
  current_percentage: number;
  current_value: number;
  deviation: number;
}

export interface SectorAllocationResponse {
  total_equity_value: number;
  allocations: SectorAllocation[];
  needs_rebalance: boolean;
  max_deviation: number;
}

export interface SectorGoal {
  sector: string;
  target_pct: number;
}
