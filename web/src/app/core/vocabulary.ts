export interface FiCategoria {
  readonly label: string;
  readonly series: number;
  readonly icon: string;
}

export const fiCategorias: Readonly<Record<string, FiCategoria>> = {
  renda_fixa: { label: 'Renda Fixa', series: 1, icon: 'landmark' },
  acoes_br: { label: 'Ações BR', series: 2, icon: 'trending-up' },
  fiis: { label: 'FIIs', series: 3, icon: 'building-2' },
  bdrs: { label: 'BDRs', series: 5, icon: 'globe' },
  etfs: { label: 'ETFs', series: 8, icon: 'layers' },
  auto: { label: 'Automática', series: 0, icon: 'circle' },
};

export const fiCategoriaApelidos: Readonly<Record<string, string>> = {
  renda: 'renda_fixa',
  caixa: 'renda_fixa',
  trade: 'acoes_br',
};

export const fiTiposDeAtivo: Readonly<Record<string, { label: string; category: string }>> = {
  br_stock: { label: 'Ação BR', category: 'acoes_br' },
  bdr: { label: 'BDR', category: 'bdrs' },
  fii: { label: 'FII', category: 'fiis' },
  etf: { label: 'ETF', category: 'etfs' },
  renda_fixa: { label: 'Renda Fixa', category: 'renda_fixa' },
};

export const fiSetores: Readonly<Record<string, { label: string; series: number }>> = {
  'Financial Services': { label: 'Financeiro', series: 1 },
  Technology: { label: 'Tecnologia', series: 2 },
  Energy: { label: 'Energia', series: 3 },
  'Consumer Cyclical': { label: 'Consumo Cíclico', series: 4 },
  Healthcare: { label: 'Saúde', series: 5 },
  Industrials: { label: 'Industrial', series: 6 },
  'Real Estate': { label: 'Imobiliário', series: 7 },
  'Consumer Defensive': { label: 'Consumo Básico', series: 8 },
  'Basic Materials': { label: 'Materiais Básicos', series: 9 },
  Utilities: { label: 'Utilidades Públicas', series: 10 },
  'Communication Services': { label: 'Telecomunicações', series: 11 },
};

export const fiSetorApelidos: Readonly<Record<string, string>> = {
  technology: 'Tecnologia',
  finance: 'Financeiro',
  healthcare: 'Saúde',
  energy: 'Energia',
  utilities: 'Utilidades Públicas',
  'consumer-discretionary': 'Consumo Cíclico',
  'consumer-staples': 'Consumo Básico',
  industrials: 'Industrial',
  materials: 'Materiais Básicos',
  'real-estate': 'Imobiliário',
  telecommunications: 'Telecomunicações',
  Miscellaneous: 'Outros',
  Finance: 'Financeiro',
  'Technology Services': 'Tecnologia',
  'Electronic Technology': 'Tecnologia',
  'Producer Manufacturing': 'Industrial',
  'Industrial Services': 'Industrial',
  'Retail Trade': 'Consumo Cíclico',
  'Consumer Services': 'Consumo Cíclico',
  'Consumer Durables': 'Consumo Cíclico',
  'Process Industries': 'Materiais Básicos',
  'Non-Energy Minerals': 'Materiais Básicos',
  'Health Technology': 'Saúde',
  'Health Services': 'Saúde',
  'Consumer Non-Durables': 'Consumo Básico',
  'Commercial Services': 'Industrial',
  Transportation: 'Industrial',
  'Energy Minerals': 'Energia',
  Communications: 'Telecomunicações',
  'Distribution Services': 'Industrial',
};

export const fiSetorSeriePorRotulo: Readonly<Record<string, number>> = {
  Financeiro: 1,
  Tecnologia: 2,
  Energia: 3,
  'Consumo Cíclico': 4,
  Saúde: 5,
  Industrial: 6,
  Imobiliário: 7,
  'Consumo Básico': 8,
  'Materiais Básicos': 9,
  'Utilidades Públicas': 10,
  Telecomunicações: 11,
};

export const fiTiposDeRendaFixa: Readonly<Record<string, string>> = {
  cdb: 'CDB',
  lci: 'LCI',
  lca: 'LCA',
  lc: 'LC',
  cri: 'CRI',
  cra: 'CRA',
  tesouro_selic: 'Tesouro Selic',
  tesouro_ipca: 'Tesouro IPCA+',
  tesouro_pre: 'Tesouro Pré',
};

export const fiLiquidez: Readonly<Record<string, string>> = {
  diaria: 'Liquidez diária',
  no_vencimento: 'No vencimento',
};

export const fiClasseTextoDaSerie: Readonly<Record<number, string>> = {
  0: 'text-series-other',
  1: 'text-series-1',
  2: 'text-series-2',
  3: 'text-series-3',
  5: 'text-series-5',
  8: 'text-series-8',
};

export const fiClasseFundoDaSerie: Readonly<Record<number, string>> = {
  0: 'bg-series-other',
  1: 'bg-series-1',
  2: 'bg-series-2',
  3: 'bg-series-3',
  5: 'bg-series-5',
  8: 'bg-series-8',
};

export const fiClasseBarraDaSerie: Readonly<Record<number, string>> = {
  0: 'bg-series-other',
  1: 'bg-series-1',
  2: 'bg-series-2',
  3: 'bg-series-3',
  5: 'bg-series-5',
  8: 'bg-series-8',
};

export const fiClasseChipDaSerie: Readonly<Record<number, string>> = {
  0: 'bg-series-other/15',
  1: 'bg-series-1/15',
  2: 'bg-series-2/15',
  3: 'bg-series-3/15',
  5: 'bg-series-5/15',
  8: 'bg-series-8/15',
};
