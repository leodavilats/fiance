// Espelha 1:1 UiHelperService.glossary do web — manter os dois em sincronia.
const Map<String, String> glossary = {
  'dy':
      'Dividend Yield — percentual do preço atual pago em dividendos nos últimos 12 meses. '
      'Acima de 6% é considerado bom para ações; acima de 8% para FIIs.',
  'ms':
      'Margem de Segurança — desconto do preço atual em relação ao preço justo calculado. '
      'Quanto maior, mais "barato" está o ativo em relação ao seu valor intrínseco.',
  'score':
      'Pontuação 0–100 calculada pelo sistema combinando valuation, histórico de dividendos '
      'e qualidade do ativo. Acima de 70 = oportunidade; 40–70 = neutro; abaixo de 40 = cuidado.',
  'bazin':
      'Método Décio Bazin — define o Preço Teto como o dividendo anual dividido pela meta de '
      'yield: 6% (ações BR), 10% (FIIs) ou 4% (ETFs, quando distribuem dividendos). Comprar '
      'abaixo do teto garante um DY mínimo. Não se aplica a BDRs (avaliadas por Graham/DCF).',
  'graham':
      'Fórmula Benjamin Graham — Preço Intrínseco = √(22,5 × LPA × VPA). Válido para empresas '
      'com P/L ≤ 15 e P/VP ≤ 1,5. Preço abaixo = potencial de valorização.',
  'pvp':
      'Preço / Valor Patrimonial — quanto se paga por cada R\$ 1 de patrimônio. P/VP < 1 indica '
      'desconto (comum em FIIs atrativos); > 1 indica ágio.',
  'lpa':
      'Lucro Por Ação — lucro líquido da empresa dividido pelo número de ações em circulação. '
      'Quanto maior e mais consistente, melhor.',
  'vpa':
      'Valor Patrimonial por Ação — patrimônio líquido da empresa dividido pelo número de '
      'ações. Indica o "valor contábil" de cada ação.',
};
