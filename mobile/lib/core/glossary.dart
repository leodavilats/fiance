import 'score_ruler.dart';

final Map<String, String> glossary = {
  'dy':
      'Dividend Yield — percentual do preço atual pago em dividendos nos últimos 12 meses. '
      'Acima de 6% é considerado bom para ações; acima de 8% para FIIs.',
  'ms':
      'Margem de Segurança — desconto do preço atual em relação ao preço justo calculado. '
      'Quanto maior, mais "barato" está o ativo em relação ao seu valor intrínseco.',
  'score': scoreGlossary,
  'perfil_de_risco':
      'Perfil de risco — decide o peso de cada critério no score e o retorno que o sistema cobra '
      'de cada classe para calcular o preço justo. No conservador os dividendos pesam 25% e o '
      'crescimento 5%; no arrojado a conta se inverte, com crescimento em 40%. Muda a ordem das '
      'oportunidades, não o preço justo de consenso. Você troca em Você → Preferências.',
  'bazin':
      'Método Décio Bazin — define o Preço Teto como o dividendo médio anual dividido pela sua '
      'meta de yield, configurável por classe em Você → Preferências (padrão: 6% ações BR, '
      '10% FIIs, 4% ETFs). A média usa os anos-calendário completos disponíveis, excluindo o ano '
      'corrente; se o yield implícito passar de 30%, troca a média pela mediana, para que um '
      'provento extraordinário não infle o teto por cinco anos. Comprar abaixo do teto garante '
      'um DY mínimo. Pressupõe dividendo estável: para empresa cíclica, projeta o passado bom '
      'para sempre. Não se aplica a BDRs.',
  'dcf':
      'Lucros descontados — projeta o lucro por ação por 5 anos usando o crescimento de receita '
      'do ativo (8% a.a. quando o dado não existe, teto de 25%), desconta a 13% a.a. e soma um '
      'valor terminal a P/L 15. Não é um fluxo de caixa descontado: desconta lucro, não caixa '
      'livre, e usa crescimento de receita como proxy do crescimento de lucro. A taxa de 13% é '
      'a mesma para qualquer empresa, sem ajuste por setor ou porte.',
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
      'O preço justo sai como faixa, do método mais conservador ao mais otimista, porque os '
      'métodos não medem a mesma coisa: Bazin mede o dividendo, Graham mede lucro e patrimônio, '
      'e os lucros descontados medem crescimento. A média deles seria um número que nenhum '
      'método sustenta. Cada um tem condições próprias — Graham se abstém fora de P/L 15 e '
      'P/VP 1,5, e Bazin exige histórico de proventos —, e a tela mostra quantos entraram na '
      'faixa. Faixa larga é sinal de que se sabe pouco, não de que o número é preciso.',
  'faixa_de_preco_justo':
      'Piso e teto dos métodos que se aplicam ao ativo. Abaixo do piso há margem a favor; acima '
      'do teto, contra; dentro da faixa não há margem nenhuma, e o produto diz isso em vez de '
      'escolher um lado. Comprar exige preço abaixo do método mais pessimista — é o que torna a '
      'medida conservadora.',
  'qualidade_da_faixa':
      'Diz com o que a faixa se apoia. `Firme`: pelo menos dois insumos econômicos diferentes '
      '(dividendo, lucro, patrimônio) e métodos que convergem. `Ampla`: os métodos discordam '
      'entre si. `Frágil`: tudo depende de um insumo só — inclusive quando há um método apenas, '
      'ou quando dois métodos leem o mesmo número. Graham e lucros descontados vivem do mesmo '
      'lucro por ação: se ele estiver errado, os dois erram juntos.',
  'premissa_e_gatilho':
      'São coisas diferentes, e a tela as separa. O **gatilho** é o preço em que a etiqueta '
      'muda — atravessá-lo reclassifica, não refuta nada. A **premissa** é o que sustenta o '
      'preço justo: o dividendo se manter, o crescimento se confirmar. Refutar uma premissa '
      'derruba a tese; cruzar um limiar só troca o nome dela.',
  'taxa_de_desconto':
      'Quanto o futuro vale menos que o presente, no cálculo de lucros descontados. Sai da '
      'Selic do dia mais um prêmio declarado de 5 pontos: em juro alto, descontar a uma taxa '
      'fixa seria exigir da empresa menos do que o título do governo paga.',
  'leitura_de_tendencia':
      'Para ativo sem nenhum método aplicável, como ETF de índice, não há preço justo e o '
      'produto diz de onde a leitura veio: médias móveis e RSI. Vem marcada como tal, e o que a '
      'derruba é a própria tendência virar — não um preço-limite, que ali não existiria.',
  'data_years':
      'Quantos anos-calendário de proventos o sistema encontrou. Menos de 3 anos torna o Bazin '
      'pouco confiável — o número aparece ao lado do veredito para você descontar isso.',
  'graham':
      'Fórmula Benjamin Graham — Preço Intrínseco = √(22,5 × LPA × VPA). Válido para empresas '
      'com P/L ≤ 15 e P/VP ≤ 1,5, e fora dessa faixa o método se abstém em vez de devolver um '
      'número que não descreve a empresa. Preço abaixo = potencial de valorização. '
      'O múltiplo 22,5 é de 1949 e do mercado americano, e não é ajustado ao juro brasileiro: '
      'com Selic alta, ele tende a ser generoso.',
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
