# fiance — Arquitetura Técnica

> Gerado por varredura completa em 2026-08-10. Complementa o README.md (setup/instalação) com detalhes de arquitetura, algoritmos e estrutura interna.

## Visão geral

fiance é uma plataforma multi-tenant de análise de investimentos focada na B3, com três frontends consumindo a mesma API: **web** (Angular 18), **mobile** (Flutter) e a API em si (**FastAPI**). Login via Google (JWT próprio emitido pelo backend), dados persistidos em Postgres (produção) / SQLite (dev), isolados por `user_id`.

**Correção importante em relação a documentação/memória antigas**: o projeto migrou de yfinance/Alpha Vantage para **BRAPI** (ações BR/FIIs/BDRs/ETFs). Finnhub (ações US), CoinGecko (cripto) e Gemini (IA) foram removidos em 2026-08-19 — o sistema não trabalha mais com ações internacionais fora de BDR nem com criptomoedas; a exposição internacional é só via BDR, e ETF passou a ser uma classe de ativo própria. A persistência não é mais JSON local — é SQLAlchemy sobre Postgres/SQLite.

---

## Backend (`backend/app/`)

### Camadas

- **`main.py`** — cria a app FastAPI, CORS, handlers globais de exceção (`ValueError`→400/404 por palavra-chave na mensagem, `Exception`→500 com log+traceback), inclui `router` sob prefixo `/api`. No `startup`: `init_db()` + warm-up em background do cache de oportunidades (`OpportunityService()._scan_universe({})`).
- **`analysis/`** — algoritmos puros de domínio (sem I/O):
  - `fair_price.py` — núcleo de valuation. `compute_fair_price()` roteia por tipo: FII → consenso `[bazin, pvp_fair]` (nunca Graham); BDR → Graham + DCF; ETF → só `bazin` (dividend yield histórico, sem Graham/DCF — ETF não tem EPS/book_value de empresa); ações BR → Bazin/Graham/DCF. `desired_yield_for()` define metas de yield (6% ações, 10% FII, 4% BDR, 4% ETF), configuráveis via `prefs` do usuário. `compute_technical()` calcula SMA50/200, RSI14, tendência, distância de 52w high/low.
  - `scoring.py` — `score_company()` calcula score 0–100 por perfil de risco (conservative/moderate/aggressive) com pesos por dimensão (value/quality/dividend/leverage/growth). FII tem scoring próprio (`_score_fii`: dividend 50% / P-VP 35% / liquidez 15%). ETF também tem scoring próprio (`_score_etf`: dividend 50% / liquidez 50%, sem fundamentos de empresa).
  - `classify.py` — `auto_category()` mapeia AssetType → categoria canônica (fii→fiis, etf→etfs, bdr→bdrs, resto→acoes_br); `resolve_category()` trata categorias legadas (`renda`/`trade`/`caixa`). Categoria `bdrs` (antes `acoes_int`) foi renomeada de verdade em 2026-08-19, sem alias — sistema ainda sem usuários em produção, então sem dado real para migrar.
  - `dip_analysis.py`, `decision.py`, `strategy.py` — análise de quedas, motor de decisão de compra/venda, estratégias de alocação.
- **`api/`** — 13 routers FastAPI (ver seção Endpoints; reduzido de 16 em 2026-08-19 — `dividends.py`, `recommendations.py`, `rebalance.py` e `watchlist.py` removidos por não terem nenhum consumidor real em web/mobile, ver KNOWN_ISSUES.md item 16).
- **`collectors/`** — integrações externas:
  - `universal.py` — `detect_type(symbol)` classifica em `br_stock|bdr|fii|etf`. Dispatcher: BR/FII/BDR/ETF → BRAPI (única fonte de cotação hoje). ETF detectado via lista curada `KNOWN_ETFS` (mesmo padrão de `KNOWN_UNITS`) além do `subType` da BRAPI. Ticker não suportado (ex.: ação US pura, cripto) levanta `UnsupportedTickerError` em vez de um asset_type — não há mais fallback "internacional genérico". Cache em camadas (fundamentals 2h, histórico 12h, dividendos 24h) + semáforo de 30 chamadas concorrentes.
  - `rates.py` — CDI/Selic/IPCA reais via BCB SGS (séries 4389/432/13522), cache 24h, fallback `14.40`/`14.40`/`5.0`.
  - `news.py` — coleta de notícias (RSS, sempre pt-BR/BR — todos os asset_types suportados são negociados na B3); `analyze_news_with_ai()` hoje é só o resumo determinístico (contagem de sentimento por item), sem IA externa.
- **`core/`** — `config.py` (Pydantic Settings, universo hardcoded de fallback), `database.py` (engine SQLAlchemy, `init_db()`), `auth.py` (validação de ID token Google contra múltiplos `aud` permitidos, emissão de JWT HS256 próprio com TTL 30 dias), `cache.py`, `context.py` (contexto do usuário da request), `universe.py` (universo dinâmico via BRAPI `/quote/list`, com bucket próprio de ETFs).
- **`models/db_models.py`** — ORM: `User`, `PortfolioPosition` (PK composta `user_id+ticker`), `PortfolioSnapshot` (histórico diário, purga após 365 dias), `WatchlistItemDb` (sem rota HTTP desde 2026-08-19 — feature nunca teve tela; mantido só o schema, ver KNOWN_ISSUES item 16), `GoalDb`, `SectorGoalDb`, `PreferencesDb` (inclui `desired_yield_stock/fii/int/etf`, `notify_price_alerts`, `notify_new_opportunities`), `PriceAlertDb`, `ClosedTradeDb` (histórico de vendas — lucro/prejuízo realizado, IR), `DeviceTokenDb` (token FCM por usuário), `NotifiedOpportunityDb` (dedupe de notificações de oportunidade).
- **`notifications/push.py`** — encapsula o Firebase Admin SDK; sem `FIREBASE_SERVICE_ACCOUNT_JSON` configurado, apenas loga em vez de enviar (degradação graciosa).
- **`services/notification_job.py`** — job periódico (chamado a cada 15min por um loop em `main.py`, sem scheduler externo) que dispara push de alertas de preço disparados e de novas oportunidades (`STRONG_BUY` ou score≥75+DY≥6%) por usuário, respeitando as preferências de notificação.
- **`optimizer/`** — só `cost_calculator.py` (custo de venda/IR). `allocator.py` e `portfolio.py` (HRP/min-vol/max-Sharpe via scipy) foram removidos em 2026-08-19 — existiam só para `/recommend`, removido no mesmo dia por falta de consumidor.
- **`repositories/`** — fachada fina (`PortfolioRepository`, `AssetRepository`) sobre `storage/portfolio_store.py`.
- **`storage/portfolio_store.py`** — persistência real via SQLAlchemy `Session`. Todo método resolve `user_id` via `_session()` (contexto da request) e garante (`_ensure_user`) merge automático do usuário antes de qualquer operação — é aqui que o multi-tenancy é aplicado.
- **`services/`** — orquestração de negócio (`asset_service`, `dashboard_service`, `dip_service`, `goal_service`, `opportunity_service`, `portfolio_service`, `projection_service`, `quick_invest_service`, `strategy_service`). `dividend_service`, `rebalance_service` e `recommendation_service` removidos em 2026-08-19 (rotas correspondentes sem consumidor).

### Endpoints (`/api/...`)

Públicos: `GET /health`, `GET /universe`, `GET /universe/search` (autocomplete de ticker por prefixo/nome), `POST /cache/clear` (`basic.py`), `POST /auth/google` (`auth.py`).

Autenticados (JWT obrigatório via `Depends(get_current_user)`):

| Método | Rota | Arquivo |
|---|---|---|
| GET/POST | `/alerts`, `GET /alerts/check`, `DELETE /alerts/{id}` | `alerts.py` |
| GET | `/asset/{symbol}`, `/asset/{symbol}/dip-analysis`, `/compare` | `assets.py` |
| GET | `/dashboard` | `dashboard.py` |
| GET | `/dip-scanner` | `dip_scanner.py` |
| GET/PUT | `/goals`, `/sector-goals` | `goals.py` |
| GET | `/opportunities` | `opportunities.py` |
| POST/GET/PUT/DELETE | `/portfolio*`, `POST /portfolio/sell`, `GET /portfolio/trades` | `portfolio_routes.py` |
| GET | `/auth/me` | `auth.py` |
| POST | `/notifications/register-token` | `notifications.py` |
| GET/PUT | `/preferences` | `preferences.py` |
| POST | `/projection/passive-income` | `projection.py` |
| GET | `/strategy` | `strategy.py` |
| POST | `/quick-invest` | `quick_invest.py` |
| GET/POST | `/renda-fixa/taxas`, `/renda-fixa/comparar` | `renda_fixa.py` |
| GET | `/sectors-summary` | `sectors.py` |
| GET | `/benchmark` | `benchmark.py` |

Removidos em 2026-08-19 por não terem consumidor real em web/mobile (ver KNOWN_ISSUES.md item 16): `GET /dividends/ranking` (nem chegava a ser importável), `GET /dip-scanner/stream` (SSE), `POST /recommend`, `POST /analyze`, `GET /rebalance`, `POST /projection/sector-allocation`, `POST /renda-fixa/analisar`, `POST /portfolio/refresh`, `DELETE /notifications/register-token`, `GET/PUT /watchlist`, `DELETE /watchlist/{ticker}`.

---

## Web (`web/src/app/`)

Angular 18 standalone components, lazy-loaded. Rotas (`app.routes.ts`): `/login` (público), `/dashboard`, `/assets`, `/market`, `/config` (atrás de `authGuard`), fallback → `/dashboard`.

- **`components/dashboard/`** — tela inicial consolidada.
- **`components/assets/`** ("Meus Ativos") — CRUD de posições + renda fixa. Tem preview client-side de rendimento RF (`calcularRendimento()`, alíquotas de IR hardcoded) — duplica regra do backend, ver Débito Técnico.
- **`components/market/`** — maior tela do app. Reduzida a 2 abas em 2026-08-19 (`activeTab`: `opportunities` | `ferramentas` — abas "Segmentos" e "Investir" removidas de Mercado nessa data; ficha de Estratégia de Investimento continua existindo só como página própria em `components/strategy/`). `market.component.ts/html` ficou reduzido a navegação de tabs (`activeTab`/`oppMode`/`toolMode`) + o modal compartilhado de análise de queda; cada sub-aba é um subcomponente próprio em `components/market/` (`opportunities-list`, `dip-scanner`, `analyze-asset`, `renda-fixa`, `compare-assets`, `contribution-simulator`, `dip-analysis-modal`). `components/sectors/`, `market/quick-invest/` e `market/investment-strategy/` foram removidos por ficarem sem nenhum consumidor.
- **`components/opportunities/`, `dip/`, `strategy/`** — abas/telas de análise. `strategy.component` (página própria de Estratégia de Investimento) ainda usa `quickInvest()` de `recommend.service.ts`. `getRebalancePlan()` (mesmo service, endpoint `/rebalance`) ficou sem nenhum consumidor no web após a remoção do rebalanceamento de Meus Ativos — ver Débito Técnico.
- **`components/config/`** — configurações e metas de yield por categoria.
- **`core/services/ui-helper.service.ts`** — mapeia labels/ícones/cores de AssetType, categoria, setor (mantém dicionários EN→PT-BR de yfinance E BRAPI simultaneamente), glossário de termos financeiros para tooltips, e funções de path SVG para sparklines feitas à mão (sem lib de charting).
- **`core/interceptors/`** — `auth.interceptor.ts` (Bearer token), `http-error.interceptor.ts`.
- **`core/guards/auth.guard.ts`**.
- **`core/models/`** — um `.model.ts` por domínio.

---

## Mobile (`mobile/`) — Flutter

Dart SDK `^3.10.7`. Dependências-chave: `dio`, `google_sign_in`, `flutter_riverpod`, `flutter_secure_storage` (JWT), `go_router` (com `StatefulShellRoute.indexedStack` de 4 branches espelhando as rotas web), `fl_chart`, `flutter_launcher_icons`.

Estrutura `lib/`:
- **`core/`** — `api_client.dart` (Dio + interceptor Bearer token), `api_repository.dart` (chamadas HTTP tipadas), `auth_service.dart` (Google Sign-In com `serverClientId` fixo = Client ID Web, para audience do idToken ser validável cross-platform), `models.dart` (DTOs espelhando os do backend), `providers.dart` (Riverpod), `router.dart`, `labels.dart` (equivalente ao `ui-helper.service.ts`, mas em Dart).
- **`features/`** — `auth/`, `dashboard/`, `assets/`, `market/` (reduzido a `opportunities_tab`, `ferramentas_tab`, `asset_detail_sheet` em 2026-08-19 — `sectors_tab.dart` e `investir_tab.dart` removidos por ficarem sem consumidor), `config/`, `shell/app_shell.dart` (NavigationBar com 4 destinos).

**Paridade com o web**: alta e ativamente mantida (commit `aef9bc5` "paridade de funcionalidades do mobile com o app web"; commits mais recentes do repo são majoritariamente polimento mobile). O mobile consome a MESMA API — sem lógica de cálculo de negócio duplicada (fair price, score, RF ficam 100% no backend). Único ponto positivo de assimetria: o preview de RF client-side existe só no web; o mobile delega ao backend (mais alinhado a single-source-of-truth nesse ponto específico).

---

## Fluxo de dados (resumo)

```
Web (Angular) ─┐
                ├─→ HTTP + JWT Bearer ─→ FastAPI (/api/*) ─→ services/ ─→ analysis/ (cálculo puro)
Mobile (Flutter)┘                              │                    └─→ repositories/ → storage/ → Postgres/SQLite
                                                └─→ collectors/ → BRAPI / BCB SGS
```
