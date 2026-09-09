import { AffirmationMode } from './common.model';

export interface QuickInvestRequest {
  /** Nulo resolve da cascata do caixa: o que sobra depois da dívida caseira e da reserva. */
  cash_available: number | null;
  min_order_value: number;
}

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

/**
 * A fatia de renda fixa, sem nomear título — o produto tem taxas e um comparador, não catálogo
 * de oferta. `amount` é anulado fora do nível prescritivo, porque instrui uma compra.
 */
export interface FixedIncomeSlice {
  amount: number | null;
  reference_monthly_pct: number | null;
  reference_source: string;
  rationale: string;
}

/** Dinheiro sem destino, e o motivo. `value` sobrevive em todo nível: explica, não instrui. */
export interface Unallocated {
  value: number;
  reason: string;
}

/**
 * Os campos marcados como opcionais nasceram depois, e o front sobe antes da API: uma resposta
 * de uma versao anterior nao os traz, e ler `.length` de ausente quebraria a tela.
 */
export interface QuickInvestResponse {
  total_cash: number | null;

  /** `cascade` quando veio da sobra do mês; `informed` quando a pessoa digitou. */
  cash_source?: 'cascade' | 'informed';

  /** `goals` quando a distribuição sai da alocação-alvo declarada; `score` quando não há meta. */
  basis?: 'goals' | 'score';

  allocated_cash: number | null;
  remaining_cash: number | null;
  allocations: QuickInvestAllocation[];
  fixed_income?: FixedIncomeSlice | null;
  unallocated?: Unallocated[];
  portfolio_balance: Record<string, unknown>;
  summary: string;
  affirmation?: AffirmationMode;
}
