# fiance

Plataforma multi-tenant de análise de investimentos focada na B3.
**FastAPI + Postgres** (`backend/`) · **Flutter** (`mobile/`), o único cliente, distribuído pelas
lojas.

Este arquivo é o **contrato de trabalho**: invariantes, armadilhas e checklists. Ele não descreve
o sistema — isso é [docs/](docs/), e o [índice](docs/README.md) diz qual arquivo responde o quê:

| Quero saber | Leia |
|---|---|
| Rodar, instalar, variáveis de ambiente | [README.md](README.md) |
| Como o sistema é montado — camadas, algoritmos, endpoints | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| O que cada tela faz | [docs/FEATURES.md](docs/FEATURES.md) |
| O que está aberto **agora** | [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) |
| Por que uma decisão foi tomada, e quando | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| Por que a interface é assim | [docs/design/](docs/design/) |
| Para onde o produto vai — visão, negócio, roadmap | [docs/produto/](docs/produto/) |
| Subir, observar e reverter | [docs/OPERACAO.md](docs/OPERACAO.md) |

**Histórico não é pendência.** Nada no CHANGELOG é trabalho a fazer, mesmo quando descreve um
problema. O que está aberto está no KNOWN_ISSUES, e só lá.

---

## Como trabalhar aqui

**Pronto = suíte verde.** Tudo abaixo roda no CI (`.github/workflows/ci.yml`) a cada push.

```bash
cd backend && python -m pytest -q                  # 1036 passam, 11 pulam sem Redis
cd backend && python -m ruff check app tests migrations
cd backend && python -m ruff format --check app tests   # o CI roda os dois
cd mobile  && flutter analyze && flutter test      # 0 issues, 125 testes
                                                   #   inclui test/lint_ui_test.dart (11 regras
                                                   #   de produto) e test/contraste_test.dart
cd mobile  && flutter build apk --release          # analyze e test nao tocam o Gradle:
                                                   #   o build Android e outra metade
cd mobile  && python tool/build_icons.py --check   # marca sincronizada
```

Três ressalvas que já custaram tempo:

- **A lista acima é a do CI, não um subconjunto dela.** O `ruff format --check` já esteve fora
  daqui e dentro do `.github/workflows/ci.yml`: quem seguia o contrato à risca não rodava o comando
  que reprovava, e o HEAD ficou vermelho sem ninguém ver.
- **Não rode `dart format`.** O formatter reescreve o `design_tokens.dart` e quebra `if`s de uma
  linha que o repo mantém.
- **O build Android custa minutos, e é o comando que ninguém roda.** `flutter analyze` e `flutter test`
  rodam sobre Dart e **nunca** invocam o Gradle: o bump do Kotlin para 2.2 deixou o release
  Android quebrado por um plugin preso na linguagem 1.6 com a suíte inteira verde. O CI tem um job
  só para isso, e localmente ele custa alguns minutos — rode ao mexer em plugin, em `pubspec.yaml`
  ou em qualquer coisa sob `mobile/android/`.

### Comentário: quase nunca

**O porquê vive no [CHANGELOG](docs/CHANGELOG.md); o que não pode ser violado vive aqui.** O fonte
não é o lugar de nenhum dos dois — comentário de justificativa envelhece calado, não é lido por
quem mais precisa, e duplica o que já está escrito em lugar melhor.

O que **não** entra no código:

- narrativa histórica: "isto era X e virou Y", "esta versão era gerada e passou a ser escrita"
- justificativa de decisão que já está no CHANGELOG ou nos invariantes acima
- comentário que repete o que a linha faz, incluindo docstring que reescreve a assinatura
- explicação de teste em docstring — a razão de um teste existir vai na **mensagem do assert**,
  que é onde ela aparece quando ele falha

O que fica:

| Onde | Por quê |
|---|---|
| **Infra** — CI, migração, gerador, configuração de build, script de operação | Não tem CHANGELOG próprio, e quem lê está prestes a executar |
| **Armadilha local**, em uma linha | O comentário evita o defeito ali, e o defeito não é óbvio na linha seguinte |
| **Escape declarado** que uma regra de `test/lint_ui_test.dart` exige | `// design-exception: regra — motivo` é contrato com a máquina, e o motivo é obrigatório |

Se a explicação é boa demais para caber em uma linha, ela não é comentário: é entrada no
CHANGELOG.

### Ao adicionar…

| O quê | Faça também | Senão |
|---|---|---|
| Coluna no model | Migração Alembic (`backend/migrations/`) | `test_database_migration.py` falha |
| Tabela com `user_id` | Entrar em `account_store.USER_SCOPED_MODELS` | `test_export_cobre_toda_tabela_com_dono` falha |
| Campo calculado numa resposta | Declarar no modelo Pydantic **e** no `fromJson` do Dart | Some **em silêncio** |
| Campo novo numa resposta que o app já lê | Deixá-lo **opcional** no Dart | O aplicativo chega por loja: há versão antiga instalada por tempo indeterminado, e ela não se atualiza no próximo carregamento |
| Limiar de score | Mudar nas duas plataformas, Python primeiro | Réguas divergem |
| Tela ou rota | Ler [docs/design/](docs/design/) antes | A IA do produto se desfaz uma tela por vez |
| Tela nova, ou texto de interface | Conferir [docs/design/AI-TELLS.md](docs/design/AI-TELLS.md) antes de aceitar como pronta | Cheiro de protótipo gerado — genérico, "sameness" de template. A **lista de frases** já é máquina; composição e hierarquia continuam sendo revisão humana |
| Cor, tipografia, espaço | Editar [design_tokens.dart](mobile/lib/core/design_tokens.dart), que é a única paleta | Hexadecimal solto em `theme.dart` cria uma cor que nenhuma tela conhece |
| Papel de cor novo | Declarar nos **dois** temas | A cor não existe num dos temas, e a tela sai com tinta de um tema no chão do outro |
| Escrita no razão | Passar por `ledger_service`, nunca por `ledger_store` na camada de API | A Carteira não muda e ninguém avisa |
| Julgamento numa tela | `FiProvenance` — método, fonte, limitação — e o papel de veredito em serifa | `test/lint_ui_test.dart` reprova: explicabilidade é invariante, não enfeite |
| Nome de tela | Usar o nome do conceito, não um sinônimo | `test/lint_ui_test.dart` reprova nome de destino aposentado — a barra do `/voce` dizia "Configurações" e a de `/sobra/desvio` dizia "Estratégia" |
| Número projetado numa tela | `FiRange` — piso, teto e cenário base | Número único a cinco anos empresta precisão de centavo a uma pilha de premissas |
| Cifra de preço justo numa tela | A base junto: quantos métodos, ou o nome do método | `/descobrir` já mostrou Bazin cru enquanto `/ativo` dizia "consenso de 3 métodos" para o mesmo ativo |
| Tela que lê dado | `AsyncValue.when` com `FiSkeleton`/`FiErrorState` | `test/lint_ui_test.dart` reprova. Sem isso a falha sai como tela vazia, e "não conseguimos ler" fica igual a "você não tem nada" |
| Frase de falha numa tela | `fiErrorMessage` — nunca texto solto | Já houve oito grafias, e `Erro 500` chegou à tela |
| Preço, ou lista de preços, numa tela | `formatIdade`. Em lista, o carimbo é o **mais antigo** (`carimboMaisAntigo`) | Dizer a idade do mais novo promete frescor que a linha de baixo não tem |
| Espera numa tela | `FiSkeleton.tela(shape:, count:)` — nunca `Center(child: CircularProgressIndicator())` | `test/lint_ui_test.dart` reprova: disco não diz o que vem, e a página salta quando o dado chega |
| Destino de raiz | `FiSearchAction` na barra | `test/lint_ui_test.dart` reprova. A busca já teve uma porta só, numa tela secundária |
| Tamanho de tipo | Escolher o **papel** em `FiType` (`body`, `caption`, `metric`, `verdict`…), nunca `fontSize:` solto | A catraca de tipo solto em `test/lint_ui_test.dart` só desce; subir exige explicar por quê |
| Dependência no `pubspec.yaml` | Rodar `flutter build apk --release` | Plugin com Gradle ou Kotlin incompatível quebra **só** o build Android, e `analyze`/`test` seguem verdes |
| Rota pública nova no backend | Decidir por escrito que ela é pública | Sem titular não há teto por usuário, e o teto por IP é o que resta |

---

## Armadilhas que não quebram o build

Esta lista existe porque cada item já quebrou a tela ou o dado **com o CI verde**.

- **Construtor que ignora chave não declarada** — `Modelo(**resultado.__dict__)` no Pydantic e
  `fromJson` no Dart descartam campo não declarado sem avisar. Três campos calculados nunca
  chegaram ao cliente assim: `consensus_methods`, `trend_basis`, `allocation_gaps`.
- **Campo obrigatório novo no Dart quebra quem não atualizou.** O cliente chega por loja: há
  versão antiga instalada, e ela não se atualiza no próximo carregamento. Campo novo nasce
  opcional; campo que some do backend derruba a versão anterior do aplicativo, não a atual.
- **`_session_global()` em caminho de request** — não filtra por usuário. É para job cross-tenant.
- **Dois refreshes simultâneos** derrubam a sessão: o refresh é rotacionado e queimado no uso. A
  renovação é compartilhada, e quem levar 401 espera a que está em voo em vez de abrir a segunda.
- **Escrita seguida de 4xx** — os handlers de `DomainError` vivem no `ExceptionMiddleware` do
  Starlette, que é *interno* ao middleware de observabilidade: a exceção nunca sobe. Quem decide
  commit ou rollback é o **status da resposta**, não a ausência de exceção. O que precisa
  sobreviver ao 4xx que provocou — contador de teto, marca de paywall — usa
  `independent_session()` / `outside_request_transaction()`.
- **Rota cara casada por prefixo com versão** — `/api/opportunities` casa, `/api/v1/opportunities`
  não. O teto morre em silêncio no dia da migração para o caminho canônico. O casamento é por
  **sufixo**.
- **Papel de cor usado como o outro papel** — direção pintada com token de estado faz o verde
  significar marca, lucro e veredito favorável ao mesmo tempo, e uma perda aparecer como aviso.
  Direção é `fiDirectionColor(delta, brightness)`; estado é `fiStateColor(FiState.x, brightness)`.
- **Vocabulário sem consumidor** — mapa de rótulos declarado e nunca importado é pior que mapa
  nenhum, porque parece resolvido enquanto quatro telas reescrevem o mapa à mão. Ao declarar um
  vocabulário novo, confira se ele chega a uma tela.
- **Série nova no vocabulário sem entrar nos mapas de classe** — a armadilha acima na forma
  inversa, consumidor sem vocabulário: uma categoria de despesa em `series: 4` pedia a classe da
  série 4 e recebia nada, porque os mapas eram montados só das séries de alocação. Os mapas
  cobrem os três blocos de categoria.
- **Regra de lint que filtra por extensão de arquivo não roda.** Duas regras varriam `.html` num
  repositório que escrevia o template dentro do `.ts`, e passaram meses lendo um arquivo só — uma
  delas era a que protege o invariante de explicabilidade. Ao escrever regra nova, confira contra
  **o que o repo tem**, e não contra o que a extensão sugere. No Dart vale igual: a regra varre
  `lib/`, e o que estiver fora não é conferido.

O `flutter test` cobre parte disso por máquina, em **11 regras** de `test/lint_ui_test.dart` —
explicabilidade em julgamento, projeção sem faixa, promessa sobre o futuro, nome acessível em
botão de ícone, serifa no papel de veredito, vocabulário de IA genérica, nome de destino
aposentado, a catraca de tipo solto, esqueleto no lugar de disco girando, busca alcançável de todo
destino de raiz, e falha de leitura numa voz só. O contraste é cobrado à parte, em
`test/contraste_test.dart`, nos dois temas.

**Vive como teste, e não como script próprio**, porque `flutter test` já é o comando do CI: regra
que exige mudar a esteira para rodar é regra que não roda. O que ainda **não** é cobrado — e era,
quando havia um verificador no front — está no [KNOWN_ISSUES](docs/KNOWN_ISSUES.md), item 14:
gráfico sem tabela equivalente, destino de navegação inexistente e controle montado à mão.

---

## Invariantes

### Domínio e cálculo

- **Regra de negócio vive só no backend** (`analysis/`, `optimizer/`). O aplicativo delega — não
  há cálculo de renda fixa duplicado em Dart.
- **Régua de score em um lugar por plataforma:** `analysis/score_ruler.py` e
  `mobile/lib/core/score_ruler.dart`. Mudar um limiar exige os dois, e o Python é o primeiro.
- **Unidades:** `roe`, `profit_margin`, `revenue_growth` e `debt_to_equity` chegam do collector em
  **percentual** (`collectors/universal._ratio_to_pct`). Crescimento no DCF também.
- **Dinheiro fiscal é `Decimal`; dinheiro de tela é `float`.** Escala e arredondamento só em
  `core/money.py` (meio para cima, não bancário). Nunca construa `Decimal` de `float` sem passar
  por texto — use `money()`. **As colunas monetárias são `Money`** (`ExactNumeric`): inteiro
  escalado por 10^8 no SQLite, `Numeric` no Postgres — o `NUMERIC` do SQLite é `real` por baixo, e
  somar `ir_amount` em float erra o número que vai para a declaração. A conversão para `float`
  acontece na fronteira do store; agregação de dinheiro é `sum_money()` em Python, nunca
  `func.sum()`. `tests/test_money_columns.py` reprova campo de dinheiro fora do tipo, e `Float`
  novo precisa ser declarado como carimbo de tempo ou percentual.
- **Fuso fiscal é brasileiro** (`core/brt.py`), não UTC — isenção mensal de IR e faixas de alíquota
  usam mês calendário BRT.
- **Veredito vem com o que o derrubaria** (`analysis/falsifiers.py`). Os limiares de margem de
  segurança dão, por álgebra, o preço em que o veredito muda. Sem preço justo a lista sai vazia —
  "fique de olho nos resultados" seria almanaque no lugar de uma condição conferível.
- **Projeção sai como faixa, nunca número único** (`analysis/scenarios.py`). `_low`/`_high` são
  campos obrigatórios de `PassiveIncomeMonth`: com default existiria caminho em que o número sai
  sozinho. `test/lint_ui_test.dart` recusa tela que exiba `portfolioValue`/`passiveIncomeMonthly`
  sem a faixa.
- **Modo de afirmação é configuração, não código** (`affirmation.py`, `AFFIRMATION_LEVEL`).
  Descritivo / analítico (padrão) / prescritivo. O que sai fora do nível 3 é o **valor por ativo**,
  que é o que instrui; a análise que o sustentava fica. Existe para que a resposta sobre CVM 19/20
  seja variável, e não refactor sob pressão.

### Carteira e livro-razão

- **Toda escrita do razão passa por `ledger_service` e reprojeta.** `POST /transactions`, o lote e a
  importação escreviam direto no `ledger_store` e não reprojetavam: a pessoa colava o extrato, o
  produto respondia `{"imported": 47}` e a Carteira não mudava. `record_entry`, `record_entries`,
  `delete_entry` e `import_entries` são a porta única.
- **O livro-razão é a fonte da carteira; a posição é projeção dele.** A matemática vive em
  `ledger/`, que não conhece banco. A escrita grava **só lançamento**
  (`ledger_service.record_position_state`, `record_sale`, `record_removal`) e reconstrói a linha de
  `portfolio` a partir dele — não há mais espelhamento. `rebuild_projection` refaz tudo do zero
  (`POST /transactions/rebuild`), e `GET /transactions/reconciliation` deixou de comparar duas
  verdades: agora confere a projeção contra a fonte. Categoria não é derivável do razão, então
  viaja junto com a escrita.
- **A apuração de IR também é projeção do razão, e a unidade é o mês.** `ledger/apuracao.py` é a
  matemática, sem banco; `apuracao_service` resolve a categoria de cada papel e liga à API. Não
  existe campo de imposto gravado numa venda: guardá-lo é que fazia a ordem de registro dentro do
  mês mudar o número, a isenção de R$ 20 mil não ser reavaliada e a venda vinda de
  `POST /transactions` não apurar nada. O IR que aparece por linha em Encerradas é **rateio** do
  mês, e diz isso; o número do DARF está em `months`. Isenção corta os dois lados — prejuízo em mês
  isento não gera crédito compensável.
- **Uma declaração de posição ancora a linha do tempo, e a assimetria é de propósito.** O que vier
  depois dela se aplica em cima, na ordem das datas. O que tem data **anterior** e *soma* posição
  (compra, bonificação, transferência de entrada) já está dentro do que foi declarado e é
  descartado, com aviso em `PositionProjection.warnings` — senão declarar 100 hoje e importar o
  extrato do ano passado daria 200. O que tem data anterior e *reduz* continua valendo: é a venda
  retroativa contra posição declarada hoje, que o produto suporta.
- **Preço médio segue a convenção brasileira:** venda reduz quantidade e custo, nunca a média.
- **Evento corporativo é lançamento** (`split`, `bonus`, `amortization`), não correção manual —
  desdobramento sem ajuste é IR errado.
- **Escrita de carteira:** `POST /portfolio/position` e `DELETE /portfolio/position/{ticker}`.
  `PUT /portfolio` é **destrutivo** e existe só para importação explícita.
- **Renda fixa é entidade de primeira classe** (`fixed_income_positions`, `/fixed-income`), marcada
  a mercado no backend. Nada de RF em `localStorage`; o ticker sintético `RF_*` não existe mais.
- **Classes de ativo:** `br_stock` | `bdr` | `fii` | `etf` | `renda_fixa` → categorias `acoes_br` |
  `bdrs` | `fiis` | `etfs` | `renda_fixa`.
- **Importação é prévia + commit** (`importing/`, `/transactions/import`): tolerante com forma,
  intolerante com ambiguidade; erro diz a linha; gravação atômica; duplicidade é apresentada para
  decisão, nunca silenciada.
- **Proventos por calendário são sugestão, nunca lançamento** (`/dividends/pending`). Toda ressalva
  ali erra para mais, então nada vem pré-selecionado e não existe "aceitar todos".

### Caixa

- **Toda escrita do caixa passa por `cashflow_service`.** `registrar`, `registrar_varias`,
  `editar`, `marcar_paga` e `apagar` são a porta única; nenhuma rota escreve em `cash_store`
  direto, do mesmo jeito que nenhuma escreve em `ledger_store`.
- **O molde de mês é prévia e commit, como a importação de extrato.**
  `GET /cashflow/month/template` lê, não grava; `POST /cashflow/entries/batch` grava o lote
  inteiro ou nenhum — meio molde de mês é pior que molde nenhum, porque quem lançou não teria como
  saber o que entrou e o que ficou de fora. O que vem marcado é só o que repete por natureza
  (`CATEGORIAS_FIXAS`, dívida e salário); variável fica visível e desmarcado, porque o valor do
  mês que passou é fato daquele mês. O copiado nasce **a vencer**, e a identidade que evita
  duplicata ignora o valor — a conta de luz muda todo mês.
- **Entrada derivada não é gravada: é montada na leitura.** `cashflow_service.entradas()` soma o
  que está na tabela com o provento derivado de `dividends_received`, **em memória**. Assim
  duplicar fica impossível por construção, `GET` não escreve, e a exportação de conta não sai com
  o mesmo provento duas vezes. `registrar` recusa entrada marcada como derivada.
- **`tem_caixa` lê só a tabela**, e por isso ignora o derivado naturalmente. Quem tem provento no
  razão e nenhum lançamento próprio não lançou caixa nenhum, e mandá-lo para o `Mês` seria a tela
  vazia que a IA nova declarou como risco.
- **Taxa anual vira mensal por juros compostos, nunca dividindo por doze.** Dividir superestima a
  referência (12% ao ano dão 0,9489% ao mês, e 1,0% na conta ingênua) e **afrouxa** a régua de
  dívida: 0,97% ao mês sairia como administrável. O erro cairia do lado de não avisar.
- **`cashflow/` é irmão de `ledger/`, e não conhece banco.** Matemática pura: `entries.py` (o
  lançamento e o vocabulário fechado), `month.py` (a projeção do mês), `debt.py` (a régua de
  dívida), `cascata.py` (a ordem). Quem liga isso à API é `cashflow_service`, no mesmo padrão de
  `apuracao_service`.
- **Provento não se lança no caixa — é derivado do razão.** O razão já é a fonte da carteira, e
  provento creditado é lançamento dele. Se a pessoa também pudesse lançar o mesmo provento no
  caixa, o dinheiro contaria duas vezes e inflaria a renda do mês **e** a sobra junto. A regra
  vive no tipo: `CashEntry` recusa categoria `provento` sem `derived=True`, e recusa `derived`
  em qualquer outra categoria. `cashflow/` não importa `ledger/` — a leitura derivada é da camada
  de serviço, que é quem tem os dois lados.
- **Valor de lançamento é sempre positivo.** Entrada e saída se distinguem por `kind`, nunca pelo
  sinal — mesma disciplina de "quantidade negativa não é lançamento, é sinal trocado".
- **Entrada não tem vencimento.** Vencimento é obrigação a cumprir, e dinheiro que se recebe não
  tem uma: com `kind: income` o formulário pede um dia só, o do crédito. O par recebido / a receber
  continua, no mesmo interruptor da saída.
- **A competência é o dia do pagamento, não do vencimento.** O caixa mede quando o dinheiro se
  moveu; conta de agosto paga em setembro é de setembro. Conta não paga conta no mês do
  vencimento, e é o que forma o `comprometido`.
- **Fato e projeção são números diferentes, e não se misturam.** `livre_agora` é fato (entrou,
  menos saiu, menos o comprometido e datado) e alimenta `/mes`; `sobra_piso`/`sobra_teto` são
  projeção (o mesmo número, menos o gasto variável ainda esperado) e alimentam `/sobra`. A
  diferença entre os dois **é** a estimativa. Um número que às vezes é fato e às vezes é projeção
  seria a pior das duas coisas.
- **Sem mês fechado não há estimativa, e ausência não vira zero.** Estimativa de gasto variável
  sai só do histórico da própria pessoa (até 3 meses fechados). Sem base, `tem_faixa` é falso e a
  sobra é o próprio `livre_agora` — tratar "não sei" como "não vai sair nada" daria uma sobra
  otimista exatamente para quem acabou de começar a lançar.
- **Pagamento de dívida sai do caixa e não é consumo.** `divida` está fora de
  `CATEGORIAS_VARIAVEIS` e de `eh_consumo`: se entrasse na base, a estimativa diria que a rotina
  custa o que a dívida custa.
- **Dívida se classifica por custo, nunca por tipo.** Não existe campo "caro" no vocabulário de
  dívida: a classe sai da taxa contra o que **a carteira da pessoa** rende (sem carteira, o CDI do
  BCB). Consignado a 0,4% e consignado a 3,5% ao mês não são a mesma decisão. **Sem taxa
  informada não há classe** — o produto não estima taxa de rotativo, que varia por banco e por
  dia. E o veredito vem com `taxa_de_virada`, que é a taxa em que ele muda.
- **A cascata pode terminar sem passo de aporte, e isso é sucesso.** Com dívida cara consumindo a
  sobra inteira, a resposta certa é não aportar. É por isso que o destino se chama `Sobra`, e não
  `Aporte`.
- **A reserva vem depois da dívida cara, e só existe com alvo declarado.** A reserva existe para
  a pessoa não precisar tomar dívida cara; quem já a tem não precisa se proteger do risco de
  contraí-la, e poupar a juros de poupança enquanto paga 14,9% ao mês é perder nas duas pontas. O
  alvo é em meses do **próprio** gasto fixo, declarado pela pessoa — o produto não inventa seis
  meses, porque número de mercado solto é o que a régua de dívida proíbe.

### Dados externos

- **Fontes:** BRAPI (ações BR/FIIs/BDRs/ETFs) e BCB SGS (CDI/Selic/IPCA). Finnhub, CoinGecko,
  Gemini e yfinance/Alpha Vantage foram descontinuados — sem ações internacionais fora de BDR, sem
  cripto, sem IA externa.
- **Dado externo passa por faixa de plausibilidade** (`collectors/plausibility.py`): campo absurdo
  vira `None`, preço absurdo rejeita o snapshot inteiro.
- **O BCB tem a mesma disciplina da BRAPI** — disjuntor, cache vencido e faixa de plausibilidade.
  As constantes de `collectors/rates.py` são o **último** recurso, e o rótulo de fonte (`bcb` /
  `bcb_cache_vencido` / `estimativa`) viaja até a tela, inclusive em `BenchmarkResponse.cdi_source`.
  A curva de CDI é extrapolada da taxa de hoje (`cdi_basis`), então é referência, não o acumulado
  histórico.
- **Fonte tem disjuntor** (`collectors/circuit.py`) — aberto, nem tenta, e quem chama cai no cache
  vencido. `GET /data-quality/source` mostra os dois sem varrer o universo.
- **Onde o cache mora é trocável** (`core/cache_backends.py`): **banco da aplicação por padrão**
  quando `DATABASE_URL` é Postgres, arquivo local quando o banco também é local, Redis quando
  `REDIS_URL` existir. `CACHE_BACKEND` (`database`/`sqlite`/`redis`) força a escolha, e nome errado
  **falha alto** — cair em silêncio para cache por nó é defeito que só aparece semanas depois. Não é
  desempenho, é correção: com dois nós e cache por nó, a mesma pessoa vê preços diferentes conforme
  o balanceador; e com disco efêmero, o cache em arquivo nasce frio a cada deploy e a cota da fonte
  paga a conta. O vencimento vai **dentro** do valor mesmo no Redis, porque `get_with_age` precisa
  do dado vencido para o disjuntor degradar. `REDIS_URL` sem o pacote instalado **falha alto**.
  A tabela `cache_entries` não é de ninguém — está em `account_store.GLOBAL_TABLES`.
- **Coleta em lote, e a ausência é lembrada** (`collectors/universal.prefetch_brapi_raw`). A BRAPI
  dá 3.000 requisições/dia; varrer o universo um ticker por vez custava ~285 por rodada. O lote de
  20 leva isso a ~15, e como tudo passa por `brapi_raw:{base}`, aquecer essa chave basta. Ticker que
  a fonte não conhece fica marcado por 30min, senão o scan o repede 96 vezes por dia. **Falha de
  rede não vira ausência** — confundir "não sei" com "não existe" esconde fonte caída por meia hora.

### API

- **Campo de resposta que some é pego por contrato:** `tests/contrato_das_rotas.json` registra os
  campos de cada rota `/api/v1`, e o teste falha dizendo a rota e o campo. O FastAPI descarta em
  silêncio o que o `response_model` não declara. Regravar é `python -m tests.contrato_das_rotas`, e
  o diff entra no mesmo commit. Metade das rotas ainda devolve `dict` solto e não tem contrato
  nenhum; `SEM_MODELO_HOJE` é a catraca que impede esse número de crescer.
- **Versão no caminho:** `/api/v1` é canônico; `/api` responde como alias em transição e carimba
  `X-API-Deprecation`.
- **Listas paginam por cursor keyset** (`core/pagination.py`), nunca offset. Onde há agregado
  (proventos, renda fixa, sugestões) o corte é **do payload**, não da consulta — senão o total
  encolhe conforme a rolagem. Onde não há (`/portfolio/trades`, `/transactions`), corta no banco.
- **Migração é *release command*, não startup.** `python -m app.release` (e o `release:` do
  Procfile) aplica; o startup só chama `conferir_revisao()` e **falha alto** se o banco estiver
  atrasado. Migrar no `lifespan` com duas réplicas são duas migrações concorrentes, e o Alembic não
  coordena isso. Banco local em SQLite continua se criando sozinho, porque é de um processo só.
- **`APP_ENV` não tem default.** Vazio falha alto no startup e, se algo escapar, falha **fechado**
  (não é development): esquecer a variável desarmava JWT, CORS e a rota de operador de uma vez.
- **Três páginas de HTML são públicas, e a lista é fechada.** `/termos`, `/privacidade` e
  `/aviso-cvm` (`api/legal.py` + `services/legal_pages.py`) ficam **fora de `/api`** porque robô de
  loja não faz login, e a ficha de segurança de dados pede uma URL de privacidade que abre sozinha.
  São páginas de documento: sem JavaScript, sem asset externo e sem paleta — a cor vem do agente do
  usuário, e uma segunda cópia dos tokens envelheceria calada. `test_paginas_juridicas.py` cobra as
  três, e crescer essa lista é decisão registrada, não efeito colateral. No backend,
  `analyze_asset(personalized=False)` e `/api/public/*` são a leitura **sem titular**, com teto por
  IP.
- **O texto jurídico não repete o que o produto afirma.** O Aviso CVM lê `affirmation.current()` no
  servidor; `AFFIRMATION_LEVEL` é configuração, e uma segunda cópia da frase acabaria desatualizada
  justamente onde a pessoa a lê. O nível publicável hoje é o **2**; o 3 fica desligado até haver
  parecer. Enquanto o texto for minuta, a constante `_MINUTA` diz isso — e é uma só, para sair de
  uma vez.
- **Busca global: o servidor devolve o que é da pessoa; a rota é do cliente.** `/search` procura
  carteira, renda fixa e universo e devolve `ref` — ticker ou id, nunca caminho. Destino de tela
  também é resultado, mas a lista vive no cliente (`buscaDestinos`): um catálogo de rotas no
  servidor seria segunda verdade sobre a IA. Por isso os destinos filtram sem rede.
- **Onboarding é derivado, não guardado.** O passo sai do que a pessoa já fez (tem posição? tem
  meta?), em `/onboarding` — um contador criaria segunda verdade. O recorte mora na URL
  (`?passo=2`) e nada bloqueia.

### Sessão, conta e privacidade

- **Multi-tenant por `user_id`**, aplicado em `storage/portfolio_store.py`.
- **"Tem carteira" é uma pergunta só:** `portfolio_store.has_holdings()`, que olha posições **e**
  renda fixa. A cerca de plano, o início do trial e o marco de ativação perguntavam a
  `list_positions`, que lê só a tabela `portfolio` — quem chegava por CDB nunca "começava".
- **Sessão tem TTL curto e refresh rotacionado.** Acesso 1h, refresh 30 dias queimado no uso.
  Revogação por `jti` (este dispositivo) e `session_cuts` (todos). Os clientes renovam **uma vez**
  ao levar 401, com a renovação compartilhada.
- **Telemetria não leva carteira.** O `before_send` de cada plataforma
  (`core/telemetry.py` e `core/telemetry.dart`) é **lista de permissão**: ticker no caminho vira `{id}`, valor
  em reais e número citado em erro são redigidos, corpo de request e `extra` não saem, do usuário
  sai só o identificador, e variável local de frame é descartada. Uma chave nova num payload nasce
  redigida. Duas suítes travam isso, e é a Política de Privacidade escrita como código.
  `SENTRY_DSN` sem o pacote instalado **falha alto**.
- **Evento de produto tem dicionário fechado** (`core/events.py`). Nome fora dele, ou propriedade
  com ticker ou valor, devolve 422 — dado de carteira não sai do produto. Marcos de ativação são
  gravados pelo **servidor** (`services/milestones.py`), não pelo cliente.
- **Exportação e exclusão de conta nunca ficam atrás de plano.**
- **Contador de uso é uma primitiva só** (`core/usage.py`): serve ao rate limiting e ao teto de
  plano. A granularidade mora no formato de `window_key`, não no schema.

### Monetização

O plano de cinco portões (G0 publicável → G4 preço cheio) está no
[CHANGELOG](docs/CHANGELOG.md), entrada de 2026-08-27.

- **Nada é cercado antes da primeira posição salva.** `entitlement.check` libera tudo enquanto a
  carteira estiver vazia, e nem grava evento de paywall: gate para quem ainda não tem o que
  analisar cobra antes de entregar. Como a primeira posição também dispara o trial, "Free com
  carteira" só existe depois de o trial acabar — é assim que os testes de cerca semeiam o estado.
- **Cerca de plano mora só em `entitlement/`** e entra desligada (`ENTITLEMENTS_ENABLED=false`).
  A régua é dado em `plans.py`; aplicar é `Depends(requires(Feature.X))`; bloqueio é 402 com corpo
  que a UI usa para montar o gate. Dois testes de arquitetura travam isso: nenhuma condicional de
  plano fora do módulo, e `analysis`/`optimizer`/`collectors`/`ledger` não importam nada dele — se
  o cálculo souber quem paga, a independência do algoritmo vira promessa. Ativo da própria carteira
  **nunca** consome cota; a rota pública também não.
- **O titular de um evento de cobrança sai da sessão de checkout, nunca do corpo.** A rota do
  webhook é pública: a assinatura protege a integridade da mensagem, não a autoridade sobre quem
  ela nomeia. `checkout_sessions` guarda quem abriu o checkout, e `BILLING_WEBHOOK_SECRET` é
  validado no startup com o mesmo rigor do JWT.
- **Ligar a cerca exige declarar quando ela subiu.** `start_trial` é chamado na primeira posição
  salva **sem consultar `ENTITLEMENTS_ENABLED`**, e não re-arma: toda conta com carteira carrega um
  `trial_ends_at` no passado. `ENTITLEMENTS_ENABLED_AT` é a âncora — o relógio conta do **mais
  tarde** entre qualificar e a cerca subir —, e a flag ligada sem ela **falha alto** no startup.
  Sem isso, virar a flag derrubaria a base inteira para Free num instante, sem volta pelo código.
- **Assinatura carrega o próprio preço** (`price_cents`, `locked`): preço travado de fundador é
  promessa pública, então é dado e não memória. Webhook é idempotente por `processed_webhooks`.
  O trial de 14 dias começa na **primeira posição salva**, não no cadastro.
- **Indicação credita na qualificação, nunca no cadastro** (`services/referral_service.py`). Conta
  é grátis de fabricar aos milhares; carteira não é. A atribuição acontece **só no login**
  (`referral_code` em `/auth/google`) e é recusada para quem já tem carteira, já foi atribuído, ou
  usou o próprio código; recusa não derruba o login. Crédito é `subscriptions.credited_until`,
  separado de `trial_ends_at` para não reabrir trial gasto, com teto declarado. A rota nunca devolve
  quem foi indicado.

### Interface

- **A navegação é o ciclo do dinheiro**: `/mes` → `/sobra` → `/patrimonio`, mais `/descobrir` e
  `/voce`, e `/ativo/:ticker` como camada. Continuam cinco destinos, e as URLs antigas
  (`/hoje`, `/carteira/*`, `/estrategia/*`) seguem como redirect — link salvo é contrato.
  `Hoje` saiu porque respondia "o que mudou", e isso é feed, não lugar: o feed vive no `Mês`, e
  o patrimônio e o veredito de saúde já existiam no `Patrimônio`. `Estratégia` se dissolveu —
  sem aporte, meta e projeção, sobrava o desvio de alocação, que é leitura de patrimônio e vive
  em `/sobra/desvio`.
- **A camada visual é escrita à mão, inteira, e existe num lugar só. Não há gerador de design.**
  Cor (nos dois temas), tipografia, espaço, raio, motion e densidade vivem em
  [mobile/lib/core/design_tokens.dart](mobile/lib/core/design_tokens.dart). As bandas das réguas, o
  vocabulário de veredito e os rótulos de categoria também são escritos — `core/product_rules.dart`
  e `core/vocabulary.dart`. O que os mantém em acordo com o cálculo é a régua de baixo:
  `analysis/score_ruler.py` é a fonte, e mudar um limiar exige as duas plataformas com o Python
  primeiro. **Não escreva hexadecimal em `theme.dart`** — a paleta mora só na fundação.
- **Contraste é verificado, não recomendado** (`mobile/test/contraste_test.dart`, no CI), nos dois
  temas e contra o **mínimo da WCAG**: 4,5:1 para texto e 3:1 para forma e limite de controle.
  `ink-3` conta como texto porque legenda é texto pequeno; série de gráfico escreve o rótulo do
  próprio chip, então também conta como texto; `hairline` fica de fora, é decoração. Piso acima da
  norma é escolha de design, e escolha de design não tem máquina: a paleta é livre, o ilegível não
  é.
- **Ícone do aplicativo é gerado**, da cor `brand` de `design_tokens.dart`, por
  `cd mobile && python tool/build_icons.py` (requer Pillow). **O launcher nativo é um segundo
  passo**: `dart run flutter_launcher_icons` — sem ele os ícones ficam com a cor antiga mesmo com a
  fundação correta.
- **Não existe alias de cor.** Os papéis são `ground-0`/`ground-1`/`ground-2`, `hairline`,
  `ink-1`/`ink-2`/`ink-3`, `brand`/`ink-on-brand`, os estados
  `favorable`/`attention`/`adverse`/`indeterminate`, a direção `up`/`down` e as séries.
- **Estado ≠ direção.** Estado é julgamento (veredito, saúde, severidade) e tem prioridade
  cromática; direção é a aritmética de um número (P&L, linha de gráfico) e tem croma baixo:
  `fiStateColor(FiState.x, brightness)` e `fiDirectionColor(delta, brightness)`. Pintar direção
  com token de estado faz uma perda aparecer como aviso, e o verde significar três coisas.
- **Fio + chão, não card + card.** A hierarquia de uma tela nasce de espaço, tipo e uma regra
  horizontal. A caixa fica reservada ao que é **objeto**: uma posição, uma opção de renda fixa,
  uma sugestão. Card dentro de card dentro de card é a forma mais reconhecível de o produto virar
  painel de BI, e o `Card(`/`ListTile` ainda é a dívida aberta do item 8 do KNOWN_ISSUES.
- **Grade de KPI é o cheiro de painel.** Três a quatro caixas centralizadas com um número dentro
  não são informação organizada, são widgets. A alternativa é uma linha de cifras sob um fio
  quando são poucas, ou uma tabela quando o que importa é comparar.
- **Tipo é papel, não tamanho.** `FiType.body`, `.caption`, `.metric`, `.verdict`… `fontSize:`
  solto tem catraca em `test/lint_ui_test.dart`, e ela só desce.
- **Serifa decide, sans mede.** O papel de veredito sai na família serifada, e o teste reprova o
  contrário: é o sinal de que aquela linha é conclusão, e não mais um número.
- **Estado de tela é um contrato, não uma escolha por tela.** Carregando, falha, vazio e conteúdo
  saem do par `FiSkeleton`/`FiErrorState` com `AsyncValue.when`. A falha guarda o **erro**, não um
  booleano: sem ele a tela só sabe dizer "algo deu errado", e uma loja de carteira chegou a servir
  sete telas com um booleano que uma só lia. Ausência de dado e falha de leitura nunca
  compartilham a mesma tela.
- **Momento é nível 1, não nota de rodapé.** Método e fonte moram na gaveta de `FiProvenance`;
  **quando o dado foi lido, não** — um preço de anteontem muda a decisão. O `asOf` é linha visível,
  e `/ativo/:ticker` diz a idade do preço ao lado do preço. O carimbo já existia em
  `collectors/universal` e parava no serviço.
- **Julgamento renderizado exige explicabilidade, e o teste cobra.** Score, veredito, preço justo e
  sugestão precisam de `FiProvenance`, `HelpTooltip` ou as funções de proveniência de
  `core/score_ruler.dart`. Mencionar em prosa não conta. O escape exige motivo escrito:
  `// design-exception: explicabilidade — …`. **Há uma forma só de escapar**, e ela nomeia a
  regra: escapar de cabeçalho não escapa de contraste.
- **Filtro e recorte vivem na rota**, não em estado local — voltar não perde o recorte, e o mesmo
  endereço leva ao mesmo lugar. Oportunidades (`q`, `dy`, `mos`, `cat`, `destaque`, `p`), quedas
  (`min_score`, `top`, `category`), tabela de posições (`cols`, `d`).
- **Densidade é preferência da conta; tema é do aparelho.** Densidade vive em
  `preferences.density`, que é do servidor; tema fica no armazenamento local do aparelho. Na
  tabela de posições o recorte da rota vence a preferência.
- **Número em português é responsabilidade do formatador, não do template.** O locale é `pt_BR`, e
  `R$ 120.000` escrito como `R$ 120,000` se lê como cento e vinte reais.
