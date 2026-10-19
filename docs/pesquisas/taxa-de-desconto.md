# Plano — como a taxa de desconto distribui o veredito

**Estado:** `[PROPOSTO]` em 2026-10-19 — aguarda o aceite do autor; nada rodou · **Serve a:**
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
