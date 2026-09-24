# ADR-014 — Um modelo por classe, e a faixa é das premissas dele

**Status:** ACEITO · substitui em parte a [ADR-011](ADR-011-preco-justo-e-faixa.md) e a
[ADR-013](ADR-013-o-tecnico-nao-decide.md)
**Data:** 2026-09-23
**Decidido por:** autor do projeto, que delegou as escolhas desta revisão

## Contexto

A [revisão de metodologia de 2026-09-23](../historico/REVISAO-METODOLOGIA-VALUATION-2026-09-23.md)
avaliou o caminho do tipo do ativo ao veredito como engenharia financeira, e não como conformidade
entre código e diagrama. Os princípios das ADRs 011 e 013 se sustentaram: faixa em vez de média,
margem contra a borda, técnico fora do veredito, silêncio com motivo. **Os métodos dentro deles não.**

## Problema

Seis defeitos críticos, todos reproduzidos contra o código:

1. **Graham só votava "barato".** Com P/L ≤ 15 e P/VP ≤ 1,5, `P² ≤ 22,5 × LPA × VPA`: sempre que
   o método se calculava, ficava acima do preço. Com ele na faixa, venda era impossível; quando ele
   sumia, a faixa saltava — R$ 12,00 era Manter e R$ 12,01, Vender com urgência.
2. **Etiqueta forte sobre evidência fraca.** Empresa em prejuízo que tinha parado de pagar recebia
   "Comprar com convicção", com confiança baixa, pelo Bazin do histórico.
3. **Armadilha de dividendo.** A média de cinco anos não via corte: numa série 2, 2, 2, 0,5, 0,3, o
   Bazin valia 4,5× o que o último ano sustentava.
4. **A faixa era divergência, não incerteza.** Mínimo e máximo de métodos com alvos diferentes, e o
   veredito dependia mais do payout que do valor.
5. **BDR descontado em moeda errada.** Selic sobre lucro em dólar: todo BDR saía caro.
6. **Técnico decidia quando não havia valor**, com o mesmo vocabulário do valuation.

E, entre os importantes: o "DCF" somava o lucro retido e ainda creditava o crescimento que ele
gera; o P/L terminal 15 neutralizava a ligação com o juro; o crescimento era de receita, com 8%
inventado quando faltava; a margem de venda disparava com 23% de distância e a de compra exigia 43%.

## Alternativas

1. **Correções locais** — tirar Graham, guardar o Bazin, limitar a etiqueta — mantendo o mínimo e
   máximo de métodos
2. **Um modelo principal por classe**, com a faixa vindo das premissas dele e outro insumo como
   confirmação
3. Média ou mediana dos métodos, que a ADR-011 já rejeitou
4. Um DCF de fluxo de caixa livre, que a fonte não sustenta (sem capex, capital de giro nem dívida
   líquida por empresa)

A 1 resolve os sintomas e mantém a faixa medindo divergência. A 2 muda **o que se combina**, não
**como**: não acrescenta método nenhum.

## Decisão

**Alternativa 2.** Cada classe tem um modelo principal, a faixa é a sensibilidade dele às premissas,
e a leitura por outro insumo diz se confirma.

### O modelo de ação

```
V = Σ_{t=1..5} LPA_n·(1+g)^t·(1 − g/ROE) ÷ (1+d)^t
  + LPA_n·(1+g)^5·(1+g_T)·(1 − g_T/ROE) ÷ ((d − g_T)·(1+d)^5)
```

- **Só se desconta o que pode ser distribuído** (`1 − g/ROE`). Em regime estável é a mesma equação
  do P/VP justificado, `VPA·(ROE − g) ÷ (d − g)` — banco passa a ser avaliado pelo mesmo modelo.
- **O crescimento sai do ROE e do que a empresa retém**, com teto de 20%. Sem ROE, o método se cala:
  o 8% padrão acabou.
- **O terminal sai da mesma taxa**, por Gordon. O P/L 15 fixo acabou.
- **O LPA é a média dos 3 últimos exercícios**, escalada pela razão entre lucros — em unit, lucro
  dividido por número de ações não dá o LPA da unit.

### O modelo de FII

`distribuição recorrente ÷ yield exigido`. A Lei 8.668/93 obriga a distribuir 95% do resultado de
caixa: o dividendo **é** o fluxo, e o Bazin deixa de ser heurística aqui.

### A taxa — onde esta ADR diverge da revisão

A revisão propôs a Selic média de 24 meses. **Medido, isso punha quase toda ação acima do preço
justo**: a média de 24 meses estava em 14%, a taxa em 19%, e a taxa em que o mercado precifica as
pagadoras maduras fica perto de 13,5%. Custo de capital é taxa de longo prazo, e dois anos no pico
do ciclo não são longo prazo.

**A base é a Selic média de 10 anos** (série 4189 do SGS), que atravessa mais de um ciclo do Copom:

```
d_ação = Selic média 10a + 5 pontos                       (hoje: 14,5%)
g_T    = meta de inflação (3%) + 1,5% real                 (4,5%)
y_FII  = máx(Selic média 10a − meta de inflação, 3%) + 3 pontos   (hoje: 9,5%)
```

O juro real de longo prazo que sai daí (6,5%) fica perto do que as NTN-B longas pagam. Sem a série,
entra a Selic do dia, e a resposta diz qual base usou. Com juros estimados, não há avaliação: a
estimativa é um número do código, e ele não pode decidir o preço justo.

### A faixa, a confirmação e a qualidade

- **Faixa:** do cenário sem crescimento e com 1 ponto a mais de taxa ao cenário com crescimento e 1
  ponto a menos. É incerteza real sobre o valor, não distância entre métodos.
- **Confirmação:** na ação, o dividendo recorrente crescendo no menor entre o crescimento sustentável
  e o de longo prazo. No FII, o VPA. Ela não define borda.
- **Qualidade:** `frágil` com lucro de menos de 3 exercícios ou instável, corte de distribuição, ou
  confirmação a mais de 30% da faixa; `ampla` sem confirmação, com confirmação perto da faixa, ou com
  faixa larga; `firme` no resto. **Frágil nunca passa de "abaixo" ou "acima" do preço justo.**
- **Confiança** sai só da qualidade: 0,70, 0,45, 0,30.

### O dividendo recorrente

`mín(média dos anos completos com cada um limitado a 2× a mediana dos outros, o mais recente)`. É
contínuo — 2,9× e 3,1× dão o mesmo resultado —, pega corte, e não apaga uma mudança de política para
cima. O custo: quem cresce o dividendo com a inflação sai cerca de 9% abaixo do último ano.

### A margem

```
abaixo do piso:  (piso − preço) ÷ piso
acima do teto:   (teto − preço) ÷ preço
```

As duas pontas medem a mesma distância em escala logarítmica, e a de venda para de ir a −∞.

### O vocabulário

As etiquetas passam a descrever posição: **Bem abaixo · Abaixo · No preço justo · Acima · Bem
acima · Sem preço justo**. A tela dizia *"não é recomendação de compra"* embaixo de *"Comprar com
convicção"*; "Vender com urgência" afirmava uma pressa que valuation não mede. Os códigos
(`STRONG_BUY`…) ficam, porque carteira, alertas e estratégia os leem.

### O que sai da faixa, e para onde vai

| Sai | Vira |
|---|---|
| Graham | indicador: o critério defensivo, passa ou não, com o preço-limite |
| O yield que a pessoa declara | **preço-teto da meta de renda**, ao lado da faixa |
| A leitura por tendência | nada — sem faixa, "Sem preço justo"; o técnico continua como contexto |

O preço-teto da meta preserva a personalização da [ADR-006](ADR-006-recomendacao-personalizada.md),
e com mais precisão: a frase-alvo era *"está 20% abaixo do preço justo **e cabe na sua meta de
renda**"* — duas afirmações que a faixa antiga fundia numa só.

### BDR e ETF

Sem preço justo. BDR porque a única taxa disponível é em reais; ETF porque o preço dele acompanha o
valor do que carrega. Os dois mostram o técnico como contexto, e dizem por que não há faixa.

## Consequências

Medido em 2026-09-23 sobre 27 ativos, pela coleta real (BRAPI e SGS):

| Leitura | Ativos |
|---|---|
| No preço justo | 12 |
| Acima | 7 |
| Bem acima | 4 — WEGE3, RADL3, ABEV3, BBDC4 |
| Abaixo | 1 — MXRF11 |
| Sem preço justo | 3 — MGLU3 (prejuízo), AAPL34 (BDR), BOVA11 (ETF) |

Quem sai caro é quem o mercado paga por crescimento acima do sustentável: a taxa em que o valor
iguala o preço de WEGE3 é 8,5%, de RADL3, 7,9%. TAEE11 e EGIE3 saem no preço justo com qualidade
firme, com taxa de equilíbrio de 13,5%.

**Ganhos**

- Nenhum método vota de um lado só; a faixa não depende do preço que julga
- A etiqueta nunca é mais forte que a evidência
- Banco ganha avaliação coerente; empresa em prejuízo deixa de ser compra
- As premissas ficam na tela, e o falsificador diz a taxa em que o valor iguala o preço

**Custos aceitos**

- **Muda o preço justo e a etiqueta de toda a base.** Quem via "Comprar" passa a ver "Abaixo do
  preço justo"
- **BDR e ETF perdem leitura de valor.** Era leitura enviesada ou de outra natureza
- **FII de papel parece barato.** Ele distribui a correção monetária como rendimento, e sem o
  subtipo do fundo o modelo não distingue isso. Declarado no 10-PROBLEMAS
- **Os parâmetros continuam sem calibração empírica.** Prêmio de 5 pontos, 3 pontos de FII, 1,5% de
  crescimento real, teto de 20%, bandas de ±15 e ±30%. Validá-los exige fundamento *point-in-time*,
  que a BRAPI não entrega
- `consensus`, `bazin`, `graham` e `dcf` continuam na resposta, com o significado novo descrito no
  modelo; o app em loja os lê

## Referências

- `backend/app/analysis/fair_price.py` · `backend/app/analysis/decision.py` ·
  `backend/app/analysis/falsifiers.py` · `backend/app/services/valuation.py`
- `backend/app/collectors/rates.py` (Selic de 10 anos) · `backend/app/collectors/universal.py`
  (séries anuais)
- `backend/tests/test_fair_price.py` · `backend/tests/test_revisao_do_valuation.py`
- [REVISAO-METODOLOGIA-VALUATION](../historico/REVISAO-METODOLOGIA-VALUATION-2026-09-23.md) ·
  [04-CALCULOS](../04-CALCULOS.md)
