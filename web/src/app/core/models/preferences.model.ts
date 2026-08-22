import { AllocationCategory, RiskProfile } from './common.model';

export interface Goal {
  category: AllocationCategory;
  target_pct: number;
  target_value?: number | null;
  deadline?: string | null;
}

export type OpportunitiesFrequency = 'off' | 'daily' | 'weekly' | 'monthly';

export interface Preferences {
  push_enabled?: boolean;
  registered_devices?: number;
  cash_available: number;
  passive_income_goal?: number | null;
  desired_yield_stock?: number;
  desired_yield_fii?: number;
  desired_yield_bdr?: number;
  desired_yield_etf?: number;
  notify_price_alerts?: boolean;
  opportunities_frequency?: OpportunitiesFrequency;
  risk_profile?: RiskProfile;
  preferred_categories?: AllocationCategory[];
  preferred_sectors?: string[];
  excluded_tickers?: string[];
  updated_at?: number | null;
}
