export type RendaFixaTipo =
  'cdb' | 'lci' | 'lca' | 'tesouro_selic' | 'tesouro_ipca' | 'tesouro_pre' | 'lc' | 'cri' | 'cra';

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
  taxa_anual_efetiva_pct: number;
  taxa_equivalente_cdi_pct: number | null;
  pct_cdi_bruto_equivalente: number | null;
  isento_ir: boolean;
  liquidez: string;
  prazo_meses: number;
  melhor_opcao: boolean;
}

export interface RendaFixaCompareRequest {
  ativos: RendaFixaAsset[];
  cdi_anual?: number | null;
  selic_anual?: number | null;
  ipca_anual?: number | null;
}

export interface RendaFixaCompareResponse {
  resultados: RendaFixaAnalysisResult[];
  cdi_referencia: number;
  selic_referencia: number;
  ipca_referencia: number;
  melhor_opcao_index: number;
  melhor_opcao_motivo: string;
  fonte_taxas: string;
}

export interface FixedIncomePosition {
  id: number;
  nome: string;
  tipo: RendaFixaTipo;
  valor_investido: number;
  taxa: number;
  tipo_taxa: TaxaTipo;
  percentual_cdi: number | null;
  data_aplicacao: string;
  vencimento: string | null;
  liquidez: Liquidez;
  isento_ir: boolean | null;
  oculto: boolean;

  valor_atual: number;
  rendimento_acumulado: number;
  rendimento_pct: number;
  meses_decorridos: number;
  taxa_anual_efetiva_pct: number;
  yield_equivalente_pct: number;

  pct_cdi_equivalente: number | null;

  valor_no_vencimento: number | null;
  rendimento_no_vencimento: number | null;
  dias_para_vencimento: number | null;
  vencimento_proximo: boolean;
}

export interface FixedIncomeListResponse {
  items: FixedIncomePosition[];
  total_investido: number;
  total_atual: number;
  total_rendimento: number;
  rendimento_pct: number;
  taxa_media_aa: number;
  cdi_referencia: number;
  fonte_taxas: string;

  next_cursor: string | null;
  has_more: boolean;
  total_count: number;
}

export interface FixedIncomePayload {
  nome: string;
  tipo: RendaFixaTipo;
  valor_investido: number;
  taxa: number;
  tipo_taxa: TaxaTipo;
  percentual_cdi?: number | null;
  data_aplicacao: string;
  vencimento?: string | null;
  liquidez: Liquidez;
  isento_ir?: boolean | null;
  oculto?: boolean;
}

export interface ReferenceRates {
  cdi_anual: number;
  selic_anual: number;
  ipca_anual: number;
  source: string;
}
