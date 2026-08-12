import { CategoryAllocation } from './dashboard.model';
import { QuickInvestAllocation } from './quick-invest.model';

export interface RebalanceResponse {
  needs_rebalance: boolean;
  allocations: CategoryAllocation[];
  total_gap_amount: number;
  suggestions: QuickInvestAllocation[];
  message: string;
}
