export type TransactionKind =
  'buy' | 'sell' | 'split' | 'bonus' | 'transfer_in' | 'transfer_out' | 'amortization' | 'adjust';

export interface Transaction {
  id: number;
  kind: TransactionKind;
  symbol: string;

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

export interface ImportIssue {
  line: number;
  message: string;
  field: string | null;
  raw: string;
}

export interface ImportRow {
  line: number;
  kind: TransactionKind;
  symbol: string;
  traded_on: string;
  quantity: number;
  price: number;
  fees: number;
  ratio_from: number;
  ratio_to: number;
  amount: number;
  note: string | null;

  duplicate_of: number | null;
}

export interface ImportPreview {
  format: string;
  rows: ImportRow[];
  issues: ImportIssue[];
  ok: boolean;
  duplicates: number;
}

export interface ImportResult {
  imported: number;
  skipped_duplicates: number;
  ids: number[];
}
