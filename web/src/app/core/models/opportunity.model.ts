import { AllocationCategory, AssetType, TrendBasis, Verdict } from './common.model';

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
  confidence: number;
  data_years: number;
  consensus_methods: number;
  trend_basis: TrendBasis;
  category_resolved: AllocationCategory;
  score: number;
  score_breakdown: Record<string, number>;
  data_completeness: number;
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
  universe_size: number;
  failed_count: number;
}
