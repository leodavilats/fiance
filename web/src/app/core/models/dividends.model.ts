export type DividendKind = 'dividendo' | 'jcp' | 'rendimento' | 'amortizacao' | 'outro';

export interface DividendReceived {
  id: number;
  ticker: string;
  paid_at: string;
  amount: number;
  kind: DividendKind | string;
  note: string | null;
}

export interface DividendMonth {
  month: string;
  total: number;
  count: number;
}

export interface DividendTickerTotal {
  ticker: string;
  total: number;
  count: number;
}

export interface DividendsReceivedResponse {
  items: DividendReceived[];
  total_received: number;
  received_this_month: number;
  received_last_12m: number;
  monthly_average_12m: number;
  by_month: DividendMonth[];
  by_ticker: DividendTickerTotal[];
  estimated_monthly: number | null;
  estimate_accuracy_pct: number | null;
  /**
   * Paginação. `items` é a página; os totais acima cobrem o conjunto inteiro.
   * Ignorar `has_more` faria a tela truncar em silêncio — que é o modo de falha
   * que este produto não pode ter numa lista que vira declaração.
   */
  next_cursor: string | null;
  has_more: boolean;
  total_count: number;
}

export interface DividendPayload {
  ticker: string;
  paid_at: string;
  amount: number;
  kind?: string;
  note?: string | null;
}

/** Provento que o calendário sugere, ainda não lançado. */
export interface PendingDividend {
  ticker: string;
  paid_at: string;
  quantity_at_date: number;
  rate_per_share: number;
  amount: number;
  kind: string;
  /** Por que este número pode estar errado, nesta linha. */
  caveats: string[];
  /** `true` quando a quantidade é a de hoje, não a da data do provento. */
  quantity_is_current: boolean;
}

export interface PendingDividendsResponse {
  items: PendingDividend[];
  count: number;
  note: string;
}
