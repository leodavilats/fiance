/** Livro-razão: os lançamentos e a conta que eles produzem. */

export type TransactionKind =
  | 'buy'
  | 'sell'
  | 'split'
  | 'bonus'
  | 'transfer_in'
  | 'transfer_out'
  | 'amortization'
  | 'adjust';

export interface Transaction {
  id: number;
  kind: TransactionKind;
  symbol: string;
  /** Dia da operação no fuso brasileiro, `YYYY-MM-DD`. */
  traded_on: string;
  quantity: number;
  price: number;
  fees: number;
  ratio_from: number;
  ratio_to: number;
  amount: number;
  note: string | null;
}

export interface TransactionListResponse {
  items: Transaction[];
  count: number;
}

/** Um passo da conta do preço médio, em número e em frase. */
export interface DerivationStep {
  traded_on: string;
  kind: TransactionKind;
  description: string;
  quantity_after: number;
  total_cost_after: number;
  avg_price_after: number;
}

export interface ProjectedPosition {
  symbol: string;
  quantity: number;
  avg_price: number;
  total_cost: number;
  realized_pnl: number;
  total_fees: number;
  first_traded_on: string | null;
  last_traded_on: string | null;
  entries_applied: number;
}

export interface DerivationResponse {
  symbol: string;
  position: ProjectedPosition;
  steps: DerivationStep[];
}

export interface ReconciliationDifference {
  ticker: string;
  reason: string;
  stored: { quantity: number; avg_price: number } | null;
  projected: ProjectedPosition | null;
}

export interface ReconciliationResponse {
  positions: number;
  projected: number;
  differences: ReconciliationDifference[];
  in_sync: boolean;
}
