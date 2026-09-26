import 'score_ruler.dart';

final Map<String, String> glossary = {
  'dy':
      'Dividend Yield — percentual do preço atual pago em dividendos nos últimos 12 meses. '
      'Acima de 6% é considerado bom para ações; acima de 8% para FIIs.',
  'ms':
      'Margem de Segurança — a distância do preço de hoje até a borda da faixa de preço justo. '
      'Abaixo do piso, é o desconto sobre o piso; acima do teto, o quanto o preço passa dele, '
      'medido sobre o próprio preço. Assim as duas pontas medem a mesma distância.',
  'score': scoreGlossary,
  'perfil_de_risco':
      'Perfil de risco — decide o peso de cada critério no score. No conservador os dividendos '
      'pesam 25% e o crescimento 5%; no arrojado a conta se inverte, com crescimento em 40%. '
      'Muda a ordem das oportunidades, não o preço justo. Você troca em Você → Preferências.',
  'bazin':
      'Pelos dividendos — a distribuição recorrente capitalizada. Em FII é o método principal: '
      'a distribuição dividida pelo yield que o juro exige. Em ação é a leitura de confirmação, '
      'com a mesma taxa do modelo de lucro. A distribuição recorrente é a média dos anos '
      'completos, cada um limitado a 2 vezes a mediana dos outros, ou a mais recente, se ela '
      'for menor — um corte de dividendo pesa na hora.',
  'dcf':
      'Lucros descontados — o método principal de ação. Desconta, por 5 anos, só o lucro que '
      'a empresa pode distribuir sem deixar de crescer, e depois um valor de longo prazo que '
      'sai da mesma taxa. O crescimento é o ROE vezes o que a empresa retém, com teto de 20% ao '
      'ano. O lucro por ação é a média dos últimos 3 exercícios, para que um ano atípico não '
      'vire capacidade. Sem ROE, não há como saber quanto o lucro cresce, e o método se cala.',
  'rsi':
      'Índice de Força Relativa (14 dias, suavização de Wilder) — mede se o preço subiu ou caiu '
      'rápido demais no curto prazo. Acima de 70, subiu rápido; abaixo de 30, caiu rápido. É '
      'contexto de preço: não entra na leitura de valor.',
  'tendencia':
      'Comparação entre a média móvel curta e a longa do preço. Com histórico de 2 anos usa 50 e '
      '200 dias; com histórico curto cai para 20 e 50 dias e a tela sinaliza isso. É contexto '
      'de preço: não entra na leitura de valor.',
  'roe':
      'Retorno sobre o Patrimônio Líquido — quanto de lucro a empresa gera para cada R\$ 1 de '
      'patrimônio. Acima de 15% a.a. é considerado bom. Não se aplica a FIIs nem ETFs.',
  'de':
      'Dívida / Patrimônio Líquido — quanto a empresa deve em relação ao próprio patrimônio. '
      'Abaixo de 100% é confortável.',
  'consenso':
      'O preço justo sai de um método principal por classe — lucros descontados para ação, '
      'distribuição recorrente para FII —, e a faixa vem das premissas dele, não da distância '
      'entre métodos que medem coisas diferentes. Outro insumo confirma ou não: o dividendo, na '
      'ação; o valor patrimonial, no FII. ETF e BDR não têm preço justo.',
  'faixa_de_preco_justo':
      'Do valor na premissa pessimista ao da otimista, com 1 ponto de taxa para cada lado. Na ação, '
      'os cenários são dois: crescer com o lucro que retém, ou não crescer e distribuir tudo. '
      'Quando o retorno não paga a taxa, crescer consome valor, e o pessimista é crescer. '
      'Abaixo do piso há margem a favor; acima do teto, contra; dentro da '
      'faixa não há margem nenhuma, e o produto diz isso em vez de escolher um lado.',
  'qualidade_da_faixa':
      'Diz quanto a faixa merece confiança. `Firme`: faixa estreita, e outro insumo cai dentro '
      'dela. `Ampla`: sem confirmação, confirmação perto da faixa, dividendo longe da faixa na '
      'ação, ou faixa larga pelo peso do crescimento. `Frágil`: lucro de menos de 3 exercícios ou '
      'instável, corte de distribuição, ou valor patrimonial que discorda no FII — e aí a leitura '
      'nunca passa de abaixo ou acima do preço justo.',
  'premissa_e_gatilho':
      'São coisas diferentes, e a tela as separa. O **gatilho** é o preço em que a etiqueta '
      'muda — atravessá-lo reclassifica, não refuta nada. A **premissa** é o que sustenta o '
      'preço justo: o crescimento se confirmar, a taxa exigida ficar onde está, a distribuição '
      'se manter. Refutar uma premissa derruba a tese; cruzar um limiar só troca o nome dela.',
  'taxa_de_desconto':
      'Quanto o futuro vale menos que o presente. Sai da Selic média de 10 anos mais um prêmio '
      'declarado de 5 pontos: custo de capital é taxa de longo prazo, e a Selic de um dia '
      'mudaria todo preço justo a cada reunião do Copom.',
  'sem_preco_justo':
      'ETF de índice, BDR e empresa sem lucro não têm preço justo, e o produto diz isso em vez '
      'de ler compra ou venda em média móvel. A tendência e o RSI continuam na tela, como '
      'contexto de preço.',
  'data_years':
      'Quantos anos-calendário completos de proventos o sistema encontrou. Com menos de 3, o '
      'dividendo não confirma a ação e o FII sai com evidência frágil.',
  'graham':
      'Critério de Graham — √(22,5 × LPA × VPA) é o preço-limite da triagem do investidor '
      'defensivo: P/L vezes P/VP até 22,5. É indicador, não preço justo: sempre que se calcula '
      'dentro do próprio filtro, fica acima do preço, e por isso nunca diria que um ativo está '
      'caro.',
  'pvp':
      'Preço / Valor Patrimonial — quanto se paga por cada R\$ 1 de patrimônio. P/VP < 1 indica '
      'desconto (comum em FIIs atrativos); > 1 indica ágio.',
  'lpa':
      'Lucro Por Ação — lucro líquido da empresa dividido pelo número de ações em circulação. '
      'Quanto maior e mais consistente, melhor.',
  'vpa':
      'Valor Patrimonial por Ação — patrimônio líquido da empresa dividido pelo número de '
      'ações. Indica o "valor contábil" de cada ação.',
  'preco_teto_pessoal':
      'Preço-teto da sua meta — até que preço a distribuição recorrente rende o yield que você '
      'declarou em Você → Preferências. É meta pessoal, não preço justo: mudar a meta muda o '
      'teto, e não a faixa.',
};
