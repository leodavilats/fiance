import { AssetType } from './common.model';
import { FairPriceBlock, TechnicalBlock } from './asset.model';

export type NewsSentiment = 'positive' | 'neutral' | 'negative';
export type DipVerdict = 'OPORTUNIDADE' | 'NEUTRO' | 'ARMADILHA';

export interface NewsItem {
  title: string;
  source: string;
  published: string;
  url: string;
  sentiment: NewsSentiment;
}

export interface DipScoreBreakdown {
  value_score: number;
  quality_score: number;
  technical_score: number;
  dividend_score: number;
  news_score: number;
}

export interface DipAnalysisResponse {
  symbol: string;
  asset_type: AssetType;
  name: string | null;
  sector: string | null;
  price: number | null;
  currency: string | null;
  fair_price: FairPriceBlock;
  technical: TechnicalBlock;
  fundamentals: Record<string, number | null>;
  dip_score: number;
  breakdown: DipScoreBreakdown;
  verdict: DipVerdict;
  verdict_label: string;
  confidence: number;
  reasons: string[];
  /** Os mesmos motivos, agrupados pela dimensão que os gerou (value, quality, technical, dividend, news). */
  reason_groups: Record<string, string[]>;
  drop_from_52w_high_pct: number | null;
  drop_from_fair_price_pct: number | null;
  news: NewsItem[];
  news_sentiment_summary: string;
  news_ai_summary?: string | null;
  news_ai_score?: number | null;
  news_impact?: 'high' | 'medium' | 'low' | null;
  news_key_topics?: string[];
  disclaimer: string;
}

export interface DipScanItem {
  symbol: string;
  name: string | null;
  asset_type: AssetType;
  sector: string | null;
  price: number | null;
  fair_price_consensus: number | null;
  margin_of_safety: number | null;
  dip_score: number;
  breakdown: DipScoreBreakdown;
  verdict: DipVerdict;
  verdict_label: string;
  confidence: number;
  drop_from_52w_high_pct: number | null;
  drop_from_fair_price_pct: number | null;
  dividend_yield: number | null;
  rsi_14: number | null;
  top_reason: string;
}

export interface DipScannerResponse {
  items: DipScanItem[];
  scanned: number;
  universe_used: string[];
  disclaimer: string;
}
