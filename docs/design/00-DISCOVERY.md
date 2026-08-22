# Fase 1 — Discovery: inventário do que existe hoje

> Varredura de código em 2026-08-21 (branch `main`, commit `abf4b90`). Este documento é
> descritivo: registra o estado atual com evidência de arquivo/linha. Julgamento e prioridade
> ficam em [01-UX-AUDIT.md](01-UX-AUDIT.md).

## 1. Superfícies navegáveis

### Web (Angular) — 6 rotas

`web/src/app/app.routes.ts`

| Rota | Componente | Guard |
|---|---|---|
| `/login` | `login` | público |
| `/dashboard` | `dashboard` | auth |
| `/assets` | `assets` ("Meus Ativos", leitura) | auth |
| `/assets/cadastro` | `portfolio-editor` (escrita) | auth |
| `/market` | `market` | auth |
| `/config` | `config` | auth |
| `**` | → `/dashboard` | — |

Navegação primária: 4 itens (`app.component.ts` — Dashboard, Meus Ativos, Mercado,
Configurações), replicados numa bottom-nav mobile-web (Início, Ativos, Mercado, Config).

### Web — destinos que NÃO são rotas

`/market` concentra 3 tabs com sub-tabs, todas em `signal`, nenhuma refletida na URL
(`market.component.ts`: `activeTab` / `oppMode` / `toolMode`):

- **Oportunidades** → "Lista de ativos" · "Em queda"
- **Rebalanceamento** → `rebalance-suggestions` + `followed-suggestions`
- **Ferramentas** → "Analisar Ativo" · "Simulador de RF" · "RF x Bolsa" · "Comparar Ativos" · "Simulador de Aportes"

Total: **8 destinos de conteúdo escondidos atrás de 2 níveis de tab, sem URL própria.**

### Mobile (Flutter) — 4 branches + 1 sub-rota

`mobile/lib/core/router.dart`: `/dashboard`, `/assets` (+ `/assets/renda-fixa`), `/market`,
`/config`. `market_screen.dart` repete as 3 tabs do web; `ferramentas_tab.dart` implementa as
ferramentas como cards de modo (`_ToolModeCard`) em vez de sub-tabs.

Assimetrias reais medidas:

| Superfície | Web | Mobile |
|---|---|---|
| Renda fixa — cadastro | dentro de `/assets/cadastro` | tela própria `/assets/renda-fixa` |
| Quick Invest | **inacessível** (ver §3) | Mercado → Ferramentas |
| Estratégia de investimento | **inacessível** (ver §3) | ausente |
| RF × Bolsa | Mercado → Ferramentas | ausente em `ferramentas_tab.dart` |

## 2. Blocos de conteúdo por tela (web)

**`/dashboard`** — 732 linhas de template, 10 blocos empilhados em coluna única:
"O que mudou" (`whats-new`), resumo de patrimônio, progresso da meta mensal, alertas,
Saúde da carteira (score + 4 sub-métricas + explicação expansível), Oportunidades,
Sinais de venda, Benchmark (Carteira vs Ibovespa), Evolução do patrimônio,
tabela de posições, e bloco "Bem-vindo ao fiance" para carteira vazia.

**`/assets`** — 830 linhas, 6 blocos: resumo (4 stats), composição (pizza ativo/setor),
renda fixa marcada a mercado (3 stats + tabela de 8 colunas), posições (tabela ordenável +
seleção múltipla + CSV), proventos recebidos (3 stats + form + tabela), operações encerradas
(stats + prejuízo acumulado + tabela de 8 colunas).

**`/assets/cadastro`** — 383 linhas: dois formulários repetidos por linha (posições, renda fixa)
com salvamento explícito por linha.

**`/config`** — 525 linhas: meta de renda passiva, metas de alocação por categoria (4 sliders),
metas por setor, preferências (perfil de risco, categorias/setores preferidos, excluídos),
aviso de push, cache, alertas de preço (CRUD).

**`/market`** — 145 linhas de navegação + 7 subcomponentes.

## 3. Código de UI sem consumidor

Confirmado por grep em todo `web/src`:

| Artefato | Tamanho | Situação |
|---|---|---|
| `components/strategy/strategy.component` | 1092 linhas HTML + 239 TS | Exportado em `components/index.ts`, **nunca roteado nem instanciado**. Único consumidor de `recommend.service.getStrategy()` e `.quickInvest()`. |
| `components/dip/dip.component` | 485 HTML + 92 TS | Idem. Renderiza "Análise por IA" e bloco de notícias — features cujo backend saiu em 2026-08-19. |
| `components/skeleton/` | — | **Zero usos** em templates; cada tela reimplementa skeleton inline (`animate-pulse` + `bg-border`). |

Consequência funcional: o conteúdo exclusivo de `strategy.component` — Perfil de investidor,
Estratégia recomendada, Ajustes necessários, Sugestões de investimento, Posições para revisar,
Alocação projetada e **Quick Invest** — não tem nenhum caminho de navegação no web. O botão
"Estratégia" do dashboard chama `goToMarket()` (`dashboard.component.ts:153`) e leva a `/market`,
que não contém estratégia. `GET /strategy` e `POST /quick-invest` existem no backend e estão
listados em `http-error.interceptor.ts:26`.

`CLAUDE.md` e `docs/ARCHITECTURE.md` afirmam que "Estratégia é web-only (leitura longa e densa)".
Na prática ela não é alcançável em nenhuma das duas plataformas.

## 4. Sistema visual atual

`web/src/styles.css` (11 KB) + `web/tailwind.config.js` + `mobile/lib/core/theme.dart`.

**Tokens que existem:** `--bg`, `--bg-2`, `--panel`, `--panel-2`, `--text`, `--muted`, `--soft`,
`--accent`, `--accent-2`, `--warn`, `--danger`, `--border`, `--shadow`, `--radius` (valor único:
14px), `--gradient-1/2`, `--series-1..11`, `--series-muted`. Dois temas (`data-theme` dark/light).
`theme.dart` espelha as cores 1:1 em Dart.

**Tokens que não existem:** escala tipográfica, escala de espaçamento, escala de raio,
escala de elevação, escala de peso, densidade, motion (durações/easings), z-index, foco.

**Classes utilitárias de domínio já no CSS global:** `.v-buy/.v-sell/.v-hold/.v-unknown`,
`.score-pill.high/mid/low`, `.dip-oportunidade/.dip-neutro/.dip-armadilha`, `.dip-badge-*`,
`.bar-good/mid/low`, `.alert-info/warning/critical`, `.tag-success/warning/danger/muted/accent`,
`.news-positive/negative/neutral`, `.cat-renda/.cat-trade/.cat-etfs/.cat-caixa`, `.tab-btn`,
`.side-panel`, `.panel-overlay`, `.range-slider`.

Nove famílias de badge/pill semânticas, todas mapeando para o mesmo trio verde/amarelo/vermelho.
`.cat-renda`, `.cat-trade`, `.cat-caixa` correspondem a categorias legadas removidas do domínio;
`.news-*` corresponde à feature de notícias sem backend.

## 5. Régua de score — três arquivos, duas divergências

| | Backend `score_ruler.py` | Web `score-ruler.ts` | Mobile `score_ruler.dart` |
|---|---|---|---|
| Limiares 75/60/40 | ✅ | ✅ | ✅ |
| Cor de "Boa oportunidade" (60–74) | — | `text-accent` → **verde** | `#38BDF8` → **azul** |
| `scoreBandFor()` (dado insuficiente) | — | ausente (lógica dispersa em `ui-helper.service.ts`) | presente |
| `trendBasisLabel` / `consensusLabel` / `confidenceLabel` | — | ausente (em `ui-helper.service.ts`) | presente |

## 6. Componentes de UI compartilhados hoje

**Web:** `alert-modal`, `benchmark-chart`, `patrimony-chart`, `empty-state`, `global-loader`,
`help-tooltip`, `logo`, `profile-modal`, `skeleton` (morto), `snackbar`.
Lógica de apresentação de domínio: `core/services/ui-helper.service.ts` (397 linhas — labels,
ícones, cores de AssetType/categoria/setor, glossário, proveniência, apresentação de score).

**Mobile:** `core/widgets/` (`ticker_autocomplete_field`, `brand_background`,
`brand_loading_indicator`, `help_tooltip`), `core/labels.dart`, `core/glossary.dart`,
`core/sector_translations.dart`, `core/format.dart` (9 linhas).

Nenhum dos dois tem componente reutilizável para: score, preço justo, margem de segurança,
gap de alocação, diagnóstico de queda, progresso de meta, linha do tempo de proventos,
bloco de decisão. Cada tela remonta esses elementos com `div`/`Row` locais.

## 7. Métricas objetivas de superfície

| Medida | Valor |
|---|---|
| Linhas de UI no web (`ts`+`html`+`css` em `src/app`) | 12 526 |
| Linhas de UI no mobile (`lib/**/*.dart`) | 9 404 |
| Maior template web | `strategy.component.html`, 1 092 linhas (inacessível) |
| Maior tela mobile | `assets_screen.dart`, 1 231 linhas |
| `<button>` no web | 97 |
| `aria-*` no web | 1 (`aria-label`) |
| `role=` no web | 2 |
| Breakpoints em uso | `sm:` 46 · `lg:` 17 · `md:` 11 · `xl:` 0 · `2xl:` 0 |
| Largura máxima de conteúdo | `max-w-[1180px]` (`app.component.ts`) |
| `tabular-nums` / `font-variant-numeric` | 0 ocorrências |
| Estados de erro mobile com exceção crua (`Text('Erro: $err')`) | 6 |

## 8. Endpoints com e sem consumidor de UI

Endpoints ativos sem nenhuma tela alcançável que os consuma:
`GET /strategy` e `POST /quick-invest` (só em `strategy.component`, inacessível),
`GET /data-quality` (nenhum método no `recommend.service`).

Endpoints consumidos: `/dashboard`, `/whats-new`, `/portfolio*`, `/fixed-income*`,
`/dividends/received*`, `/opportunities`, `/dip-scanner`, `/asset/{symbol}`,
`/asset/{symbol}/dip-analysis`, `/compare`, `/benchmark`, `/income-compare`,
`/suggestions/followed*`, `/rebalance-suggestions`, `/sectors-summary`, `/goals`,
`/sector-goals`, `/preferences`, `/projection/passive-income`, `/renda-fixa/*`, `/alerts*`,
`/universe/search`, `/auth/*`, `/notifications/register-token`, `/cache/clear`.
