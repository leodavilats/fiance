# Plano — o veredito com a taxa da ADR, medido contra o que veio depois

**Estado:** `[PROPOSTO]` em 2026-10-19 — aguarda o aceite do autor; **só pode rodar depois da ADR da
A12** ([10-PROBLEMAS](../10-PROBLEMAS.md)), e só se ela trocar a taxa

## A pergunta

> Com a taxa de desconto escolhida na ADR, a ação **abaixo do preço justo** rendeu mais, nos 12 meses
> seguintes, que a ação **acima**?

É a pergunta da [calibração](calibracao.md), com uma única mudança: a taxa. Se a ADR mantiver a taxa
de hoje, esta pesquisa não roda, porque a execução 0 já respondeu.

## O que é igual à calibração

Tudo, menos a taxa: o modelo do app sem cópia, só o que se sabia na data, o universo, os períodos, a
medida e as quatro condições juntas (abaixo menos acima ≥ 3 pontos ao ano, t de Newey-West ≥ 2, ordem
abaixo > dentro > acima, 10 ações em cada ponta em 80% dos meses).

## Teto: uma variação

**A taxa da ADR, e só ela.** Nada de prêmio, crescimento ou janela ajustados aqui. Se não passar, a
conclusão é "nem com a taxa nova o veredito ordena o retorno", e ela vai para o 10-PROBLEMAS.

- **Passa no estudo** (vereditos de jan/2011 a dez/2017): libera a validação, uma vez
- **Passa na validação** (vereditos de jan/2019 a dez/2021): libera a prova, uma vez
- A prova (2023-01 a 2025-09) segue lacrada até lá

## A taxa não pode ter sido escolhida pelo retorno

A ADR se apoia na [distribuição do veredito](taxa-de-desconto.md), que não olha retorno. **Se alguém
tiver medido retorno por taxa antes da ADR, esta pesquisa perde o estudo**: roda direto na validação,
e o relatório diz por quê.

## Risco declarado

- **O estudo já foi olhado** com a taxa de hoje. O que se viu foi o retorno por grupo, não por taxa;
  mesmo assim, a régua que vale é a validação
- **Os riscos da calibração continuam valendo:** ações perderam do CDI de 2011 a 2018, as janelas de
  12 meses se sobrepõem e o balanço reapresentado entra como se fosse sabido antes
