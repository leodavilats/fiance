# fiance

Plataforma multi-tenant de análise de investimentos focada na B3. Stack: FastAPI+Postgres (backend/), Angular 18 (web/), Flutter (mobile/).

**Documentação técnica completa em `docs/`** — leia antes de trabalhar em qualquer parte não trivial do sistema:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — estrutura de camadas, algoritmos de valuation/scoring, endpoints da API, fluxo de dados entre web/mobile/backend.
- [docs/FEATURES.md](docs/FEATURES.md) — inventário de features por tela (Dashboard, Meus Ativos, Mercado, Configurações).
- [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) — limitações conhecidas e débito técnico (verificar antes de assumir que um bug antigo já foi corrigido ou não).

Setup/instalação/variáveis de ambiente: ver [README.md](README.md) (já atualizado e não duplicado aqui).

## Notas rápidas para trabalhar neste repo

- Fontes de dados: **BRAPI** (ações BR/FIIs/BDRs), **Finnhub** (ações US), **CoinGecko** (cripto), **BCB SGS** (CDI/Selic/IPCA reais), **Gemini** (explicações de carteira e sentimento de notícias). yfinance/Alpha Vantage foram descontinuados.
- Persistência: SQLAlchemy sobre Postgres (produção) / SQLite (dev). Multi-tenant por `user_id`, aplicado na camada `storage/portfolio_store.py`.
- Regras de negócio (fair price, scoring, RF) vivem **só no backend** (`analysis/`). O mobile sempre delega ao backend; o web tem um preview client-side de RF que duplica a regra — cuidado ao alterar alíquotas/juros de RF, atualizar os dois lados.
- Web e mobile espelham a mesma navegação de 4 abas e as mesmas sub-abas de Mercado — ao adicionar uma feature em uma tela, considerar replicar na outra plataforma para manter paridade (é uma prioridade ativa do projeto, ver histórico de commits).
- Sem testes automatizados relevantes no momento (ver KNOWN_ISSUES.md) — validar mudanças manualmente até que isso mude.
