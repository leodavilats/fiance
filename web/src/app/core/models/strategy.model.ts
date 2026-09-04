import { AffirmationMode } from './common.model';

export interface InvestorProfile {
  type: string;
  description: string;
  goals: { [category: string]: number };
  risk_tolerance: string;
}

export interface AllocationGap {
  category: string;
  target_pct: number;
  current_pct: number;
  gap_pct: number;
  target_value: number;
  current_value: number;
  gap_value: number;
  action: string;
}

export interface TransactionCost {
  ir_rate_pct: number;
  ir_amount: number;
  net_profit: number;
  observation: string;
}

export interface InvestmentSuggestion {
  ticker: string;
  name: string | null;
  asset_type: string;
  category: string;
  objective: string;
  price: number;

  quantity: number | null;
  invest_amount: number | null;
  score: number;
  dividend_yield: number | null;
  margin_of_safety: number | null;
  verdict: string;
  already_held: boolean;
  reasons: string[];
  transaction_cost: TransactionCost | null;
}

export interface ReduceSuggestion {
  ticker: string;
  name: string | null;
  category: string;
  verdict: string;
  label: string;
  quantity: number | null;
  current_value: number | null;
  pnl_pct: number | null;
  overweight_category: boolean;
  reasons: string[];
}

export interface CurrentAllocation {
  category: string;
  current_value: number;
  current_pct: number;
  assets_count: number;
}

export interface ProjectedAllocation {
  category: string;
  projected_value: number;
  projected_pct: number;
  assets_count: number;
}

export interface RebalanceTarget {
  ticker: string;
  name: string | null;
  category: string;
  score: number;
  verdict: string;
}

export type RebalanceAction = 'comprar_mais' | 'vender' | 'realocar' | 'manter';

export interface RebalanceItem {
  ticker: string;
  name: string | null;
  category: string;
  verdict: string;
  action: RebalanceAction;
  current_value: number | null;
  quantity: number | null;
  pnl_pct: number | null;
  reasons: string[];
  realocar_para: RebalanceTarget | null;
  requires_tax_review: boolean;
}

export interface RebalanceSuggestionsResponse {
  allocation_gaps: AllocationGap[];
  items: RebalanceItem[];
  tax_disclaimer: string | null;
}

export interface InvestmentStrategy {
  profile: InvestorProfile;
  total_capital: number;
  cash_available: number;
  total_invested: number;
  current_allocation: CurrentAllocation[];
  allocation_gaps: AllocationGap[];
  suggestions: InvestmentSuggestion[];
  reduce_suggestions: ReduceSuggestion[];
  projected_allocation: ProjectedAllocation[];
  summary: string;
  affirmation?: AffirmationMode;
}
