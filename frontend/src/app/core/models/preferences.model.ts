export interface WatchlistItem {
  ticker: string;
  note: string;
  created_at?: number | null;
}

export interface Goal {
  category: 'renda' | 'trade' | 'cripto' | 'caixa';
  target_pct: number;
}

export interface Preferences {
  cash_available: number;
  desired_yield: number;
  updated_at?: number | null;
}
