import { RiskProfile, Strategy } from './common.model';

export interface RecommendRequest {
  cash: number;
  profile: RiskProfile;
  max_positions: number;
  universe?: string[] | null;
  exclude_sectors: string[];
  strategy: Strategy;
  explain: boolean;
}

export interface Allocation {
  ticker: string;
  name: string | null;
  sector: string | null;
  price: number;
  quantity: number;
  invested: number;
  weight: number;
  score: number;
  rationale: string;
}

export interface RecommendResponse {
  profile: RiskProfile;
  strategy: Strategy;
  cash_input: number;
  cash_invested: number;
  cash_remaining: number;
  allocations: Allocation[];
  metrics: { expected_return?: number; volatility?: number; sharpe?: number };
  explanation: string;
  disclaimer: string;
}
