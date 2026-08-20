# fiance — Limitações conhecidas e débito técnico

> Gerado por varredura completa em 2026-08-10.
>
> **Leia primeiro a seção final** ("Auditoria de produto e engenharia", 2026-08-20): ela
> substitui vários itens abaixo, que ficaram obsoletos com a implementação do roadmap da
> auditoria.

## Limitações históricas — status atual

| Limitação (registrada em 2026-07) | Status |
|---|---|
| BDR (ex. AAPL34) classificado como `br_stock`; units (SANB11, TAEE11, BPAC11...) classificadas como `fii` | ✅ **Corrigido.** `collectors/universal.py::detect_type()` testa BDR antes de FII; set `KNOWN_UNITS` trata as units conhecidas como `br_stock`; camada extra em `_fetch_brapi` reclassifica por nome (`UNIT/UNT/UNITS`) se necessário. |
| CDI fixo 13,5% no web vs 14,40% no backend | ✅ **Corrigido.** Ambos convergem via `GET /renda-fixa/taxas` → `collectors/rates.py` (BCB SGS real, fallback 14.40). O `signal(14.4)` no Angular é só valor inicial pré-fetch. |
| `fair_price` aplicando Graham em FII | ✅ **Corrigido.** FII usa exclusivamente `[bazin, pvp_fair]`; Graham só roda para ações BR/internacionais. |
| Fundamentos de BDR inconsistentes (LPA/VPA na escala do recibo, não da ação-mãe) | ✅ **Resolvido (validado com dado real em 2026-08-10).** Testado AAPL34 (BRAPI) vs AAPL (Finnhub): a BRAPI já retorna EPS escalado ao próprio preço da BDR (P/E implícito ≈33,8 vs P/E real da Apple ≈35,5 — coerente). `book_value` costuma vir `None` para BDRs na BRAPI (gap de dado, não erro de escala); `graham_fair_price()` já trata isso retornando `None` quando falta book_value, e o DCF segue funcionando só com EPS. Nenhuma correção de código necessária — a causa raiz (yfinance) já não existe mais. |
| Componentes compartilhados (RF form, allocation-view) não extraídos | ✅ **`market.component` corrigido em 2026-08-12** — quebrado em subcomponentes (`opportunities-list`, `dip-scanner`, `analyze-asset`, `renda-fixa`, `dip-analysis-modal`), sem mudança de comportamento. `quick-invest`/`investment-strategy` foram removidos de Mercado em 2026-08-19 (ver item novo abaixo), não existem mais como subcomponentes dessa tela. `assets.component.html`/`strategy.component.html` ainda têm formulários inline sem extração — não fizeram parte desta rodada. |

## Débito técnico / oportunidades de melhoria

1. **Testes automatizados** — iniciados em 2026-08-10: `backend/tests/` cobre as funções puras mais críticas (`analysis/classify.py`, `analysis/fair_price.py`, `analysis/renda_fixa_analysis.py`, `collectors/universal.py::detect_type`), incluindo testes de regressão para os bugs já corrigidos (BDR×FII×unit, FII nunca usa Graham, BDR sem book_value não quebra). **Em 2026-08-12, ganhou testes de API/contrato** (`test_api_dashboard.py`, `test_api_strategy.py`, `test_api_quick_invest.py`, `test_api_portfolio.py`) via `TestClient` real (autenticado com `issue_access_token`, sem mock de auth), incluindo um teste de contrato que garante que `cash_available` continua ausente da resposta de `/dashboard` — proteção direta contra as duas regressões silenciosas que escaparam em 2026-08-12 (`/strategy` zerando `cash_available` sem erro; crash de parsing no mobile por campo removido do model). 81 testes no total, todos passando (`pytest -q` dentro de `backend/`). Ainda faltam: `scoring.py`, `dip_analysis.py`, `decision.py`, `strategy.py` (lógica pura), e nada no web (`*.spec.ts`) nem no mobile (só o `widget_test.dart` de scaffold).
2. ~~**Prints de debug em produção**~~ — ✅ **Corrigido em 2026-08-10.** `backend/app/llm/gemini_client.py` trocou os `print()` de prompt/resposta da IA por `logger.debug`.
3. **Duplicação de regra de negócio (RF)** — `calcularRendimento()`/`calcularValorFinal()` em `assets.component.ts` (alíquotas de IR, juros compostos) replicam `backend/app/analysis/renda_fixa_analysis.py::analyze_one()`. Investigado em 2026-08-10: **não é um preview isolado** — esses métodos alimentam vários `computed()` da tela inteira de Meus Ativos (total investido, valor atual, alocação por tipo, taxa média). Migrar para chamada assíncrona ao backend exigiria reescrever essa cadeia de signals para lidar com estado assíncrono por linha (loading, corrida entre edições), com teste manual completo no navegador — decisão do usuário: manter como está por ora e tratar como item dedicado futuro, não fazer às cegas. Risco aceito: mudança de regra de IR (ex. nova faixa) precisa ser replicada nos dois lados manualmente.
4. ~~**`market.component.html` com 1627 linhas**~~ — ✅ **Corrigido em 2026-08-12** (ver seção nova abaixo). Agora só a navegação de tabs + modal compartilhado; cada sub-aba é subcomponente próprio.
5. **Universo hardcoded como fallback** — `backend/app/core/config.py::default_universe` mantém uma lista de ~400 tickers hardcoded, mesmo já existindo universo dinâmico via BRAPI (`core/universe.py`). É um fallback defensivo intencional, mas extenso.
6. ~~**Rota `/dividends/ranking` intencionalmente desativada**~~ — ✅ **Removida em 2026-08-19** (ver item 16). O arquivo importava `DividendService` de um lugar que nunca o exportava — a rota já não era importável, então "desativada" era, na prática, "quebrada". Reativar a feature no futuro significa reescrevê-la do zero, não descomentar nada.
7. **BDR sem ajuste de escala** — ver tabela acima, item de fair price de BDR.
8. **Labels/ícones duplicados cross-stack** (`ui-helper.service.ts` no web vs `labels.dart` no mobile) — duplicação estrutural (TS↔Dart não compartilha código nativamente), não um descuido, mas motivo de fricção quando se adiciona um novo AssetType/setor. **Parcialmente mitigado em 2026-08-10** (ver design system, abaixo): as cores agora são idênticas nos dois lados; ainda é preciso lembrar de atualizar os dois arquivos manualmente se um novo AssetType/categoria for adicionado.
9. **Sparklines feitas à mão** (`ui-helper.service.ts`, geração manual de path SVG) em vez de usar uma lib de charting — funciona, mas é mais lógica para manter internamente.
10. ~~**Composição da Carteira (web) não agrupa Ações Internacionais**~~ — ✅ **Corrigido em 2026-08-11.** `alocacaoPorTipo()` em `assets.component.ts` bucketava por `asset_type` bruto (`bdr`/`us_stock` apareciam como fatias separadas "BDR"/"Ação EUA"), em vez de `category_resolved` (que já une os dois em "Ações INT", como o resto da tela). Troca de `assetTypeSeriesColor/-Label/-Icon` por `categoryBarColor/-Label/-Icon` no template.
11. ~~**Modais do mobile com campos colados**~~ — ✅ **Corrigido em 2026-08-11.** `AlertDialog`s de "Novo alerta de preço", "Adicionar ativo" e "Vender" não tinham espaçamento entre os `TextField`/`DropdownButtonFormField` (`Column` sem `SizedBox` entre os filhos). Adicionado `SizedBox(height: 16)` entre campos nos 3 diálogos (`config_screen.dart`, `assets_screen.dart`).
12. ~~**Nomes de setor em inglês no mobile**~~ — ✅ **Corrigido em 2026-08-11.** O mobile exibia `sector.sector`/`a.sector` cru (taxonomia BRAPI/yfinance em inglês), sem o equivalente de `UiHelperService.translateSector()` do web. Novo `mobile/lib/core/sector_translations.dart` (mesmo dicionário do web) aplicado em `sectors_tab.dart`, `asset_detail_sheet.dart` e `config_screen.dart` (metas por setor).
13. ~~**`GET /rebalance` (backend), `getRebalancePlan()` (web) sem consumidor**~~ — ✅ **Removido em 2026-08-19** (ver item 16). Rota, serviço e wrapper web deletados por completo.
14. **`Base.metadata.create_all()` não migra colunas novas em tabelas existentes** — bug real encontrado e corrigido em 2026-08-11: ao adicionar `notify_price_alerts`/`notify_new_opportunities` em `PreferencesDb`, qualquer request tocando preferências (incl. o Dashboard) quebrava com 500 (`no such column`) contra o banco de dev já existente — e quebraria do mesmo jeito em produção (Postgres no Railway) no próximo deploy. Corrigido com `_add_missing_columns()` em `app/core/database.py`: depois do `create_all()`, compara colunas do model com as da tabela real e faz `ALTER TABLE ... ADD COLUMN` (com `DEFAULT` quando o valor padrão do model é um escalar simples, pra não quebrar linhas já existentes). Roda automaticamente no `init_db()`, sem intervenção manual. **Lição para o futuro:** qualquer coluna nova em um model existente precisa continuar tendo um default simples (bool/int/float/str) para essa migração leve funcionar sozinha; se precisar de um default calculado ou de backfill mais complexo, isso ainda exigiria intervenção manual (Alembic não está configurado no projeto).

15. **`quickInvest()`/`getStrategy()` removidos do mobile, mas endpoints seguem ativos** — em 2026-08-19 as abas "Segmentos" e "Investir" foram removidas de Mercado (web e mobile), a pedido do usuário. No mobile, `api_repository.dart::quickInvest()`/`getStrategy()` (só usados por `investir_tab.dart`, também removido) foram deletados. No web, `POST /quick-invest` continua em uso pela página própria de Estratégia (`strategy.component.ts`), então `RecommendService.quickInvest()` não é código morto — só deixou de ser chamado a partir de Mercado. `SectorsComponent` (visão "por setor" de Mercado) e `InvestmentStrategyComponent`/`QuickInvestComponent` (subcomponentes da antiga aba Investir de Mercado) foram deletados do web por ficarem sem consumidor algum.
16. **Varredura e remoção de rotas órfãs do backend (2026-08-19)** — auditoria cruzando toda rota registrada em `app/api/__init__.py` contra os clients web (`recommend.service.ts`) e mobile (`api_repository.dart`) encontrou 10 rotas sem nenhum consumidor real (wrapper de client existente não conta como uso — só chamada de tela conta). Removidas por completo, incluindo o código que existia só para servi-las:
    - `GET/PUT /watchlist`, `DELETE /watchlist/{ticker}` — feature de watchlist nunca chegou a ter tela nem no web nem no mobile. Removidos `app/api/watchlist.py` e os models Pydantic `WatchlistItem`/`WatchlistRequest`. **Não removida:** a tabela `WatchlistItemDb` e as funções `list_watchlist`/`replace_watchlist`/`remove_watchlist` em `storage/portfolio_store.py` — são camada de schema/dados, deixadas intactas de propósito (reativar a feature no futuro não exige migração).
    - `GET /dividends/ranking` — nem estava registrada (import quebrado, ver item 6). Removidos o arquivo de rota, `DividendService` e o model `DividendRankingResponse`.
    - `GET /dip-scanner/stream` (SSE) — só a versão não-streaming (`/dip-scanner`) tinha consumidor. Removida a rota e `DipService.scan_dips_stream()`.
    - `POST /recommend`, `POST /analyze` — motor de otimização de carteira antigo (perfil de risco + alocação), substituído na prática pelo fluxo de Estratégia (`/strategy`) que já é o que as telas usam. Removidos `app/api/recommendations.py`, `RecommendationService`, os models `RecommendRequest`/`RecommendResponse`/`Allocation`, e — por ficarem sem nenhum chamador depois disso — o módulo inteiro de otimização quantitativa (`app/optimizer/allocator.py`, `app/optimizer/portfolio.py`: HRP, min-vol, max-Sharpe via scipy) e `explain_portfolio()`/`_format_allocations()` em `llm/gemini_client.py`. **Se a intenção era reativar esse motor de recomendação um dia, ele foi apagado — recuperável via git history, não some do repo, mas não existe mais no código atual.**
    - `POST /projection/sector-allocation` — só o `/projection/passive-income` (Simulador de Aportes) tinha consumidor. Removidos a rota, `ProjectionService.analyze_sector_allocation()` e os models `SectorAllocation`/`SectorAllocationResponse` (web e backend).
    - `POST /renda-fixa/analisar` — só `/renda-fixa/comparar` (usado pelo Simulador de RF) tinha consumidor; a função interna `analyze_one()` continua existindo porque `compare_options()` a chama internamente — só a rota HTTP dedicada foi removida.
    - `POST /portfolio/refresh` — removidos a rota e `PortfolioService.refresh_portfolio()`.
    - `DELETE /notifications/register-token` — o `POST` (registrar token) continua ativo; só o `DELETE` (usado só por um wrapper mobile nunca chamado, `unregisterDeviceToken()`, também removido) foi tirado. A função de storage `unregister_device_token()` continua existindo porque `notification_job.py` a chama internamente para limpar tokens inválidos.

    Suite de testes (`pytest -q`, 89 testes) e `dart analyze` (mobile) passando depois da limpeza; dois testes de contrato do `/rebalance` foram removidos junto (`tests/test_api_benchmark_rebalance.py` → renomeado `test_api_benchmark_compare.py`, mantendo os testes de `/benchmark` e `/compare` que não eram sobre rebalance).

## Remoção de Finnhub/CoinGecko/Gemini, BDR-only e adição de ETF (2026-08-19)

Pedido do usuário: simplificar as fontes de dados para só **BRAPI + BCB SGS**, unificar toda exposição internacional em **BDR** (removendo `us_stock`/Finnhub) e remover **cripto** (`crypto`/CoinGecko) por completo, adicionando uma nova classe de ativo **ETF** com categoria de alocação própria.

- **Enums**: `AssetType` perdeu `us_stock`/`crypto`, ganhou `etf`. `AssetCategory` perdeu `cripto`/`acoes_int`, ganhou `etfs`/`bdrs`. A categoria antes chamada `acoes_int` foi **renomeada de verdade para `bdrs`** (não só o texto visível) — decisão tomada no mesmo dia, já que o sistema não tinha usuários em produção ainda: nenhum dado real de `Goal.category`/`PortfolioPosition.category` para migrar, então **sem alias legado** — `_LEGACY_MAP`/`resolve_category()` não ganharam entrada `acoes_int`→`bdrs` (seria proteção para um cenário que não existe).
- **Detecção (`collectors/universal.py::detect_type`)**: sem Finnhub, não há mais fallback "internacional genérico" — ticker que não bate BDR/FII/unit/br_stock/`KNOWN_ETFS` levanta `UnsupportedTickerError` (400/404 explícito na API, ignorado silenciosamente em varreduras em lote que já tratavam exceção por item). ETF é detectado via `KNOWN_ETFS` (lista curada, mesmo papel que `KNOWN_UNITS` tem para units) e via `subType` da BRAPI em `core/universe.py`.
- **Fair price/score/dip (`analysis/`)**: ETF não tem EPS/book_value de empresa — fair price usa só `bazin` (dividend yield histórico, sem Graham/DCF); `scoring.py::_score_etf` usa dividend yield + liquidez (sem value/quality/growth tradicionais); `dip_analysis.py` reusa o ramo padrão (o `_crypto_score` dedicado foi removido).
- **IR (`optimizer/cost_calculator.py`)**: ETF e BDR (`AssetCategory.bdrs`) tributados a 15% flat sem isenção mensal; a isenção de R$35k/mês de cripto deixou de existir.
- **Gemini removido por completo**: `app/llm/gemini_client.py` deletado; `collectors/news.py::analyze_news_with_ai` e `analysis/strategy.py::_rank_category_opportunities` promoveram o fallback determinístico (que já existia e era testado) a caminho único — não há mais tentativa de chamada de IA externa.
- **Preferences**: `desired_yield_int` renomeado para `desired_yield_bdr` (nome antigo era um resquício de quando a categoria cobria BDR+ações US) em `PreferencesDb`/`Preferences`/`PreferencesRequest`/`portfolio_store.py`; nova coluna `desired_yield_etf` (default 0.04). Ambas cobertas automaticamente por `_add_missing_columns()` no próximo boot — sem migração manual (a coluna antiga `desired_yield_int`, se já existir em algum banco, fica órfã e sem uso).
- **Sem script de limpeza de dados**: um script de migração (`cleanup_crypto_us_stock.py`) foi escrito, validado manualmente contra o SQLite de dev (dry-run e execute) e depois **removido** no mesmo dia — o sistema ainda não tem usuários em produção, então não existe posição real de `crypto`/`us_stock` para apagar; mantê-lo seria código morto para um cenário que não existe. Se o sistema já estiver em uso quando `crypto`/`us_stock` precisarem ser removidos de novo (não é o caso aqui, é só uma nota para o futuro), esse script precisaria ser reescrito do zero — recuperável via git history desta mesma data, não existe mais no código atual.
- **Web/mobile**: `AssetType`/`AllocationCategory` (TS) e os mapas de label/ícone/cor espelhados (`ui-helper.service.ts` ↔ `labels.dart`, ver item 8 abaixo) perderam `us_stock`/`crypto`/`cripto`/`acoes_int` e ganharam `etf`/`etfs`/`bdrs`. `desired_yield_int`→`desired_yield_bdr` e o form control `yield_int`→`yield_bdr` (web) / `desiredYieldInt`→`desiredYieldBdr` (mobile) renomeados junto. Corrigido de brinde: `strategy.component.ts::assetLabel` não tinha entrada para `bdr` (caía cru na tela de Estratégia).
- Suite de testes (`pytest -q`, 87 testes), `ruff check` e `flutter analyze` passando; build do Angular (`ng build`) validado sem erros de tipo.

## Unificação visual web↔mobile — Fase 1 (2026-08-10)

Varredura visual completa encontrou: paletas de cor divergentes entre web e mobile (nenhuma cor de marca/ganho/perda/categoria batia, exceto na logo), mobile sem dark mode (tema indigo padrão do Material, não a marca verde/ciano), ícones de navegação diferentes, e uma **inconsistência interna no próprio web** (`categoryBarColor()` tinha FIIs e Cripto trocados em relação a `categoryBarClass`/`categoryColor`).

Ações tomadas (só tokens de design — sem reestruturar telas, por decisão do usuário):
- `web/src/app/core/services/ui-helper.service.ts::categoryBarColor()` corrigido para bater com as outras 3 funções de cor de categoria (FIIs=laranja, Cripto=amarelo).
- `mobile/lib/core/theme.dart` (novo) — tokens espelhando 1:1 as CSS custom properties de `web/src/styles.css` (`--bg`, `--panel`, `--accent`, `--accent-2`, `--warn`, `--danger`, `--radius`), para dark e light. Fonte trocada para Inter (`google_fonts`), igual ao web.
- `mobile/lib/core/theme_provider.dart` (novo) — dark como padrão + toggle persistido (`shared_preferences`), espelhando `theme.service.ts`. Toggle exposto em Configurações.
- `mobile/lib/core/labels.dart` — cores de categoria trocadas para os hex exatos do Tailwind `*-400` usados no web (`acoes_int` e `fiis` e `cripto` estavam com cores erradas: `fiis` era âmbar em vez de laranja, `cripto` era rosa em vez de amarelo).
- Cores de ganho/perda/alerta hardcoded (`Colors.green.shade700`/`Colors.red.shade700`/etc., ~20 ocorrências em 9 arquivos) substituídas por `gainColor()`/`lossColor()`/`warnColor()` do tema — reagem automaticamente ao dark/light mode agora.
- Ícones de navegação (`app_shell.dart`) trocados para os equivalentes Material mais próximos dos ícones Lucide do web (`briefcase`→`work_outline`, `target`→`track_changes_outlined`).
- `pubspec.yaml`: adicionadas `google_fonts` e `shared_preferences`.
- Validado com `flutter analyze` (0 erros, só warnings pré-existentes não relacionados) e `flutter build apk --debug`.

**Não feito nesta fase** (ficou fora do escopo combinado): quebra de `market.component.html` (1627 linhas) e dos arquivos grandes do mobile em componentes menores; padronização de espaçamento/`BoxDecoration` no mobile (ainda cada widget define os próprios valores, sem spacing scale); teste visual manual completo em dispositivo/emulador (recomenda-se rodar `flutter run` e navegar as 4 abas em dark e light antes de considerar fechado).

## Assistente de finanças — venda/P&L realizado/IR + explicações educacionais (2026-08-10)

Pedido do usuário: transformar o produto em assistente de finanças mais completo (registrar venda de ativos, explicações mais ricas, notificações push). Planejado em 3 fases (ver plano salvo na sessão); Fases 1 e 2 executadas nesta sessão, Fase 3 (push) depende de credenciais do Firebase que só o usuário pode gerar.

**Fase 1 — venda de ativos, P&L realizado, IR, trade log:**
- Nova tabela `closed_trades` (`ClosedTradeDb`), sem migração manual (o projeto usa `Base.metadata.create_all()`).
- `cost_calculator.calculate_sell_cost()` ganhou o parâmetro `gross_value_month_before` para aplicar corretamente a isenção mensal de IR (R$20k ações BR, R$35k cripto) sobre o **acumulado do mês**, não por transação isolada como antes (uso só em simulação de estratégia).
- Novos endpoints `POST /portfolio/sell` e `GET /portfolio/trades`. Nova função de storage `reduce_position_quantity()` (decrementa ou remove a posição ao vender).
- Web e mobile: botão "Vender" por posição (parcial ou total) + seção "Operações Encerradas" com totais de lucro/prejuízo realizado e IR pago.
- 5 novos testes (`test_cost_calculator.py`, `test_portfolio_sell.py`) cobrindo isenção mensal acumulada e o fluxo completo de venda (parcial, total, quantidade insuficiente, ticker inexistente).

**Fase 2 — explicações educacionais (usa o que já existia, sem nova lógica de negócio):**
- Web: `p.reasons` (já vinha da API, nunca era exibido) agora aparece expansível ao clicar na pill de Decisão em Meus Ativos; tooltip de glossário adicionado no cabeçalho "P. justo".
- Mobile: `PortfolioPosition.reasons` adicionado ao model (fonte já mandava o campo, só faltava mapear); botão "Por quê?" no card de ativo abre um bottom sheet com os motivos. Novo `core/glossary.dart` (espelha 1:1 o glossário do web) + widget `core/widgets/help_tooltip.dart` (toque em vez de hover, adequado a touch); tooltips de DY e MS adicionados nos cards de Oportunidades.

**Fase 3 — notificações push (alertas de preço + novas oportunidades):**
- Usuário criou o projeto Firebase (`fiance-89340`) e forneceu `google-services.json` (`mobile/android/app/google-services.json`, **não commitado** — está no `.gitignore` do mobile). Plugin `com.google.gms.google-services` aplicado em `settings.gradle.kts`/`app/build.gradle.kts`; `minSdk` elevado para 23 (exigido por `firebase_messaging`); core library desugaring habilitado (exigido por `flutter_local_notifications`).
- Mobile: `firebase_core`, `firebase_messaging`, `flutter_local_notifications` adicionados. `core/notifications_service.dart` inicializa o FCM, pede permissão, registra o token no backend (`POST /notifications/register-token`) logo após entrar na `AppShell` (ou seja, só com usuário autenticado), reage a `onTokenRefresh`, e mostra notificação local quando o app está em primeiro plano. Toggles "Notificar alertas de preço" / "Notificar novas oportunidades" em Configurações.
- Backend: nova tabela `device_tokens` (token FCM por usuário, com realocação se o mesmo token aparecer para outro usuário — troca de conta no aparelho) e `notified_opportunities` (evita notificar a mesma oportunidade repetidamente). `PreferencesDb` ganhou `notify_price_alerts`/`notify_new_opportunities` (default `True`). `app/notifications/push.py` encapsula o Firebase Admin SDK — **se `FIREBASE_SERVICE_ACCOUNT_JSON` não estiver configurado no `.env`, o envio é apenas logado, não falha** (mesmo padrão de degradação graciosa usado em `gemini_client.py` para a IA opcional). `app/services/notification_job.py` roda a cada 15 min (`asyncio.create_task` em `main.py`, sem dependência externa de scheduler) verificando alertas de preço não disparados (reaproveita a lógica de `alerts.py::check_alerts`, e agora **de fato marca `triggered_at`**, que antes existia no schema mas nunca era setado) e oportunidades novas (`STRONG_BUY` ou score≥75+DY≥6%, limitado a 3 por ciclo por usuário para não inundar).
- **Concluído (2026-08-11):** usuário gerou a chave de conta de serviço e ela foi configurada em `FIREBASE_SERVICE_ACCOUNT_JSON` no `.env` local do backend (não commitado — `.env` já é gitignored). Validado que o Firebase Admin SDK inicializa de verdade com a credencial (`_get_firebase_app()` retorna uma instância válida). **Em produção (Railway ou outro host), a mesma variável de ambiente precisa ser configurada manualmente** — o `.env` local não é deployado. Também não há suporte iOS ainda (só `google-services.json`/Android; faltaria `GoogleService-Info.plist` se o app for publicado na App Store).
- 9 novos testes (`test_push.py`, `test_notification_storage.py`) cobrindo o fallback sem credencial e o CRUD de tokens/oportunidades notificadas.

## Mobile — auto-login, splash animado, Configurações por módulos, diagnóstico de push (2026-08-11)

- **Auto-login corrigido**: o app sempre abria em `/login`, mesmo com sessão válida salva (`AuthService.readToken()` nunca era checado no boot). Novo `authStatusProvider` (`core/providers.dart`) lê o token salvo e, se existir, valida contra o novo endpoint `GET /auth/me` (também restaura o perfil do usuário sem precisar logar de novo). Nova `SplashScreen` (`features/auth/splash_screen.dart`) é a rota inicial (`/splash`) e decide automaticamente entre `/dashboard` (token válido) e `/login` (sem token ou token expirado/inválido — nesse caso desloga localmente).
- **Visual do login/splash**: novo `core/widgets/brand_background.dart` (glow radial nas cores da marca) e `core/widgets/brand_loading_indicator.dart` (logo pulsando, sem depender de pacote de animação) substituem o fundo liso e o `CircularProgressIndicator` genérico. Tagline trocada de "Análise de investimentos B3 na sua mão" (mencionava só B3) para "Ações, FIIs, cripto e renda fixa — tudo em um só assistente" (decisão do usuário, cobre o escopo real do app).
- **Configurações reorganizada em módulos** (`_SettingsCard`): Conta, Aparência, Preferências financeiras, Notificações, Metas de alocação por categoria, Metas de alocação por setor, Alertas de preço — cada um em um `Card` com cabeçalho ícone+título, substituindo a `ListView` plana de `Divider`s. Nenhuma lógica interna das seções (`_GoalsSection`, `_SectorGoalsSection`, `_AlertsSection`) foi alterada.
- **Diagnóstico de push**: novo botão "Enviar notificação de teste" no módulo Notificações, chamando `POST /notifications/test` (novo endpoint — busca os tokens do usuário atual via `list_device_tokens(user_id)` e usa `send_push` já existente). A resposta distingue os dois pontos de falha possíveis: `tokens_found == 0` → o token nunca foi registrado no servidor (permissão negada ou erro de rede no aparelho); `tokens_found > 0` mas nada chega → problema de credencial/entrega no servidor (conferir `FIREBASE_SERVICE_ACCOUNT_JSON` no Railway). `notifications_service.dart` agora guarda `permissionStatus`/`tokenRegistered`/`lastError` em vez de só logar com `debugPrint`. **Removido em 2026-08-12** (decisão do usuário: a integração já estava validada, o botão de teste não tinha mais utilidade) — `POST /notifications/test` e o botão não existem mais; `permissionStatus`/`tokenRegistered`/`lastError` permanecem, ainda usados pelo fluxo real de registro de push.
- **Bug real corrigido**: faltava `com.google.firebase.messaging.default_notification_channel_id` no `AndroidManifest.xml` — sem isso, pushes recebidos com o app em background caem no canal de fallback do FCM em vez do canal `fiance_default` já criado em `notifications_service.dart` (não impedia a entrega, mas descasava o canal/importância).
- **Ainda não verificado end-to-end**: se `FIREBASE_SERVICE_ACCOUNT_JSON` está de fato salvo no ambiente do Railway (só confirmamos que funciona com o `.env` local) — o botão de teste (removido em 2026-08-12, ver acima) era a ferramenta pra descobrir isso sem adivinhar; sem ele, essa verificação exigiria olhar os logs do backend em produção diretamente.

## Ajustes de usabilidade — caixa/metas/notificações/mercado/IA (2026-08-12)

Pedido do usuário para simplificar e corrigir usabilidade em mobile/web/backend:

- **"Caixa disponível" removida** — nunca ficava atualizada como preferência persistida. Quick invest e `/strategy` agora recebem o valor pontualmente na requisição (query param `cash_available` em `/strategy`, corpo em `/quick-invest`), não mais de preferences. `DashboardSummary.cash_available` removido da resposta do backend e dos models web/mobile.
- **Notificação de teste removida** (ver seção anterior); pushes reais ganharam campo `type` consistente (`price_alert`, `new_opportunity`) no payload `data`, preparando terreno para novos tipos.
- **Metas por categoria/setor** saíram do Dashboard e passaram a aparecer só em Ativos, que ganhou agrupamento por categoria/setor com indicador "atual X% · meta Y%" (mobile e web). Edição de metas continua em Configurações.
- **Autocomplete de ticker** ligado na busca do Mercado (mobile e web) e, na rodada seguinte (ver abaixo), também no diálogo de criar alerta de preço — reusando `TickerAutocompleteField`/`searchTickers()` já existentes, sem endpoint novo.
- **Estratégia de IA** (`analysis/strategy.py::build_investment_strategy`) deixou de escolher só a primeira oportunidade disponível por gap de alocação — agora usa o Gemini (`rank_opportunities_for_gap` em `llm/gemini_client.py`) para ponderar score/DY/margem de segurança/sentimento de notícias entre as candidatas do gap, com fallback determinístico (ordem por score) se a chamada falhar ou o Gemini estiver indisponível.
- **Regressão real encontrada e corrigida no mesmo dia**: `DashboardSummary.fromJson` no mobile ainda fazia cast não-nulo de `cash_available`, que o backend parou de enviar — quebrava Dashboard e Meus Ativos com `type Null is not a subtype of type num`. Motivou a rodada de testes de API abaixo.

## Score de oportunidades unificado, cadência de notificação e limpeza de "caixa disponível" nas Oportunidades (2026-08-19)

Pedido do usuário: usar todos os indicadores calculáveis no score de oportunidade, permitir configurar cadência de ajuste de carteira (diária/semanal/mensal) e considerar preferências de ativos/categorias na recomendação.

- **`opportunity_service.py` parou de usar um score ad-hoc** (`mos*60 + dy*1.5 + rsi_bonus*10 + trend_bonus`) e passou a chamar `scoring.py::score_opportunity()` — combina margem de segurança, qualidade (ROE/margem), endividamento, crescimento de receita, dividend yield e técnico, ponderados por perfil de risco (`OPPORTUNITY_WEIGHTS`). `score_company()`/`rank()` (baseados em P/L·P/VP) continuam no arquivo mas seguem sem nenhum consumidor real — candidatos a remoção numa próxima rodada se continuarem órfãos.
- **`PreferencesDb` ganhou** `risk_profile`, `preferred_categories`, `preferred_sectors`, `excluded_tickers` (boost de +5/+3 no score por categoria/setor preferido; exclusão remove o ticker da lista e do resumo de notificação) e `opportunities_frequency` (`off`/`daily`/`weekly`/`monthly`, substitui o booleano `notify_new_opportunities`). `notify_price_alerts` continua imediato (é alerta de risco, não sugestão de ajuste).
- **`notification_job.py`**: alertas de preço continuam a cada ciclo de 15min; o resumo de oportunidades só dispara quando a cadência configurada venceu desde `last_digest_sent_at`, agregando as melhores em um único push (antes eram até 3 pushes individuais por ciclo).
- **Vestígio morto removido**: `cash_available` de `PreferencesDb` nunca foi resettável de fato desde a remoção de 2026-08-12 (ver seção abaixo) — `PUT /preferences` nunca recebia esse campo, então ficava sempre em 0. Isso tornava `Opportunity.suggested_quantity`/`suggested_invest` e `OpportunitiesResponse.cash_available` permanentemente inertes (a condição `cash > 0` nunca era verdadeira), incluindo o bloco correspondente em `dashboard.component.html` que nunca renderizava. Removidos dos dois lados (backend e web) — a coluna `cash_available` na tabela `preferences` continua existindo (sem migração de drop), mas nada mais a lê para esse fim.

## Robustez e usabilidade — testes de API, split do market, limpeza, evolução de patrimônio (2026-08-12)

- **Testes de API** — ver item 1 da lista de débito técnico, acima.
- **`market.component` quebrado em subcomponentes** — ver item 4 da lista de débito técnico, acima.
- **`opportunities.component` (web) removido** — código morto confirmado (só era exportado pelo barrel `components/index.ts`, sem nenhum consumidor real nas rotas ativas).
- **Gráfico de evolução de patrimônio**: dado já existia (`PortfolioSnapshot`, embutido em `GET /dashboard`/`GET /portfolio`, sem endpoint novo). Web trocou o SVG manual (`snapshotPath()`/`snapshotAreaPath()` em `ui-helper.service.ts`, removidos) por `PatrimonyChartComponent` (segue a skill `dataviz`: crosshair, tooltip, tabela alternativa para acessibilidade, cores 100% via tokens de tema). Mobile ganhou a mesma visualização do zero (não existia nada antes) via `fl_chart` em `dashboard_screen.dart`.

---

# Auditoria de produto e engenharia (19/08/2026) — implementação completa em 20/08/2026

A auditoria mapeou 7 achados P0, 9 erros de cálculo, dois caminhos de perda de dados e um
endpoint de manutenção aberto. **Todas as cinco fases do roadmap foram implementadas.** Esta
seção substitui, para os itens que toca, o que está registrado acima.

## Correção de premissa

O documento anterior (e o `CLAUDE.md`) afirmava que não havia testes automatizados relevantes.
Havia — e agora são **206**, rodando em CI (`.github/workflows/ci.yml`: ruff + pytest no backend,
build e formatação no web, analyze + test no mobile) em todo push. O `conftest` também deixou de
stubar `get_dividends → []` e `get_history → {}`: PETR4 traz histórico de proventos e série de
preços, então a bateria passa pelo caminho onde os bugs de valuation moravam.

## Achados P0 — todos resolvidos

| Achado | Resolução |
|---|---|
| D1/D2 — renda fixa sem rendimento e presa ao `localStorage` | Tabela `fixed_income_positions` + CRUD `/fixed-income`, marcada a mercado no backend reusando `analyze_one()`. `AssetType.renda_fixa` criado (as posições apareciam como `br_stock`). Posições `RF_*` legadas removidas pela migração `0002`. |
| D3 — dois caminhos de perda da carteira inteira | `POST /portfolio/position` e `DELETE /portfolio/position/{ticker}` como escrita por item; `PUT /portfolio` fica só para importação e **rejeita lista vazia**. Mobile: FAB só com `dashboard.hasValue` e cadastro por item. Web: o branch de erro não marca `_initialized`, mostra banner e bloqueia edição. |
| D4 — quatro erros de unidade/janela no preço justo | Média de dividendos sobre anos-calendário completos com denominador correto; DY somando os últimos 12 meses **por data**; guard do DCF aceitando percentual; `range` do histórico configurável com degradação, e tendência de curto prazo rotulada quando falta série para a SMA200. |
| D5 — cache global com cálculo personalizado | O cache passou a guardar **dado de mercado** por ticker; preço justo e score são calculados por request. As metas de yield voltaram a ter efeito e o cálculo deixou de vazar entre tenants. |
| POST `/api/cache/clear` público | Movido para o `admin_router`, dentro do router protegido. `jwt_secret` default agora aborta o startup fora de `development`. |
| `cash_available` destruído a cada salvamento | Campo entrou em `PreferencesRequest` e o PUT passou a ser parcial (`exclude_unset`). |
| `/projection/passive-income` devolvendo zero | Era `item.ticker` sobre um dict; o `AttributeError` caía num `except` e virava `continue`. Corrigido, com `gather` sobre as posições. |

## Demais dores (D6–D10)

- **D6** — benchmark passou a usar retorno **ponderado no tempo**: aporte não é mais
  rentabilidade. A resposta expõe `method` e `net_contributions`.
- **D7** — a escrita de snapshot saiu do caminho de request (`services/snapshot_job.py`, job
  diário com lock), sempre sobre `list_positions()` + renda fixa. O cliente não controla mais o
  que entra na série histórica.
- **D8** — pesos do score renormalizados sobre as dimensões disponíveis, com
  `data_completeness` na resposta; a UI mostra score incompleto em cinza com o motivo.
- **D9** — % do CDI multiplicativo, IPCA+ compondo inflação, constante única de dias por mês,
  benchmark `0.85` substituído por dois números explícitos, liquidez no critério de melhor
  opção, e o cálculo duplicado no Angular **apagado**.
- **D10** — alertas agrupados com contagem, teto e uma ação cada; régua única de score nas três
  plataformas; setor traduzido nos alertas do backend; `confidence`/`data_years`/
  `consensus_methods` expostos ao lado de todo veredito.

## Itens acima que ficaram obsoletos

- **Item 1 (testes)** — ver "Correção de premissa".
- **Item 3 (duplicação de regra de RF)** — resolvido: `calcularRendimento()`/
  `calcularValorFinal()` foram removidos do Angular. A cadeia de `computed()` que dependia deles
  foi reescrita sobre `GET /fixed-income`, que já devolve tudo marcado a mercado.
- **Item 8 (labels duplicados)** — segue estrutural (TS↔Dart), mas os pontos que mais divergiam
  ganharam fonte única de referência: régua de score e tradução de setor existem nos três lados
  com o mesmo valor, e o backend deixou de emitir setor cru.
- **Item 14 (`create_all` não migra colunas)** — obsoleto: **Alembic** foi introduzido
  (`backend/migrations/`). `init_db()` marca bancos pré-Alembic na revisão baseline e aplica as
  migrações. A ressalva sobre "default simples" não vale mais — migração com backfill agora é
  suportada (a `0004` faz isso).
- **Item 16, último bullet (`DELETE /notifications/register-token`)** — a rota **voltou**, agora
  com consumidor: o logout do mobile desregistra o aparelho. Sem isso, depois do logout o
  aparelho continuava recebendo o resumo de carteira da conta anterior.

## Débito técnico remanescente

1. **Cache é um SQLite local, não compartilhado.** Ganhou arquivo dedicado
   (`.cache/http_cache.db`, sobrescrevível por `CACHE_DB_PATH`), WAL, `busy_timeout` e conexão
   reaproveitada por thread — o que resolveu o `database is locked` causado por compartilhar
   arquivo com o banco do usuário. Mas continua **local ao processo**: com mais de um worker na
   mesma máquina, cada um mantém a própria cópia e refaz o scan. Os jobs de background já são
   protegidos por lock no banco, então múltiplos workers não duplicam notificação. Escalar
   horizontalmente exige um volume compartilhado para `CACHE_DB_PATH` ou trocar a camada por
   Redis — a decisão foi manter SQLite por ora, sem provisionar infra nova.
2. **`brapi_history_range` default `3mo`.** O plano gratuito da BRAPI só aceita ranges curtos, e
   com 3 meses a SMA200 é estruturalmente incalculável. O sistema passou a ser honesto sobre
   isso (tendência de curto prazo rotulada como tal, e `GET /data-quality` reporta a cobertura),
   mas a tendência de longo prazo só existe de fato com plano pago e `BRAPI_HISTORY_RANGE=2y`.
3. **Unidade dos fundamentos da BRAPI não foi confirmada com chamada real.** `_ratio_to_pct`
   assume que `returnOnEquity`/`profitMargins`/`revenueGrowth`/`debtToEquity` vêm como razão
   decimal e multiplica por 100 — contrato explícito, no lugar da heurística
   `if f > 1.0: return f` que lia um ROE de 120% como 1,2%. Vale confirmar contra uma resposta
   real da API; `GET /data-quality` dá a visibilidade para isso.
4. **Universo hardcoded como fallback** (`config.default_universe`, ~400 tickers) — segue como
   estava: fallback defensivo intencional, mas extenso.
5. **Sem testes no web.** O mobile ganhou testes de régua de score e de tela de login (e o
   `widget_test.dart` que falhava por timeout em `pumpAndSettle` foi corrigido); o web continua
   sem `*.spec.ts`. A auditoria recomendava não investir aí antes de fechar as lacunas de regra
   financeira e isolamento — que agora estão fechadas, então este é o próximo alvo natural.
6. **Sparklines feitas à mão** em `ui-helper.service.ts` — inalterado.
7. **Proventos e sugestões seguidas são lançamento manual.** `/dividends/received` e
   `/suggestions/followed` dependem do usuário registrar. O caminho automático (calendário de
   proventos da BRAPI × quantidade em carteira, com confirmação) não foi implementado — a base
   de dados para ele já existe.
