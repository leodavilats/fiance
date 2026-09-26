# fiance

Plataforma de análise de investimentos focada na B3, multi-tenant.
**FastAPI + Postgres** (`backend/`) · **Flutter** (`mobile/`), o único cliente.

Este arquivo é o **contrato de trabalho**: o que não pode ser violado, e as armadilhas que não
quebram o build. Ele não descreve o sistema — isso é [docs/](docs/), e
[docs/README.md](docs/README.md) diz qual arquivo responde o quê.

| Quero saber | Leia |
|---|---|
| **Isto existe? Em que estado?** | [docs/08-ESTADO.md](docs/08-ESTADO.md) |
| Rodar, instalar, variáveis | [README.md](README.md) · [docs/07-OPERACAO.md](docs/07-OPERACAO.md) |
| Visão, público, negócio | [docs/01-PRODUTO.md](docs/01-PRODUTO.md) |
| Vocabulário e regras de negócio | [docs/02-DOMINIO.md](docs/02-DOMINIO.md) |
| Camadas, fronteiras, segurança | [docs/03-ARQUITETURA.md](docs/03-ARQUITETURA.md) |
| Fórmulas e suas limitações | [docs/04-CALCULOS.md](docs/04-CALCULOS.md) |
| Regras de tela | [docs/05-INTERFACE.md](docs/05-INTERFACE.md) |
| Como trabalhar sem quebrar | [docs/06-DESENVOLVIMENTO.md](docs/06-DESENVOLVIMENTO.md) |
| Por que uma decisão foi tomada | [docs/decisoes/](docs/decisoes/) |
| O que está aberto **agora** | [docs/10-PROBLEMAS.md](docs/10-PROBLEMAS.md) |
| O que vem depois | [docs/09-FUTURO.md](docs/09-FUTURO.md) |

**Histórico não é pendência.** Nada em [docs/historico/](docs/historico/) é trabalho a fazer, mesmo
quando descreve um problema. O que está aberto está no 10-PROBLEMAS, e só lá.

---

## Pronto = suíte verde

**Esta é a lista do CI, não um subconjunto dela.**

```bash
cd backend && python -m pytest -q
cd backend && python -m ruff check app tests migrations
cd backend && python -m ruff format --check app tests
cd mobile  && flutter analyze && flutter test
cd mobile  && flutter build apk --release
cd mobile  && python tool/build_icons.py --check
```

- **Não rode `dart format`** — reescreve o `design_tokens.dart` e quebra os `if`s de uma linha.
- **`analyze` e `test` nunca tocam o Gradle.** O build Android é outra metade, e é o comando que
  ninguém roda. Obrigatório ao mexer em plugin, `pubspec.yaml` ou `mobile/android/`.

---

## Invariantes

O que não pode ser violado. O **porquê** está nas [decisões](docs/decisoes/).

### Domínio

- **Regra de negócio vive só no backend** (`analysis/`, `ledger/`, `cashflow/`). O aplicativo delega.
- **`ledger/`, `cashflow/` e `analysis/` não conhecem banco.** Se precisar importar `storage/`, a
  solução está errada — passe o dado por parâmetro.
- **Régua de score em um lugar por plataforma:** `analysis/score_ruler.py` e
  `mobile/lib/core/score_ruler.dart`. Mudar um limiar exige os dois, **Python primeiro**.
- **Dinheiro fiscal é `Decimal`; dinheiro de tela é `float`.** Escala e arredondamento só em
  `core/money.py`, meio para cima. Nunca construa `Decimal` de `float` sem passar por texto — use
  `money()`. Colunas monetárias são `Money`; agregação é `sum_money()`, nunca `func.sum()`.
- **Fuso fiscal é brasileiro** (`core/brt.py`), não UTC.
- **Unidades:** `roe`, `profit_margin`, `revenue_growth`, `debt_to_equity` chegam em **percentual**.
  Yield desejado e margem de segurança são **fração**.
- **Veredito vem com o que o derrubaria** (`analysis/falsifiers.py`). Sem preço justo, a lista sai
  vazia — nada de falsificador genérico.
- **Preço justo é um modelo por classe, e a faixa é das premissas dele** (`fair_low`/`fair_high`).
  Nunca média, nunca mínimo e máximo de métodos que medem coisas diferentes. A margem mede contra a
  **borda**: abaixo do piso, sobre o piso; acima do teto, sobre o preço; zero dentro.
- **Nenhum método vota de um lado só, e a faixa não depende do preço que julga.** Graham é
  indicador, nunca borda: dentro do próprio filtro ele sempre fica acima do preço.
- **O yield que a pessoa declara é meta de renda** (`personal_ceiling`), nunca borda da faixa.
- **Juro estimado não avalia.** A taxa sai da Selic média de 10 anos (`rates_for_valuation`); sem
  juro real, o método se cala em vez de descontar por um número do código.
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

- **Fontes: BRAPI e BCB SGS.** Só essas duas.
- **O sistema não inventa dado.** Fonte fora do ar degrada em ordem: cache válido → cache vencido com
  idade visível → ausência declarada. **Falha de rede não vira ausência.**
- **Dado externo passa por faixa de plausibilidade.** Campo absurdo vira `None`; preço absurdo
  rejeita o snapshot.
- **Fonte tem disjuntor.** Aberto, nem tenta.
- **`CACHE_BACKEND` errado falha alto.** Cair em silêncio para cache por nó faz a mesma pessoa ver
  preços diferentes.
- **A cota se gasta no pregão** (`core/pregao.py`, 10h–18h30 nos dias de pregão da B3). O portão vale para a varredura
  do universo, **não** para busca de um ativo pedido por alguém.

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
- **Exportação e exclusão de conta nunca ficam atrás de plano.**

### Monetização

- **Cerca de plano mora só em `entitlement/`**, e entra desligada. Nenhuma condicional de plano fora
  do módulo; `analysis`/`cashflow`/`collectors`/`ledger` não importam nada dele.
- **Nada é cercado antes da primeira posição salva.**
- **`ENTITLEMENTS_ENABLED` sem `ENTITLEMENTS_ENABLED_AT` falha alto.**
- **O titular de um evento de cobrança sai da sessão de checkout, nunca do corpo.**
- **Ativo da própria carteira nunca consome cota.**

### Interface

- **A navegação é o ciclo do dinheiro:** `/mes` → `/sobra` → `/patrimonio`, mais `/descobrir` e
  `/voce`. URLs antigas seguem como redirect — link salvo é contrato.
- **A paleta mora só em `design_tokens.dart`.** Não escreva hexadecimal em `theme.dart`.
- **Papel de cor novo se declara nos dois temas.**
- **Estado ≠ direção.** `fiStateColor` para julgamento, `fiDirectionColor` para aritmética.
- **Tipo é papel, não tamanho.** `fontSize:` solto tem catraca em zero.
- **Serifa decide, sans mede.**
- **Fio + chão, não card + card.** A caixa é `FiObject`, e só para objeto. `Card`, `ListTile`,
  `SwitchListTile`, `CircleAvatar` estão em catraca zero.
- **Controle vem do sistema.** `Switch`, `Slider`, chips e `ExpansionTile` do Material só existem
  dentro de `core/widgets/` (`FiSwitch`, `FiSlider`, `FiChoiceChip`, `FiDisclosure`); `InkWell` e
  `GestureDetector` fora dele estão em catraca. Gráfico vem com tabela equivalente.
- **Julgamento exige explicabilidade.** Escape só com `// design-exception: regra — motivo`.
- **Estado de tela é contrato:** `AsyncValue.when` com `FiSkeleton`/`FiErrorState`. A falha guarda o
  **erro**, não um booleano. Vazio e falha nunca compartilham a mesma tela.
- **Falha usa `fiErrorMessage`**, nunca texto solto.
- **Preço vem com `formatAge`.** Em lista, o carimbo é o **mais antigo**.
- **Espera é `FiSkeleton.screen()`**, nunca disco girando.
- **Número em português é do formatador**, não do template.

---

## Armadilhas que não quebram o build

Cada item já quebrou a tela ou o dado **com o CI verde**.

- **Construtor que ignora chave não declarada.** `Modelo(**resultado.__dict__)` e o `fromJson`
  descartam campo não declarado em silêncio. Três campos calculados nunca chegaram ao cliente assim.
- **Campo obrigatório novo no Dart quebra quem não atualizou.** O cliente chega por loja. Campo novo
  nasce opcional.
- **Escrita seguida de 4xx:** quem decide commit ou rollback é o **status da resposta**, não a
  ausência de exceção. O que precisa sobreviver ao 4xx usa `independent_session()`.
- **Papel de cor usado como o outro papel** faz uma perda aparecer como aviso.
- **Vocabulário sem consumidor** é pior que vocabulário nenhum. E série nova precisa entrar nos mapas
  dos **três** blocos de categoria.
- **Regra de lint que filtra por extensão não roda.** A regra varre `lib/`; o que estiver fora não é
  conferido. Confira contra o que o repositório tem.

---

## Ao adicionar…

| O quê | Faça também |
|---|---|
| Coluna no model | Migração Alembic |
| Tabela com `user_id` | `account_store.USER_SCOPED_MODELS` |
| Campo calculado numa resposta | Modelo Pydantic **e** `fromJson` do Dart |
| Campo novo que o app já lê | Deixá-lo opcional no Dart |
| Limiar de score | As duas plataformas, Python primeiro |
| Campo de dinheiro | Tipo `Money` |
| Tela ou rota | Ler [docs/05-INTERFACE.md](docs/05-INTERFACE.md) antes |
| Dependência no `pubspec.yaml` | `flutter build apk --release` |
| Rota pública nova | Decidir por escrito que ela é pública |

---

## Comentário: quase nunca

**O porquê vive nas [decisões](docs/decisoes/); o que não pode ser violado vive aqui.** O fonte não é
lugar de nenhum dos dois.

**Não entra:** narrativa histórica, justificativa que já está numa ADR, comentário que repete a
linha, docstring que reescreve a assinatura, explicação de teste em docstring — a razão de um teste
existir vai na **mensagem do assert**.

**Fica:** infra (CI, migração, build, script de operação), armadilha local em uma linha, e escape
declarado que uma regra de lint exige.

Se a explicação é boa demais para caber em uma linha, ela não é comentário: é uma ADR.
