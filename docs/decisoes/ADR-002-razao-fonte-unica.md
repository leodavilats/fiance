# ADR-002 — Livro-razão como fonte única da carteira

**Status:** ACEITO
**Data:** ~2026-08 *(escrita retroativamente em 2026-09-13)*

## Contexto

A carteira precisa mostrar posição, preço médio e resultado. O imposto precisa apurar ganho por mês.
Ambos derivam dos mesmos fatos: compras, vendas, proventos, eventos corporativos.

A implementação original mantinha **duas verdades**: uma tabela de posições, escrita diretamente, e
uma lista de lançamentos ao lado. As duas eram atualizadas em paralelo.

## Problema

Duas verdades divergem. E divergiram de formas concretas:

- `POST /transactions`, o lote e a importação escreviam direto no store **sem reprojetar**. A pessoa
  colava o extrato, o produto respondia `{"imported": 47}`, e a carteira não mudava
- o imposto era gravado na venda, então a **ordem de registro dentro do mês** mudava o número, a
  isenção de R$ 20 mil não era reavaliada, e a venda vinda de `POST /transactions` não apurava nada
- a reconciliação comparava duas verdades, o que só diz que discordam — não qual está certa

## Alternativas

1. **Manter duas verdades e sincronizar** com mais cuidado
2. **Razão como fonte única**, posição e imposto como projeções recalculáveis
3. Posição como fonte, razão como log de auditoria

A alternativa 3 foi descartada porque o imposto brasileiro **exige** o histórico: preço médio,
compensação de prejuízo e isenção mensal não são deriváveis de um saldo.

## Decisão

**O livro-razão é a fonte; tudo o mais é projeção dele.**

- a escrita grava **só lançamento** e reconstrói a linha de posição a partir dele
- não há mais espelhamento
- `ledger_service` é a **porta única**: `record_entry`, `record_entries`, `delete_entry`,
  `import_entries`
- a apuração de imposto é projeção, e **não existe campo de imposto gravado numa venda**
- `rebuild_projection` refaz tudo do zero
- a reconciliação confere a projeção **contra a fonte**, não contra outra verdade

Uma declaração de posição ancora a linha do tempo, com assimetria proposital: o que tem data anterior
e **soma** posição é descartado com aviso; o que **reduz** continua valendo.

## Consequências

**Ganhos**

- Impossível, por construção, a carteira discordar dos lançamentos
- A apuração de imposto sempre reflete a regra atual, não a que valia quando a venda foi gravada
- A ordem de registro dentro do mês deixou de importar
- Reprocessar é sempre possível

**Custos aceitos**

- Toda escrita reprojeta, o que custa mais que gravar um saldo
- Categoria **não** é derivável do razão e viaja junto com a escrita
- Escrever direto no `ledger_store` a partir da API é um erro que não quebra nada visivelmente — por
  isso é invariante documentado

**Consequência não prevista, hoje aberta:** o razão é a camada mais bem construída do sistema e
**não tem nenhuma tela no aplicativo** desde a remoção do front web. Ver
[10-PROBLEMAS](../10-PROBLEMAS.md), seção D.

## Referências

- [02-DOMINIO](../02-DOMINIO.md)
- `backend/app/ledger/`, `backend/app/services/ledger_service.py`
