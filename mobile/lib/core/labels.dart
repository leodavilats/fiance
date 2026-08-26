import 'package:flutter/material.dart';

import 'design_tokens.dart';

const _categoryLabels = {
  'renda_fixa': 'Renda Fixa',
  'acoes_br': 'Ações BR',
  'bdrs': 'BDRs',
  'fiis': 'FIIs',
  'etfs': 'ETFs',
  'auto': 'Automática',
};

const _assetTypeLabels = {
  'br_stock': 'Ação BR',
  'bdr': 'BDR',
  'fii': 'FII',
  'etf': 'ETF',
  'renda_fixa': 'Renda Fixa',
};

const _rendaFixaTipoLabels = {
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

String rendaFixaTipoLabel(String? tipo) {
  if (tipo == null) return '—';
  return _rendaFixaTipoLabels[tipo] ?? tipo;
}

String liquidezLabel(String? liquidez) =>
    liquidez == 'diaria' ? 'Liquidez diária' : 'No vencimento';

String categoryLabel(String? category) {
  if (category == null) return '—';
  return _categoryLabels[category] ?? category;
}

String assetTypeLabel(String? assetType) {
  if (assetType == null) return '—';
  return _assetTypeLabels[assetType] ?? assetType;
}

/// Índice de série por categoria — o mesmo mapa do web
/// (`UiHelperService.categoryColor`), para que "FIIs" tenha a mesma cor nas
/// duas plataformas. Antes eram duas paletas independentes, ambas fora dos
/// tokens.
const _categorySeries = {
  'renda_fixa': 1,
  'acoes_br': 2,
  'fiis': 3,
  'bdrs': 5,
  'etfs': 8,
};

Color categoryColor(String? category, Brightness brightness) =>
    fiSeriesColor(_categorySeries[category] ?? 0, brightness);

IconData categoryIcon(String? category) {
  const icons = {
    'renda_fixa': Icons.account_balance_outlined,
    'acoes_br': Icons.show_chart,
    'bdrs': Icons.public_outlined,
    'fiis': Icons.apartment_outlined,
    'etfs': Icons.layers_outlined,
  };
  return icons[category] ?? Icons.category_outlined;
}

/// Setor → série, espelhando `UiHelperService.sectorSeriesColor`.
///
/// Antes a cor saía de `sector.hashCode % paleta.length`: estável dentro de uma
/// sessão, mas arbitrária, diferente do web e sem relação com o significado.
/// Setor fora do mapa cai em "outros", que é uma resposta — não uma cor
/// sorteada.
const _sectorSeries = {
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

Color sectorColor(String sector, Brightness brightness) =>
    fiSeriesColor(_sectorSeries[sector] ?? 0, brightness);
