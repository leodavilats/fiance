# ADR-005 — Cache no banco da aplicação, com backend trocável

**Status:** ACEITO
**Data:** ~2026-09 *(escrita retroativamente em 2026-09-13)*

## Contexto

A BRAPI concede 3.000 requisições por dia. O cache não é otimização: é o que torna o produto viável
dentro da cota.

O cache original ficava em arquivo local.

## Problema

Dois problemas, e só um é de desempenho.

**Correção:** com mais de um nó e cache por nó, a **mesma pessoa vê preços diferentes** conforme o
balanceador a mandar para um processo ou outro. Não é lentidão — é o produto dizendo dois números
para a mesma pergunta.

**Custo:** com disco efêmero, o cache em arquivo nasce frio a cada deploy, e a cota da fonte paga a
conta.

Havia ainda um requisito não óbvio: o **disjuntor precisa do dado vencido** para degradar. Um cache
que apenas expira e some não serve — `get_with_age` precisa ler o valor velho e a idade dele.

## Alternativas

1. Cache em arquivo local
2. Redis obrigatório
3. **Cache no banco da aplicação, com backend trocável**

Redis obrigatório foi descartado por adicionar um serviço para resolver um problema que o banco já
resolve, numa operação de uma pessoa só.

## Decisão

**O cache mora onde fizer sentido, e a escolha é automática:**

| Condição | Backend |
|---|---|
| `DATABASE_URL` é Postgres | Banco da aplicação *(padrão)* |
| Banco é local | Arquivo |
| `REDIS_URL` existe | Redis |

`CACHE_BACKEND` (`database`/`sqlite`/`redis`) força a escolha, e **nome errado falha alto**. Cair em
silêncio para cache por nó é defeito que só aparece semanas depois, como uma reclamação de "os preços
não batem".

O vencimento vai **dentro do valor**, inclusive no Redis, porque o disjuntor precisa do dado vencido.

A tabela `cache_entries` não é de ninguém: está em `account_store.GLOBAL_TABLES`.

## Consequências

**Ganhos**

- Correção com mais de um nó, sem serviço adicional
- O cache sobrevive ao deploy
- O disjuntor pode degradar para dado vencido, com a idade visível na tela
- Dois workers no Procfile passaram a ser seguros

**Custos aceitos**

- O banco da aplicação carrega tráfego de cache
- Três caminhos de código em vez de um, e o teste tem de cobrir os três — o CI sobe um Redis de
  serviço por isso
- **O caminho do Redis nunca rodou contra um servidor real fora do CI**. Ver
  [10-PROBLEMAS](../10-PROBLEMAS.md), item 1

## Referências

- [03-ARQUITETURA](../03-ARQUITETURA.md)
- `backend/app/core/cache_backends.py`, `backend/app/collectors/circuit.py`
