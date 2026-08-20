# fiance

Plataforma multi-tenant de análise de investimentos focada na B3. Stack: FastAPI+Postgres (backend/), Angular 22 (web/), Flutter (mobile/).

**Documentação técnica completa em `docs/`** — leia antes de trabalhar em qualquer parte não trivial do sistema:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — estrutura de camadas, algoritmos de valuation/scoring, endpoints da API, fluxo de dados entre web/mobile/backend.
- [docs/FEATURES.md](docs/FEATURES.md) — inventário de features por tela (Dashboard, Meus Ativos, Mercado, Configurações).
- [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) — limitações conhecidas e débito técnico (verificar antes de assumir que um bug antigo já foi corrigido ou não).

Setup/instalação/variáveis de ambiente: ver [README.md](README.md) (já atualizado e não duplicado aqui).

## Notas rápidas para trabalhar neste repo

- Fontes de dados: **BRAPI** (ações BR/FIIs/BDRs/ETFs) e **BCB SGS** (CDI/Selic/IPCA reais). Finnhub (ações US), CoinGecko (cripto), Gemini (IA) e yfinance/Alpha Vantage foram descontinuados — o sistema não trabalha mais com ações internacionais fora de BDR nem com criptomoedas.
- Classes de ativo suportadas: `br_stock` | `bdr` | `fii` | `etf` | `renda_fixa` (asset type) → categorias de alocação `acoes_br` | `bdrs` | `fiis` | `etfs` | `renda_fixa`.
- Persistência: SQLAlchemy sobre Postgres (produção) / SQLite (dev). Multi-tenant por `user_id`, aplicado na camada `storage/portfolio_store.py`. **Migrações são versionadas com Alembic** (`backend/migrations/`); `init_db()` marca bancos pré-Alembic na revisão baseline automaticamente. Coluna nova exige uma migração — não basta mexer no model.
- Regras de negócio (fair price, scoring, RF, IR) vivem **só no backend** (`analysis/`, `optimizer/`). Web e mobile delegam: não há mais cálculo de renda fixa duplicado no Angular.
- **Renda fixa é entidade de primeira classe** (tabela `fixed_income_positions`, CRUD em `/fixed-income`), marcada a mercado no backend. Nada de RF vive em `localStorage`, e o ticker sintético `RF_*` não existe mais.
- Escrita de carteira: use `POST /portfolio/position` e `DELETE /portfolio/position/{ticker}`. `PUT /portfolio` é **destrutivo** (substitui tudo) e existe só para importação explícita.
- Unidades: `roe`, `profit_margin`, `revenue_growth` e `debt_to_equity` chegam do collector em **percentual** (ver `collectors/universal._ratio_to_pct`). Crescimento no DCF também é percentual.
- Régua de score em um único lugar por plataforma: `backend/app/analysis/score_ruler.py`, `web/src/app/core/score-ruler.ts`, `mobile/lib/core/score_ruler.dart`. Mudar um limiar exige mudar os três.
- Fuso fiscal: isenção mensal de IR e faixas de alíquota usam mês calendário **brasileiro** (`core/brt.py`), não UTC.
- Web e mobile espelham a mesma navegação de 4 abas e as mesmas sub-abas de Mercado — ao adicionar uma feature em uma tela, considerar replicar na outra plataforma. Duas assimetrias são **decisão declarada**, não lacuna: Estratégia é web-only (leitura longa e densa) e push exige o app instalado (o web sinaliza isso na tela de Configurações).
- Testes: `cd backend && python -m pytest -q` (206 testes) e `python -m ruff check app tests migrations`. Mobile: `flutter analyze && flutter test`. Web: `npm run format:check && npx ng build`. Tudo roda no CI (`.github/workflows/ci.yml`) em todo push — mudança que quebra a suíte não deve ser mergeada.
