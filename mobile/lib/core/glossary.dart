import 'score_ruler.dart';

final Map<String, String> glossary = {
  'preco_justo':
      'Quanto o ativo vale pela conta do sistema, feita com os números que a empresa ou o fundo '
      'publicou. Sai como faixa, e não como um número só, porque depende de premissas que podem '
      'não se confirmar. É leitura sobre dado público, não recomendação de compra.',
  'dy':
      'Dividendos dos últimos 12 meses sobre o preço de hoje (DY, de dividend yield) — quanto do '
      'preço voltou para quem tinha o ativo, em dividendos, no último ano. Um DY de 6% quer dizer '
      'R\$ 6 recebidos para cada R\$ 100 de preço. Olha para trás: não garante o próximo ano.',
  'ms':
      'Margem de segurança — a folga entre o preço de hoje e a faixa de preço justo. Positiva: o '
      'preço está abaixo do piso da faixa, e o número é o desconto sobre o piso. Negativa: o preço '
      'passa do teto, e o número é o quanto do preço de hoje fica acima dele. Dentro da faixa, é '
      'zero: nem folga, nem excesso.',
  'score': scoreGlossary,
  'perfil_de_risco':
      'Perfil de risco — decide o peso de cada critério no score. No conservador os dividendos '
      'pesam 26% e o crescimento 5%; no arrojado a conta se inverte, com crescimento em 44%. '
      'Em FII, o conservador dá 60% aos dividendos e o arrojado, 65% ao desconto. '
      'Muda a ordem das oportunidades, não o preço justo. Você troca em Você → Como eu invisto.',
  'bazin':
      'Pelos dividendos — o valor que o ativo teria só pelo que ele distribui num ano típico, '
      'dividido pelo rendimento que o juro exige. No fundo imobiliário (FII) é a conta principal; '
      'na ação é a segunda conta, a que confirma ou não a faixa, com a mesma taxa exigida da conta '
      'pelo lucro. O ano típico é a média dos anos completos, cada um limitado a 2 vezes a mediana '
      'dos outros, ou o mais recente, se for menor — um corte de dividendo pesa na hora.',
  'dcf':
      'Pelo lucro distribuível — a conta principal da ação. Traz para o valor de hoje, pela taxa '
      'exigida, o lucro que a empresa pode distribuir sem deixar de crescer: 5 anos crescendo, e '
      'depois um valor de longo prazo. O crescimento é o retorno sobre o patrimônio (ROE) vezes a '
      'parte do lucro que a empresa retém, com teto de 20% ao ano. O lucro por ação é a média dos '
      'últimos 3 anos fechados, para que um ano atípico não pese demais. Sem ROE, não há como '
      'saber quanto o lucro cresce, e a conta se cala.',
  'vpa':
      'Valor patrimonial (VPA, valor patrimonial por ação ou por cota) — o patrimônio que está no '
      'balanço, o que a empresa ou o fundo tem menos o que deve, dividido pelas ações ou cotas. No '
      'fundo imobiliário é a segunda conta, a que confirma ou não a faixa.',
  'confirmacao':
      'Segunda conta — uma leitura do valor feita com outro dado, para ver se a faixa se sustenta: '
      'os dividendos, na ação; o valor patrimonial, no fundo imobiliário. Ela não mexe na faixa: '
      'diz quanto confiar nela.',
  'rsi':
      'Índice de força relativa (RSI) — um número de 0 a 100 que mede se o preço subiu ou caiu '
      'rápido demais no curto prazo, nos últimos 14 pregões. Acima de 70, subiu rápido; abaixo '
      'de 30, caiu rápido. É contexto de preço: não entra na leitura de valor. (Suavização de '
      'Wilder, a das plataformas de gráfico.)',
  'tendencia':
      'Para onde o preço vem andando: compara a média do preço num período curto com a de um '
      'período longo. Com histórico de 2 anos, usa 50 e 200 dias; com histórico curto, 20 e 50 '
      'dias, e a tela avisa. É contexto de preço: não entra na leitura de valor.',
  'roe':
      'Retorno sobre o patrimônio (ROE) — quanto de lucro a empresa gera por ano para cada R\$ 1 '
      'que os sócios têm nela. Um ROE de 15% quer dizer R\$ 15 de lucro por ano para cada '
      'R\$ 100 de patrimônio. Não se aplica a FII nem a ETF.',
  'de':
      'Dívida sobre patrimônio — quanto a empresa deve em relação ao que os sócios têm nela. '
      'Abaixo de 100% quer dizer que ela deve menos do que tem.',
  'consenso':
      'O preço justo sai de uma conta principal por tipo de ativo — o lucro distribuível, na '
      'ação; o que o fundo distribui, no fundo imobiliário —, e a faixa vem das premissas dela, '
      'não da distância entre contas que medem coisas diferentes. Uma segunda conta, com outro '
      'dado, confirma ou não: os dividendos, na ação; o valor patrimonial, no fundo. ETF e BDR '
      'não têm preço justo.',
  'faixa_de_preco_justo':
      'De quanto a quanto o ativo vale, do piso ao teto: do valor na premissa pessimista ao da '
      'otimista, com 1 ponto de taxa a mais e a menos. Na ação, os cenários são dois: crescer com '
      'o lucro que retém, ou não crescer e distribuir tudo. Quando o retorno não paga a taxa, '
      'crescer consome valor, e o pessimista é crescer. Abaixo do piso há folga a favor; acima do '
      'teto, excesso contra; dentro da faixa não há margem nenhuma, e o produto diz isso em vez '
      'de escolher um lado.',
  'qualidade_da_faixa':
      'Diz quanto a faixa merece confiança. Firme: faixa estreita, e a segunda conta, com outro '
      'dado, cai dentro dela. Ampla: sem segunda conta, segunda conta perto da faixa, dividendo '
      'longe da faixa na ação, ou faixa larga pelo peso do crescimento. Frágil: lucro de menos de '
      '3 anos ou instável, corte de distribuição, ou valor patrimonial que discorda no fundo '
      'imobiliário — e aí a leitura nunca passa de abaixo ou acima do preço justo.',
  'premissa_e_gatilho':
      'São coisas diferentes, e a tela as separa. O gatilho é o preço em que a etiqueta muda — '
      'atravessá-lo reclassifica, não refuta nada. A premissa é o que sustenta o preço justo: o '
      'crescimento se confirmar, a taxa exigida ficar onde está, a distribuição se manter. '
      'Refutar uma premissa derruba a tese, que é a leitura inteira; cruzar um gatilho só troca o '
      'nome dela.',
  'taxa_de_desconto':
      'Taxa exigida — o retorno mínimo, ao ano, para o investimento valer a pena; é com ela que '
      'o lucro de amanhã vira valor de hoje. Sai da Selic média de 10 anos mais um prêmio '
      'declarado de 5 pontos: custo de capital é taxa de longo prazo, e a Selic de um dia '
      'mudaria todo preço justo a cada reunião do Copom.',
  'selic':
      'Selic — o juro básico da economia brasileira, decidido pelo Banco Central. O preço justo '
      'usa a média dos últimos 10 anos, lida do Banco Central, e não a do dia.',
  'yield':
      'Rendimento exigido (yield) — quanto o fundo precisa distribuir por ano, sobre o preço, '
      'para valer a pena. É o juro acima da inflação, no longo prazo, mais um prêmio pelo risco '
      'de 3 pontos; no fundo de papel, soma-se a meta de inflação.',
  'distribuicao_recorrente':
      'O que o fundo distribui num ano típico, por cota: a média dos anos completos, cada um '
      'limitado a 2 vezes a mediana dos outros, ou o mais recente, se for menor. Um pagamento '
      'extraordinário não vira capacidade, e um corte pesa na hora.',
  'fii_de_papel':
      'Fundo imobiliário de papel vive de dívidas imobiliárias (recebíveis), e o que ele distribui '
      'já traz a correção pela inflação. Por isso exige rendimento maior que o de tijolo, o fundo '
      'que tem imóveis. A classificação vem de uma lista mantida à mão; fora dela, o fundo é '
      'tratado como tijolo.',
  'sem_preco_justo':
      'ETF de índice, BDR e empresa sem lucro não têm preço justo, e o produto diz isso em vez '
      'de ler compra ou venda em média móvel. A tendência e o índice de força relativa (RSI) '
      'continuam na tela, como contexto de preço.',
  'data_years':
      'Quantos anos-calendário completos de proventos o sistema encontrou. Com menos de 3, o '
      'dividendo não confirma a ação, e o fundo imobiliário sai com evidência frágil.',
  'graham':
      'Critério de Graham — o preço-limite do filtro que Benjamin Graham propôs para o investidor '
      'defensivo: a raiz de 22,5 × lucro por ação × valor patrimonial por ação. Equivale a exigir '
      'que o preço sobre lucro (P/L) vezes o preço sobre valor patrimonial (P/VP) fique até 22,5. '
      'É indicador, não preço justo: sempre que se calcula dentro do próprio filtro, fica acima '
      'do preço, e por isso nunca diria que um ativo está caro.',
  'pvp':
      'Preço sobre valor patrimonial (P/VP) — quanto se paga por cada R\$ 1 de patrimônio que '
      'está no balanço. Abaixo de 1, paga-se menos do que o patrimônio (desconto); acima de 1, '
      'mais (ágio).',
  'lpa':
      'Lucro por ação (LPA) — o lucro da empresa dividido pelo número de ações. O preço justo usa '
      'a média dos últimos anos fechados, para que um ano atípico não pese demais.',
  'payout':
      'Payout — a parte do lucro que a empresa distribui aos sócios. O resto ela retém para '
      'crescer.',
  'preco_teto_pessoal':
      'Preço-teto da sua meta — até que preço o que o ativo distribui num ano típico rende, em '
      'proventos, o percentual ao ano que você declarou em Você → Como eu invisto. É meta pessoal, não preço justo: mudar a meta muda o '
      'teto, e não a faixa.',
};
