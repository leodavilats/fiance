# fiance — features por tela

> Inventário do que cada tela faz, organizado pela navegação **atual**. Revisado em 2026-09-11,
> conferido rota por rota contra `mobile/lib/core/router.dart`.
>
> Este arquivo esteve duas revisões de navegação atrás: descrevia **Hoje** e **Estratégia**, que
> não existem mais, e não mencionava nenhuma tela do caixa. É a doença que o
> [KNOWN_ISSUES](KNOWN_ISSUES.md) descreve no próprio cabeçalho — inventário envelhece mais rápido
> que princípio, e envelhece calado.
>
> Estrutura, wireframes e o racional de cada decisão em [design/](design/).

## Navegação

Cinco destinos, e eles são **o ciclo do dinheiro**: entra, sobra, vira patrimônio. Não é a
topologia do backend nem uma lista de funcionalidades.

| Destino | Pergunta que responde | Rota |
|---|---|---|
| **Mês** | como estou agora, e o que exige atenção? | `/mes` |
| **Sobra** | o que eu faço com o que sobrou? | `/sobra` |
| **Patrimônio** | quanto eu tenho, e o que nele exige atenção? | `/patrimonio` |
| **Descobrir** | o que eu poderia comprar? | `/descobrir` |
| **Você** | com que régua o produto me avalia? | `/voce` |
| **Ativo** | este ativo específico vale? | `/ativo/:ticker` |

`/ativo/:ticker` é **camada, não destino**: não aparece na navegação e é alcançável de qualquer
lista. As URLs antigas (`/hoje`, `/carteira/*`, `/estrategia/*`, `/dashboard`, `/assets`,
`/market`, `/config`, `/strategy`) seguem como redirect nas duas plataformas — link salvo é
contrato. Todo alvo de topo é **absoluto**: relativo resolve contra o primeiro segmento casado e
manda o link para o curinga.

---

## Mês

O primeiro lugar depois do login, e a única tela que fala do dinheiro que ainda não foi investido.

- **A resposta, primeiro.** Um veredito em serifa sobre a pressão do mês — o que está comprometido
  contra o que entrou — com a razão embaixo e `<app-provenance>` dizendo método, fonte e
  limitação. Dívida cara, quando existe, é o que decide o veredito.
- **Livre agora**, em `fi-money-xl`. É **fato**, não projeção: entrou, menos saiu, menos o
  comprometido e datado. Ao lado, uma linha de cifras sob um fio: entrou · saiu · comprometido.
- **A ponte para a Sobra.** Uma frase diz que, descontando o que ainda deve sair, a sobra parte de
  um piso — e liga para `/sobra`. Sem mês fechado não há estimativa, e a tela diz isso em vez de
  tratar ausência como zero.
- **Exige atenção** — só dívida de classe *caseira*, com a taxa e a `taxa_de_virada`, que é a taxa
  em que o veredito muda.
- **A vencer** — contas com vencimento no mês e ainda não pagas, com "marcar como paga" por linha.
- **O mês** — todo movimento em ordem de data, com categoria, "a receber"/"a vencer" e a marca
  `do seu razão` no provento derivado, que não é editável porque não foi lançado.
- **O que mudou** — o feed, deliberadamente por último: é o menos decisivo do mês.
- **Recorte de mês na URL** (`?mes=2026-08`), com um seletor que só aparece havendo mais de um mês.

Sub-rotas: `/mes/lancar` (formulário de lançamento, aceita `?editar=`), `/mes/repetir` (o molde do
mês anterior — prévia e commit, com o que repete por natureza já marcado), `/mes/dividas` (CRUD de
dívida, classificada por **custo** e nunca por tipo), `/mes/atividade` (o histórico completo).

No mobile, `lancar` e `repetir` são *bottom sheets* em vez de rotas, e o feed é a rota
`/mes/feed`. Gesto e navegação podem diferir; o conceito e o nome, não.

## Sobra

- **A sobra, no piso.** Projeção, e por isso sai como **faixa**: o piso é o que já está livre menos
  o gasto variável ainda esperado; o teto é o mês fechando como o mais barato dos últimos três.
  Um `<details>` mostra a conta com os meses que formaram a base.
- **A ordem** — a cascata, como lista numerada sobre fio (não como cards: passo de uma ordem não é
  objeto). Cada passo traz o valor, a razão e `O que derrubaria isto`. Dívida cara vem antes de
  aporte por aritmética de taxa, e a tela diz que dívida não é valor mobiliário.
  **A ordem pode terminar sem aporte, e isso é a resposta** — não uma falha.
- **Aporte** (`/sobra/aporte`) — abre já com a sobra resolvida pela cascata, sem pedir o valor;
  "Simular outro valor" é a alternativa, não o caminho principal. Traz a ordem de compra, a fatia
  de renda fixa quando ela cabe, e **o troco com a razão dele** (ordem mínima, teto por categoria,
  arredondamento). Sem meta declarada não inventa 50/25/25: distribui por score e diz que é isso.
- **Alocação × meta** (`/sobra/desvio`) — o desvio entre onde a carteira está e onde a pessoa
  disse que ela deveria estar. Quatro camadas visualmente distintas: informação, cálculo, sugestão
  rotulada como sugestão, e ação.

## Patrimônio

- **A resposta, primeiro** — o veredito de saúde da carteira em serifa, com a régua ao lado e até
  três razões que **nomeiam o papel e o setor** que concentram. Abaixo de quatro ativos negociados
  a leitura não sai, e a tela explica por quê em vez de mostrar régua indeterminada sem contexto.
- **Valor da carteira** em `fi-money-xl`, com o resultado em R$ e %, sobre quanto foi aportado, e a
  contagem de ativos negociados e aplicações de renda fixa, mais o momento da última avaliação.
- **As quatro dimensões** — concentração, setor, diversificação e risco, como **tabela**: nota e
  o que cada uma mede. Era uma grade de quatro células, que é o cheiro de painel.
- **Alocação × meta**, ou o estado vazio que explica por que desvio de meta inexistente seria
  número inventado.
- **Ver em detalhe** e **Registro e manutenção**, separados de propósito: o primeiro é leitura do
  patrimônio, o segundo é operação sobre o livro-razão.

| Sub-rota | Conteúdo |
|---|---|
| `/patrimonio/composicao` | pizza por classe ou por setor, sempre com a lista ao lado |
| `/patrimonio/posicoes` | tabela profissional — colunas configuráveis e densidade, com o recorte na URL (`cols`, `d`); seleção de até 4 para comparar; exportação CSV; venda parcial ou total |
| `/patrimonio/encerradas` | lucro realizado, IR **rateado** por linha (o número do DARF é mensal, e a tela diz isso) e prejuízo disponível para compensar |
| `/patrimonio/proventos` | recebido no mês / 12 meses / média, quebra por ativo, e o confronto com a estimativa |
| `/patrimonio/desempenho` | evolução do patrimônio e carteira × CDI × Ibovespa (TWR) |
| `/patrimonio/projecao` | simulador de aporte e renda passiva — **sempre em faixa**, nunca número único |
| `/patrimonio/editar` | escrita: CRUD de posições e de renda fixa, salvamento explícito por linha |

Renda fixa entra **na mesma tabela** das outras posições, falando a língua dela (taxa efetiva,
% do CDI, vencimento, liquidez) em vez de receber colunas de ação vazias. Marcada a mercado no
backend. As sub-rotas compartilham `CarteiraStore` — trocar de aba não refaz
`POST /portfolio/evaluate`, que é a chamada mais cara do produto.

`composicao`, `posicoes`, `encerradas` e `proventos` são abas **dentro** de `/patrimonio`, e a
renda fixa da pessoa tem rota própria (`/patrimonio/renda-fixa`): a tabela de edição não cabe
numa aba de telefone.

## Descobrir

- **Oportunidades** (`/descobrir/oportunidades`) — varredura do universo. Abre com um veredito
  sobre a **lista inteira**, antes de qualquer linha. Cada item responde *por que apareceu* antes
  de mostrar número, e o preço justo sai por `<app-fair-price>`, que nunca mostra a cifra sem dizer
  quantos métodos a formaram — nem um traço no lugar da ausência, sempre a razão nomeada. Filtros
  na URL (`q`, `dy`, `mos`, `cat`, `destaque`, `p`).
- **Quedas** (`/descobrir/quedas`) — scanner de dip com drawer de diagnóstico: a queda, a leitura,
  as evidências (breakdown do score), o valuation e a conclusão. Recorte na URL (`min_score`,
  `top`, `category`).
- **Renda fixa** (`/descobrir/renda-fixa`) — duas perguntas na mesma tela: comparar títulos entre
  si depois do IR, e renda fixa × bolsa na mesma unidade (renda recorrente líquida a.a.), com a
  valorização potencial mostrada **separada** — renda fixa não tem, e a tela diz isso. No mobile
  são duas rotas (`renda-fixa` e `renda-fixa-vs-bolsa`), porque duas ferramentas numa tela de
  telefone viram duas telas.
- **Comparar** (`/descobrir/comparar`) — até 4 ativos lado a lado. Aceita `?tickers=`.

## Ativo

`/ativo/:ticker` — página de research, e **rota pública renderizada no servidor**: é o canal de
aquisição, e robô não faz login.

- **Cabeçalho:** ticker, nome, tipo, setor, preço, distância do topo de 52 semanas e **quando o
  preço foi lido** — momento é nível 1, porque preço de anteontem muda a decisão.
- **N1:** a leitura em uma frase, o veredito no vocabulário único, a régua de confiança e os
  `reasons` do backend.
- **N2:** preço atual × consenso (com o número de métodos na própria cifra) × margem de segurança.
- **N3 — valuation:** **um bloco por método** (Bazin, Graham, DCF, P/VP justo em FII), cada um com
  preço estimado, distância do atual e o insumo que usou. Método que não se aplica **diz por quê**
  em vez de deixar campo vazio.
- **N3:** fundamentos (só os que existem), tendência **com a base sobre a qual foi medida**,
  proventos.
- **O que faria a tese mudar** — os falsificadores, cada um com a condição e o veredito em que ela
  desemboca. Sem preço justo a lista sai vazia, porque almanaque não é condição conferível.
- **N4:** "Como calculamos" — meta de yield usada, LPA, VPA, P/VP, base da tendência.

## Você

- **Preferências** (`/voce/preferencias`) — três eixos nomeados, e não uma lista de campos:
  **Preço justo** (o yield exigido de cada classe, que é o divisor do preço-teto de Bazin),
  **Score de oportunidade** (perfil de risco, categorias e setores preferidos, ativos excluídos —
  nada aqui altera o preço justo, muda a ordem) e **Avisos**. Mais **Esta tela**, que é a densidade
  e o único ajuste que salva na hora — e a tela diz isso, porque o resto passa pelo Salvar.
- **Objetivos** (`/voce/objetivos`) — renda passiva mensal e alocação por categoria. Fica em Você,
  e não na Sobra, porque declarar meta é armar a estratégia; ver o desvio é ler o patrimônio.
- **Alertas** (`/voce/alertas`) — CRUD de alerta de preço; aceita `?ticker=`. Alerta de preço é
  imediato; o resumo de oportunidades tem cadência. **Push exige o app instalado**, e a tela diz.
- **Indicação** (`/voce/indicacao`) — o código da pessoa. Crédito entra na **qualificação**, nunca
  no cadastro, e a rota nunca devolve quem foi indicado.
- **Conta e dados** (`/voce/conta`) — origem de cada dado (BRAPI, BCB SGS), como preço justo e
  score são calculados, exportação e exclusão da conta (nunca atrás de plano), limpeza de cache.

No mobile, `/voce` é uma tela única com seções e só `objetivos` tem rota própria.

## Público, sem login

Três páginas de documento e uma leitura sem titular. **A lista é fechada** — crescer é decisão
registrada, não efeito colateral.

- **`/termos`**, **`/privacidade`**, **`/aviso-cvm`** — HTML servido pelo backend
  (`api/legal.py`). Robô de loja não faz login, e a ficha de segurança de dados pede uma URL de
  privacidade que abra sozinha; é para cá que o aplicativo manda quem toca em "Termos" nas
  configurações. O Aviso CVM **lê a postura em vigor no servidor** em vez de repetir a frase:
  `AFFIRMATION_LEVEL` é configuração, e uma segunda cópia acabaria desatualizada justamente onde a
  pessoa a lê.
- **`GET /api/public/asset/{ticker}`** — a análise acima, sem titular e com teto por IP: a mesma
  URL devolve o mesmo conteúdo para quem chega por um link compartilhado.

## Autenticação

Login via Google. Acesso de 1h e refresh de 30 dias **rotacionado e queimado no uso**; revogação
por `jti` (este aparelho) e `session_cuts` (todos). O aplicativo renova **uma vez** ao levar 401,
com a renovação compartilhada: dois refreshes simultâneos derrubam a sessão.

## Notificações

Alerta de preço disparado é imediato via FCM. O resumo de oportunidades (`STRONG_BUY`, ou score
≥ 75 com DY ≥ 6%, excluindo o que já está na carteira e os tickers excluídos) sai por cadência
configurável — off, diária, semanal ou mensal. O mesmo push lista posições com veredito de venda.

## Busca

`/search` procura carteira, renda fixa e universo e devolve `ref` — ticker ou id, **nunca
caminho**. Destino de tela também é resultado, mas a lista vive no cliente (`buscaDestinos`): um
catálogo de rotas no servidor seria segunda verdade sobre a arquitetura de informação, e por isso
os destinos filtram sem rede. A porta é `FiSearchAction`, na barra de todo destino de raiz, e leva
à rota `/busca`.
