export type RendaFixaTipo =
  | 'cdb'
  | 'lci'
  | 'lca'
  | 'tesouro_selic'
  | 'tesouro_ipca'
  | 'tesouro_pre'
  | 'lc'
  | 'cri'
  | 'cra';

export type TaxaTipo = 'pre_fixado' | 'pos_fixado' | 'hibrido';
export type Liquidez = 'diaria' | 'no_vencimento';

export interface RendaFixaAsset {
  tipo: RendaFixaTipo;
  valor_investido: number;
  taxa: number;
  prazo_meses: number;
  tipo_taxa: TaxaTipo;
  percentual_cdi?: number | null;
  liquidez: Liquidez;
  nome?: string | null;
  isento_ir?: boolean | null;
}

export interface IrBreakdown {
  aliquota_pct: number;
  valor_ir: number;
  prazo_dias: number;
}

export interface RendaFixaAnalysisResult {
  tipo: string;
  nome: string | null;
  valor_investido: number;
  valor_bruto: number;
  rendimento_bruto: number;
  ir: IrBreakdown;
  valor_liquido: number;
  rendimento_liquido: number;
  taxa_liquida_aa: number;
  taxa_equivalente_cdi_pct: number | null;
  isento_ir: boolean;
  liquidez: string;
  prazo_meses: number;
  melhor_opcao: boolean;
}

export interface RendaFixaCompareRequest {
  ativos: RendaFixaAsset[];
  cdi_anual?: number | null;
  selic_anual?: number | null;
}

export interface RendaFixaCompareResponse {
  resultados: RendaFixaAnalysisResult[];
  cdi_referencia: number;
  selic_referencia: number;
  melhor_opcao_index: number;
}

export interface ReferenceRates {
  cdi_anual: number;
  selic_anual: number;
  ipca_anual: number;
  source: string;
}
