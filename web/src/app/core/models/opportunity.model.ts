import { AllocationCategory, AssetType, Verdict } from './common.model';

export interface Opportunity {
  ticker: string;
  name: string | null;
  asset_type: AssetType;
  sector: string | null;
  price: number | null;
  fair_price: number | null;
  bazin: number | null;
  graham: number | null;
  pvp: number | null;
  margin_of_safety: number | null;
  dividend_yield: number | null;
  verdict: Verdict;
  label: string;
  category_resolved: AllocationCategory;
  score: number;
  in_portfolio: boolean;
  is_interesting: boolean;
  reasons: string[];
}

export interface OpportunitiesResponse {
  items: Opportunity[];
  total_items: number;
  total_pages: number;
  current_page: number;
  page_size: number;
}
