export interface IncomeOption {
  kind: string;
  label: string;
  ticker: string | null;
  net_income_yield_pct: number;
  income_basis: string;
  upside_pct: number | null;
  has_upside: boolean;
  liquidity: string;
  tax_note: string;
  risk_note: string;
  monthly_income_estimate: number;
  score: number | null;
  data_completeness: number | null;
}

export interface IncomeCompareResponse {
  amount: number;
  horizon_months: number;
  cdi_anual: number;
  ipca_anual: number;
  rates_source: string;
  fixed_income: IncomeOption[];
  assets: IncomeOption[];
  best_income_option: IncomeOption | null;
  verdict: string;
  disclaimer: string;
}
