export interface DividendRankingItem {
  ticker: string;
  name: string | null;
  sector: string | null;
  price: number | null;
  dividend_yield_12m: number | null;
  total_dividends_12m: number | null;
  fair_price_bazin: number | null;
  verdict: string | null;
}

export interface DividendRankingResponse {
  items: DividendRankingItem[];
}
