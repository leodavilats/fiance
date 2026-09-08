# fiance

Plataforma multi-tenant de análise de investimentos focada na B3.
**FastAPI + Postgres** (`backend/`) · **Angular 22** (`web/`) · **Flutter** (`mobile/`).

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
cd backend && python -m pytest -q                  # 1004 passam, 11 pulam sem Redis
cd backend && python -m ruff check app tests migrations
cd backend && python -m ruff format --check app tests   # o CI roda os dois
cd mobile  && flutter analyze && flutter test      # 0 issues, 109 testes
                                                   #   inclui test/lint_ui_test.dart:
                                                   #   6 regras do lint:ui, no Dart
cd web     && npm run format:check && npm test && npm run build && npm run lint:ui   # 152 testes
node design-tokens/build-rules.mjs --check         # reguas e vocabulario sincronizados
node design-tokens/check-contrast.mjs              # contraste AA, web e mobile
node design-tokens/check-parity.mjs                # os cinco destinos existem nas duas
python design-tokens/build-icons.py --check        # marca sincronizada
```

Duas ressalvas que já custaram tempo:

- **Confira o código de saída, não o texto.** O build do Angular imprime erro como
  `X [ERROR] TS…`; um `grep -i error` ingênuo passa reto.
- **`lint:ui` roda depois do build** — a fonte de verdade das classes é o CSS emitido.
- **A lista acima é a do CI, não um subconjunto dela.** O `ruff format --check` já esteve fora
  daqui e dentro do `.github/workflows/ci.yml`: quem seguia o contrato à risca não rodava o comando
  que reprovava, e o HEAD ficou vermelho sem ninguém ver.
- **Não rode `dart format`.** O CI do mobile é `flutter analyze && flutter test`. O formatter
  reescreve o `design_tokens.dart` gerado e quebra `if`s de uma linha que o repo mantém.

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
| **Escape declarado** que o `lint:ui` exige | `<!-- design-exception: regra — motivo -->` é contrato com a máquina |

Se a explicação é boa demais para caber em uma linha, ela não é comentário: é entrada no
CHANGELOG.

### Ao adicionar…

| O quê | Faça também | Senão |
|---|---|---|
| Coluna no model | Migração Alembic (`backend/migrations/`) | `test_database_migration.py` falha |
| Tabela com `user_id` | Entrar em `account_store.USER_SCOPED_MODELS` | `test_export_cobre_toda_tabela_com_dono` falha |
| Campo calculado numa resposta | Declarar no modelo Pydantic / `fromJson` do Dart | Some **em silêncio** |
| `<lucide-icon>` | Registrar em `LucideAngularModule.pick({...})` ([app.config.ts](web/src/app/app.config.ts)) | Quebra a tela em runtime |
| Classe CSS global | Confirmar que existe em [styles.css](web/src/styles.css) | Quebra a tela em silêncio |
| Botão, campo ou tabela | Usar `.btn-*`, `.input`, `.field-label`, `.data-table` de [styles.css](web/src/styles.css) | `lint:ui` reprova controle montado à mão |
| Tipo numa tela | Escolher o **papel** (`fi-body`, `fi-caption`, `fi-metric`…), nunca `text-sm` | `lint:ui` reprova tamanho solto |
| Limiar de score | Mudar nas três plataformas, Python primeiro | Réguas divergem |
| Tela ou rota | Ler [docs/design/](docs/design/) antes | IA diverge entre plataformas |
| Tela nova, ou texto de interface | Conferir [docs/design/AI-TELLS.md](docs/design/AI-TELLS.md) antes de aceitar como pronta | Cheiro de protótipo gerado — genérico, "sameness" de template |
| Cor, tipografia, espaço | Editar [foundation.css](web/src/foundation.css) **e** o espelho em [design_tokens.dart](mobile/lib/core/design_tokens.dart) | Web e mobile divergem, e nenhuma máquina avisa |
| Papel de cor novo | Declarar nos **dois** temas de `foundation.css` | `check-contrast.mjs` reprova papel que só existe num tema |
| Camada empilhada | Usar `z-nav`/`z-drawer`/`z-drawer-panel`/`z-sheet`/`z-popover`/`z-loader`/`z-toast` | `lint:ui` reprova `z-[…]` **e** `z-50` — uma regra, as duas grafias |
| Diálogo sobreposto | Aplicar `fiDialog` — papel, foco preso e foco devolvido | Tab escapa para a página atrás |
| Escrita no razão | Passar por `ledger_service`, nunca por `ledger_store` na camada de API | A Carteira não muda e ninguém avisa |
| Tela nova no mobile que julga | `FiProvenance`, e o papel de veredito em serifa | `test/lint_ui_test.dart` reprova — as seis regras valem lá também |
| Seção numa tela | Usar `<app-section title="…">`, que emite o `<h2>` | Seção sem cabeçalho: `/mes` tinha 5 seções e nenhuma parada de navegação |
| Julgamento numa tela do mobile | `FiProvenance` — método, fonte, momento, limitação | `test/lint_ui_test.dart` reprova: o invariante de explicabilidade vale nas duas plataformas |
| Componente Angular novo | Escrever o `template` no próprio `.ts` — não há `.html` separado em `web/src/app/components` | Divergência de padrão na mesma pasta |

---

## Armadilhas que não quebram o build

Esta lista existe porque cada item já quebrou a tela ou o dado **com o CI verde**.

- **`redirectTo` relativo em rota de dois segmentos** manda o link salvo para o curinga.
  `{ path: 'carteira/posicoes', redirectTo: 'patrimonio/posicoes' }` resolve contra o primeiro
  segmento casado e leva a `/carteira/patrimonio/posicoes`, que não existe — a pessoa cai em
  `/mes` sem entender por quê. Valia para os oito redirects de dois segmentos do produto, e o
  teste passava verde porque comparava a **string declarada**, não a resolução. Todo alvo de topo
  é absoluto, e `app.routes.server.spec.ts` reprova o que não começa com `/`.
- **`index.html` sem `<base href="/">`** deixa rota de dois segmentos (`/voce/preferencias`)
  pedir os chunks em caminho relativo aninhado; o SSR devolve HTML, o módulo não carrega e a
  tela abre **em branco** por link direto. Passa despercebido navegando por dentro do app.
- **Ícone Lucide não registrado** — `The "x" icon has not been provided...` em runtime.
- **Classe CSS inexistente** — já aconteceu com `.card`, `.btn-primary`, `.tag`, `.verdict-pill`,
  `verdict-*`, `bg-success`.
- **Construtor que ignora chave não declarada** — `Modelo(**resultado.__dict__)` no Pydantic e
  `fromJson` no Dart descartam campo não declarado sem avisar. Três campos calculados nunca
  chegaram ao cliente assim: `consensus_methods`, `trend_basis`, `allocation_gaps`.
- **Cor do Tailwind declarada como string** — o modificador de opacidade (`bg-brand/20`) é
  **descartado em silêncio**. As cores da config são funções que emitem `color-mix` por isso.
- **Classe de controle fora de `@layer components`** derrota as utilitárias. Escritas soltas
  depois de `@tailwind utilities`, `.btn-*` e `.input` venciam por ordem de cascata:
  `class="btn-secondary hidden sm:inline-flex"` ficava **visível**, porque
  `.btn-secondary { display: inline-flex }` derrotava o `display: none` do `hidden`. Valia para
  todo botão do produto — esconder controle por breakpoint não fazia nada, e não havia erro
  nenhum. O sintoma que apareceu foi outro: o cabeçalho vazando 3px em 320px. Regra sem camada
  sempre vence regra em camada, então a camada de controle de [styles.css](web/src/styles.css)
  mora dentro de `@layer components`, e `e2e/afordancia.spec.ts` cobra isso.
- **Bundle de entrada sem hash servido com cache longo** congela o deploy. `main.js`,
  `polyfills.js` e `styles.css` saíam sem hash e com `max-age=31536000`: quem já tinha visitado o
  site ficava com o bundle antigo por um ano, e nenhuma mudança aparecia — nem a reforma inteira
  do design. `outputHashing: all` no build, `immutable` no estático e `no-cache` no HTML, que é
  quem aponta para eles. `e2e/ssr.spec.ts` cobra os dois.
- **Anel de foco em elemento não operável.** O `<h1>` recebe foco a cada troca de rota, para o
  leitor de tela não perder o lugar — mas tem `tabindex="-1"` e está fora da ordem de tabulação,
  então o anel ali não diz onde a tecla vai agir. Toda tela abria parecendo ter um controle
  selecionado. Medir por seletor engana: a régua é `document.activeElement`.
- **`<img>` com `src` vazio** desenha o texto alternativo dentro da caixa e estoura o layout:
  o avatar de quem não tem foto ficava 41px numa caixa de 34. Conta sem foto renderiza a
  inicial, não um `<img>` sem fonte.
- **`_session_global()` em caminho de request** — não filtra por usuário. É para job cross-tenant.
- **Dois refreshes simultâneos** derrubam a sessão: o refresh é rotacionado e queimado no uso. No
  web isso é coordenado **entre abas** por Web Lock — `_refreshInFlight` sozinho vale só dentro de
  uma aba, e duas abas têm dois nulos e o mesmo refresh no `localStorage`.
- **Escrita seguida de 4xx** — os handlers de `DomainError` vivem no `ExceptionMiddleware` do
  Starlette, que é *interno* ao middleware de observabilidade: a exceção nunca sobe. Quem decide
  commit ou rollback é o **status da resposta**, não a ausência de exceção. O que precisa
  sobreviver ao 4xx que provocou — contador de teto, marca de paywall — usa
  `independent_session()` / `outside_request_transaction()`.
- **Rota cara casada por prefixo com versão** — `/api/opportunities` casa, `/api/v1/opportunities`
  não. O teto morre em silêncio no dia da migração para o caminho canônico. O casamento é por
  **sufixo**.

- **Papel de cor usado como o outro papel** — `.good`/`.warn` pintavam P&L, que é **direção**, com
  os tokens de **estado**. O verde passava a significar marca, lucro e veredito favorável ao mesmo
  tempo, e uma perda aparecia como aviso. As classes foram removidas: direção é `text-up` /
  `text-down`; estado é `text-favorable` / `text-attention` / `text-adverse` / `text-indeterminate`.
- **Vocabulário gerado sem consumidor** — `fiTiposDeRendaFixa` e `fiLiquidez` saíam de
  `product-rules.json` e não eram importados por ninguém no web, enquanto quatro telas reescreviam o mapa
  à mão. O mobile fazia certo desde sempre (`core/labels.dart`). Ao gerar um vocabulário novo,
  confira se ele chega a uma tela — gerado e ignorado é pior que não gerado, porque parece
  resolvido. **A causa era o barrel:** `core/vocabulary.ts` não estava em `core/index.ts`, então
  a tela que quisesse usá-lo teria de importar por caminho. Agora está.
- **Série nova no vocabulário sem entrar nos mapas de classe** — `fiClasseTextoDaSerie` e irmãos
  eram montados só das séries de `categories`. Uma categoria de despesa em `series: 4` pedia
  `fiClasseTextoDaSerie[4]` e recebia `undefined`: a armadilha acima na forma inversa, consumidor
  sem vocabulário. O gerador agora varre os três blocos de categoria.

O `npm run lint:ui` cobre treze dessas, em **22 regras** — e a classificação importa: regra que
protege acessibilidade, contrato de produto ou erro silencioso **reprova o CI**; regra que
protege só preferência visual **avisa e não reprova**, porque bloquear por gosto gasta a
autoridade das que valem. Raio fora da escala e ícone decorando título são as duas que avisam.

Sete são de tela quebrada ou informação escondida: ícone não registrado, classe inexistente,
julgamento sem explicabilidade, gráfico sem tabela, botão de ícone sem `aria-label`, número
projetado sem faixa e promessa sobre o futuro — este último poupa a negação, porque "não há
garantia de retorno" é a frase certa e "retorno garantido" é a errada.

Cinco são de coerência do sistema, e existem porque o produto já as perdeu por inteiro:

| Regra | O que reprova | Por quê |
|---|---|---|
| Escala de papéis | `text-sm`, `font-bold` e afins no template | 384 utilitárias de tamanho conviviam com 372 papéis, dando dois corpos para a mesma coisa em telas vizinhas — e é no papel que "serifa decide, sans mede" vive |
| Quatro raios *(avisa)* | `rounded-xl`, `rounded-full`, `rounded-lg` sem sombra | `sm` marca, `md` assentado, `lg` **só o que flutua** (flutuar é ter sombra), `pill`. Havia três raios para a mesma caixa. Preferência fundamentada, não erro silencioso — e o `rounded-xl` já é pego pela regra de classe não emitida |
| Um foco só | `focus:ring*`, `focus:outline-none` | O anel é `outline` na cor da marca e já vem em `.input`/`.btn-*`/`.fi-focusable`; o do Tailwind desenhava outra coisa, e `outline-none` sem substituto apaga o foco |
| Controle do sistema | `<button>`/`<input>`/`<select>` sem classe do sistema | Havia nove grafias de botão só de ícone, com cinco alturas. Escape: `<!-- design-exception: controle — motivo -->` |
| Título sem ícone *(avisa)* | `<lucide-icon>` dentro de `<h1..h4>` | Ao lado de um título o ícone não acrescenta informação — faz a seção parecer cabeçalho de card de painel. Mantém lista de exceção por nome de arquivo, e regra que precisa conhecer nomes de arquivo é revisão com passos extras |
| Contorno de controle | `border: … var(--fi-hairline)` num seletor de controle | `hairline` é separador, e com ele a borda de `.btn-secondary` desenhava a **1,20:1** — um quarto dos 3:1 que a WCAG 1.4.11 pede. Controle desabilitado fica de fora, que a norma isenta |

---

## Invariantes

### Domínio e cálculo

- **Regra de negócio vive só no backend** (`analysis/`, `optimizer/`). Web e mobile delegam — não
  há cálculo de renda fixa duplicado no Angular.
- **Régua de score em um lugar por plataforma:** `analysis/score_ruler.py`,
  `web/src/app/core/score-ruler.ts`, `mobile/lib/core/score_ruler.dart`. Mudar um limiar exige os
  três, e o Python é o primeiro.
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
  sozinho. O `lint:ui` recusa tela que exiba `portfolio_value`/`passive_income_monthly` sem a faixa.
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
- **Cinco rotas são públicas e renderizadas no servidor, e a lista é fechada.** A raiz (`/`) é a
  landing de validação, e a página de ativo (`/ativo/:ticker`) é o canal de aquisição: robô não faz
  login e o modelo não comporta mídia paga.
  O texto jurídico (`/termos`, `/privacidade`, `/aviso-cvm`) está lá por outro motivo: robô de loja
  também não faz login, e a ficha de segurança de dados pede uma URL de privacidade que abre
  sozinha. A fronteira está em `web/src/app/app.routes.server.ts`, o teste lista as cinco pelo
  nome, e crescer essa lista é decisão registrada — não efeito colateral. No backend,
  `analyze_asset(personalized=False)` e `/api/public/*` são a leitura **sem titular**, com teto por
  IP.
- **O texto jurídico não repete o que o produto afirma.** O Aviso CVM lê
  `GET /api/public/affirmation`; `AFFIRMATION_LEVEL` é configuração, e uma segunda cópia da frase
  acabaria desatualizada justamente onde a pessoa a lê. O nível publicável hoje é o **2**; o 3 fica
  desligado até haver parecer. Enquanto o texto for minuta, `<app-legal-draft-notice>` diz isso —
  e é um componente só, para sair de uma vez.
- **O código do web roda também no Node.** Use `DOCUMENT` e `isPlatformBrowser`; nunca `document`,
  `localStorage`, `window` ou `navigator` direto — nem em inicializador de campo, que é onde a
  guarda mais escapa. Serviço que busca dado de titular também não roda no servidor: no SSR não há
  titular, a chamada responde 401 e ainda segura o render esperando a rede. `e2e/ssr.spec.ts` pede
  as rotas servidas **sem executar JavaScript** e exige conteúdo no HTML cru; sem ele o produto
  passou meses entregando página vazia para robô, com o teste de navegador verde por hidratação.
- **Busca global: o servidor devolve o que é da pessoa; a rota é do cliente.** `/search` procura
  carteira, renda fixa e universo e devolve `ref` — ticker ou id, nunca caminho. Destino de tela
  também é resultado, mas a lista vive em cada cliente (`SEARCH_DESTINATIONS` no web,
  `buscaDestinos` no mobile): as árvores diferem, e um catálogo de rotas no servidor seria segunda
  verdade sobre a IA. Por isso os destinos filtram sem rede.
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
  ao levar 401, com a renovação compartilhada. No web, `httpErrorInterceptor` é o mais externo.
- **Telemetria não leva carteira.** O `before_send` de cada plataforma
  (`core/telemetry.py`/`.ts`/`.dart`) é **lista de permissão**: ticker no caminho vira `{id}`, valor
  em reais e número citado em erro são redigidos, corpo de request e `extra` não saem, do usuário
  sai só o identificador, e variável local de frame é descartada. Uma chave nova num payload nasce
  redigida. Três suítes travam isso, e é a Política de Privacidade escrita como código.
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
- **Assinatura carrega o próprio preço** (`price_cents`, `locked`): preço travado de fundador é
  promessa pública, então é dado e não memória. Webhook é idempotente por `processed_webhooks`.
  O trial de 14 dias começa na **primeira posição salva**, não no cadastro.
- **Indicação credita na qualificação, nunca no cadastro** (`services/referral_service.py`). Conta
  é grátis de fabricar aos milhares; carteira não é. A atribuição acontece **só no login**
  (`referral_code` em `/auth/google`) e é recusada para quem já tem carteira, já foi atribuído, ou
  usou o próprio código; recusa não derruba o login. Crédito é `subscriptions.credited_until`,
  separado de `trial_ends_at` para não reabrir trial gasto, com teto declarado. A rota nunca devolve
  quem foi indicado.

### Interface — web e mobile

- **A navegação é o ciclo do dinheiro**: `/mes` → `/sobra` → `/patrimonio`, mais `/descobrir` e
  `/voce`, e `/ativo/:ticker` como camada. Continuam cinco destinos, e as URLs antigas
  (`/hoje`, `/carteira/*`, `/estrategia/*`) seguem como redirect — link salvo é contrato.
  `Hoje` saiu porque respondia "o que mudou", e isso é feed, não lugar: o feed vive no `Mês`, e
  o patrimônio e o veredito de saúde já existiam no `Patrimônio`. `Estratégia` se dissolveu —
  sem aporte, meta e projeção, sobrava o desvio de alocação, que é leitura de patrimônio e vive
  em `/sobra/desvio`.
- **A camada visual é escrita; a régua é gerada.** Cor, tipografia, espaço, raio, motion e
  densidade vivem em [web/src/foundation.css](web/src/foundation.css), escrito à mão, com espelho
  à mão em [mobile/lib/core/design_tokens.dart](mobile/lib/core/design_tokens.dart). O que continua
  gerado é o que precisa ser **igual nas três plataformas por ser número, e não aparência**:
  `design-tokens/product-rules.json` → `node design-tokens/build-rules.mjs` → as bandas das cinco
  réguas (que espelham `score_ruler.py`), o vocabulário de veredito e os rótulos de categoria,
  setor, tipo de ativo, tipo de renda fixa e liquidez. Qualquer chave `*Ruler` vira
  `fi<Nome>Bands`/`fi<Nome>Domain` automaticamente. Nunca edite os quatro gerados — eles dizem
  isso no cabeçalho — nem escreva hexadecimal em `styles.css`, `tailwind.config.js` ou `theme.dart`.
- **A paridade é de conceito, não de valor. Igualdade visual não é exigida.** O contrato é
  *mesma intenção, não mesma implementação*: conceito, nome e hierarquia são iguais nas duas
  plataformas; espaçamento, composição, navegação, gesto e **valor de cor** são livres. Um
  telefone sob sol pode precisar de mais contraste que um monitor, e exigir o mesmo hexadecimal
  impediria a correção. O que a máquina cobra são duas coisas:
  - **`check-contrast.mjs`** mede `foundation.css` **e** `design_tokens.dart`, cada um contra o
    **piso** — não um contra o outro. Reprova papel abaixo do piso, papel declarado só num tema,
    contorno de controle sob 3:1 e preenchimento que não se distingue do próprio poço. Também
    confere as **duas cópias do tema claro** do CSS: eram 44 papéis sem guarda, e quem editasse
    só a consulta de mídia quebrava o contraste de quem está no padrão do sistema.
  - **`check-parity.mjs`** responde se os cinco destinos existem nas duas plataformas. Existe
    porque a resposta já foi *não* por meses — o web migrou para o ciclo do dinheiro e o mobile
    ficou sem `/mes` e `/sobra`, com a documentação afirmando que os shells eram espelhos.
    Ausência conhecida é **dívida registrada** em `DIVIDA_HOJE`, e a lista só encolhe: um item
    que passe a existir reprova, porque lista de dívida que não encolhe é a documentação
    mentindo de novo. **Hoje ela está vazia**, e foi ela quem cobrou a própria baixa.
- **Ícone e favicon são gerados**, do `brand` de `foundation.css` via
  `python design-tokens/build-icons.py` (requer Pillow). **O launcher nativo é um segundo passo**:
  `cd mobile && dart run flutter_launcher_icons` — sem ele os ícones do app ficam com a cor antiga
  mesmo com a fundação correta.
- **Não existe alias de cor.** Nada de `bg-accent`, `text-tx`, `bg-panel`, `text-muted`, nem paleta
  crua do Tailwind. Os papéis são `ground`/`ground-1`/`ground-2`, `hairline`, `ink`/`ink-2`/`ink-3`,
  `brand`/`on-brand`, os estados `favorable`/`attention`/`adverse`/`indeterminate`, a direção
  `up`/`down` e as séries `series-1..11`/`series-other`.
- **Estado ≠ direção.** Estado é julgamento (veredito, saúde, severidade) e tem prioridade
  cromática; direção é a aritmética de um número (P&L, linha de gráfico) e tem croma baixo. No
  mobile: `fiStateColor(FiState.x, brightness)` e `fiDirectionColor(delta, brightness)`.
- **Fio + chão, não card + card.** A hierarquia de uma página nasce de espaço, tipo e uma regra
  horizontal — `.fi-block` é isso. A caixa (`.card`) fica reservada ao que é **objeto**: uma
  posição, uma opção de renda fixa, uma sugestão. Card dentro de card dentro de card era a forma
  mais reconhecível de o produto virar painel de BI, e havia três níveis em `renda-fixa`.
- **Controle vem do sistema, não do template.** `.btn-primary`, `.btn-secondary`, `.btn-icon`
  (`-quiet`, `-danger`), `.btn-link`, `.btn-quiet` (`.btn-explain`), `.menu-item`, `.input`
  (`.input-bare`), `.field-label`, `.data-table`, `.notice` (`-attention`/`-adverse`/`-brand`).
  Remontar um deles com utilitárias produz alvo de toque, raio e foco diferentes a cada tela.
- **Grade de KPI é o cheiro de painel.** Três a quatro caixas centralizadas com um número dentro
  não são informação organizada, são widgets. A alternativa é uma linha de cifras sob um fio
  (`<dl>`) quando são poucas, ou `.data-table` quando o que importa é comparar.
- **Julgamento renderizado exige explicabilidade, e o lint cobra.** Score, veredito, preço justo e
  sugestão precisam de `<app-provenance>`, `<app-help-tooltip>` ou equivalente. Mencionar em prosa
  não conta. O escape exige motivo escrito: `<!-- design-exception: explicabilidade — ... -->`.
  **Há uma forma só de escapar**, e ela nomeia a regra: escapar de cabeçalho não escapa de
  contraste. Eram cinco grafias para a mesma ideia.
- **Contraste é verificado, não recomendado** (`design-tokens/check-contrast.mjs`, no CI). `ink-3`
  conta como texto (4,5:1) porque legenda é texto pequeno; série de gráfico conta como forma (3:1)
  porque nunca é a única informação; `hairline` fica de fora, é decoração.
- **Filtro e recorte vivem na URL**, não em `sessionStorage`/`signal` — link salvo é contrato.
  Oportunidades (`q`, `dy`, `mos`, `cat`, `destaque`, `p`), quedas (`min_score`, `top`, `category`),
  tabela de posições (`cols`, `d`).
- **Densidade é preferência da conta; tema é do aparelho.** Densidade vive em `preferences.density`,
  aplicada pelo `DensityService` como `[data-density]` no `<html>`; tema vive em `localStorage`. Na
  tabela de posições a URL vence a preferência.
- **Push exige o app instalado, e isso é decisão declarada** — o web sinaliza em `/voce/alertas`.
