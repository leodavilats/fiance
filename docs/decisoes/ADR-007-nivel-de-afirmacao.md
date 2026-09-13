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
  com `allocated_cash`, item 12 de [10-PROBLEMAS](../10-PROBLEMAS.md)

**Estado atual:** nível **2**. O nível 3 está desligado, e ligá-lo é a decisão registrada em
[ADR-006](ADR-006-recomendacao-personalizada.md).

## Referências

- `backend/app/affirmation.py`
- [ADR-006](ADR-006-recomendacao-personalizada.md)
