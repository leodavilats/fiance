export type RiskProfile = 'conservative' | 'moderate' | 'aggressive';
export type Strategy = 'score_weighted' | 'max_sharpe' | 'min_volatility' | 'hrp';
export type AssetType = 'br_stock' | 'bdr' | 'fii' | 'etf' | 'renda_fixa';
export type Verdict = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL' | 'UNKNOWN';

export type AllocationCategory = 'renda_fixa' | 'acoes_br' | 'bdrs' | 'fiis' | 'etfs';

export type PortfolioCategory = AllocationCategory | 'auto';
export type LegacyPortfolioCategory = PortfolioCategory | 'renda' | 'trade' | 'caixa';

export type TrendBasis = 'long' | 'short' | 'none';

export interface TickerSuggestion {
  ticker: string;
  name: string;
}

export interface GlobalSearchItem {
  kind: 'position' | 'fixed_income' | 'asset';
  title: string;
  subtitle: string;
  ref: string;
}

export interface GlobalSearchGroup {
  label: string;
  items: GlobalSearchItem[];
}

export interface GlobalSearchResponse {
  query: string;
  groups: GlobalSearchGroup[];
  total: number;
}

export interface DeletionPolicy {
  sla_days: number;
  removes: string[];
  note: string;
  confirmation_phrase: string;
}

export interface AffirmationMode {
  level: number;
  name: string;
  disclaimer: string;
  prescriptive: boolean;
  asset_level: boolean;
  personalized: boolean;
}
