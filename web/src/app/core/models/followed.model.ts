export interface FollowedSuggestion {
  id: number;
  ticker: string;
  source: string;
  action: string;
  quantity: number;
  price: number;
  followed_on: string;
  score_at_suggestion: number | null;
  verdict_at_suggestion: string | null;
  note: string | null;

  invested: number;
  current_value: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  days_held: number;
  ibov_pct_since: number | null;
  beat_ibov: boolean | null;
}

export interface SuggestionOutcomeGroup {
  source: string;
  count: number;
  invested: number;
  current_value: number;
  pnl: number;
  pnl_pct: number;
  ibov_pct: number | null;
}

export interface FollowedSuggestionsResponse {
  items: FollowedSuggestion[];
  total_invested: number;
  total_current_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  ibov_pct_same_period: number | null;
  beat_ibov: boolean | null;
  by_source: SuggestionOutcomeGroup[];
  summary: string;
  /**
   * Paginação. `items` é a página; os totais acima cobrem o conjunto inteiro.
   * Ignorar `has_more` faria a tela truncar em silêncio — que é o modo de falha
   * que este produto não pode ter numa lista que vira declaração.
   */
  next_cursor: string | null;
  has_more: boolean;
  total_count: number;
}

export interface FollowedSuggestionPayload {
  ticker: string;
  source?: string;
  action?: string;
  quantity: number;
  price: number;
  followed_on?: string;
  score_at_suggestion?: number | null;
  verdict_at_suggestion?: string | null;
  note?: string | null;
}
