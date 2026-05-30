export type RiskProfile = 'conservative' | 'moderate' | 'aggressive';
export type Strategy = 'score_weighted' | 'max_sharpe' | 'min_volatility' | 'hrp';
export type AssetType = 'br_stock' | 'fii' | 'us_stock' | 'crypto';
export type Verdict = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL' | 'UNKNOWN';

// Categorias principais usadas em Goals
export type AllocationCategory = 'renda_fixa' | 'acoes_br' | 'acoes_int' | 'fiis' | 'cripto';

// Categorias adicionais para portfolio items (inclui legadas)
export type PortfolioCategory = AllocationCategory | 'auto' | 'renda' | 'trade';
