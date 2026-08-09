export interface SectorAsset {
  ticker: string;
  name: string | null;
  score: number;
  price: number | null;
  dividend_yield: number | null;
  verdict: string;
  label: string;
}

export interface SectorSummary {
  sector: string;
  count: number;
  avg_score: number;
  avg_dy: number;
  top_assets: SectorAsset[];
}

export interface SectorsSummaryResponse {
  sectors: SectorSummary[];
  total_assets: number;
  failed_count: number;
}
