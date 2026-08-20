# fiance — Arquitetura Técnica

> Gerado por varredura completa em 2026-08-10; **revisado em 2026-08-20** após a
> implementação completa da auditoria de produto e engenharia (19/08/2026).
> Complementa o README.md (setup/instalação) com detalhes de arquitetura,
> algoritmos e estrutura interna.

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
- **`api/`** — 19 routers FastAPI (ver seção Endpoints). `basic.py` separa `router` (público: health/universe) de `admin_router` (protegido: `/cache/clear`, `/metrics`) — deixar `/cache/clear` público era DoS aberto.
- **`collectors/`** — integrações externas:
  - `universal.py` — `detect_type(symbol)` classifica em `br_stock|bdr|fii|etf`. Dispatcher: BR/FII/BDR/ETF → BRAPI (única fonte de cotação hoje). ETF detectado via lista curada `KNOWN_ETFS` (mesmo padrão de `KNOWN_UNITS`) além do `subType` da BRAPI. Ticker não suportado (ex.: ação US pura, cripto) levanta `UnsupportedTickerError` em vez de um asset_type — não há mais fallback "internacional genérico". Cache em camadas (fundamentals 2h, histórico 12h, dividendos 24h) + semáforo de 30 chamadas concorrentes.
  - `rates.py` — CDI/Selic/IPCA reais via BCB SGS (séries 4389/432/13522), cache 24h, fallback `14.40`/`14.40`/`5.0`.
  - `news.py` — coleta de notícias (RSS, sempre pt-BR/BR — todos os asset_types suportados são negociados na B3); `analyze_news_with_ai()` hoje é só o resumo determinístico (contagem de sentimento por item), sem IA externa.
- **`core/`** — `config.py` (Pydantic Settings, universo hardcoded de fallback), `database.py` (engine SQLAlchemy, `init_db()`), `auth.py` (validação de ID token Google contra múltiplos `aud` permitidos, emissão de JWT HS256 próprio com TTL 30 dias), `cache.py`, `context.py` (contexto do usuário da request), `universe.py` (universo dinâmico via BRAPI `/quote/list`, com bucket próprio de ETFs).
- **`models/db_models.py`** — ORM: `User`, `PortfolioPosition` (PK composta `user_id+ticker`), `PortfolioSnapshot` (histórico diário, purga após 365 dias), `WatchlistItemDb` (sem rota HTTP desde 2026-08-19 — feature nunca teve tela; mantido só o schema, ver KNOWN_ISSUES item 16), `GoalDb`, `SectorGoalDb`, `PreferencesDb` (inclui `desired_yield_stock/fii/int/etf`, `notify_price_alerts` — imediato, alertas de risco —, `opportunities_frequency` (`off|daily|weekly|monthly`, substituiu o antigo `notify_new_opportunities` booleano), `risk_profile`, `preferred_categories`/`preferred_sectors`/`excluded_tickers` (CSV) e `last_digest_sent_at`), `PriceAlertDb`, `ClosedTradeDb` (histórico de vendas — lucro/prejuízo realizado, IR), `DeviceTokenDb` (token FCM por usuário), `NotifiedOpportunityDb` (dedupe de notificações de oportunidade).
- **`notifications/push.py`** — encapsula o Firebase Admin SDK; sem `FIREBASE_SERVICE_ACCOUNT_JSON` configurado, apenas loga em vez de enviar (degradação graciosa).
- **`services/notification_job.py`** — job periódico (chamado a cada 15min por um loop em `main.py`, sem scheduler externo). Alertas de preço continuam imediatos a cada ciclo (`notify_price_alerts`). O resumo de oportunidades (`STRONG_BUY` ou score≥75+DY≥6%, excluindo posições já na carteira e `excluded_tickers`) só dispara quando a cadência configurada em `opportunities_frequency` já venceu desde `last_digest_sent_at` (`_digest_due()`), agregando as melhores em um único push por ciclo. O mesmo push também lista tickers já na carteira com veredito `SELL`/`STRONG_SELL` (reaproveitando o scan já feito, sem chamada extra), como aviso de que vale revisar — a análise completa de por quê fica em `/strategy`.
- **`optimizer/`** — só `cost_calculator.py` (custo de venda/IR). Desde 2026-08-20 aplica **compensação de prejuízo acumulado** por categoria (a legislação permite abater prejuízo de ganhos futuros; sem isso o IR devido era superestimado) e devolve `loss_offset_used`/`taxable_profit` para o saldo ficar auditável. `allocator.py` e `portfolio.py` (HRP/min-vol/max-Sharpe via scipy) foram removidos em 2026-08-19 — existiam só para `/recommend`, removido no mesmo dia por falta de consumidor.
- **`repositories/`** — fachada **tipada** (`PortfolioRepository`, `AssetRepository`) sobre `storage/portfolio_store.py`. Antes anotava tudo como `-> list[dict]`, apagando os TypedDicts do store — foi assim que nasceu o bug de `item.ticker` vs `item["ticker"]`.
- **`storage/portfolio_store.py`** — persistência real via SQLAlchemy `Session`. Todo método resolve `user_id` via `_session()` — é aqui que o multi-tenancy é aplicado. `_ensure_user` roda **só em caminhos de escrita** (`ensure_user=True`); leitura não paga o SELECT extra. Quando há sessão de request ativa, `_session()` a reutiliza em vez de abrir outra. `_session_global()` existe para jobs cross-tenant e **não** filtra por usuário — nunca usar em caminho de requisição.
- **`services/`** — orquestração de negócio: `asset_service`, `benchmark_service` (retorno **ponderado no tempo**, para aporte não virar rentabilidade), `dashboard_service` (alertas agrupados com ação e teto), `dip_service`, `dividends_service` (proventos recebidos de fato), `fixed_income_service` (marcação a mercado da RF), `followed_service` (resultado das sugestões seguidas vs Ibovespa), `goal_service`, `income_compare_service` (renda fixa × bolsa na mesma unidade), `opportunity_service` (scan com stale-while-revalidate), `portfolio_service`, `projection_service`, `quick_invest_service`, `snapshot_job` (snapshot diário fora do caminho de request), `strategy_service`, `whats_new_service`.

### Endpoints (`/api/...`)

Públicos: `GET /health`, `GET /universe`, `GET /universe/search` (autocomplete de ticker por prefixo/nome) em `basic.py`, e `POST /auth/google` (`auth.py`).

`POST /cache/clear` e `GET /metrics` deixaram de ser públicos em 2026-08-20 — estão no `admin_router`, dentro do router protegido.

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
| POST/GET | `/cache/clear`, `/metrics`, `POST /metrics/reset` | `basic.py` (admin_router) |

Removidos em 2026-08-19 por não terem consumidor real em web/mobile (ver KNOWN_ISSUES.md item 16): `GET /dividends/ranking` (nem chegava a ser importável), `GET /dip-scanner/stream` (SSE), `POST /recommend`, `POST /analyze`, `GET /rebalance`, `POST /projection/sector-allocation`, `POST /renda-fixa/analisar`, `POST /portfolio/refresh`, `DELETE /notifications/register-token`, `GET/PUT /watchlist`, `DELETE /watchlist/{ticker}`.

---

## Web (`web/src/app/`)

Angular 22 standalone components, lazy-loaded. Rotas (`app.routes.ts`): `/login` (público), `/dashboard`, `/assets`, `/assets/cadastro`, `/market`, `/config` (atrás de `authGuard`), fallback → `/dashboard`. O `authGuard` valida o `exp` do JWT, não só a presença do token.

- **`components/dashboard/`** — tela inicial consolidada.
- **`components/assets/`** ("Meus Ativos") — **análise**, somente leitura: resumo, composição, renda fixa marcada a mercado, posições (tabela ordenável, seleção múltipla para comparar, exportação CSV), proventos recebidos, venda e histórico. Não há mais cálculo de RF no cliente.
- **`components/portfolio-editor/`** — **cadastro** (`/assets/cadastro`): CRUD de posições e de renda fixa, com salvamento explícito por linha. Antes tudo convivia em `assets` com autosave por debounce sobre um PUT destrutivo.
- **`components/market/`** — maior tela do app. Reduzida a 2 abas em 2026-08-19 (`activeTab`: `opportunities` | `ferramentas` — abas "Segmentos" e "Investir" removidas de Mercado nessa data; ficha de Estratégia de Investimento continua existindo só como página própria em `components/strategy/`). `market.component.ts/html` ficou reduzido a navegação de tabs (`activeTab`/`oppMode`/`toolMode`) + o modal compartilhado de análise de queda; cada sub-aba é um subcomponente próprio em `components/market/` (`opportunities-list`, `dip-scanner`, `analyze-asset`, `renda-fixa`, `compare-assets`, `contribution-simulator`, `dip-analysis-modal`). `components/sectors/`, `market/quick-invest/` e `market/investment-strategy/` foram removidos por ficarem sem nenhum consumidor.
- **`components/opportunities/`, `dip/`, `strategy/`** — abas/telas de análise. `strategy.component` (página própria de Estratégia de Investimento) ainda usa `quickInvest()` de `recommend.service.ts`. `getRebalancePlan()` (mesmo service, endpoint `/rebalance`) ficou sem nenhum consumidor no web após a remoção do rebalanceamento de Meus Ativos — ver Débito Técnico.
- **`components/config/`** — configurações e metas de yield por categoria.
- **`core/services/ui-helper.service.ts`** — labels/ícones/cores de AssetType, categoria e setor, glossário de termos (inclui DCF, RSI, tendência, ROE, D/E, consenso e anos de provento), rótulos de proveniência do veredito e apresentação do score (cinza + "dado insuficiente" quando `data_completeness` é baixo). A régua de score em si vive em `core/score-ruler.ts`.
- **`core/interceptors/`** — `auth.interceptor.ts` (Bearer token), `http-error.interceptor.ts`.
- **`core/guards/auth.guard.ts`**.
- **`core/models/`** — um `.model.ts` por domínio.

---

## Mobile (`mobile/`) — Flutter

Dart SDK `^3.10.7`. Dependências-chave: `dio`, `google_sign_in`, `flutter_riverpod`, `flutter_secure_storage` (JWT), `go_router` (com `StatefulShellRoute.indexedStack` de 4 branches espelhando as rotas web), `fl_chart`, `flutter_launcher_icons`.

Estrutura `lib/`:
- **`core/`** — `api_client.dart` (Dio + interceptor Bearer token), `api_repository.dart` (chamadas HTTP tipadas), `auth_service.dart` (Google Sign-In com `serverClientId` fixo = Client ID Web, para audience do idToken ser validável cross-platform), `models.dart` (DTOs espelhando os do backend), `providers.dart` (Riverpod), `router.dart`, `labels.dart` (equivalente ao `ui-helper.service.ts`, mas em Dart).
- **`features/`** — `auth/`, `dashboard/`, `assets/`, `market/` (reduzido a `opportunities_tab`, `ferramentas_tab`, `asset_detail_sheet` em 2026-08-19 — `sectors_tab.dart` e `investir_tab.dart` removidos por ficarem sem consumidor), `config/`, `shell/app_shell.dart` (NavigationBar com 4 destinos).

**Paridade com o web**: alta e ativamente mantida. O mobile consome a MESMA API — sem lógica de cálculo de negócio duplicada (fair price, score, RF e IR ficam 100% no backend). Renda fixa (`features/assets/fixed_income_screen.dart`) e Quick Invest (`features/market/quick_invest_view.dart`) foram adicionados em 2026-08-20, fechando as duas lacunas que custavam. Duas assimetrias restantes são **decisão declarada**: Estratégia é web-only (leitura longa e densa) e push exige o app (o web sinaliza isso em Configurações em vez de oferecer um controle sem efeito).

---

## Fluxo de dados (resumo)

```
Web (Angular) ─┐
                ├─→ HTTP + JWT Bearer ─→ FastAPI (/api/*) ─→ services/ ─→ analysis/ (cálculo puro)
Mobile (Flutter)┘                              │                    └─→ repositories/ → storage/ → Postgres/SQLite
                                                └─→ collectors/ → BRAPI / BCB SGS
```
