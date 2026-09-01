import { AffirmationMode } from './common.model';

export interface QuickInvestRequest {
  cash_available: number;
  use_current_goals: boolean;
  prioritize_rebalance: boolean;
  min_order_value: number;
}

/**
 * Uma linha da sugestão de aporte.
 *
 * Os números de ação — quanto, quantas cotas, a que preço — chegam anuláveis de
 * propósito: a resposta passa por `affirmation.apply` no backend, que retira o
 * valor que instrui quando o modo não é prescritivo (o padrão é o analítico).
 * Tratá-los como sempre presentes imprimia "R$ " sozinho.
 */
export interface QuickInvestAllocation {
  ticker: string;
  name: string | null;
  category: string;
  sector: string | null;
  current_price: number | null;
  suggested_quantity: number | null;
  suggested_investment: number | null;
  rationale: string;
  score?: number;
  dividend_yield?: number;
}

export interface QuickInvestResponse {
  total_cash: number | null;
  allocated_cash: number | null;
  remaining_cash: number | null;
  allocations: QuickInvestAllocation[];
  portfolio_balance: Record<string, any>;
  summary: string;
  affirmation?: AffirmationMode;
}
