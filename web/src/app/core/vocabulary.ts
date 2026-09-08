// As bandas de régua e o vocabulário do produto, escritos à mão.
//
// Os limiares de score espelham `backend/app/analysis/score_ruler.py`, que é a fonte: mudar um
// limiar exige mudar o Python primeiro, e depois aqui e no espelho de `mobile/lib/core/`.

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

export const fiCategoriasDeDespesa: Readonly<Record<string, FiCategoria>> = {
  moradia: { label: 'Moradia', series: 1, icon: 'house' },
  contas_da_casa: { label: 'Contas da casa', series: 2, icon: 'plug-zap' },
  mercado: { label: 'Mercado', series: 3, icon: 'shopping-cart' },
  transporte: { label: 'Transporte', series: 4, icon: 'compass' },
  saude: { label: 'Saúde', series: 5, icon: 'stethoscope' },
  educacao: { label: 'Educação', series: 6, icon: 'book-open' },
  lazer: { label: 'Lazer', series: 7, icon: 'shopping-bag' },
  cuidados_pessoais: { label: 'Cuidados pessoais', series: 8, icon: 'circle-user' },
  divida: { label: 'Dívida', series: 9, icon: 'receipt' },
  outros: { label: 'Outros', series: 0, icon: 'circle' },
};

export const fiCategoriasDeEntrada: Readonly<Record<string, FiCategoria>> = {
  salario: { label: 'Salário', series: 1, icon: 'wallet' },
  decimo_terceiro: { label: '13º salário', series: 2, icon: 'gift' },
  ferias: { label: 'Férias', series: 3, icon: 'sunrise' },
  renda_variavel: { label: 'Renda variável', series: 4, icon: 'chart-line' },
  provento: { label: 'Provento', series: 5, icon: 'coins' },
  reembolso: { label: 'Reembolso', series: 6, icon: 'circle-arrow-down' },
  outros: { label: 'Outros', series: 0, icon: 'circle' },
};

export const fiTiposDeDivida: Readonly<Record<string, string>> = {
  rotativo_cartao: 'Rotativo do cartão',
  cheque_especial: 'Cheque especial',
  credito_pessoal: 'Crédito pessoal',
  financiamento_imovel: 'Financiamento de imóvel',
  financiamento_veiculo: 'Financiamento de veículo',
  parcelamento: 'Parcelamento',
  outros: 'Outros',
};

export const fiClasseTextoDaSerie: Readonly<Record<number, string>> = {
  0: 'text-series-other',
  1: 'text-series-1',
  2: 'text-series-2',
  3: 'text-series-3',
  4: 'text-series-4',
  5: 'text-series-5',
  6: 'text-series-6',
  7: 'text-series-7',
  8: 'text-series-8',
  9: 'text-series-9',
};

export const fiClasseFundoDaSerie: Readonly<Record<number, string>> = {
  0: 'bg-series-other',
  1: 'bg-series-1',
  2: 'bg-series-2',
  3: 'bg-series-3',
  4: 'bg-series-4',
  5: 'bg-series-5',
  6: 'bg-series-6',
  7: 'bg-series-7',
  8: 'bg-series-8',
  9: 'bg-series-9',
};

export const fiClasseBarraDaSerie: Readonly<Record<number, string>> = {
  0: 'bg-series-other',
  1: 'bg-series-1',
  2: 'bg-series-2',
  3: 'bg-series-3',
  4: 'bg-series-4',
  5: 'bg-series-5',
  6: 'bg-series-6',
  7: 'bg-series-7',
  8: 'bg-series-8',
  9: 'bg-series-9',
};

export const fiClasseChipDaSerie: Readonly<Record<number, string>> = {
  0: 'bg-series-other/15',
  1: 'bg-series-1/15',
  2: 'bg-series-2/15',
  3: 'bg-series-3/15',
  4: 'bg-series-4/15',
  5: 'bg-series-5/15',
  6: 'bg-series-6/15',
  7: 'bg-series-7/15',
  8: 'bg-series-8/15',
  9: 'bg-series-9/15',
};

export const fiClasseBordaDaSerie: Readonly<Record<number, string>> = {
  0: 'border-series-other/30',
  1: 'border-series-1/30',
  2: 'border-series-2/30',
  3: 'border-series-3/30',
  4: 'border-series-4/30',
  5: 'border-series-5/30',
  6: 'border-series-6/30',
  7: 'border-series-7/30',
  8: 'border-series-8/30',
  9: 'border-series-9/30',
};
