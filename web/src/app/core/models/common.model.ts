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

/**
 * Um achado da busca global.
 *
 * `ref` é o identificador — ticker, ou id da posição de renda fixa. O servidor
 * não manda rota de propósito: as árvores do web e do app diferem, e um
 * catálogo de rotas no servidor seria uma segunda verdade sobre a arquitetura
 * de informação.
 */
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

/**
 * O modo de afirmação sob o qual a resposta foi montada.
 *
 * Vem junto de toda rota que passa por `affirmation.apply`. Fora do modo
 * prescritivo o servidor retira o valor que instrui — quanto aportar, quantas
 * cotas — e a tela precisa dizer que ele foi retido, senão o traço no lugar do
 * número lê como dado faltando.
 */
export interface AffirmationMode {
  level: number;
  name: string;
  disclaimer: string;
  prescriptive: boolean;
  asset_level: boolean;
  personalized: boolean;
}
