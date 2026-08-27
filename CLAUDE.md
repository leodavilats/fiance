# fiance

Plataforma multi-tenant de análise de investimentos focada na B3. Stack: FastAPI+Postgres (backend/), Angular 22 (web/), Flutter (mobile/).

**Documentação em [docs/](docs/)** — comece pelo [índice](docs/README.md), que diz qual arquivo
responde o quê. Em resumo:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — como o sistema é montado: camadas, algoritmos de
  valuation/scoring, endpoints, estrutura de pastas do web e do mobile.
- [docs/FEATURES.md](docs/FEATURES.md) — o que cada tela faz, pela navegação atual (5 destinos).
- [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) — **só o que está aberto**, verificado contra o
  código. Leia antes de assumir que algo é bug novo.
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — histórico datado e o **por quê** das decisões, incluindo
  as revertidas. Nada ali é pendência.
- [docs/design/](docs/design/) — o redesign de UX/UI: auditoria, arquitetura de informação,
  wireframes, design system, e o log do que já está no ar.

Setup/instalação/variáveis de ambiente: ver [README.md](README.md) (já atualizado e não duplicado aqui).

## Notas rápidas para trabalhar neste repo

- Fontes de dados: **BRAPI** (ações BR/FIIs/BDRs/ETFs) e **BCB SGS** (CDI/Selic/IPCA reais). Finnhub (ações US), CoinGecko (cripto), Gemini (IA) e yfinance/Alpha Vantage foram descontinuados — o sistema não trabalha mais com ações internacionais fora de BDR nem com criptomoedas.
- Classes de ativo suportadas: `br_stock` | `bdr` | `fii` | `etf` | `renda_fixa` (asset type) → categorias de alocação `acoes_br` | `bdrs` | `fiis` | `etfs` | `renda_fixa`.
- Persistência: SQLAlchemy sobre Postgres (produção) / SQLite (dev). Multi-tenant por `user_id`, aplicado na camada `storage/portfolio_store.py`. **Migrações são versionadas com Alembic** (`backend/migrations/`); `init_db()` marca bancos pré-Alembic na revisão baseline automaticamente. Coluna nova exige uma migração — não basta mexer no model.
- Regras de negócio (fair price, scoring, RF, IR) vivem **só no backend** (`analysis/`, `optimizer/`). Web e mobile delegam: não há mais cálculo de renda fixa duplicado no Angular.
- **Renda fixa é entidade de primeira classe** (tabela `fixed_income_positions`, CRUD em `/fixed-income`), marcada a mercado no backend. Nada de RF vive em `localStorage`, e o ticker sintético `RF_*` não existe mais.
- Escrita de carteira: use `POST /portfolio/position` e `DELETE /portfolio/position/{ticker}`. `PUT /portfolio` é **destrutivo** (substitui tudo) e existe só para importação explícita.
- Unidades: `roe`, `profit_margin`, `revenue_growth` e `debt_to_equity` chegam do collector em **percentual** (ver `collectors/universal._ratio_to_pct`). Crescimento no DCF também é percentual.
- Régua de score em um único lugar por plataforma: `backend/app/analysis/score_ruler.py`, `web/src/app/core/score-ruler.ts`, `mobile/lib/core/score_ruler.dart`. Mudar um limiar exige mudar os três — e o Python é o primeiro.
- **Tokens de design são gerados, não escritos.** Cor, tipografia, espaço, raio, motion e as bandas das réguas saem de `design-tokens/tokens.json` via `node design-tokens/build.mjs`, que emite `web/src/tokens.css`, `web/src/app/core/design-tokens.ts` e `mobile/lib/core/design_tokens.dart`. Nunca edite os gerados nem escreva hexadecimal em `styles.css`, `tailwind.config.js` ou `theme.dart` — o job `design-tokens` do CI falha se divergirem. Qualquer chave `*Ruler` em `tokens.json` vira `fi<Nome>Bands`/`fi<Nome>Domain` nas duas plataformas automaticamente.
- **Ícone e favicon também são gerados.** A marca (quadrado arredondado + `trending-up` do Lucide) sai de `tokens.json` via `python design-tokens/build-icons.py`, que emite `web/public/favicon.svg`, `favicon-512.png`, `apple-touch-icon.png` e os dois PNGs de `mobile/assets/icon/`. Requer Pillow. Nunca edite esses arquivos à mão — eles já carregaram a marca antiga por uma versão inteira. Os dois hex que não cabem em token (`theme-color` no `index.html` e `adaptive_icon_background` no `pubspec.yaml`) são conferidos pelo `--check`, que roda no CI.
- **Não existe alias de cor.** Não use `bg-accent`, `text-tx`, `bg-panel`, `text-muted` nem paleta crua do Tailwind (`red-400`, `grey`, `white`): a camada foi removida. Os papéis são `ground`/`ground-1`/`ground-2`, `hairline`, `ink`/`ink-2`/`ink-3`, `brand`/`on-brand`, os estados `favorable`/`attention`/`adverse`/`indeterminate`, a direção `up`/`down` e as séries `series-1..11`/`series-other`. Opacidade funciona (`bg-brand/20`) porque as cores da config são funções que emitem `color-mix` — declará-las como string faz o Tailwind **descartar o modificador em silêncio**.
- **Estado ≠ direção, nas duas plataformas.** Estado é julgamento (veredito, saúde, severidade) e tem prioridade cromática; direção é a aritmética de um número (P&L, linha de gráfico) e tem croma baixo. No mobile use `fiStateColor(FiState.x, brightness)` e `fiDirectionColor(delta, brightness)` — `gainColor`/`lossColor`/`warnColor` não existem mais.
- **Classe CSS que não existe não quebra o build** — quebra a tela em silêncio, do mesmo jeito que um ícone Lucide não registrado. Já aconteceu com `.card`, `.btn-primary`, `.tag`, `.verdict-pill`, `verdict-*` e `bg-success`. Ao usar uma classe global, confirme que ela está em `web/src/styles.css`.
- Fuso fiscal: isenção mensal de IR e faixas de alíquota usam mês calendário **brasileiro** (`core/brt.py`), não UTC.
- **A navegação do web mudou em 2026-08-21.** São 5 destinos por intenção (`/hoje`, `/carteira`, `/descobrir`, `/estrategia`, `/voce`), os cinco na navegação principal desde 2026-08-27 — antes `/voce` só existia no bottom nav do mobile com 20 rotas endereçáveis (`/hoje/atividade` entrou em 2026-08-26), mais `/ativo/:ticker` como camada; `/market` foi dissolvido e as tabs em `signal` viraram rotas. As URLs antigas seguem como redirect. O mobile seguiu a mesma IA em 2026-08-22: 5 destinos, 19 rotas, `market_screen`/`rebalance_tab` removidos e Estratégia criada (não existia em nenhuma plataforma). Metas no mobile ainda vivem em Configurações e RF × Bolsa não tem cliente Dart. As telas de Hoje e Carteira no mobile foram reestruturadas em 2026-08-26 (`features/hoje/`, `features/carteira/`); `dashboard_screen.dart` e `assets_screen.dart` não existem mais. Ver [docs/design/](docs/design/) antes de adicionar tela ou rota. Push exige o app instalado e isso é **decisão declarada** (o web sinaliza em `/voce/alertas`). A assimetria de Estratégia era bug, não decisão: `strategy.component` nunca tinha sido roteado. **Corrigido em 2026-08-21** — Estratégia é `/estrategia` e Quick Invest é `/estrategia/aporte`; no mobile, desde 2026-08-22.
- **Ícone do Lucide precisa ser registrado à mão** em `LucideAngularModule.pick({...})` (`web/src/main.ts`). Nome ausente ou errado **não quebra o build** — quebra a tela em runtime (`The "x" icon has not been provided...`). Ao adicionar um `<lucide-icon>`, registre o import e abra a tela.
- Filtro e recorte de tela vivem **na URL**, não em `sessionStorage`/`signal`: oportunidades (`q`, `dy`, `mos`, `cat`, `destaque`, `p`), quedas (`min_score`, `top`, `category`) e a tabela de posições (`cols`, `d`). Link salvo é contrato.
- Testes: `cd backend && python -m pytest -q` (250 testes) e `python -m ruff check app tests migrations`. Mobile: `flutter analyze && flutter test` (27 testes). Web: `npm run format:check && npm run build` — **confira o código de saída**: o build imprime os erros como `X [ERROR] TS…`, então um `grep -i error` ingênuo passa reto por eles. Tudo roda no CI (`.github/workflows/ci.yml`) em todo push — mudança que quebra a suíte não deve ser mergeada.
