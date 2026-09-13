# ADR-010 — Remover `optimizer/` e o enum de estratégias

**Status:** ACEITO
**Data:** 2026-09-13
**Decidido por:** autor do projeto

## Contexto

`backend/app/optimizer/` contém **um arquivo: `__init__.py`, com uma linha**. Nenhum módulo do
projeto o importa.

`models/enums.py` declara `OptimizationStrategy` com quatro valores — `score_weighted`,
`max_sharpe`, `min_volatility`, `hrp` (paridade hierárquica de risco) — e **nada os usa**.

O autor desconhecia a existência de ambos até a entrevista de 2026-09-13.

## Problema

**A documentação descrevia `optimizer/` como camada de regra de negócio.** O `CLAUDE.md` afirmava
que "regra de negócio vive só no backend (`analysis/`, `optimizer/`)" e listava `optimizer` entre os
módulos proibidos de importar `entitlement`.

Um diretório vazio descrito como camada viva tem custo real: o documento é lido a cada sessão de
trabalho por uma IA que escreve a maior parte do código. Uma camada inexistente descrita como
existente é uma instrução para colocar código num lugar que não é lugar nenhum.

O enum tem custo parecido: sugere que o produto tem otimização de carteira por teoria moderna de
portfólio. Não tem.

## Alternativas

1. **Apagar** os dois
2. Manter, e construir a otimização depois
3. Manter o enum e apagar o diretório

## Decisão

**Apagar os dois.** O diretório `backend/app/optimizer/` e o enum `OptimizationStrategy`.

Toda menção a `optimizer/` sai da documentação.

Isso **não** decide contra otimização de carteira como funcionalidade: ela permanece em
[09-FUTURO](../09-FUTURO.md) como `CONSIDERADO`. Decide apenas que um diretório vazio e um enum
órfão não são o começo dela, e que descrevê-los como camada custa mais do que preservá-los.

Se a otimização for construída, ela começa com a pergunta que ninguém respondeu ainda: **Sharpe e HRP
servem a alguém que não tem tempo?**

## Consequências

**Ganhos**

- A documentação passa a descrever camadas que existem
- Um leitor — pessoa ou IA — não supõe capacidade que o produto não tem
- Uma referência a menos para manter em acordo

**Custos aceitos**

- Se a otimização for construída, o diretório e o enum voltam a ser criados. O custo disso é
  desprezível: um diretório e quatro constantes
- O histórico do git preserva o que havia, que é uma linha de `__init__.py`

**Ação necessária no código** — esta ADR não se cumpre sozinha:

```bash
rm -r backend/app/optimizer/
# e remover OptimizationStrategy de backend/app/models/enums.py
```

Registrado em [10-PROBLEMAS](../10-PROBLEMAS.md), seção G.

## Referências

- `backend/app/optimizer/`, `backend/app/models/enums.py`
