import 'package:flutter/material.dart';

/// Traduz as categorias/tipos de ativo (valores brutos do backend, tipo
/// "acoes_br", "br_stock") para rótulos legíveis em português.

const _categoryLabels = {
  'renda_fixa': 'Renda Fixa',
  'acoes_br': 'Ações BR',
  'acoes_int': 'Ações Internacionais',
  'fiis': 'FIIs',
  'cripto': 'Cripto',
  'auto': 'Automática',
};

const _assetTypeLabels = {
  'br_stock': 'Ação BR',
  'bdr': 'BDR',
  'fii': 'FII',
  'us_stock': 'Ação Internacional',
  'crypto': 'Criptomoeda',
};

String categoryLabel(String? category) {
  if (category == null) return '—';
  return _categoryLabels[category] ?? category;
}

String assetTypeLabel(String? assetType) {
  if (assetType == null) return '—';
  return _assetTypeLabels[assetType] ?? assetType;
}

/// Cor consistente por categoria — espelha exatamente
/// UiHelperService.categoryColor/-BarClass/-BgClass do web (Tailwind *-400).
Color categoryColor(String? category) {
  const colors = {
    'renda_fixa': Color(0xFF60A5FA), // blue-400
    'acoes_br': Color(0xFF4ADE80), // green-400 (cor de marca)
    'acoes_int': Color(0xFFC084FC), // purple-400
    'fiis': Color(0xFFFB923C), // orange-400
    'cripto': Color(0xFFFACC15), // yellow-400
  };
  return colors[category] ?? const Color(0xFF9CA3AF);
}

IconData categoryIcon(String? category) {
  const icons = {
    'renda_fixa': Icons.account_balance_outlined,
    'acoes_br': Icons.show_chart,
    'acoes_int': Icons.public_outlined,
    'fiis': Icons.apartment_outlined,
    'cripto': Icons.currency_bitcoin,
  };
  return icons[category] ?? Icons.category_outlined;
}
