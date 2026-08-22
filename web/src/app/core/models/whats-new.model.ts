export type WhatsNewKind =
  | 'patrimony'
  | 'verdict_change'
  | 'allocation'
  | 'maturity'
  | 'new_opportunity'
  | 'tax'
  | 'empty';

export type WhatsNewSeverity = 'info' | 'warning' | 'critical' | 'positive';

export type ActionKind = 'analyze' | 'sell' | 'rebalance' | 'goals' | 'market' | 'fixed_income';

export interface WhatsNewItem {
  kind: WhatsNewKind;
  severity: WhatsNewSeverity;
  title: string;
  detail: string;
  ticker: string | null;
  action: ActionKind | null;
  action_label: string | null;
}

export interface WhatsNewResponse {
  items: WhatsNewItem[];
  since: number | null;
  days_since: number | null;
  generated_at: number;
}
