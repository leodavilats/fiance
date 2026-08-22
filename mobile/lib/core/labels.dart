import 'package:flutter/material.dart';

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

Color categoryColor(String? category) {
  const colors = {
    'renda_fixa': Color(0xFF60A5FA),
    'acoes_br': Color(0xFF4ADE80),
    'bdrs': Color(0xFFC084FC),
    'fiis': Color(0xFFFB923C),
    'etfs': Color(0xFFFACC15),
  };
  return colors[category] ?? const Color(0xFF9CA3AF);
}

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

const _sectorPalette = [
  Color(0xFF60A5FA),
  Color(0xFF4ADE80),
  Color(0xFFC084FC),
  Color(0xFFFB923C),
  Color(0xFFFACC15),
  Color(0xFFF472B6),
  Color(0xFF34D399),
  Color(0xFF818CF8),
  Color(0xFFFB7185),
  Color(0xFFA3E635),
  Color(0xFF22D3EE),
];

Color sectorColor(String sector) {
  final index = sector.hashCode.abs() % _sectorPalette.length;
  return _sectorPalette[index];
}
