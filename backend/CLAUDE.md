# backend

Contrato de trabalho do backend. O que vale para o repositório inteiro está no
[CLAUDE.md da raiz](../CLAUDE.md); o porquê, nas [decisões](../docs/decisoes/).

Leitura da área: [docs/app/](../docs/app/README.md) — [dominio](../docs/app/dominio.md) ·
[arquitetura](../docs/app/arquitetura.md) · [calculos](../docs/app/calculos/README.md) ·
[desenvolvimento](../docs/app/desenvolvimento.md).

```bash
python -m pytest -q
python -m ruff check app tests migrations
python -m ruff format --check app tests
```

---

## Invariantes

### Domínio

- **`ledger/`, `cashflow/` e `analysis/` não conhecem banco.** Se precisar importar `storage/`, a
  solução está errada — passe o dado por parâmetro.
- **Dinheiro fiscal é `Decimal`; dinheiro de tela é `float`.** Escala e arredondamento só em
  `core/money.py`, meio para cima. Nunca construa `Decimal` de `float` sem passar por texto — use
  `money()`. Colunas monetárias são `Money`; agregação é `sum_money()`, nunca `func.sum()`.
- **Fuso fiscal é brasileiro** (`core/brt.py`), não UTC.
- **Veredito vem com o que o derrubaria** (`analysis/falsifiers.py`). Sem preço justo, a lista sai
  vazia — nada de falsificador genérico.
- **Preço justo é um modelo por classe, e a faixa é das premissas dele** (`fair_low`/`fair_high`).
  Nunca média, nunca mínimo e máximo de métodos que medem coisas diferentes. A margem mede contra a
  **borda**: abaixo do piso, sobre o piso; acima do teto, sobre o preço; zero dentro.
- **Nenhum método vota de um lado só, e a faixa não depende do preço que julga.** Graham é
  indicador, nunca borda: dentro do próprio filtro ele sempre fica acima do preço.
- **O yield que a pessoa declara é meta de renda** (`personal_ceiling`), nunca borda da faixa.
- **Juro estimado não avalia.** A taxa de ação sai do juro real do Tesouro IPCA+ mais longo, pela
  `fiance-dados`; o yield de FII, da Selic média de 10 anos (`rates_for_valuation`). Sem o juro da
  classe, o método se cala: ação nunca cai para a Selic, nem desconta por um número do código.
- **Sem faixa, não há leitura de valor** (`decision.basis = none`, "Sem preço justo"). BDR e ETF não
  têm método. A regra vive só em `decide()` — nunca numa tela.
- **Análise técnica não decide**, com faixa ou sem ela. Tendência e RSI são contexto: não mudam a
  leitura nem somam confiança. Os dois saem do mesmo preço.
- **A qualidade limita a etiqueta** (`band_quality`). Frágil nunca passa de abaixo ou acima do preço
  justo. A confirmação por outro insumo entra na qualidade, nunca na borda.
- **A etiqueta descreve posição, não ordem.** "Abaixo do preço justo", nunca "Comprar".
- **Silêncio tem motivo** (`methods[]`). Inaplicável, sem dado, lucro negativo, ROE insuficiente,
  sem juro, taxa implausível e pouco distribuído são coisas diferentes.
- **Falsificador distingue gatilho de premissa** (`kind`). Atravessar limiar reclassifica; refutar
  premissa derruba a tese.
- **Projeção sai como faixa, nunca número único** (`analysis/scenarios.py`). `_low`/`_high` são
  obrigatórios.
- **Modo de afirmação é configuração, não código** (`affirmation.py`, `AFFIRMATION_LEVEL`).

### Carteira e razão

- **Toda escrita do razão passa por `ledger_service` e reprojeta.** `record_entry`, `record_entries`,
  `delete_entry`, `import_entries` são a porta única.
- **O razão é a fonte; a posição é projeção dele.** Não há espelhamento.
- **A apuração de IR também é projeção, e a unidade é o mês.** Não existe imposto gravado numa venda.
- **Uma declaração de posição ancora a linha do tempo.** O que tem data anterior e *soma* é
  descartado com aviso; o que *reduz* continua valendo.
- **Preço médio segue a convenção brasileira:** venda reduz quantidade e custo, nunca a média. O day
  trade (compra e venda no mesmo dia) é apartado na projeção e não toca o preço médio.
- **Evento corporativo é lançamento**, não correção manual.
- **Valor negativo não é lançamento, é sinal trocado.**
- **`PUT /portfolio` é destrutivo** e existe só para importação explícita.
- **Renda fixa é entidade de primeira classe.** Nada de RF em armazenamento local.
- **Importação é prévia + commit:** erro diz a linha, gravação atômica, duplicidade apresentada para
  decisão.
- **Provento por calendário é sugestão, nunca lançamento.** Nada pré-selecionado.

### Caixa

- **Toda escrita passa por `cashflow_service`.**
- **Provento não se lança no caixa — é derivado do razão.** `CashEntry` recusa categoria `provento`
  sem `derived=True`, e `derived` em qualquer outra categoria.
- **Fato e projeção não se misturam.** `livre_agora` é fato; `sobra_piso`/`sobra_teto` é projeção.
- **Sem mês fechado não há estimativa, e ausência não vira zero.**
- **Competência é o dia do pagamento**, não do vencimento.
- **Entrada não tem vencimento.**
- **Taxa anual vira mensal por juros compostos, nunca dividindo por doze.**
- **Dívida se classifica por custo, nunca por tipo. Sem taxa informada não há classe.**
- **A cascata pode terminar sem aporte, e isso é sucesso.**
- **A reserva vem depois da dívida cara, e só existe com alvo declarado.** Declara-se o número de
  meses; a base é o gasto fixo e o saldo é a renda fixa de liquidez diária.
- **Alvo não declarado não julga.** Sem meta declarada, `goals_for_judgement()` devolve lista vazia:
  a composição aparece, o desvio não.
- **Pagamento de dívida sai do caixa e não é consumo.**

### Dados externos

- **Dado externo passa por faixa de plausibilidade.** Campo absurdo vira `None`; preço absurdo
  rejeita o snapshot.
- **Fonte tem disjuntor.** Aberto, nem tenta.
- **`CACHE_BACKEND` errado falha alto.** Cair em silêncio para cache por nó faz a mesma pessoa ver
  preços diferentes.
- **Dado de mercado vale até a próxima carga da base** (`universal.validade`). A base vira uma vez
  por dia de pregão, às 23h (`core/pregao.py::CARGA`, o cron do `data-job`); cotação, histórico e
  varredura valem até lá. Se a base ainda não tem o pregão que já deveria ter, revalida em 30 min.
  Mudar o cron do `data-job` exige mudar `CARGA`.

### API e dados

- **Campo que some é pego por contrato** — de resposta, inclusive aninhado, e de entrada; campo de
  entrada que vira obrigatório (`!`) também. Regravar é `python -m tests.contrato_das_rotas`, no
  mesmo commit.
- **`/api/v1` é canônico**; `/api` é alias em transição.
- **Listas paginam por cursor keyset**, nunca offset.
- **Rota cara casa por sufixo**, não por prefixo — `/api/v1/opportunities` precisa casar.
- **Migração é release command**, não startup. O startup só confere e falha alto.
- **`APP_ENV` não tem default.** Vazio falha alto, e falha fechado.
- **`_session_global()` não filtra por usuário** — é para job cross-tenant, nunca para request.
- **Tabela com `user_id` entra em `account_store.USER_SCOPED_MODELS`.**
- **Coluna nova exige migração Alembic.**

### Sessão e privacidade

- **Acesso 1h, refresh 30 dias rotacionado e queimado no uso.**
- **Dois refreshes simultâneos derrubam a sessão** — a renovação é compartilhada.
- **"Tem carteira" é `portfolio_store.has_holdings()`**, que olha posições **e** renda fixa.
- **Telemetria não leva carteira.** O `before_send` é lista de permissão; chave nova nasce redigida.
- **Evento de produto tem dicionário fechado.** Nome fora dele devolve 422.
- **Exportação, importação e exclusão de conta nunca ficam atrás de plano.** A exportação volta
  só para conta sem dados financeiros, cada parte pela sua porta de escrita.

### Monetização

- **Cerca de plano mora só em `entitlement/`**, e entra desligada. Nenhuma condicional de plano fora
  do módulo; `analysis`/`cashflow`/`collectors`/`ledger` não importam nada dele.
- **Nada é cercado antes da primeira posição salva.**
- **`ENTITLEMENTS_ENABLED` sem `ENTITLEMENTS_ENABLED_AT` falha alto.**
- **O titular de um evento de cobrança sai da sessão de checkout, nunca do corpo.**
- **Ativo da própria carteira nunca consome cota.**

---

## Armadilhas que não quebram o build

- **Escrita seguida de 4xx:** quem decide commit ou rollback é o **status da resposta**, não a
  ausência de exceção. O que precisa sobreviver ao 4xx usa `independent_session()`.

---

## Ao adicionar…

| O quê | Faça também |
|---|---|
| Coluna no model | Migração Alembic |
| Tabela com `user_id` | `account_store.USER_SCOPED_MODELS` |
| Campo de dinheiro | Tipo `Money` |
| Rota | Regravar o contrato no mesmo commit |
| Rota pública nova | Decidir por escrito que ela é pública |
