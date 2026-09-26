# ADR-007 — Nível de afirmação como configuração, não código

**Status:** ACEITO
**Data:** ~2026-08 *(escrita retroativamente em 2026-09-13)*

## Contexto

Quanto o produto pode **afirmar** sobre um investimento é uma questão de posicionamento e de
regulação, e a resposta pode mudar — por decisão do autor, por parecer jurídico, ou por exigência de
loja.

## Problema

Se o quanto o produto afirma estiver **espalhado pelo código** — um texto numa tela, um campo numa
resposta, um rótulo num componente —, mudar de posição vira refactor. E refactor sob pressão, com
prazo externo, é como se perdem invariantes.

O cenário concreto a evitar: uma exigência chega, e a resposta é caçar afirmações em 37 mil linhas.

## Alternativas

1. Escrever o texto onde ele aparece e mudar quando necessário
2. **Um nível de afirmação configurável, que filtra a resposta no servidor**
3. Duas versões do produto

## Decisão

**`AFFIRMATION_LEVEL` é configuração de ambiente, com três níveis**, e o filtro acontece no servidor,
sobre o payload inteiro.

| Nível | Nome | O que entrega |
|---|---|---|
| 1 | Descritivo | Descreve a carteira. Não avalia ativo, não sugere operação |
| 2 | **Analítico** *(padrão)* | Leitura de critérios objetivos, por ativo, com metodologia à vista |
| 3 | Prescritivo | Acrescenta o **valor por ativo** — quanto aportar em quê |

O que sai fora do nível 3 é o **valor por ativo**, que é o que instrui: `amount`,
`suggested_amount`, `suggested_quantity`, `action`, `recommended_action` e outros de `ACTION_FIELDS`.
**A análise que os sustentava fica.**

**Sai também todo campo de onde o valor se reconstrói por aritmética.** Anular o alocado e deixar o
caixa e a sobra é entregar o alocado por subtração. Por isso saem, fora do nível 3, `remaining_cash`
(caixa − alocado), o valor de cada linha de `unallocated` (somado, dá a sobra), o valor e o
percentual de `portfolio_balance` (a carteira *depois* do aporte, que menos a de antes é o aporte da
categoria) e `projected_value`/`projected_pct` da estratégia, pelo mesmo motivo. Onde a chave é
genérica demais para valer em todo payload — `value` —, ela sai só dentro do bloco que a torna
instrução: `ACTION_FIELDS_WITHIN`. Fica o que a pessoa já sabe ou declarou (o caixa que entrou, a
meta), o preço de cada ativo e o **motivo** do que não coube. `tests/test_affirmation.py`
(`TestSubtracao`) tenta reconstruir o alocado pelo caminho de cada campo e exige que falhe.

O aviso ao usuário acompanha o nível, e `/aviso-cvm` lê `affirmation.current()` **no servidor** — uma
segunda cópia da frase desatualizaria justamente onde a pessoa a lê.

Há uma segunda chave, `SUITABILITY_PERSONALIZATION_ALLOWED`, que no nível 3 governa se a saída
continua personalizada. Sem ela, o nível 3 prescreve sem personalizar.

## Consequências

**Ganhos**

- Mudar a postura do produto é **trocar uma variável de ambiente**, com efeito imediato e sem deploy
  de código
- O texto jurídico nunca descreve um nível diferente do que está sendo entregue
- A resposta a uma exigência externa é configuração, não refactor sob pressão — que é exatamente por
  que isto existe

**Custos aceitos**

- Todo payload passa por um filtro recursivo
- Um campo novo que instrui precisa entrar em `ACTION_FIELDS`, e **esquecer disso vaza instrução no
  nível errado, em silêncio**
- O filtro pode anular um campo e deixar de pé uma subtração que dependia dele — foi o que aconteceu
  com `allocated_cash` até 2026-09-25. Campo novo que é soma, diferença ou fatia de um valor de ação
  entra na mesma lista, e o teste de subtração só enxerga o que o cenário dele produz
- Fora do nível 3, a tela de aporte mostra o caixa, a ordem e o motivo do que não coube, mas
  nenhuma cifra do que sai do caixa: o que sobra aparece como —

**Estado atual:** nível **2**. O nível 3 está desligado, e ligá-lo é a decisão registrada em
[ADR-006](ADR-006-recomendacao-personalizada.md).

## Referências

- `backend/app/affirmation.py`
- [ADR-006](ADR-006-recomendacao-personalizada.md)
