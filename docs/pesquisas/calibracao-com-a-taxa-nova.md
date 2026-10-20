# Plano — o veredito com a taxa da ADR, medido contra o que veio depois

**Estado:** `[ENCERRADO]` em 2026-10-19 — **nem com a taxa nova o veredito ordena o retorno**: a ordem
aparece, mas sem tamanho nem força. Protocolo `[ACEITO]` pelo autor no mesmo dia; rodou depois da
[ADR-028](../decisoes/ADR-028-taxa-de-acao-pelo-juro-real-do-tesouro.md), que escolheu a taxa sem olhar retorno

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

## Resultado — 2026-10-19: não passou no estudo

Taxa da ADR-028 (Tesouro IPCA+ mais longo + meta de inflação + 5 pontos), vereditos de jan/2011 a
dez/2017, 84 meses, retrato de 2026-10-19:

| | Taxa de hoje ([calibração](calibracao.md)) | Taxa da ADR-028 | Para passar |
|---|---|---|---|
| Abaixo, retorno médio em 12 meses | 4,0% | 6,3% | — |
| Dentro | 5,3% | 4,7% | — |
| Acima | 3,0% | 3,6% | — |
| Abaixo menos acima | −0,7 ponto | +1,1 ponto | ≥ 3 pontos: **não** |
| t de Newey-West | −0,09 | 0,18 | ≥ 2: **não** |
| Ordem abaixo > dentro > acima | não | **sim** | sim: **sim** |
| Meses com 10 ações em cada ponta | 0% | 11% | ≥ 80%: **não** |
| Ações por mês: abaixo, dentro, acima | 2,8 · 3,3 · 48,8 | 5,5 · 8,5 · 41,5 | — |

- **A ordem passou a aparecer, mas pequena e sem força.** 1,1 ponto ao ano, com t de 0,18, é o que o
  acaso produz com essa amostra
- **O grupo abaixo continua pequeno demais.** Cinco ações por mês em média; em 89% dos meses, menos
  de 10. Com a régua ainda pendendo para cima, não há amostra para medir o lado de baixo
- **Pelo protocolo, a validação segue lacrada** e a prova também. A conclusão é "nem com a taxa nova o
  veredito ordena o retorno"

Isso não desfaz a ADR-028: ela escolheu a taxa pela régua, não pela previsão, e diz isso. O preço
justo continua descrevendo posição, não antecipando retorno.

Registro em `fiance-trend/backend/registro_calibracao_taxa_nova.jsonl`; mês a mês em
`fiance-trend/backend/resultados/calibracao_taxa_nova_estudo.json`.
