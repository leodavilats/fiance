/**
 * Renda fixa e ativos de bolsa na mesma tela.
 *
 * O comparador de RF e o de ativos eram universos separados: o produto tinha os
 * dois lados da conta e nunca os colocava juntos, apesar de essa ser a pergunta
 * que define a alocação de quase todo investidor brasileiro.
 */
export interface IncomeOption {
  kind: string;
  label: string;
  ticker: string | null;
  /** Renda recorrente líquida esperada (% a.a.) — a única unidade comparável. */
  net_income_yield_pct: number;
  income_basis: string;
  /** Valorização potencial. Renda fixa não tem, e isso é explícito. */
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
