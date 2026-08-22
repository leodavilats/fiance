import 'score_ruler.dart';

final Map<String, String> glossary = {
  'dy':
      'Dividend Yield — percentual do preço atual pago em dividendos nos últimos 12 meses. '
      'Acima de 6% é considerado bom para ações; acima de 8% para FIIs.',
  'ms':
      'Margem de Segurança — desconto do preço atual em relação ao preço justo calculado. '
      'Quanto maior, mais "barato" está o ativo em relação ao seu valor intrínseco.',
  'score': scoreGlossary,
  'bazin':
      'Método Décio Bazin — define o Preço Teto como o dividendo médio anual dividido pela sua '
      'meta de yield, configurável por classe em Configurações (padrão: 6% ações BR, 10% FIIs, '
      '4% ETFs). A média usa os anos-calendário completos disponíveis, excluindo o ano corrente. '
      'Comprar abaixo do teto garante um DY mínimo. Não se aplica a BDRs (Graham/DCF).',
  'dcf':
      'Fluxo de Caixa Descontado simplificado — projeta o lucro por ação por 5 anos usando o '
      'crescimento de receita do ativo (8% a.a. quando o dado não existe ou é implausível), '
      'desconta a 13% a.a. e soma um valor terminal a P/L 15.',
  'rsi':
      'Índice de Força Relativa (14 dias) — mede se o ativo subiu ou caiu rápido demais no curto '
      'prazo. Acima de 70 indica sobrecompra; abaixo de 30, sobrevenda. É sinal de timing.',
  'tendencia':
      'Comparação entre a média móvel curta e a longa do preço. Com histórico de 2 anos usa 50 e '
      '200 dias; com histórico curto cai para 20 e 50 dias e a tela sinaliza isso.',
  'roe':
      'Retorno sobre o Patrimônio Líquido — quanto de lucro a empresa gera para cada R\$ 1 de '
      'patrimônio. Acima de 15% a.a. é considerado bom. Não se aplica a FIIs nem ETFs.',
  'de':
      'Dívida / Patrimônio Líquido — quanto a empresa deve em relação ao próprio patrimônio. '
      'Abaixo de 100% é confortável.',
  'consenso':
      'Média dos métodos de preço justo aplicáveis ao ativo. A tela mostra quantos métodos '
      'entraram na conta: um consenso de um método é bem menos confiável que de três.',
  'data_years':
      'Quantos anos-calendário de proventos o sistema encontrou. Menos de 3 anos torna o Bazin '
      'pouco confiável — o número aparece ao lado do veredito para você descontar isso.',
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
