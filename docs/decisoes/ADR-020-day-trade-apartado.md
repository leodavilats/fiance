# ADR-020 — Day trade é apartado na projeção, e apurado em conta própria

**Status:** ACEITO
**Data:** 2026-09-25
**Decidido por:** agente de desenvolvimento, por delegação do item 20 do 10-PROBLEMAS; as escolhas
abertas estão declaradas aqui

## Contexto

A apuração de IR é projeção do razão, com o mês como unidade
([02-DOMINIO](../02-DOMINIO.md#regras-de-imposto)). Até aqui ela tratava toda venda como operação
comum: custo pelo preço médio, 15% ou 20% por categoria, isenção de R$ 20 mil em ações. Compra e
venda do mesmo ativo no mesmo dia saía como venda comum, com a alíquota e a isenção erradas, e o
preço médio da posição absorvia a compra do dia.

O razão guarda só a data (`traded_on`), sem hora e sem corretora.

## Problema

A regra da Receita aparta o day trade: a quantidade casada no dia é apurada à parte, a 20%, sem
isenção, e o prejuízo dela só compensa ganho da mesma espécie. O que sobra de compra entra no preço
médio; o que sobra de venda é venda comum contra ele. A corretora retém 1% do resultado positivo do
dia.

Se só a apuração apartasse o day trade, a carteira mostraria um preço médio e a apuração usaria
outro.

## Alternativas

1. **Apartar só na apuração.** Rejeitada: o preço médio da tela divergiria do fiscal, e a venda
   comum seguinte seria apurada contra uma média que a pessoa não vê.
2. **Apartar na projeção** (`ledger/projection.py`), que alimenta a posição e a apuração.
3. **Esperar hora e corretora no modelo.** Rejeitada: coluna nova e importação nova para um caso
   que a data já resolve, desde que a limitação fique declarada.

## Decisão

A alternativa 2. Em cada dia com compra **e** venda do mesmo ativo, a projeção casa
`mín(comprado, vendido)` pelos preços médios do dia, com as taxas na proporção do que casou, e
registra uma `Realizacao` de day trade. A sobra de compra entra na média; a sobra de venda sai contra
ela. A ordem de registro dentro do dia deixa de importar, e vender antes de comprar no mesmo dia
deixa de ser "venda sem posição".

As escolhas abertas:

- **Corretora única.** Sem corretora no razão, compra numa e venda noutra no mesmo dia vira day
  trade. É o caso raro, e fica declarado ao usuário.
- **A separação por categoria continua.** O day trade tem conta própria por categoria
  (`acoes_br`, `bdrs`, `etfs`, `fiis`), como a operação comum já tinha. No FII a Receita junta comum
  e day trade na mesma ficha, a 20% nos dois. Aqui ficam separados, e o prejuízo de day trade de FII
  não abate ganho comum de FII. O erro, quando existe, é para mais imposto.
- **A venda de day trade conta no volume da isenção.** A lei fala do "total das alienações" de ações
  no mês, e a venda casada é alienação. Ler assim nunca faz alguém pagar menos do que deve.
- **O IRRF é 1% do resultado líquido do dia, por categoria**, e só quando positivo. Ele se deduz do
  imposto de day trade da mesma categoria; o que sobra passa para os meses seguintes. A Receita
  permite abatê-lo de outros impostos de renda variável, e aqui ele fica na própria conta: de novo,
  o erro é para mais.
- **A linha de day trade em Encerradas leva o `id` da última venda do dia.** A rota de venda procura
  a linha pelo lançamento que acabou de gravar, e a ordenação desempata por `id × 2 + day_trade`.

## Consequências

**Ganhos**

- A alíquota, a isenção e a compensação do day trade saem certas
- O preço médio da carteira é o mesmo da apuração, e segue a convenção da Receita
- A ordem de registro dentro do dia não muda número nenhum

**Custos aceitos**

- Quem já tinha compra e venda no mesmo dia vê o preço médio mudar ao atualizar: era o número errado
- Três leituras conservadoras (FII separado, volume da isenção, IRRF na própria conta) podem mostrar
  imposto maior que o devido
- Corretora única é premissa, não dado

## Referências

- `backend/app/ledger/projection.py` · `backend/app/ledger/apuracao.py`
- `backend/tests/test_day_trade.py`
- [04-CALCULOS](../04-CALCULOS.md), seção *Apuração de imposto*
