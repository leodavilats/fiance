export type AllocationCategory = 'renda_fixa' | 'acoes_br' | 'acoes_int' | 'fiis' | 'cripto';

export interface WatchlistItem {
  ticker: string;
  note: string;
  created_at?: number | null;
}

export interface Goal {
  category: AllocationCategory;
  target_pct: number;
  target_value?: number | null;
  deadline?: string | null;
}

export interface Preferences {
  cash_available: number;
  desired_yield: number;
  updated_at?: number | null;
}
