# Auditoria do veredito por ativo

> ## ⏳ DOCUMENTO TEMPORÁRIO
>
> **Critério de morte:** quando os 40 itens estiverem riscados, **apague este arquivo**, remova a
> linha do índice em [README](../README.md) e a seção correspondente em
> [10-PROBLEMAS](../10-PROBLEMAS.md).
>
> Ele existe para que o caminho do preço ao veredito — a parte do sistema que mais decide o que a
> pessoa faz com o próprio dinheiro — tenha os seus defeitos listados num lugar só, e não numa
> conversa.

Levantado em **2026-09-20**, sobre o fluxo que [04-CALCULOS](../04-CALCULOS.md) desenha na seção
*Veredito*. Cada item foi conferido contra o código, e onde a resposta dependia de comportamento e
não de leitura, o motor foi executado.

**Ao fechar um item, risque-o com a data** — como em [PARIDADE-WEB-APP](PARIDADE-WEB-APP.md). A
numeração não muda, porque ela é referência daqui para fora.

---

## Como ler

Cada item carrega três julgamentos, e eles não se misturam:

| Coluna | O que responde |
|---|---|
| **Premissa** | O raciocínio que originou o item descreve o sistema corretamente? `✅` sim · `⚠️` em parte · `❌` não |
| **Prioridade** | Quanto custa deixar como está |
| **Viável hoje** | Dá para resolver com BRAPI e BCB, que são as duas fontes que existem |

`⚠️` e `❌` **não anulam o item** — significam que a descrição precisa ser corrigida antes de
alguém trabalhar nela, senão o trabalho parte de uma premissa errada.

---

## O que foi medido

Duas medições feitas em 2026-09-20 contra o código em produção. Elas são a âncora dos itens 8, 19,
23 e 24, e qualquer uma pode ser repetida.

### A guarda de dividendo extraordinário quase não pega

`backend/app/analysis/fair_price.py` troca a média pela mediana quando o yield implícito passa de
30% (`_IMPLIED_DY_OUTLIER`). Com preço R$ 10 e dividendo recorrente de R$ 0,50:

| Dividendo extraordinário | Bazin resultante | Mediana disparou? |
|---|---|---|
| R$ 5 | 23,33 — 2,8× inflado | não |
| R$ 9 | 36,67 — 4,4× | não |
| R$ 12 | 46,67 — 5,6× | não |
| R$ 15 | 8,33 — correto | **sim** |

A proteção só alcança o absurdo, deixa passar o que contamina, e **ela própria é uma
descontinuidade**: entre R$ 12 e R$ 15 o preço justo salta de 46,67 para 8,33.

### A razão contradiz o rótulo na mesma tela

Faixa R$ 12,50–19,60, preço R$ 10, margem +20% → veredito de faixa `BUY`. A tendência de baixa
rebaixa para `HOLD`; o RSI de 25 promove de volta para `BUY`. O veredito final é **idêntico** ao de
faixa, mas a lista de razões exibida contém:

> *"O preço está descontado, mas a tendência principal é de queda: a leitura cai de comprar para
> manter."*

…ao lado da etiqueta **Comprar**. Duas afirmações opostas sobre o mesmo ativo, na mesma folha.

---

## Os cinco blocos

Os 40 itens são cinco problemas vistos de ângulos diferentes. Atacar por bloco custa menos que
atacar por item, porque dentro de um bloco a decisão é uma só.

| Bloco | O que é | Itens | Natureza |
|---|---|---|---|
| **A** | O técnico decide sem mandato | 1, 18, 19, 26, 36, 37, 38 | Decisão de produto |
| **B** | A faixa não carrega a própria incerteza | 2, 3, 4, 5, 15, 23, 31, 35, 40 | Decisão de produto |
| **C** | Falsificador que não falsifica | 27, 28, 29, 39 | Decisão de produto |
| **D** | Premissas sem fundamentação econômica | 6, 7, 9, 10, 11, 13, 14, 17, 33, 34 | Majoritariamente escrita |
| **E** | Defeito mecânico, não decisão | 8, 12, 16, 20, 21, 22, 24, 25, 30, 32 | Correção direta |

**Ordem sugerida: E → A → B → C → D.** O bloco E não precisa de decisão nenhuma e hoje distorce
número real. A e B mudam o que a tela diz sobre quase toda a base, e por isso pedem ADR antes de
código — como as quatro decisões de [ADR-011](../decisoes/ADR-011-preco-justo-e-faixa.md) e
[ADR-012](../decisoes/ADR-012-o-alvo-e-de-quem-declara.md).

---

## Bloco A · O técnico decide sem mandato

O valuation produz uma conclusão e a análise técnica a reescreve, sem que esteja escrito em lugar
nenhum por que um deve prevalecer sobre o outro. É a decisão mais cara em aberto: medida em
2026-09-20, ela move **11 das 22 ações** da amostra para sinal de venda, seis delas com margem zero
ou positiva.

### 1 · A decisão final pode contradizer o valuation

Premissa `✅` · Prioridade **alta** · Viável `sim`

Tendência e RSI alteram a conclusão sem que nenhum fundamento tenha mudado. Definir o papel de cada
camada — se modificam veredito, confiança ou apenas contexto — é a decisão que abre o bloco.

`backend/app/analysis/decision.py`

### 18 · Tendência e RSI vêm da mesma fonte

Premissa `✅` · Prioridade **alta** · Viável `sim`

Os dois derivam do histórico de preço. Uma queda produz tendência de baixa **e** RSI baixo, e o
fluxo os trata como dois sinais.

### 19 · O RSI desfaz o que a tendência fez

Premissa `✅` · Prioridade **alta** · Viável `sim`

Confirmado na medição acima, e a consequência é maior que a descrita: além da cadeia de correções,
**a razão exibida contradiz a etiqueta**. Para o usuário, é o sistema discordando de si mesmo.

### 26 · A confiança sobe por informação redundante

Premissa `✅` · Prioridade **alta** · Viável `sim`

Tendência e RSI somam confiança como se fossem evidências independentes. Ver também o item 25.

### 36 · Não há hierarquia declarada entre fundamento e mercado

Premissa `✅` · Prioridade **alta** · Viável `sim`

É o item 1 em forma geral: três tipos de evidência se combinam sem que se diga o que cada um mede.

### 37 · A regra de tendência é assimétrica

Premissa `✅` · Prioridade **alta** · Viável `sim`

Alta só aumenta confiança, e apenas quando o veredito já era Manter ou Vender. Baixa rebaixa três
categorias. A mesma variável tem poderes diferentes conforme a direção, e isso nunca foi decidido
por escrito.

### 38 · Médias de 50 e 200 dias são indicadores atrasados

Premissa `✅` · Prioridade baixa · Viável `sim`

É a natureza do indicador, não um defeito de implementação. Cabe declarar em
[04-CALCULOS](../04-CALCULOS.md), não corrigir.

---

## Bloco B · A faixa não carrega a própria incerteza

A faixa hoje é apenas `mín` e `máx`. Tudo o que diferencia uma faixa confiável de uma frágil —
quantos métodos, se são independentes, se um extremo é outlier, onde o preço está dentro dela — se
perde antes de chegar ao veredito.

### 2 · Mínimo e máximo viram piso e teto econômicos

Premissa `⚠️` · Prioridade **alta** · Viável `sim`

A faixa não *afirma* ser piso e teto econômicos — mas a margem de segurança é medida contra eles,
então na prática é assim que funcionam. A ressalva não salva o item: o efeito é o descrito.

`backend/app/analysis/fair_price.py::margin_of_safety_in_band`

### 3 · A dispersão não afeta a decisão proporcionalmente

Premissa `⚠️` · Prioridade média · Viável `sim`

A dispersão **já** afeta a decisão por dois caminhos: alarga a faixa (o que puxa o preço para
dentro dela) e tira 0,1 da confiança. O que falta é ela mudar a *interpretação* — hoje uma faixa de
5,5× e uma de 1,1× produzem vereditos da mesma natureza.

### 4 · Um método só é tratado como faixa validada

Premissa `✅` · Prioridade **alta** · Viável `sim`

Com um método, piso = teto, e uma estimativa pontual passa a funcionar como limite exato.
`consensus_methods` já viaja até a tela; o que falta é consequência sobre o veredito.

### 5 · Métodos não são evidências independentes

Premissa `✅` · Prioridade **alta** · Viável `sim`

Graham usa LPA e VPA; os lucros descontados usam LPA. **Duas das três "confirmações" da ação
compartilham o mesmo insumo.** Não exige dado novo — exige reconhecer a dependência ao medir
robustez.

### 15 · A margem é zerada em toda a região interna

Premissa `✅` · Prioridade **alta** · Viável `sim`

Preço rente ao piso e preço rente ao teto recebem margem 0. A posição relativa dentro da faixa é
informação que existe e é descartada.

### 23 · Valores extremos dominam a faixa

Premissa `✅` · Prioridade **alta** · Viável `sim`

Comprovado pela medição: um Bazin de 46,67 vindo de dividendo extraordinário vira teto da faixa sem
que nada o questione.

### 31 · O nível de evidência varia por classe

Premissa `✅` · Prioridade média · Viável `sim`

Ação até três métodos, BDR e FII dois, ETF nenhum. A confiança acompanha a classe do ativo, não a
qualidade da evidência.

### 35 · O resultado final esconde a origem da incerteza

Premissa `⚠️` · Prioridade média · Viável `sim`

`basis`, `consensus_methods` e `method_dispersion` **já** viajam na resposta desde 2026-09-19. O que
falta é consolidá-los numa leitura de qualidade e mostrá-la junto do veredito.

### 40 · A faixa esconde a causa da divergência

Premissa `✅` · Prioridade média · Viável `sim`

`method_dispersion` é só `teto ÷ piso`. Um outlier isolado e três métodos genuinamente discordantes
produzem o mesmo número.

---

## Bloco C · Falsificador que não falsifica

O invariante do produto diz que **o veredito vem com o que o derrubaria**. O que ele entrega é o
preço que muda a etiqueta — que é outra coisa.

### 27 · Falsificadores de preço medem mudança de banda

Premissa `✅` · Prioridade **alta** · Viável `sim`

Atravessar um limiar não demonstra que a premissa do valuation deixou de valer. São gatilhos de
reclassificação apresentados como refutação.

`backend/app/analysis/falsifiers.py`

### 28 · O falsificador de dividendo não explica o que testa

Premissa `⚠️` · Prioridade média · Viável `sim`

O significado **é** definido no código: o corte que levaria a margem exatamente à borda da compra
(+15%) — daí o fator 0,85. O defeito é de comunicação, não de derivação: a tela mostra a conta sem
dizer a condição que ela testa.

### 29 · Falsificadores técnicos não são falsificadores

Premissa `✅` · Prioridade **alta** · Viável `sim`

"A tendência virar" altera um indicador; não refuta premissa econômica alguma. Como o ETF depende
inteiramente desse caminho, é ali que o problema é mais visível.

### 39 · O falsificador de dividendo só existe com Bazin no piso

Premissa `⚠️` · Prioridade média · Viável `sim`

Para o **veredito**, a restrição é correta: com Bazin fora do piso, cortar o dividendo não move a
margem. Para a **premissa**, o item está certo — a sustentabilidade do dividendo importa
independentemente da posição que o método ocupa.

---

## Bloco D · Premissas sem fundamentação econômica

Nenhuma destas premissas tem origem escrita. Algumas já aparecem como limitação declarada em
[04-CALCULOS](../04-CALCULOS.md); nenhuma tem justificativa.

### 6 · As premissas do modelo de lucros descontados são arbitrárias

Premissa `✅` · Prioridade **alta** · Viável `parcial`

Desconto de 13%, múltiplo terminal 15, horizonte de 5 anos — e o valor terminal domina o resultado.
A Selic vem do BCB e permitiria ancorar a taxa; beta e WACC não existem nas fontes atuais.

### 7 · Crescimento de receita é aplicado ao LPA

Premissa `✅` · Prioridade **alta** · Viável `parcial`

Margem, despesa financeira, imposto e número de ações rompem a relação. Depende de a fonte fornecer
crescimento de lucro, o que hoje não está confirmado.

### 9 · Bazin depende de dividendo histórico

Premissa `✅` · Prioridade **alta** · Viável `sim`

Cinco anos de média incorporam o que não se repete. A guarda existente falha — ver a medição.

### 10 · Yields exigidos são fixos por classe

Premissa `⚠️` · Prioridade média · Viável `parcial`

Eles **são** configuráveis por usuário (`desired_yield_stock` e irmãos). O que não existe é variação
por risco do ativo: mesma taxa para empresa endividada e para empresa sem dívida.

### 11 · VPA é usado como preço justo de FII

Premissa `✅` · Prioridade média · Viável `parcial`

Valor patrimonial contábil não é valor econômico do imóvel. Cap rate e vacância não existem na
fonte, então o caminho realista é rebaixar o VPA a referência, não substituí-lo.

### 13 · Os filtros de Graham dependem do próprio preço

Premissa `✅` · Prioridade média · Viável `sim`

P/L e P/VP usam o preço atual para decidir se o método roda. O método se abstém justamente quando o
preço está alto — circularidade real, e sutil.

### 14 · Graham não se aplica a todo modelo de negócio

Premissa `✅` · Prioridade média · Viável `parcial`

O setor existe na resposta; estrutura de capital, não.

### 17 · Os limiares de margem não têm origem declarada

Premissa `✅` · Prioridade média · Viável `sim`

±15% e ±30% separam Comprar, Manter e Vender sem justificativa escrita.

### 33 · VPA extremo, negativo ou zero

Premissa `⚠️` · Prioridade baixa · Viável `sim`

Conferido: VPA zero e negativo **já** fazem o método se abster. O que não existe é tratamento para
VPA positivo mas absurdo, que entra na faixa sem questionamento — caso particular do item 23.

### 34 · Crescimento negativo, zero e ausente

Premissa `❌` · Prioridade média · Viável `sim`

Conferido: **ausente e zero não são iguais.** Sem dado, o modelo usa o padrão de 8%; com zero ou
negativo, usa 0. Os que se confundem são **zero e negativo** — deterioração e estagnação produzem o
mesmo preço justo. O item continua válido nessa forma menor.

---

## Bloco E · Defeito mecânico, não decisão

Não dependem de decisão de produto. Hoje distorcem número real.

### 8 · A regra de crescimento acima de 25% é uma descontinuidade

Premissa `✅` · Prioridade **alta** · Viável `sim`

Crescimento acima de 25% **não é limitado a 25%: volta ao padrão de 8%**. Uma empresa crescendo 30%
é avaliada como se crescesse 8%, e uma crescendo 24% usa os 24%.

### 12 · Bazin como regra geral para ETF

Premissa `⚠️` · Prioridade baixa · Viável `n/a`

Na prática nenhum ETF de índice tem dividendo que sustente o método: os quatro medidos saem sem
faixa e caem na leitura de tendência. O método está declarado e não produz nada — o que sobra é
limpar a declaração.

### 16 · Os limiares criam saltos abruptos

Premissa `✅` · Prioridade média · Viável `sim`

Variação mínima de preço troca a etiqueta. Histerese resolve sem mudar a régua.

### 20 · Sem valuation, o técnico ainda recomenda comprar ou vender

Premissa `⚠️` · Prioridade baixa · Viável `feito em parte`

Desde 2026-09-19 a resposta declara `basis: trend`, então a distinção existe no dado. O que falta é
a confiança refletir a diferença — o que pertence ao item 25.

### 21 · Ausência de dado não é classificada

Premissa `✅` · Prioridade média · Viável `sim`

Dado ausente, zero, negativo, inconsistente e velho levam à mesma abstenção silenciosa.

### 22 · LPA negativo é tratado como incapacidade do modelo

Premissa `✅` · Prioridade média · Viável `sim`

Prejuízo é informação econômica, não ausência de informação. Caso particular do 21.

### 24 · Dividendo extraordinário contamina o Bazin

Premissa `✅` · Prioridade **alta** · Viável `sim`

Ver a medição: a guarda existe e falha em 2,8×, 4,4× e 5,6× de inflação.

### 25 · A confiança não representa incerteza

Premissa `✅` · Prioridade **alta** · Viável `sim`

Ela é soma de constantes — 0,4 inicial, +0,2 por ter faixa, −0,1 por dispersão, +0,15 por ter
técnico, 0,35 fixo na leitura de tendência. Nenhuma tem relação declarada com qualidade de dado,
convergência ou sensibilidade a premissa.

### 30 · Inaplicável e sem dados são a mesma coisa

Premissa `✅` · Prioridade média · Viável `sim`

Um ETF que nenhum método avalia e uma ação sem LPA no momento produzem a mesma resposta vazia.

### 32 · A precisão exibida excede a precisão real

Premissa `✅` · Prioridade média · Viável `sim`

Centavos e décimos de ponto percentual saem de uma taxa de desconto escolhida a dedo. A casa decimal
promete o que a metodologia não entrega.

---

## O que este documento não decide

Ele **lista e qualifica**; não escolhe. Os blocos A, B e C mudam o que a tela diz sobre quase toda a
base, e essa escolha é de produto — quando for feita, ela vira ADR em
[decisoes/](../decisoes/), e os itens correspondentes são riscados aqui com a data.
