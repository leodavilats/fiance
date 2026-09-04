export interface BenchmarkPoint {
  date: string;
  portfolio_pct: number;
  cdi_pct: number;
  ibov_pct: number | null;
}

export interface BenchmarkResponse {
  points: BenchmarkPoint[];
  ibov_available: boolean;
  portfolio_return_pct: number;
  cdi_return_pct: number;
  ibov_return_pct: number | null;
  /**
   * Origem da taxa que gerou a curva de CDI: `bcb` | `bcb_cache_vencido` |
   * `estimativa`. O backend sempre mandou; o TypeScript não declarava, e o
   * FastAPI descarta em silêncio o que o cliente não pede — a curva era
   * desenhada sem dizer se veio do Banco Central ou de um valor de reserva.
   */
  cdi_source: string;
  /**
   * Como a curva foi construída. `taxa_atual_composta` extrapola a taxa de hoje
   * para trás: é referência, não o CDI acumulado histórico.
   */
  cdi_basis: string;
}
