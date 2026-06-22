export interface PriceAlert {
  id: number;
  ticker: string;
  condition: 'above' | 'below';
  target_price: number;
  note: string | null;
  created_at: number;
  triggered_at: number | null;
}

export interface PriceAlertTriggered {
  id: number;
  ticker: string;
  condition: 'above' | 'below';
  target_price: number;
  note: string | null;
  current_price: number;
}
