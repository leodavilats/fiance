export type RiskProfile = 'conservative' | 'moderate' | 'aggressive';
export type Strategy = 'score_weighted' | 'max_sharpe' | 'min_volatility' | 'hrp';
// `renda_fixa` existe desde que a renda fixa passou a ser entidade de
// primeira classe no backend; antes as posições de RF vinham como
// `br_stock`, contaminando todo agrupamento por tipo de ativo.
export type AssetType = 'br_stock' | 'bdr' | 'fii' | 'etf' | 'renda_fixa';
export type Verdict = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL' | 'UNKNOWN';

export type AllocationCategory = 'renda_fixa' | 'acoes_br' | 'bdrs' | 'fiis' | 'etfs';

// 'renda' | 'trade' | 'caixa' são nomes legados: o backend ainda os traduz
// (analysis/classify._LEGACY_MAP) para carteiras salvas antes da renomeação,
// mas nada novo deve produzi-los.
export type PortfolioCategory = AllocationCategory | 'auto';
export type LegacyPortfolioCategory = PortfolioCategory | 'renda' | 'trade' | 'caixa';

export type TrendBasis = 'long' | 'short' | 'none';

export interface TickerSuggestion {
  ticker: string;
  name: string;
}
