// GERADO AUTOMATICAMENTE — NÃO EDITE ESTE ARQUIVO.
// Fonte: design-tokens/tokens.json · Gerador: design-tokens/build.mjs
// Regenerar: node design-tokens/build.mjs

import 'package:flutter/material.dart';

class FiCategoria {
  const FiCategoria(this.label, this.series, this.icon);

  final String label;
  final int series;
  final IconData icon;
}

const Map<String, FiCategoria> fiCategorias = {
  'renda_fixa': FiCategoria('Renda Fixa', 1, Icons.account_balance_outlined),
  'acoes_br': FiCategoria('Ações BR', 2, Icons.show_chart),
  'fiis': FiCategoria('FIIs', 3, Icons.apartment_outlined),
  'bdrs': FiCategoria('BDRs', 5, Icons.public_outlined),
  'etfs': FiCategoria('ETFs', 8, Icons.layers_outlined),
  'auto': FiCategoria('Automática', 0, Icons.category_outlined),
};

const Map<String, String> fiCategoriaApelidos = {
  'renda': 'renda_fixa',
  'caixa': 'renda_fixa',
  'trade': 'acoes_br',
};

const Map<String, String> fiTiposDeAtivo = {
  'br_stock': 'Ação BR',
  'bdr': 'BDR',
  'fii': 'FII',
  'etf': 'ETF',
  'renda_fixa': 'Renda Fixa',
};

const Map<String, String> fiTipoDeAtivoParaCategoria = {
  'br_stock': 'acoes_br',
  'bdr': 'bdrs',
  'fii': 'fiis',
  'etf': 'etfs',
  'renda_fixa': 'renda_fixa',
};

const Map<String, String> fiSetores = {
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

const Map<String, String> fiSetorApelidos = {
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

const Map<String, int> fiSetorSeriePorRotulo = {
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

const Map<String, String> fiTiposDeRendaFixa = {
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

const Map<String, String> fiLiquidez = {
  'diaria': 'Liquidez diária',
  'no_vencimento': 'No vencimento',
};
