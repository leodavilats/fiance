/**
 * Proventos recebidos.
 *
 * Todo número de renda no produto era estimativa derivada de DY, e o histórico
 * real não existia em tabela nenhuma: "quanto eu recebi este mês" não tinha
 * resposta.
 */
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
  /** Recebido / estimado, em %. Transforma estimativa em fato confrontável. */
  estimate_accuracy_pct: number | null;
}

export interface DividendPayload {
  ticker: string;
  paid_at: string;
  amount: number;
  kind?: string;
  note?: string | null;
}
