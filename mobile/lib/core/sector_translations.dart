// Espelha 1:1 UiHelperService.translateSector() do web — manter em sincronia.
const Map<String, String> _sectorTranslations = {
  'Financial Services': 'Financeiro',
  'Technology': 'Tecnologia',
  'Healthcare': 'Saúde',
  'Energy': 'Energia',
  'Basic Materials': 'Materiais Básicos',
  'Industrials': 'Industrial',
  'Consumer Cyclical': 'Consumo Cíclico',
  'Consumer Defensive': 'Consumo Básico',
  'Real Estate': 'Imobiliário',
  'Utilities': 'Utilidades Públicas',
  'Communication Services': 'Telecomunicações',
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
  'crypto': 'Cripto',
  // Chaves abaixo usam a taxonomia da BRAPI (/quote/list), diferente da
  // usada acima — mapeadas pras mesmas categorias em português.
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

String translateSector(String? sector) {
  if (sector == null || sector.isEmpty) return '—';
  return _sectorTranslations[sector] ?? sector;
}
