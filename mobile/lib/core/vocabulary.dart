
class FiCategory {
  const FiCategory(this.label, this.series);

  final String label;
  final int series;
}

const Map<String, FiCategory> fiCategories = {
  'renda_fixa': FiCategory('Renda Fixa', 1),
  'acoes_br': FiCategory('Ações BR', 2),
  'fiis': FiCategory('FIIs', 3),
  'bdrs': FiCategory('BDRs', 5),
  'etfs': FiCategory('ETFs', 8),
  'auto': FiCategory('Automática', 0),
};

const Map<String, String> fiCategoryAliases = {
  'renda': 'renda_fixa',
  'caixa': 'renda_fixa',
  'trade': 'acoes_br',
};

const Map<String, String> fiAssetTypes = {
  'br_stock': 'Ação BR',
  'bdr': 'BDR',
  'fii': 'FII',
  'etf': 'ETF',
  'renda_fixa': 'Renda Fixa',
};

const Map<String, String> fiAssetTypeToCategory = {
  'br_stock': 'acoes_br',
  'bdr': 'bdrs',
  'fii': 'fiis',
  'etf': 'etfs',
  'renda_fixa': 'renda_fixa',
};

const Map<String, String> fiSectors = {
  'Financial Services': 'Financeiro',
  'Technology': 'Tecnologia',
  'Energy': 'Energia',
  'Consumer Cyclical': 'Consumo Cíclico',
  'Healthcare': 'Saúde',
  'Industrials': 'Industrial',
  'Real Estate': 'Imobiliário',
  'Consumer Defensive': 'Consumo Básico',
  'Basic Materials': 'Materiais Básicos',
  'Utilities': 'Utilidades Públicas',
  'Communication Services': 'Telecomunicações',
};

const Map<String, String> fiSectorAliases = {
  'technology': 'Tecnologia',
  'finance': 'Financeiro',
  'healthcare': 'Saúde',
  'energy': 'Energia',
  'utilities': 'Utilidades Públicas',
  'consumer-discretionary': 'Consumo Cíclico',
  'consumer-staples': 'Consumo Básico',
  'industrials': 'Industrial',
  'materials': 'Materiais Básicos',
  'real-estate': 'Imobiliário',
  'telecommunications': 'Telecomunicações',
  'Miscellaneous': 'Outros',
  'Finance': 'Financeiro',
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
  'Transportation': 'Industrial',
  'Energy Minerals': 'Energia',
  'Communications': 'Telecomunicações',
  'Distribution Services': 'Industrial',
};

const Map<String, int> fiSectorSeriesByLabel = {
  'Financeiro': 1,
  'Tecnologia': 2,
  'Energia': 3,
  'Consumo Cíclico': 4,
  'Saúde': 5,
  'Industrial': 6,
  'Imobiliário': 7,
  'Consumo Básico': 8,
  'Materiais Básicos': 9,
  'Utilidades Públicas': 10,
  'Telecomunicações': 11,
};

const Map<String, String> fiFixedIncomeKinds = {
  'cdb': 'CDB',
  'lci': 'LCI',
  'lca': 'LCA',
  'lc': 'LC',
  'cri': 'CRI',
  'cra': 'CRA',
  'tesouro_selic': 'Tesouro Selic',
  'tesouro_ipca': 'Tesouro IPCA+',
  'tesouro_pre': 'Tesouro Pré',
};

const Map<String, String> fiLiquidity = {
  'diaria': 'Liquidez diária',
  'no_vencimento': 'No vencimento',
};

const Map<String, FiCategory> fiExpenseCategories = {
  'moradia': FiCategory('Moradia', 1),
  'contas_da_casa': FiCategory('Contas da casa', 2),
  'mercado': FiCategory('Mercado', 3),
  'transporte': FiCategory('Transporte', 4),
  'saude': FiCategory('Saúde', 5),
  'educacao': FiCategory('Educação', 6),
  'lazer': FiCategory('Lazer', 7),
  'cuidados_pessoais': FiCategory('Cuidados pessoais', 8),
  'divida': FiCategory('Dívida', 9),
  'outros': FiCategory('Outros', 0),
};

const Map<String, FiCategory> fiIncomeCategories = {
  'salario': FiCategory('Salário', 1),
  'decimo_terceiro': FiCategory('13º salário', 2),
  'ferias': FiCategory('Férias', 3),
  'renda_variavel': FiCategory('Renda variável', 4),
  'provento': FiCategory('Provento', 5),
  'reembolso': FiCategory('Reembolso', 6),
  'outros': FiCategory('Outros', 0),
};

const Map<String, String> fiDebtKinds = {
  'rotativo_cartao': 'Rotativo do cartão',
  'cheque_especial': 'Cheque especial',
  'credito_pessoal': 'Crédito pessoal',
  'financiamento_imovel': 'Financiamento de imóvel',
  'financiamento_veiculo': 'Financiamento de veículo',
  'parcelamento': 'Parcelamento',
  'outros': 'Outros',
};

const Map<String, String> fiLedgerKinds = {
  'buy': 'Compra',
  'sell': 'Venda',
  'split': 'Desdobramento',
  'bonus': 'Bonificação',
  'transfer_in': 'Transferência de entrada',
  'transfer_out': 'Transferência de saída',
  'amortization': 'Amortização',
  'adjust': 'Declaração de posição',
};

const Map<String, String> fiLedgerKindExplanations = {
  'buy': 'Aumenta a quantidade e o custo. Entra no preço médio.',
  'sell': 'Reduz quantidade e custo, nunca a média — é a convenção brasileira. Apura ganho no mês.',
  'split': 'Multiplica a quantidade sem mexer no valor investido. Sem ele, o imposto sai errado.',
  'bonus': 'Ações recebidas sem desembolso. Aumentam a quantidade e diluem a média.',
  'transfer_in': 'Papel que chegou de outra corretora, com o custo que ele já tinha.',
  'transfer_out': 'Papel que saiu para outra corretora. Reduz a posição sem apurar ganho.',
  'amortization': 'Devolução de capital, comum em FII. Reduz o custo, não a quantidade.',
  'adjust': 'Ancora a linha do tempo: o que vier depois se aplica em cima do que você declarou.',
};

const Map<String, String> fiDividendKinds = {
  'dividendo': 'Dividendo',
  'jcp': 'JCP',
  'rendimento': 'Rendimento',
  'amortizacao': 'Amortização',
  'outro': 'Outro',
};

const Map<String, String> fiAccountData = {
  'positions': 'posições',
  'snapshots': 'fotografias do patrimônio',
  'goals': 'metas',
  'sector_goals': 'metas por setor',
  'preferences': 'preferências',
  'notified_opportunities': 'oportunidades já avisadas',
  'device_tokens': 'aparelhos que recebem aviso',
  'price_alerts': 'alertas de preço',
  'fixed_income_positions': 'aplicações de renda fixa',
  'dividends_received': 'proventos recebidos',
  'followed_suggestions': 'ativos seguidos',
  'transactions': 'livro-razão',
  'audit_log': 'registro de auditoria',
  'subscription': 'assinatura',
  'checkout_sessions': 'sessões de pagamento',
  'usage_counters': 'contadores de uso',
  'product_events': 'eventos de uso do produto',
  'revoked_tokens': 'sessões revogadas',
  'referral_code': 'seu código de indicação',
  'referrals_made': 'indicações feitas',
  'cash_entries': 'lançamentos do caixa',
  'cash_recurrences': 'lançamentos recorrentes',
  'debts': 'dívidas',
};
