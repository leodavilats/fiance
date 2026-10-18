# ADR-026 — O preço confirma o evento na medida do tamanho dele

**Status:** ACEITO
**Data:** 2026-10-18
**Decidido por:** autor do projeto

## Contexto

O data-job só ajusta a série por um evento da B3 depois de o preço confirmar o que foi publicado
([ADR-022](ADR-022-dados-de-mercado-coletados-em-lote.md)). A confirmação compara a razão entre o
fechamento da véspera e a abertura seguinte com o fator do evento, e aceita até **12%** de diferença.

A [validação contra a brapi](../pesquisas/validacao-brapi.md) mostrou que a folga fixa erra dos dois
lados:

- **Recusa evento grande que aconteceu.** Num grupamento de 100 para 1, a razão observada de 86 fica
  14% fora; a série não ajusta e guarda um ganho de 8.066% num dia (BTYU11). O mesmo com PDGR3
  (+11.100%), SEQL3 e outros 82 eventos.
- **Aceita evento pequeno por acaso.** Numa bonificação de 10%, a razão 1,0 — o preço não se mexeu —
  está a 9% do fator e passa. A queda esperada é do tamanho do ruído de um dia; o preço não decide.

## Problema

Qual regra de confirmação acompanha o tamanho do evento, sem aceitar o que o preço desmente?

## Alternativas

1. **Alargar a folga fixa.** Rejeitada: 25% aceitaria uma bonificação de 20% com o preço parado, e
   ainda recusaria o grupamento de 100 com razão 70.
2. **O preço mais perto do fator do que de 1.** Rejeitada na medição: não limita o exagero — um
   desdobramento de 2 com razão 14,9 passaria — e aceita evento pequeno que o preço desmente.
3. **Folga proporcional ao tamanho, com veto no evento pequeno.**

## Decisão

A alternativa 3, em escala logarítmica:

- **Evento grande** (o fator passa de 25% para cima ou para baixo): confirma quando a razão observada
  fica a até **metade da distância** entre o fator e 1. Para 2 para 1, de 1,41 a 2,83; para 10 para 1,
  de 3,2 a 32; para 100 para 1, de 10 a 1.000.
- **Evento pequeno** (até 25%): **vale o que a B3 publicou**, a menos que o preço o desminta por mais
  de 25%.

Medido em produção antes de aplicar: 85 eventos passam de divergente a confirmado, nenhum perde a
confirmação, e os 30 que continuam recusados são todos desmentidos pelo preço — o Itaú de 2011 (100
para 1 publicado, preço parado), GSHP3 (2 para 1 publicado, razão 14,9), ETER3, SUZB6 e outros.

## Consequências

**Ganhos**

- A série deixa de guardar ganhos e perdas de milhares por cento que eram evento
- Bonificação pequena entra pela publicação, não por sorte do pregão
- O que o preço desmente continua de fora, e marcado ([migração 0021](../../data-job/migrations/versions/0021_salto_perto_de_fator.py))

**Custos aceitos**

- O histórico ajustado de 85 papéis muda — retorno passado que alguém já tenha usado sai diferente
- Num evento grande, uma razão a meio caminho entre o fator e 1 passa: a folga é larga de propósito,
  porque papel pouco líquido abre longe do fechamento no dia do evento
