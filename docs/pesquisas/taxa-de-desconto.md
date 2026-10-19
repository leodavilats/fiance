# Plano — como a taxa de desconto distribui o veredito

**Estado:** `[ENCERRADO]` em 2026-10-19 — **duas candidatas passam no critério, por pouco**; com qualquer uma, mais de 70% das ações seguem acima da faixa. Protocolo `[ACEITO]` pelo autor no mesmo dia, antes da execução, com o critério de 80% como está · **Serve a:**
[10-PROBLEMAS](../10-PROBLEMAS.md), item A12

## A pergunta

> Com cada definição candidata de taxa de desconto, em que proporção a faixa do preço justo põe as
> ações **abaixo**, **dentro** e **acima** dela, mês a mês, de 2011 a 2025?

A [calibração](calibracao.md) mostrou que, com a Selic média de 10 anos + 5 pontos, 9 em cada 10 ações
com faixa ficavam acima do preço justo. A ADR da A12 precisa decidir se essa taxa continua. Esta
pesquisa dá o fato que falta para a decisão: o que cada taxa faz com a régua.

## Esta pesquisa não olha retorno

**Nenhum retorno é calculado nem gravado.** O código da pesquisa lê preço só até a data do veredito.
Por isso ela não gasta período (estudo, validação e prova seguem como estão) e **não pode ser usada
para escolher a taxa que "acerta"**: ela mostra como a régua se distribui, não se a régua prevê.

## As candidatas — no máximo 4, fixadas antes

Todas saem de dado da base, nunca de um número escrito no código: juro estimado não avalia.

| # | Taxa de desconto nominal | De onde vem |
|---|---|---|
| 0 | Selic média de 10 anos + 5 pontos | A de hoje (`rates_for_valuation`) |
| 1 | Selic média de 10 anos + 3 pontos | A mesma base, prêmio menor |
| 2 | Taxa do Tesouro Prefixado mais longo à venda + 5 pontos | `mercado.tesouro`: o juro nominal longo que o mercado cobrava na data, e não a média do passado |
| 3 | Taxa real do Tesouro IPCA+ mais longo à venda + meta de inflação do modelo + 5 pontos | `mercado.tesouro`, com a mesma meta de inflação que o modelo já usa |

Nas candidatas 2 e 3, vale a taxa de venda do último dia útil do mês. Mês sem título à venda fica sem
faixa, com o motivo declarado, e não usa a taxa de outro mês.

Nova candidata só entra por adendo, escrito antes de rodar.

## O modelo é o do app

Como na calibração: a pesquisa monta a `ValuationRates` com a taxa candidata e chama
`compute_fair_price` e `decide()` do backend. O app não muda, e não há segunda fórmula.

## Universo e período

O da calibração: ações com volume mediano de R$ 5 milhões em 63 pregões, sem units, com balanço pela
data de entrega. De **jan/2011 a set/2025**, tudo de uma vez, porque nenhum retorno entra.

## O que sai

Por candidata e por mês:

- a fração de ações **abaixo**, **dentro** e **acima** da faixa, entre as que têm faixa;
- quantas ficam sem faixa, e por qual motivo (`methods[]`): uma taxa pode calar o método por
  "taxa implausível";
- a largura mediana da faixa, como fração do piso.

E um resumo por candidata: a mediana dos meses e os meses de juro mais alto e mais baixo.

## Critério para a ADR — escrito antes de ver

Uma candidata é **compatível com uma régua de posição** se, na mediana dos meses, **nem "acima" nem
"abaixo" passa de 80%** das ações com faixa. Régua que põe quase tudo de um lado só não distingue
nada.

O critério não escolhe a taxa: a escolha é da ADR. Se nenhuma candidata passar, isso também vai para a
ADR, e o caminho deixa de ser trocar a taxa.

## Depois da ADR

Se a ADR trocar a taxa, a ordem do retorno se mede de novo, com outro protocolo:
[calibracao-com-a-taxa-nova](calibracao-com-a-taxa-nova.md).

## Risco declarado

- **O título mais longo muda ao longo do tempo.** Vencimentos novos entram e saem da venda, e a taxa
  "mais longa" salta quando isso acontece. O relatório marca os meses em que o título de referência
  trocou
- **O Tesouro Direto não é a curva de juros inteira.** É o que a base tem de 2005 em diante, e é o
  juro que uma pessoa física de fato conseguia comprar

## Resultado — 2026-10-19

177 fins de mês (jan/2011 a set/2025), retrato de 2026-10-19, 79 ações com faixa por mês em média. As
quatro candidatas tiveram taxa em todos os meses: nenhuma ficou sem título à venda e nenhuma calou o
método por taxa implausível.

| # | Candidata | Taxa (mín.–máx.) | Abaixo | Dentro | Acima | Largura da faixa | Critério |
|---|---|---|---|---|---|---|---|
| 0 | Selic média de 10 anos + 5 | 13,5%–20,4% | 5,6% | 7,6% | **87,7%** | 36% | não passa |
| 1 | Selic média de 10 anos + 3 | 11,5%–18,4% | 10,0% | 14,4% | **76,7%** | 41% | passa |
| 2 | Prefixado mais longo + 5 | 11,0%–21,5% | 6,6% | 9,6% | **83,6%** | 36% | não passa |
| 3 | IPCA+ mais longo + meta + 5 | 11,1%–15,7% | 11,6% | 16,8% | **71,4%** | 43% | passa |

Abaixo, dentro e acima são a mediana dos meses; a largura é a mediana, como fração do piso.

- **A taxa de hoje não passa.** Com ela, a mediana dos meses põe 88% das ações acima da faixa, o que
  confirma, em 15 anos, o que a [calibração](calibracao.md) viu de 2011 a 2017
- **As duas que passam passam por pouco**, e com o mercado ainda pendendo para um lado: com qualquer
  uma, mais de 70% das ações ficam acima da faixa na mediana dos meses
- **O juro não explica tudo.** Na candidata 3, o mês de juro mais baixo (out/2019, 11,1%) teve **mais**
  ações acima (79,5%) do que o de juro mais alto (jan/2016, 15,7%: 73,2%). Em 2016 os preços estavam
  no chão. O desequilíbrio vem também do modelo de lucro, e não só da taxa
- **A candidata 3 é a mais estável** (taxa entre 11% e 16%, com 2 trocas de título de referência),
  porque o juro real longo oscila menos que a Selic e que o prefixado. A 2 trocou de título 10 vezes
- **Sem faixa, pelo mesmo motivo nas quatro:** lucro negativo (3.199 papéis-mês), ROE insuficiente
  (1.867), sem dado (1.801) e units (1.190). A taxa não muda quem tem faixa, só onde ela fica

**Para a ADR da A12:** o critério deixa duas opções, a 1 e a 3, e nenhuma resolve o desequilíbrio
sozinha. A escolha é da ADR. Se ela trocar a taxa, a ordem do retorno se mede pela
[calibração com a taxa nova](calibracao-com-a-taxa-nova.md). Esta pesquisa não mediu retorno de
nenhuma candidata.

Registro em `fiance-trend/backend/registro_taxa.jsonl`; mês a mês em
`fiance-trend/backend/resultados/taxa_de_desconto.json`.
