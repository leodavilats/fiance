export interface PassiveIncomeMonth {
  month: string;
  portfolio_value: number;
  portfolio_value_low: number;
  portfolio_value_high: number;
  passive_income_monthly: number;
  passive_income_monthly_low: number;
  passive_income_monthly_high: number;
  passive_income_yearly: number;
  dividend_yield_avg: number;
}

export interface ScenarioMonth {
  scenario: string;
  month: string;
  portfolio_value: number;
  passive_income_monthly: number;
}

export interface ScenarioSeries {
  code: string;
  label: string;
  rationale: string;
  portfolio_growth_rate: number;
  dividend_growth_rate: number;
  months: ScenarioMonth[];
  final_passive_income_monthly: number;
  final_portfolio_value: number;
  months_to_target?: number | null;
  target_date?: string | null;
}

export interface TargetEstimate {
  monthly_income: number;
  earliest_months?: number | null;
  expected_months?: number | null;
  latest_months?: number | null;
  earliest_date?: string | null;
  expected_date?: string | null;
  latest_date?: string | null;
  reached_in_all_scenarios: boolean;
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
  scenarios: ScenarioSeries[];

  target?: TargetEstimate | null;
  target_monthly_income?: number;

  disclaimer: string;
  assumptions: Record<string, unknown>;
}

export interface SectorGoal {
  sector: string;
  target_pct: number;
}
