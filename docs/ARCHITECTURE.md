# fianceAI — Arquitetura Técnica

> Gerado por varredura completa em 2026-08-10. Complementa o README.md (setup/instalação) com detalhes de arquitetura, algoritmos e estrutura interna.

## Visão geral

fianceAI é uma plataforma multi-tenant de análise de investimentos focada na B3, com três frontends consumindo a mesma API: **web** (Angular 18), **mobile** (Flutter) e a API em si (**FastAPI**). Login via Google (JWT próprio emitido pelo backend), dados persistidos em Postgres (produção) / SQLite (dev), isolados por `user_id`.

**Correção importante em relação a documentação/memória antigas**: o projeto migrou de yfinance/Alpha Vantage para **BRAPI** (ações BR/FIIs/BDRs), **Finnhub** (ações US) e **CoinGecko** (cripto). A persistência não é mais JSON local — é SQLAlchemy sobre Postgres/SQLite.

---

## Backend (`backend/app/`)

### Camadas

- **`main.py`** — cria a app FastAPI, CORS, handlers globais de exceção (`ValueError`→400/404 por palavra-chave na mensagem, `Exception`→500 com log+traceback), inclui `router` sob prefixo `/api`. No `startup`: `init_db()` + warm-up em background do cache de oportunidades (`OpportunityService()._scan_universe({})`).
- **`analysis/`** — algoritmos puros de domínio (sem I/O):
  - `fair_price.py` — núcleo de valuation. `compute_fair_price()` roteia por tipo: FII → consenso `[bazin, pvp_fair]` (nunca Graham); ações BR/internacionais → Graham + DCF. `desired_yield_for()` define metas de yield (6% ações, 10% FII, 4% internacional), configuráveis via `prefs` do usuário. `compute_technical()` calcula SMA50/200, RSI14, tendência, distância de 52w high/low.
  - `scoring.py` — `score_company()` calcula score 0–100 por perfil de risco (conservative/moderate/aggressive) com pesos por dimensão (value/quality/dividend/leverage/growth). FII tem scoring próprio (`_score_fii`: dividend 50% / P-VP 35% / liquidez 15%). Cripto tem score neutro fixo (50).
  - `classify.py` — `auto_category()` mapeia AssetType → categoria canônica (fii→fiis, crypto→cripto, us_stock/bdr→acoes_int, resto→acoes_br); `resolve_category()` trata categorias legadas.
  - `dip_analysis.py`, `decision.py`, `strategy.py` — análise de quedas, motor de decisão de compra/venda, estratégias de alocação.
- **`api/`** — 16 routers FastAPI (ver seção Endpoints).
- **`collectors/`** — integrações externas:
  - `universal.py` — `detect_type(symbol)` classifica em `br_stock|bdr|fii|us_stock|crypto`. Dispatcher: BR/FII/BDR → BRAPI; crypto → CoinGecko (mapa fixo ~14 moedas); US → Finnhub. Cache em camadas (fundamentals 2h, histórico 12h, dividendos 24h) + semáforo de 30 chamadas concorrentes.
  - `rates.py` — CDI/Selic/IPCA reais via BCB SGS (séries 4389/432/13522), cache 24h, fallback `14.40`/`14.40`/`5.0`.
  - `news.py` — coleta de notícias (RSS).
- **`core/`** — `config.py` (Pydantic Settings, universo hardcoded de fallback), `database.py` (engine SQLAlchemy, `init_db()`), `auth.py` (validação de ID token Google contra múltiplos `aud` permitidos, emissão de JWT HS256 próprio com TTL 30 dias), `cache.py`, `context.py` (contexto do usuário da request), `universe.py` (universo dinâmico via BRAPI `/quote/list`).
- **`llm/gemini_client.py`** — dois usos do Gemini: `explain_portfolio()` (explicação textual da carteira, `gemini-2.0-flash`, disclaimer obrigatório) e `analyze_news_sentiment()` (sentimento de notícias, `gemini-flash-lite-latest` com fallback, parsing robusto de JSON com heurística de palavras-chave se falhar).
- **`models/db_models.py`** — ORM: `User`, `PortfolioPosition` (PK composta `user_id+ticker`), `PortfolioSnapshot` (histórico diário, purga após 365 dias), `WatchlistItemDb`, `GoalDb`, `SectorGoalDb`, `PreferencesDb` (inclui `desired_yield_stock/fii/int`, `notify_price_alerts`, `notify_new_opportunities`), `PriceAlertDb`, `ClosedTradeDb` (histórico de vendas — lucro/prejuízo realizado, IR), `DeviceTokenDb` (token FCM por usuário), `NotifiedOpportunityDb` (dedupe de notificações de oportunidade).
- **`notifications/push.py`** — encapsula o Firebase Admin SDK; sem `FIREBASE_SERVICE_ACCOUNT_JSON` configurado, apenas loga em vez de enviar (degradação graciosa, mesmo padrão do Gemini opcional).
- **`services/notification_job.py`** — job periódico (chamado a cada 15min por um loop em `main.py`, sem scheduler externo) que dispara push de alertas de preço disparados e de novas oportunidades (`STRONG_BUY` ou score≥75+DY≥6%) por usuário, respeitando as preferências de notificação.
- **`optimizer/`** — `allocator.py`, `cost_calculator.py`, `portfolio.py`: otimização de alocação de carteira.
- **`repositories/`** — fachada fina (`PortfolioRepository`, `AssetRepository`) sobre `storage/portfolio_store.py`.
- **`storage/portfolio_store.py`** — persistência real via SQLAlchemy `Session`. Todo método resolve `user_id` via `_session()` (contexto da request) e garante (`_ensure_user`) merge automático do usuário antes de qualquer operação — é aqui que o multi-tenancy é aplicado.
- **`services/`** — orquestração de negócio (`asset_service`, `dashboard_service`, `dip_service`, `dividend_service`, `goal_service`, `opportunity_service`, `portfolio_service`, `projection_service`, `quick_invest_service`, `recommendation_service`, `strategy_service`).

### Endpoints (`/api/...`)

Públicos: `GET /health`, `GET /universe`, `GET /universe/search` (autocomplete de ticker por prefixo/nome), `POST /cache/clear` (`basic.py`), `POST /auth/google` (`auth.py`).

Autenticados (JWT obrigatório via `Depends(get_current_user)`):

| Método | Rota | Arquivo |
|---|---|---|
| GET/POST | `/alerts`, `GET /alerts/check`, `DELETE /alerts/{id}` | `alerts.py` |
| GET | `/asset/{symbol}`, `/asset/{symbol}/dip-analysis` | `assets.py` |
| GET | `/dashboard` | `dashboard.py` |
| GET | `/dip-scanner`, `/dip-scanner/stream` (SSE) | `dip_scanner.py` |
| GET | `/dividends/ranking` | `dividends.py` ⚠️ ver Débito Técnico |
| GET/PUT | `/goals`, `/sector-goals` | `goals.py` |
| GET | `/opportunities` | `opportunities.py` |
| POST/GET/PUT/DELETE | `/portfolio*`, `POST /portfolio/sell`, `GET /portfolio/trades` | `portfolio_routes.py` |
| GET | `/auth/me` | `auth.py` |
| POST/DELETE | `/notifications/register-token` | `notifications.py` |
| GET/PUT | `/preferences` | `preferences.py` |
| POST | `/projection/passive-income`, `/projection/sector-allocation` | `projection.py` |
| POST | `/quick-invest` | `quick_invest.py` |
| POST | `/recommend`, `/analyze` | `recommendations.py` |
| GET/POST | `/renda-fixa/taxas`, `/renda-fixa/analisar`, `/renda-fixa/comparar` | `renda_fixa.py` |
| GET | `/sectors-summary` | `sectors.py` |
| GET/PUT/DELETE | `/watchlist*` | `watchlist.py` |

---

## Web (`web/src/app/`)

Angular 18 standalone components, lazy-loaded. Rotas (`app.routes.ts`): `/login` (público), `/dashboard`, `/assets`, `/market`, `/config` (atrás de `authGuard`), fallback → `/dashboard`.

- **`components/dashboard/`** — tela inicial consolidada.
- **`components/assets/`** ("Meus Ativos") — CRUD de posições + renda fixa. Tem preview client-side de rendimento RF (`calcularRendimento()`, alíquotas de IR hardcoded) — duplica regra do backend, ver Débito Técnico.
- **`components/market/`** — maior tela do app. Sub-abas reduzidas de 4 para 3 (Segmentos unificado em "Explorar", commit `d44485f`). `market.component.ts/html` ficou reduzido a navegação de tabs (`activeTab`/`oppMode`/`toolMode`) + o modal compartilhado de análise de queda; cada sub-aba é um subcomponente próprio em `components/market/` (`opportunities-list`, `dip-scanner`, `analyze-asset`, `quick-invest`, `investment-strategy`, `renda-fixa`, `dip-analysis-modal`).
- **`components/sectors/`, `opportunities/`, `dip/`, `strategy/`** — abas/telas de análise.
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
- **`features/`** — `auth/`, `dashboard/`, `assets/`, `market/` (dividido em `opportunities_tab`, `sectors_tab`, `investir_tab`, `ferramentas_tab`, `asset_detail_sheet`), `config/`, `shell/app_shell.dart` (NavigationBar com 4 destinos).

**Paridade com o web**: alta e ativamente mantida (commit `aef9bc5` "paridade de funcionalidades do mobile com o app web"; commits mais recentes do repo são majoritariamente polimento mobile). O mobile consome a MESMA API — sem lógica de cálculo de negócio duplicada (fair price, score, RF ficam 100% no backend). Único ponto positivo de assimetria: o preview de RF client-side existe só no web; o mobile delega ao backend (mais alinhado a single-source-of-truth nesse ponto específico).

---

## Fluxo de dados (resumo)

```
Web (Angular) ─┐
                ├─→ HTTP + JWT Bearer ─→ FastAPI (/api/*) ─→ services/ ─→ analysis/ (cálculo puro)
Mobile (Flutter)┘                              │                    └─→ repositories/ → storage/ → Postgres/SQLite
                                                └─→ collectors/ → BRAPI / Finnhub / CoinGecko / BCB SGS / Gemini
```
