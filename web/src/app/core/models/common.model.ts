export type RiskProfile = 'conservative' | 'moderate' | 'aggressive';
export type Strategy = 'score_weighted' | 'max_sharpe' | 'min_volatility' | 'hrp';
export type AssetType = 'br_stock' | 'bdr' | 'fii' | 'etf';
export type Verdict = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL' | 'UNKNOWN';

export type AllocationCategory = 'renda_fixa' | 'acoes_br' | 'bdrs' | 'fiis' | 'etfs';

export type PortfolioCategory = AllocationCategory | 'auto' | 'renda' | 'trade';

export interface TickerSuggestion {
  ticker: string;
  name: string;
}
