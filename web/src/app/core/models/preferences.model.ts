import { AllocationCategory } from './common.model';

export interface Goal {
  category: AllocationCategory;
  target_pct: number;
  target_value?: number | null;
  deadline?: string | null;
}

export interface Preferences {
  cash_available: number;
  passive_income_goal?: number | null;
  desired_yield_stock?: number;
  desired_yield_fii?: number;
  desired_yield_bdr?: number;
  desired_yield_etf?: number;
  updated_at?: number | null;
}
