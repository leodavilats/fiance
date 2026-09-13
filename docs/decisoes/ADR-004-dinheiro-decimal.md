# ADR-004 — Dinheiro fiscal em `Decimal`, dinheiro de tela em `float`

**Status:** ACEITO
**Data:** ~2026-07 *(escrita retroativamente em 2026-09-13)*

## Contexto

O sistema calcula imposto de renda. O número que sai da apuração é o número que a pessoa declara à
Receita Federal.

## Problema

`float` é binário e não representa exatamente valores decimais. Somar centenas de operações em
`float` acumula erro, e o erro aparece exatamente onde não pode: no valor do imposto.

Havia um agravante específico e não óbvio: **o tipo `NUMERIC` do SQLite é `real` por baixo**. Declarar
uma coluna como `Numeric` e desenvolver contra SQLite dá a impressão de precisão exata, e o erro só
aparece em produção — ou, pior, não aparece, e o número declarado fica errado em centavos.

## Alternativas

1. `float` em tudo, arredondando na saída
2. `Decimal` em tudo, inclusive nas respostas da API
3. **`Decimal` no cálculo fiscal, `float` na fronteira de saída**
4. Inteiro em centavos

A alternativa 2 foi descartada porque JSON não tem `Decimal`, e serializar como string exigiria que
cada cliente convertesse — mais superfície de erro, não menos. A 4 é correta e foi descartada por
custo de conversão em toda a base.

## Decisão

**`Decimal` para dinheiro fiscal; `float` para dinheiro de tela.** A conversão acontece na fronteira
do store.

Regras que sustentam isso:

- escala e arredondamento **só** em `core/money.py`, meio para cima, **não** bancário
- **nunca construa `Decimal` a partir de `float`** sem passar por texto — use `money()`
- colunas monetárias são `Money` (`ExactNumeric`): inteiro escalado por 10⁸ no SQLite, `Numeric` no
  Postgres
- agregação de dinheiro é `sum_money()` em Python, **nunca `func.sum()`** no banco

`tests/test_money_columns.py` reprova campo de dinheiro fora do tipo, e um `Float` novo precisa ser
declarado como carimbo de tempo ou percentual para passar.

## Consequências

**Ganhos**

- O número que vai para a declaração é exato
- O teste impede regressão silenciosa
- O comportamento é idêntico em SQLite e Postgres

**Custos aceitos**

- Duas representações do mesmo conceito, e uma fronteira onde a conversão acontece
- `func.sum()` não pode ser usado em coluna de dinheiro, o que empurra agregação para o Python e
  custa memória em conjuntos grandes
- Arredondamento meio para cima difere do padrão do Python (bancário), e isso precisa estar escrito
  ou alguém "corrige"

## Referências

- [02-DOMINIO](../02-DOMINIO.md), seção Unidades
- `backend/app/core/money.py`, `backend/tests/test_money_columns.py`
