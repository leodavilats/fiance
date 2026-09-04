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

  cdi_source: string;

  cdi_basis: string;
}
