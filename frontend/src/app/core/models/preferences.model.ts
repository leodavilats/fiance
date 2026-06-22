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
  updated_at?: number | null;
}
