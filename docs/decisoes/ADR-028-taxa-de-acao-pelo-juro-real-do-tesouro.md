# ADR-028 — A taxa exigida de ação sai do juro real do Tesouro

**Status:** ACEITO
**Data:** 2026-10-19
**Decidido por:** autor do projeto

## Contexto

A taxa exigida do preço justo de ação é a Selic média de 10 anos mais 5 pontos
([ADR-014](ADR-014-um-modelo-por-classe.md)). A [calibração](../pesquisas/calibracao.md) mostrou que,
com ela, 9 em cada 10 ações ficavam acima da faixa de 2011 a 2017, e o item A12 do
[10-PROBLEMAS](../10-PROBLEMAS.md) pediu esta decisão.

A [distribuição do veredito por taxa](../pesquisas/taxa-de-desconto.md) mediu quatro candidatas de
2011 a 2025, **sem olhar retorno**, contra um critério fixado antes: uma régua de posição não pode pôr
mais de 80% das ações de um lado só, na mediana dos meses.

| Candidata | Acima da faixa | Critério |
|---|---|---|
| Selic média de 10 anos + 5 (a de hoje) | 88% | não passa |
| Selic média de 10 anos + 3 | 77% | passa |
| Tesouro Prefixado mais longo + 5 | 84% | não passa |
| Tesouro IPCA+ mais longo + meta de inflação + 5 | 71% | passa |

## Problema

Que taxa o preço justo de ação usa para descontar o lucro?

## Alternativas

1. **Manter a Selic média + 5.** Rejeitada: a régua põe quase tudo acima da faixa e não distingue.
2. **Selic média + 3.** Rejeitada: passa no critério, mas o prêmio de 3 pontos é um número escolhido
   para passar, e a base continua sendo uma média de juro de curto prazo dos últimos dez anos.
3. **O juro real do Tesouro IPCA+ mais longo, mais a meta de inflação, mais 5 pontos.**

## Decisão

A alternativa 3, só para ação:

- **A taxa** é a taxa de venda do **Tesouro IPCA+** (sem juros semestrais) de vencimento mais longo
  entre os que estão à venda no último dia da base, mais a meta de inflação do modelo (3%), mais o
  prêmio de 5 pontos. É o juro real que o mercado cobra hoje por prazo longo, e não a média do passado
- **A fonte é a base própria**, pela `fiance-dados` (`/v1/tesouro`), como todo dado de mercado do
  backend
- **Sem título à venda, ou com a base fora do ar e sem cache, o método se cala** (`sem_juro`). Nada de
  voltar para a Selic: seria outro modelo com o mesmo nome. A degradação é a de sempre: cache válido,
  cache vencido com idade visível, ausência declarada
- **FII não muda.** O rendimento exigido de fundo segue saindo da Selic média de 10 anos
  ([ADR-019](ADR-019-fii-de-papel-exige-yield-nominal.md)): a medida foi feita só em ação
- **A premissa mostra o título:** a taxa real usada e o vencimento do título de referência

## Consequências

**Ganhos**

- A régua de ação deixa de pôr quase todo o mercado acima do preço justo: na mediana de 2011 a 2025,
  71% acima, 17% dentro e 12% abaixo
- A taxa acompanha o juro de longo prazo da data, que oscila menos que a Selic (de 11% a 16% em 15
  anos, contra 13% a 20%)
- A base da taxa passa a ser dado de mercado da base própria, e não só a série do BCB

**Custos aceitos**

- **Ainda pende para um lado.** Mais de 70% das ações seguem acima da faixa. A taxa não é o único
  motor do desequilíbrio; o modelo de lucro também é
- **O veredito de ação muda para todo mundo.** Uma ação que estava acima da faixa pode passar para
  dentro sem que o preço tenha mexido
- **Ação e FII passam a ter bases de juro diferentes.** A tela diz qual é a de cada um
- **O título de referência muda** quando um vencimento novo entra ou sai da venda, e a taxa salta
  junto. Na medida de 15 anos, isso aconteceu duas vezes
- **Esta decisão não diz que o veredito prevê retorno.** Isso se mede na
  [calibração com a taxa nova](../pesquisas/calibracao-com-a-taxa-nova.md), que só pôde rodar depois
  desta ADR
