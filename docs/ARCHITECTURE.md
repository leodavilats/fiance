# fiance — Arquitetura Técnica

> Referência de **como o sistema é montado por dentro**: camadas, algoritmos, endpoints e
> estrutura de pastas. Revisado em **2026-08-28**.
>
> Setup e variáveis de ambiente ficam no [README.md](../README.md). O que cada tela faz fica em
> [FEATURES.md](FEATURES.md). O histórico das decisões fica em [CHANGELOG.md](CHANGELOG.md).

## Visão geral

fiance é uma plataforma multi-tenant de análise de investimentos focada na B3, com três frontends consumindo a mesma API: **web** (Angular 22), **mobile** (Flutter) e a API em si (**FastAPI**). Login via Google (JWT próprio emitido pelo backend), dados persistidos em Postgres (produção) / SQLite (dev), isolados por `user_id`.

**Correção importante em relação a documentação/memória antigas**: o projeto migrou de yfinance/Alpha Vantage para **BRAPI** (ações BR/FIIs/BDRs/ETFs). Finnhub (ações US), CoinGecko (cripto) e Gemini (IA) foram removidos em 2026-08-19 — o sistema não trabalha mais com ações internacionais fora de BDR nem com criptomoedas; a exposição internacional é só via BDR, e ETF passou a ser uma classe de ativo própria. A persistência não é mais JSON local — é SQLAlchemy sobre Postgres/SQLite.

---

## Backend (`backend/app/`)

### Camadas

- **`main.py`** — cria a app FastAPI, CORS, middleware de observabilidade e handlers globais de exceção, inclui `router` sob prefixo `/api`. Erros de domínio são **tipados** (`core/errors.py`: `DomainError`/`NotFoundError`/`ConflictError` carregam o status) — o mapeamento por palavra-chave na mensagem (`"não encontrado" in msg`) foi removido. Usa `lifespan` (não `on_event`): `init_db()`, limpeza das posições `RF_*` legadas e `core/jobs.start_background_jobs()`.
- **`core/jobs.py`** — jobs de background com **lock cooperativo no banco** (tabela `job_locks`, TTL que expira sozinho): warm-up do scan de mercado, ciclo de notificação, snapshot diário de patrimônio e manutenção de cache. Antes eram dois `asyncio.create_task` soltos, executados por todo worker — o que gerava push duplicado com mais de um worker.
- **`core/observability.py`** — middleware que abre **uma sessão de banco por request**, memoiza o pipeline caro por request, cronometra latência por rota e propaga `X-Request-Id`. Contadores de chamada externa e cache hit rate expostos em `GET /api/metrics`.
- **`core/brt.py`** — fuso fiscal (UTC-3 fixo; o Brasil não usa horário de verão desde 2019). A isenção mensal de R$ 20 mil e as faixas de IR são apuradas por mês calendário brasileiro, não UTC.
- **`analysis/`** — algoritmos puros de domínio (sem I/O):
  - `fair_price.py` — núcleo de valuation, dividido em duas metades: `compute_fair_price_inputs()` produz o que **não** depende de preferência (dado de mercado, cacheável globalmente) e `fair_price_from_inputs()` aplica o `desired_yield` do usuário (CPU pura, por request). `compute_fair_price()` continua existindo como atalho. A média de dividendos usa anos-calendário **completos**, com denominador igual aos anos cobertos pelo histórico; o DCF recebe crescimento em **percentual**. `compute_technical()` expõe `trend_basis` (`long` com SMA 50/200, `short` com 20/50 quando o histórico é curto, `none` sem série) — antes a tendência ficava permanentemente `unknown`. Roteamento por tipo: FII → consenso `[bazin, pvp_fair]` (nunca Graham); BDR → Graham + DCF; ETF → só `bazin` (dividend yield histórico, sem Graham/DCF — ETF não tem EPS/book_value de empresa); ações BR → Bazin/Graham/DCF. `desired_yield_for()` define metas de yield (6% ações, 10% FII, 4% BDR, 4% ETF), configuráveis via `prefs` do usuário. `compute_technical()` calcula SMA50/200, RSI14, tendência, distância de 52w high/low.
  - `scoring.py` — `score_opportunity()` é o score real usado por `opportunity_service.py` (0–100): combina margem de segurança (preço justo), qualidade (ROE/margem), endividamento (D/E), crescimento de receita, dividend yield e técnico (RSI/tendência, peso baixo — buy-and-hold, não day trade), ponderado por perfil de risco (`OPPORTUNITY_WEIGHTS`, conservative/moderate/aggressive). FII/ETF usam subconjunto (mos+dividend+liquidez, sem EPS/ROE/dívida de empresa). Os pesos são **renormalizados sobre as dimensões disponíveis** e o breakdown carrega `data_completeness`: ausência de dado deixa de pontuar como nota baixa. `score_company()`/`rank()`/`PROFILE_WEIGHTS` (modelo alternativo baseado em P/L·P/VP, sem consumidor) foram **removidos em 2026-08-20** junto de `CompanyFundamentals`/`ScoredCompany` — eram ~200 das 380 linhas do arquivo e o risco real era um dev corrigir o modelo errado.
  - `score_ruler.py` — régua única do score (limiares 75/60/40 e critério de destaque), espelhada em `web/src/app/core/score-ruler.ts` e `mobile/lib/core/score_ruler.dart`. Antes o mesmo número tinha três réguas.
  - `sectors.py` — tradução dos setores crus da BRAPI para português, usada pelos alertas do backend (que emitiam "Setor Financial Services concentrado").
  - `renda_fixa_analysis.py` — % do CDI **multiplicativo** (110% do CDI = 1,10 × CDI), IPCA+ compondo inflação com juro real, constante única de dias por mês, e dois números explícitos de comparação com CDI (líquido e equivalente bruto por faixa de IR) no lugar do benchmark `cdi × 0.85` hardcoded. `analyze_one(prazo_meses_override=...)` é o que permite marcar uma posição a mercado.
  - `classify.py` — `auto_category()` mapeia AssetType → categoria canônica (fii→fiis, etf→etfs, bdr→bdrs, resto→acoes_br); `resolve_category()` trata categorias legadas (`renda`/`trade`/`caixa`). Categoria `bdrs` (antes `acoes_int`) foi renomeada de verdade em 2026-08-19, sem alias — sistema ainda sem usuários em produção, então sem dado real para migrar.
  - `dip_analysis.py`, `decision.py`, `strategy.py` — análise de quedas, motor de decisão de compra/venda, estratégias de alocação. `strategy.py::build_investment_strategy()` (consumido por `GET /strategy`) já usava `opportunity_service.get_opportunities()` para sugerir compras por gap de alocação — herda automaticamente o score/boost de preferências novos. Ganhou também `reduce_suggestions` (2026-08-19): posições já na carteira com veredito `SELL`/`STRONG_SELL` (via `PortfolioService.evaluate_portfolio`), sinalizando também se a categoria está acima da meta.
  - `falsifiers.py` — lê a régua **ao contrário**: os limiares de margem de segurança dão, por
    álgebra, o preço em que o veredito muda, e o Bazin dá o corte de dividendo que apaga o desconto.
    Não há falsificador genérico — sem preço justo a lista sai vazia, porque "fique de olho nos
    resultados" seria almanaque no lugar de uma condição conferível. O teste fecha o círculo: passa
    o preço anunciado de volta pelo `decide` e confere que o veredito vira o prometido.
  - `scenarios.py` — os três cenários da projeção. O conservador zera o crescimento (só o aporte
    trabalha) e o otimista multiplica as premissas por um fator **declarado**, não estimado.
    `_low`/`_high` são obrigatórios em `PassiveIncomeMonth`: com default existiria um caminho em que
    o número sai sozinho.
  - `portfolio_health.py` — saúde da carteira na mesma régua do score de ativo.
- **`api/`** — 33 routers FastAPI (ver seção Endpoints). `basic.py` separa `router` (público: health/universe) de `admin_router` (protegido: `/cache/clear`, `/metrics`) — deixar `/cache/clear` público era DoS aberto.
- **`collectors/`** — integrações externas:
  - `universal.py` — `detect_type(symbol)` classifica em `br_stock|bdr|fii|etf`. Dispatcher: BR/FII/BDR/ETF → BRAPI (única fonte de cotação hoje). ETF detectado via lista curada `KNOWN_ETFS` (mesmo padrão de `KNOWN_UNITS`) além do `subType` da BRAPI. Ticker não suportado (ex.: ação US pura, cripto) levanta `UnsupportedTickerError` em vez de um asset_type — não há mais fallback "internacional genérico". Cache em camadas (fundamentals 2h, histórico 12h, dividendos 24h) + semáforo de 30 chamadas concorrentes.
  - `rates.py` — CDI/Selic/IPCA reais via BCB SGS (séries 4389/432/13522), cache 24h, fallback `14.40`/`14.40`/`5.0`.
  - `news.py` — coleta de notícias (RSS, sempre pt-BR/BR — todos os asset_types suportados são negociados na B3); `analyze_news_with_ai()` hoje é só o resumo determinístico (contagem de sentimento por item), sem IA externa.
  - `plausibility.py` — faixa de plausibilidade sobre todo dado externo: campo absurdo vira `None`,
    preço absurdo **rejeita o snapshot inteiro**. Dado errado que entra silenciosamente é pior que
    dado ausente, porque vira veredito.
  - `circuit.py` — disjuntor por fonte. Aberto, nem tenta, e quem chama cai no cache vencido.
    `GET /data-quality/source` mostra plausibilidade e disjuntor sem varrer o universo.
- **`core/`** — `config.py` (Pydantic Settings, universo hardcoded de fallback), `database.py` (engine SQLAlchemy, `init_db()`), `auth.py` (validação de ID token Google contra múltiplos `aud` permitidos, emissão de JWT HS256 próprio com TTL 30 dias), `cache.py`, `context.py` (contexto do usuário da request), `universe.py` (universo dinâmico via BRAPI `/quote/list`, com bucket próprio de ETFs).
  Acrescentados desde a revisão anterior:
  - `money.py` — dinheiro fiscal em `Decimal`, com escala e arredondamento (meio para cima, não
    bancário) num lugar só. `money()` constrói a partir de texto: `Decimal(0.1)` é
    `0.1000000000000000055…`. Dinheiro de tela continua `float`, e continua certo.
  - `sessions.py` — sessão com TTL curto e refresh **rotacionado**: acesso de 1h, refresh de 30 dias
    queimado ao ser usado, revogação por `jti` (um dispositivo) e `session_cuts` (todos).
  - `pagination.py` — cursor **keyset**, `(ordenação, id)`, nunca offset: com offset, inserir um
    registro entre duas páginas empurra tudo e o item da borda aparece duas vezes.
  - `cache_backends.py` — onde o cache mora é trocável: arquivo local por padrão, Redis com
    `REDIS_URL`. O vencimento vai **dentro** do valor mesmo no Redis, porque `get_with_age` precisa
    do dado vencido para o disjuntor degradar; TTL nativo o apagaria justo quando ele começa a
    servir. `REDIS_URL` sem o pacote instalado falha alto.
  - `usage.py` — contador de uso como primitiva única, servindo rate limiting e teto de plano. A
    granularidade mora no formato de `window_key`, não no schema.
  - `ratelimit.py` — tetos por usuário e por IP, sobre `usage.py`.
  - `events.py` — evento de produto com **dicionário fechado**: nome fora dele, ou propriedade com
    ticker ou valor, devolve 422. Dado de carteira não sai do produto.
- **`models/db_models.py`** — ORM: `User`, `PortfolioPosition` (PK composta `user_id+ticker`), `PortfolioSnapshot` (histórico diário, purga após 365 dias), `GoalDb`, `SectorGoalDb`, `PreferencesDb` (inclui `desired_yield_stock/fii/int/etf`, `notify_price_alerts` — imediato, alertas de risco —, `opportunities_frequency` (`off|daily|weekly|monthly`, substituiu o antigo `notify_new_opportunities` booleano), `risk_profile`, `preferred_categories`/`preferred_sectors`/`excluded_tickers` (CSV) e `last_digest_sent_at`), `PriceAlertDb`, `ClosedTradeDb` (histórico de vendas — lucro/prejuízo realizado, IR), `DeviceTokenDb` (token FCM por usuário), `NotifiedOpportunityDb` (dedupe de notificações de oportunidade).
- **`notifications/push.py`** — encapsula o Firebase Admin SDK; sem `FIREBASE_SERVICE_ACCOUNT_JSON` configurado, apenas loga em vez de enviar (degradação graciosa).
- **`services/notification_job.py`** — job periódico (chamado a cada 15min por um loop em `main.py`, sem scheduler externo). Alertas de preço continuam imediatos a cada ciclo (`notify_price_alerts`). O resumo de oportunidades (`STRONG_BUY` ou score≥75+DY≥6%, excluindo posições já na carteira e `excluded_tickers`) só dispara quando a cadência configurada em `opportunities_frequency` já venceu desde `last_digest_sent_at` (`_digest_due()`), agregando as melhores em um único push por ciclo. O mesmo push também lista tickers já na carteira com veredito `SELL`/`STRONG_SELL` (reaproveitando o scan já feito, sem chamada extra), como aviso de que vale revisar — a análise completa de por quê fica em `/strategy`.
- **`optimizer/`** — só `cost_calculator.py` (custo de venda/IR). Desde 2026-08-20 aplica **compensação de prejuízo acumulado** por categoria (a legislação permite abater prejuízo de ganhos futuros; sem isso o IR devido era superestimado) e devolve `loss_offset_used`/`taxable_profit` para o saldo ficar auditável. `allocator.py` e `portfolio.py` (HRP/min-vol/max-Sharpe via scipy) foram removidos em 2026-08-19 — existiam só para `/recommend`, removido no mesmo dia por falta de consumidor.
- **`ledger/`** — o livro-razão, e a **fonte de verdade** da carteira. Não conhece banco:
  `entries.py` define os lançamentos (`buy`, `sell`, `split`, `bonus`, `amortization`) e
  `projection.py::project_position` dobra os lançamentos na posição. Preço médio segue a convenção
  brasileira — venda reduz quantidade e custo, **nunca** a média. Evento corporativo é lançamento,
  não correção manual: desdobramento sem ajuste é IR errado. A escrita grava **só lançamento**
  (`services/ledger_service.record_position_state`, `record_sale`, `record_removal`) e reconstrói a
  linha de `portfolio` a partir dele — a posição é projeção, não fonte. `rebuild_projection` refaz
  tudo do zero (`POST /transactions/rebuild`) e `GET /transactions/reconciliation` confere a
  projeção contra a fonte, em vez de comparar duas verdades.
- **`importing/`** — importação de operações (`parser.py`, rota `/transactions/import`), em duas
  fases: prévia e commit. Tolerante com a forma do arquivo, intolerante com ambiguidade; o erro diz
  a linha; a gravação é atômica; duplicidade é **apresentada para decisão**, nunca silenciada.
- **`entitlement/`** — a cerca de plano, e o **único** lugar do código com condicional de plano.
  Entra desligada (`ENTITLEMENTS_ENABLED=false`: todo mundo tem tudo). `plans.py` é a régua como
  **dado**, com a justificativa de cada linha; `guard.py` aplica via `Depends(requires(Feature.X))`;
  bloqueio é 402 com corpo que a UI usa para montar o gate; `meter.py` conta consumo sobre
  `core/usage.py`. Dois testes de arquitetura travam isso: nenhuma condicional de plano fora do
  módulo, e `analysis`/`optimizer`/`collectors`/`ledger` não importam nada dele — se o cálculo
  souber quem paga, a independência do algoritmo vira promessa. Ativo da própria carteira nunca
  consome cota; a rota pública também não.
- **`payments/`** — `billing.py` (catálogo, checkout que **não** concede nada, webhook idempotente
  por `processed_webhooks`, reconciliação) e `provider.py` (protocolo do provedor). A assinatura
  carrega o **próprio preço** (`price_cents`, `locked`): preço travado de fundador é promessa
  pública, então é dado e não memória — reajustar a tabela não alcança quem contratou antes. O
  provedor real ainda não existe; o de desenvolvimento assina com o mesmo HMAC de propósito, para
  que o caminho de verificação seja exercitado.
- **`affirmation.py`** — o modo de afirmação como **configuração** (`AFFIRMATION_LEVEL`):
  descritivo, analítico (padrão) e prescritivo. A diferença é estrutural — o que sai fora do nível 3
  é o **valor por ativo**, que é o que instrui; a análise que o sustentava fica. Existe para que a
  resposta sobre CVM 19/20 seja uma variável, e não um refactor sob pressão.
- **`repositories/`** — fachada **tipada** (`PortfolioRepository`, `AssetRepository`) sobre `storage/portfolio_store.py`. Antes anotava tudo como `-> list[dict]`, apagando os TypedDicts do store — foi assim que nasceu o bug de `item.ticker` vs `item["ticker"]`.
- **`storage/portfolio_store.py`** — persistência real via SQLAlchemy `Session`. Todo método resolve `user_id` via `_session()` — é aqui que o multi-tenancy é aplicado. `_ensure_user` roda **só em caminhos de escrita** (`ensure_user=True`); leitura não paga o SELECT extra. Quando há sessão de request ativa, `_session()` a reutiliza em vez de abrir outra. `_session_global()` existe para jobs cross-tenant e **não** filtra por usuário — nunca usar em caminho de requisição.
- **`services/`** — orquestração de negócio: `asset_service`, `benchmark_service` (retorno **ponderado no tempo**, para aporte não virar rentabilidade), `dashboard_service` (alertas agrupados com ação e teto), `dip_service`, `dividends_service` (proventos recebidos de fato), `fixed_income_service` (marcação a mercado da RF), `followed_service` (resultado das sugestões seguidas vs Ibovespa), `goal_service`, `income_compare_service` (renda fixa × bolsa na mesma unidade), `opportunity_service` (scan com stale-while-revalidate), `portfolio_service`, `projection_service`, `quick_invest_service`, `snapshot_job` (snapshot diário fora do caminho de request), `strategy_service`, `whats_new_service`. Acrescentados desde a revisão anterior:
  `ledger_service` (espelha a escrita no razão), `search_service` (busca global — devolve `ref`,
  ticker ou id, **nunca** caminho de rota), `milestones` (marcos de ativação gravados pelo
  **servidor**, não pelo cliente), `referral_service` (indicação — crédito na qualificação, nunca
  no cadastro), `subscription_service`, `analytics_service` e `dividend_calendar_service`
  (calendário de proventos → `/dividends/pending`, sempre **sugestão**, nunca lançamento).

### Endpoints (`/api/v1/...`)

O caminho canônico é **`/api/v1`**. `/api` continua respondendo como alias em transição — os apps
instalados apontam para lá — e carimba `X-API-Deprecation`; toda resposta carrega `X-API-Version`.
A versão muda quando uma resposta deixa de ser retrocompatível; campo **adicionado** não muda a
versão.

Públicos: `GET /health`, `GET /universe`, `GET /universe/search` (autocomplete de ticker por
prefixo/nome) em `basic.py`, `POST /auth/google` (`auth.py`) e as rotas **sem titular**
`GET /public/asset/{ticker}` e `GET /public/universe` (`public.py`) — leitura impessoal de
propósito, para que a mesma URL devolva o mesmo conteúdo ao robô e a quem chega pelo link, com teto
por IP em vez de por usuário.

`POST /cache/clear` e `GET /metrics` **não** são públicos: vivem no `admin_router`, dentro do router protegido.

Autenticados (JWT obrigatório via `Depends(get_current_user)`):

| Método | Rota | Arquivo |
|---|---|---|
| GET/POST | `/alerts`, `GET /alerts/check`, `DELETE /alerts/{id}` | `alerts.py` |
| GET | `/asset/{symbol}`, `/asset/{symbol}/dip-analysis`, `/compare` | `assets.py` |
| GET | `/dashboard` | `dashboard.py` |
| GET | `/dip-scanner` | `dip_scanner.py` |
| GET/PUT | `/goals`, `/sector-goals` | `goals.py` |
| GET | `/opportunities` | `opportunities.py` |
| GET/PUT | `/portfolio` (PUT = importação destrutiva) | `portfolio_routes.py` |
| POST/DELETE | `/portfolio/position`, `/portfolio/position/{ticker}` (escrita por item) | `portfolio_routes.py` |
| POST/GET | `/portfolio/evaluate`, `/portfolio/sell`, `GET /portfolio/trades` | `portfolio_routes.py` |
| GET | `/auth/me` | `auth.py` |
| POST/DELETE | `/notifications/register-token` | `notifications.py` |
| GET/PUT | `/preferences` | `preferences.py` |
| POST | `/projection/passive-income` | `projection.py` |
| GET | `/strategy` | `strategy.py` |
| POST | `/quick-invest` | `quick_invest.py` |
| GET/POST | `/renda-fixa/taxas`, `/renda-fixa/comparar` | `renda_fixa.py` |
| GET | `/sectors-summary` | `sectors.py` |
| GET | `/benchmark` (retorno TWR, com `net_contributions`) | `benchmark.py` |
| GET | `/whats-new` | `whats_new.py` |
| GET/POST/PUT/DELETE | `/fixed-income`, `/fixed-income/{id}` | `fixed_income.py` |
| GET/POST/PUT/DELETE | `/dividends/received`, `/dividends/received/{id}` | `dividends.py` |
| GET | `/income-compare` | `income_compare.py` |
| GET/POST/DELETE | `/suggestions/followed`, `/suggestions/followed/{id}` | `followed.py` |
| GET | `/rebalance-suggestions` | `strategy.py` |
| GET | `/data-quality` | `data_quality.py` |
| GET/POST | `/transactions`, `POST /transactions/import` (prévia + commit) | `transactions.py` |
| GET | `/transactions/reconciliation` (razão × posição corrente) | `transactions.py` |
| GET | `/search` (carteira, renda fixa e universo; devolve `ref`) | `search.py` |
| GET | `/onboarding` (passo **derivado**, não guardado) | `onboarding.py` |
| GET | `/dividends/pending` (calendário → sugestão, nunca lançamento) | `dividends.py` |
| GET | `/demo/portfolio` (análise real, sem gravar nada) | `demo.py` |
| GET | `/account/export`, `DELETE /account` (nunca atrás de plano) | `account.py` |
| GET | `/entitlements` (o que o plano libera) | `entitlements.py` |
| POST | `/events` (dicionário fechado; 422 fora dele) | `events.py` |
| GET | `/billing/plans`, `POST /billing/checkout`, `/billing/webhook` | `billing.py` |
| GET | `/billing/reconciliation` (rota de operador) | `billing.py` |
| GET | `/referral`, `POST /referral/rotate` | `referral.py` |
| GET | `/data-quality/source` (plausibilidade e disjuntor) | `data_quality.py` |
| POST/GET | `/cache/clear`, `/metrics`, `POST /metrics/reset` | `basic.py` (admin_router) |

Onze rotas foram removidas em 2026-08-19 por não terem consumidor real — a lista e o motivo de
cada uma estão em [CHANGELOG.md](CHANGELOG.md). Vale a regra que saiu dali: **wrapper de client
não conta como uso, só chamada de tela conta.**

Dois campos são calculados internamente e **precisam estar declarados** no modelo de resposta para
chegarem ao cliente: `consensus_methods` em `FairPriceBlock` e `trend_basis` em `TechnicalBlock`.
`Modelo(**resultado.__dict__)` descarta chave não declarada em silêncio — foi assim que os dois
ficaram invisíveis até 2026-08-21. `test_fair_price.py` tem regressão para ambos.

---

## Web (`web/src/app/`)

Angular 22, standalone components, todas as rotas lazy-loaded. **40 entradas em
`app.routes.ts`**: as rotas de conteúdo, os layouts de seção e os redirects das URLs antigas. O
`authGuard` valida o `exp` do JWT, não só a presença do token.

Cinco destinos por intenção, mais o ativo como camada — o racional está em
[design/INFORMATION-ARCHITECTURE.md](design/INFORMATION-ARCHITECTURE.md):

| Rota | Componente |
|---|---|
| `/hoje` | `dashboard/` — central de decisão em 3 níveis |
| `/carteira` + 6 sub-rotas | `carteira-resumo/`, `composicao/`, `desempenho/`, `proventos/`, `posicoes/`, `encerradas/`, `portfolio-editor/` |
| `/descobrir` + 3 | `market/opportunities-list/`, `market/dip-scanner/`, `market/compare-assets/` |
| `/estrategia` + 4 | `strategy/`, `quick-invest/`, `metas/`, `shell/renda-fixa-page` (une `market/renda-fixa` e `market/income-compare`), `market/contribution-simulator/` |
| `/ativo/:ticker` | `ativo/` — página de research |
| `/voce` + 3 | `preferencias/`, `alertas/`, `conta/` |

- **`components/shell/`** — layouts de seção (`carteira`, `descobrir`, `estrategia`, `voce`), cada
  um com `SectionNavComponent` + `router-outlet`. A sub-navegação é feita de links roteados, não de
  tabs com estado local: cada destino tem URL, deep link e botão voltar.
- **`components/score-ruler/`** — a régua, elemento-assinatura do produto. Aceita um conjunto de
  bandas, então serve tanto o score de um ativo quanto a saúde da carteira.
- **`components/insight/`** — o padrão único de insight: o que aconteceu → por que importa → o que
  sustenta → o que fazer.
- **`core/services/carteira-store.service.ts`** — estado da carteira compartilhado pelas sete
  sub-rotas de `/carteira`. Sem ele, cada troca de sub-aba refaria `POST /portfolio/evaluate`, que
  é a chamada mais caras do produto.
- **`core/services/dip-analysis.service.ts`** — estado do drawer de diagnóstico de queda,
  compartilhado dentro de Descobrir. Vive num serviço porque um layout com `router-outlet` não
  recebe `output` de filho roteado.
- **`core/design-tokens.ts`** — **gerado** de `design-tokens/tokens.json`. Não editar.
- **`core/score-ruler.ts`** — apresentação da régua; os limiares vêm dos tokens gerados, que
  espelham `analysis/score_ruler.py`.
- **`core/services/ui-helper.service.ts`** — labels, ícones e cores de AssetType/categoria/setor,
  glossário e rótulos de proveniência.
- **`core/interceptors/`** — `auth.interceptor.ts` (Bearer), `http-error.interceptor.ts`.
- **`src/tokens.css`** — **gerado**. `styles.css` é uma camada de compatibilidade: os nomes antigos
  (`--accent`, `--panel`…) apontam para `--fi-*` e não carregam valor próprio.

**Pegadinha:** ícone do Lucide precisa ser registrado à mão em `LucideAngularModule.pick({...})`
(`src/app/app.config.ts`). Nome ausente não quebra o build — quebra a tela em runtime.

---

## Mobile (`mobile/`) — Flutter

Dart SDK `^3.10.7`. Dependências-chave: `dio`, `google_sign_in`, `flutter_riverpod`,
`flutter_secure_storage` (JWT), `go_router`, `fl_chart`, `google_fonts`.

`StatefulShellRoute.indexedStack` com **5 branches**, espelhando os destinos do web: `/hoje`,
`/carteira` (+ `renda-fixa`), `/descobrir` (+ `quedas`, `comparar`), `/estrategia` (+ `aporte`,
`metas`, `renda-fixa`, `projecao`), `/voce`. `/ativo/:ticker` fica fora do shell de abas. URLs
antigas seguem como redirect.

Estrutura `lib/`:
- **`core/`** — `api_client.dart` (Dio + Bearer), `api_repository.dart` (chamadas tipadas),
  `auth_service.dart` (Google Sign-In com `serverClientId` = Client ID Web, para o `aud` do idToken
  ser validável cross-platform), `models.dart` (DTOs), `providers.dart` (Riverpod), `router.dart`,
  `labels.dart` (equivalente ao `ui-helper.service.ts`), `theme.dart`.
- **`core/design_tokens.dart`** — **gerado** de `design-tokens/tokens.json`. Não editar.
  `theme.dart` é camada de compatibilidade: `AppColors` e `appRadius` apontam para os tokens.
- **`core/widgets/`** — `score_ruler.dart` (a régua, espelhando o web), `error_state.dart`
  (`FiErrorState` + `fiErrorMessage`, que traduz exceção em causa humana),
  `ticker_autocomplete_field.dart`, `help_tooltip.dart`, `brand_background.dart`.
- **`features/`** — `hoje/`, `carteira/`, `market/` (Descobrir: `opportunities_tab`,
  `quick_invest_view`, `asset_detail_sheet`), `estrategia/`, `config/`, `busca/`, `assets/`,
  `auth/`, `tools/tools_views.dart` (views de ferramenta, cada uma roteada) e `shell/`
  (`app_shell`, `tool_screen`). `dashboard_screen.dart` e `assets_screen.dart` foram
  reestruturados em 2026-08-26 e **não existem mais**.

**Paridade com o web.** O mobile consome a MESMA API, sem regra de cálculo duplicada — fair price,
score, renda fixa e IR ficam 100% no backend. Cores, tipografia e réguas semânticas são geradas da
mesma fonte, então não podem divergir.

A paridade fechou em **2026-08-28**: metas têm tela própria (`/estrategia/metas`) e RF × Bolsa
ganhou cliente Dart (`/estrategia/renda-fixa-vs-bolsa`). A única assimetria que resta é **decisão,
não lacuna**: push exige o app instalado, e o web sinaliza isso em `/voce/alertas`. O que continua
aberto está em [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

---

## Fluxo de dados (resumo)

```
Web (Angular) ─┐
                ├─→ HTTP + JWT Bearer ─→ FastAPI (/api/*) ─→ services/ ─→ analysis/ (cálculo puro)
Mobile (Flutter)┘                              │                    └─→ repositories/ → storage/ → Postgres/SQLite
                                                └─→ collectors/ → BRAPI / BCB SGS
```
