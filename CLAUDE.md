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

**Histórico não é pendência.** Nada no CHANGELOG é trabalho a fazer, mesmo quando descreve um
problema. O que está aberto está no KNOWN_ISSUES, e só lá.

---

## Como trabalhar aqui

**Pronto = suíte verde.** Tudo abaixo roda no CI (`.github/workflows/ci.yml`) a cada push.

```bash
cd backend && python -m pytest -q                  # 771 passam, 11 pulam sem Redis
cd backend && python -m ruff check app tests migrations
cd mobile  && flutter analyze && flutter test      # 0 issues, 49 testes
cd web     && npm run format:check && npm test && npm run build && npm run lint:ui   # 98 testes
cd web     && npm run e2e                          # 10 testes em navegador
node design-tokens/build.mjs --check               # tokens sincronizados
node design-tokens/check-contrast.mjs              # contraste AA
python design-tokens/build-icons.py --check        # marca sincronizada
```

Duas ressalvas que já custaram tempo:

- **Confira o código de saída, não o texto.** O build do Angular imprime erro como
  `X [ERROR] TS…`; um `grep -i error` ingênuo passa reto.
- **`lint:ui` roda depois do build** — a fonte de verdade das classes é o CSS emitido.
- **Não rode `dart format`.** O CI do mobile é `flutter analyze && flutter test`. O formatter
  reescreve o `design_tokens.dart` gerado e quebra `if`s de uma linha que o repo mantém.

### Ao adicionar…

| O quê | Faça também | Senão |
|---|---|---|
| Coluna no model | Migração Alembic (`backend/migrations/`) | `test_database_migration.py` falha |
| Tabela com `user_id` | Entrar em `account_store.USER_SCOPED_MODELS` | `test_export_cobre_toda_tabela_com_dono` falha |
| Campo calculado numa resposta | Declarar no modelo Pydantic / `fromJson` do Dart | Some **em silêncio** |
| `<lucide-icon>` | Registrar em `LucideAngularModule.pick({...})` ([app.config.ts](web/src/app/app.config.ts)) | Quebra a tela em runtime |
| Classe CSS global | Confirmar que existe em [styles.css](web/src/styles.css) | Quebra a tela em silêncio |
| Limiar de score | Mudar nas três plataformas, Python primeiro | Réguas divergem |
| Tela ou rota | Ler [docs/design/](docs/design/) antes | IA diverge entre plataformas |
| Cor, tipografia, espaço | Editar `design-tokens/tokens.json` e rodar o gerador | Job `design-tokens` falha |

---

## Armadilhas que não quebram o build

Esta lista existe porque cada item já quebrou a tela ou o dado **com o CI verde**.

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
- **`_session_global()` em caminho de request** — não filtra por usuário. É para job cross-tenant.
- **Dois refreshes simultâneos** derrubam a sessão: o refresh é rotacionado e queimado no uso.

O `npm run lint:ui` cobre sete dessas: ícone não registrado, classe inexistente, julgamento sem
explicabilidade, gráfico sem tabela, botão de ícone sem `aria-label`, número projetado sem faixa e
promessa sobre o futuro — este último poupa a negação, porque "não há garantia de retorno" é a
frase certa e "retorno garantido" é a errada.

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

- **O livro-razão é a fonte da carteira; a posição é projeção dele.** A matemática vive em
  `ledger/`, que não conhece banco. A escrita grava **só lançamento**
  (`ledger_service.record_position_state`, `record_sale`, `record_removal`) e reconstrói a linha de
  `portfolio` a partir dele — não há mais espelhamento. `rebuild_projection` refaz tudo do zero
  (`POST /transactions/rebuild`), e `GET /transactions/reconciliation` deixou de comparar duas
  verdades: agora confere a projeção contra a fonte. Categoria não é derivável do razão, então
  viaja junto com a escrita.
- **Uma declaração de posição ancora a linha do tempo.** O que vier depois dela se aplica em cima,
  na ordem das datas; o que veio antes é irrelevante, porque ela já o substituiu. É o que permite
  registrar venda retroativa contra posição declarada hoje sem fabricar histórico.
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

### Dados externos

- **Fontes:** BRAPI (ações BR/FIIs/BDRs/ETFs) e BCB SGS (CDI/Selic/IPCA). Finnhub, CoinGecko,
  Gemini e yfinance/Alpha Vantage foram descontinuados — sem ações internacionais fora de BDR, sem
  cripto, sem IA externa.
- **Dado externo passa por faixa de plausibilidade** (`collectors/plausibility.py`): campo absurdo
  vira `None`, preço absurdo rejeita o snapshot inteiro.
- **Fonte tem disjuntor** (`collectors/circuit.py`) — aberto, nem tenta, e quem chama cai no cache
  vencido. `GET /data-quality/source` mostra os dois sem varrer o universo.
- **Onde o cache mora é trocável** (`core/cache_backends.py`): arquivo local por padrão, Redis
  quando `REDIS_URL` existir. Não é desempenho, é correção — com dois nós e cache por nó, a mesma
  pessoa vê preços diferentes conforme o balanceador. O vencimento vai **dentro** do valor mesmo no
  Redis, porque `get_with_age` precisa do dado vencido para o disjuntor degradar. `REDIS_URL` sem o
  pacote instalado **falha alto**.

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
- **A página de ativo é a única rota pública, e é renderizada no servidor.** É o canal de
  aquisição: robô não faz login e o modelo não comporta mídia paga. A fronteira está em
  `web/src/app/app.routes.server.ts` e tem teste. No backend, `analyze_asset(personalized=False)` e
  `/api/public/*` são a leitura **sem titular**, com teto por IP.
- **O código do web roda também no Node.** Use `DOCUMENT` e `isPlatformBrowser`; nunca `document`
  ou `localStorage` direto.
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
- **Sessão tem TTL curto e refresh rotacionado.** Acesso 1h, refresh 30 dias queimado no uso.
  Revogação por `jti` (este dispositivo) e `session_cuts` (todos). Os clientes renovam **uma vez**
  ao levar 401, com a renovação compartilhada. No web, `httpErrorInterceptor` é o mais externo.
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

- **Cinco destinos por intenção**, iguais nas duas plataformas: `/hoje`, `/carteira`, `/descobrir`,
  `/estrategia`, `/voce`, mais `/ativo/:ticker` como camada. URLs antigas seguem como redirect.
  Meta mora em Estratégia porque é a referência que produz o desvio.
- **Tokens de design são gerados, não escritos.** Cor, tipografia, espaço, raio, motion e as bandas
  das réguas saem de `design-tokens/tokens.json` via `node design-tokens/build.mjs`, que emite
  `web/src/tokens.css`, `web/src/app/core/design-tokens.ts` e `mobile/lib/core/design_tokens.dart`.
  Nunca edite os gerados nem escreva hexadecimal em `styles.css`, `tailwind.config.js` ou
  `theme.dart`. Qualquer chave `*Ruler` vira `fi<Nome>Bands`/`fi<Nome>Domain` automaticamente.
- **Ícone e favicon também são gerados**, de `tokens.json` via `python design-tokens/build-icons.py`
  (requer Pillow). **O launcher nativo é um segundo passo**: `cd mobile && dart run
  flutter_launcher_icons` — sem ele os ícones do app ficam com a cor antiga mesmo com `tokens.json`
  correto.
- **Não existe alias de cor.** Nada de `bg-accent`, `text-tx`, `bg-panel`, `text-muted`, nem paleta
  crua do Tailwind. Os papéis são `ground`/`ground-1`/`ground-2`, `hairline`, `ink`/`ink-2`/`ink-3`,
  `brand`/`on-brand`, os estados `favorable`/`attention`/`adverse`/`indeterminate`, a direção
  `up`/`down` e as séries `series-1..11`/`series-other`.
- **Estado ≠ direção.** Estado é julgamento (veredito, saúde, severidade) e tem prioridade
  cromática; direção é a aritmética de um número (P&L, linha de gráfico) e tem croma baixo. No
  mobile: `fiStateColor(FiState.x, brightness)` e `fiDirectionColor(delta, brightness)`.
- **Julgamento renderizado exige explicabilidade, e o lint cobra.** Score, veredito, preço justo e
  sugestão precisam de `<app-provenance>`, `<app-help-tooltip>` ou equivalente. Mencionar em prosa
  não conta. O escape exige motivo escrito: `<!-- sem-explicabilidade: ... -->`.
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
