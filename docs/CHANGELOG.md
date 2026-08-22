# fiance — histórico de mudanças

> Registro datado do que mudou e **por quê**, incluindo as decisões que foram tomadas e depois
> revertidas. É aqui que mora o contexto: por que a categoria `acoes_int` foi renomeada sem alias,
> por que o script de limpeza de cripto foi escrito e apagado no mesmo dia, por que o motor de
> otimização quantitativa foi removido.
>
> **O que está aberto hoje** fica em [KNOWN_ISSUES.md](KNOWN_ISSUES.md), não aqui. Este arquivo é
> só passado — nada nele deve ser lido como pendência.
>
> Mais recente primeiro.

---

## Redesign de UX/UI (2026-08-21 e 2026-08-22)

Auditoria completa de experiência e reformulação da arquitetura de informação nas duas
plataformas. Os documentos de projeto estão em [design/](design/); o log de execução, com o que
está no ar e o que não está, em [design/07-IMPLEMENTATION.md](design/07-IMPLEMENTATION.md).

O resumo do que mudou de contrato ou de estrutura:

- **Web: 6 rotas → 36.** Cinco destinos por intenção (`/hoje`, `/carteira`, `/descobrir`,
  `/estrategia`, `/voce`) mais `/ativo/:ticker`. `/market` dissolvido; as tabs que guardavam
  estado em `signal` viraram rotas. URLs antigas seguem como redirect.
- **Mobile: 4 abas → 5 destinos, 19 rotas.** `market_screen`/`rebalance_tab` removidos;
  Estratégia criada (não existia em nenhuma plataforma).
- **Estratégia e Quick Invest do web voltaram a existir.** `strategy.component` nunca tinha sido
  roteado — era código morto de 1092 linhas, apesar de `GET /strategy` e `POST /quick-invest`
  estarem no ar.
- **Contrato (aditivo):** `consensus_methods` em `FairPriceBlock` e `trend_basis` em
  `TechnicalBlock`. Os dois eram calculados e descartados em silêncio por
  `Modelo(**resultado.__dict__)`, porque o Pydantic ignora chave não declarada. Regressão em
  `test_fair_price.py`.
- **Cliente Dart:** `RebalanceSuggestions` passou a ler `allocation_gaps`, que também era
  descartado. Regressão em `test_allocation_gap_test.dart`.
- **Design tokens gerados** de `design-tokens/tokens.json` para CSS, TypeScript e Dart, com job
  próprio no CI. A régua de score havia divergido entre web e mobile por ser mantida à mão em três
  arquivos.
- **Removidos por não terem consumidor:** `dip.component` (485 linhas, renderizava IA e notícias
  cujo backend saiu em 2026-08-19), `market.component`, `analyze-asset`, `assets.component`,
  `config.component`, `SkeletonComponent`, `EmptyStateComponent`.
- **Defeitos silenciosos corrigidos:** `.card`, `.btn-primary`, `.btn-secondary` e
  `.pagination-btn` eram usados em 13 templates e **não existiam em nenhum CSS**; cinco variáveis
  CSS inexistentes em `assets.component.scss`; 16 ícones Lucide não registrados (seis anteriores ao
  redesign); `rgba(var(--accent) / 0.5)`, sintaxe inválida desde sempre.

---

## Auditoria de produto e engenharia (2026-08-19 → 2026-08-20)

### Correção de premissa

O documento anterior (e o `CLAUDE.md`) afirmava que não havia testes automatizados relevantes.
Havia — e agora são **206**, rodando em CI (`.github/workflows/ci.yml`: ruff + pytest no backend,
build e formatação no web, analyze + test no mobile) em todo push. O `conftest` também deixou de
stubar `get_dividends → []` e `get_history → {}`: PETR4 traz histórico de proventos e série de
preços, então a bateria passa pelo caminho onde os bugs de valuation moravam.

### Achados P0 — todos resolvidos

| Achado | Resolução |
|---|---|
| D1/D2 — renda fixa sem rendimento e presa ao `localStorage` | Tabela `fixed_income_positions` + CRUD `/fixed-income`, marcada a mercado no backend reusando `analyze_one()`. `AssetType.renda_fixa` criado (as posições apareciam como `br_stock`). Posições `RF_*` legadas removidas pela migração `0002`. |
| D3 — dois caminhos de perda da carteira inteira | `POST /portfolio/position` e `DELETE /portfolio/position/{ticker}` como escrita por item; `PUT /portfolio` fica só para importação e **rejeita lista vazia**. Mobile: FAB só com `dashboard.hasValue` e cadastro por item. Web: o branch de erro não marca `_initialized`, mostra banner e bloqueia edição. |
| D4 — quatro erros de unidade/janela no preço justo | Média de dividendos sobre anos-calendário completos com denominador correto; DY somando os últimos 12 meses **por data**; guard do DCF aceitando percentual; `range` do histórico configurável com degradação, e tendência de curto prazo rotulada quando falta série para a SMA200. |
| D5 — cache global com cálculo personalizado | O cache passou a guardar **dado de mercado** por ticker; preço justo e score são calculados por request. As metas de yield voltaram a ter efeito e o cálculo deixou de vazar entre tenants. |
| POST `/api/cache/clear` público | Movido para o `admin_router`, dentro do router protegido. `jwt_secret` default agora aborta o startup fora de `development`. |
| `cash_available` destruído a cada salvamento | Campo entrou em `PreferencesRequest` e o PUT passou a ser parcial (`exclude_unset`). |
| `/projection/passive-income` devolvendo zero | Era `item.ticker` sobre um dict; o `AttributeError` caía num `except` e virava `continue`. Corrigido, com `gather` sobre as posições. |

### Demais dores (D6–D10)

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

### Itens acima que ficaram obsoletos

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

### Features entregues


#### "O que mudou" — primeiro bloco do Dashboard
`GET /whats-new` compara o estado atual com o anterior e devolve até 5 linhas: variação de
patrimônio (já descontando aportes), posições com sinal de venda, vencimento de renda fixa
próximo, categoria fora da meta, prejuízo disponível para compensar IR e destaque de
oportunidade. **Cada linha tem uma ação** que leva à tela onde a decisão acontece. Sem nada a
dizer, o bloco diz isso — em vez de sumir. Web e mobile.

#### Renda fixa de verdade (`/fixed-income`)
Tabela própria no servidor com tipo, valor, taxa, tipo de taxa, % do CDI, data de aplicação,
vencimento, liquidez e isenção. **Marcada a mercado no backend**: rendimento acumulado, valor
hoje, projeção até o vencimento e aviso de vencimento próximo. Entra no patrimônio total, no
P&L, na alocação, na saúde da carteira, na projeção de renda passiva e no Quick Invest.
Cadastro no web (`/assets/cadastro`) e tela dedicada no mobile.

#### Proventos recebidos
Antes todo número de renda era estimativa derivada de dividend yield. Agora dá para lançar o
que caiu na conta (`/dividends/received`), ver total do mês, dos últimos 12 meses, média
mensal, quebra por ativo — e **confrontar com a estimativa do próprio app**.

#### Renda fixa × bolsa na mesma tela (Mercado → Ferramentas → RF x Bolsa)
"Com a Selic a 14,4%, vale mais o CDB ou o FII?" — ambos os lados na mesma unidade (renda
recorrente líquida a.a.), com valorização potencial mostrada **separada** (renda fixa não tem, e
a tela diz isso) e um veredito em texto.

#### Resultado das sugestões seguidas (Mercado → Rebalanceamento)
Registre o que você executou a partir de uma sugestão e o app mostra o resultado contra o
Ibovespa, agregado por origem da sugestão. Torna o produto auditável por quem usa.

#### Compensação de prejuízo de IR
Prejuízo realizado passa a abater ganho futuro da mesma categoria, como a legislação permite —
o app superestimava o IR devido de quem já havia realizado prejuízo. O saldo por categoria
aparece em Operações Encerradas, e cada venda mostra quanto foi compensado.

#### Proveniência e frescor do dado
Ao lado de cada veredito: anos de proventos encontrados, quantos métodos entraram no consenso e
confiança. Score com dado incompleto sai **cinza** e rotulado "dado insuficiente" em vez de
colorido com a nota. O dashboard mostra a idade das cotações e se o CDI/Selic vem do BCB ou é
estimativa.

#### Alertas com desfecho
Agrupados por tipo, com contagem e teto de 4 — e cada um com uma ação (ver análise, simular
venda, rebalancear, ajustar meta). Antes eram alertas sem limite e a única ação da tela era ir
para Mercado.

#### Cadastro separado de análise (web)
`/assets` é leitura (o retorno diário); `/assets/cadastro` é escrita (tarefa rara), com
salvamento explícito por linha. O autosave por debounce sobre um PUT destrutivo saiu.

#### Desktop mais aproveitado
Tabela de posições ordenável por qualquer coluna, seleção de até 4 ativos para comparar (leva
direto ao comparador) e exportação CSV da carteira.

#### Quick Invest no mobile
"Recebi meu salário, onde aporto" foi implementado primeiro no web, apesar de ser um caso de uso
mais de celular. Disponível no mobile em Mercado → Ferramentas. **Nota de 2026-08-21:** a versão
web nunca foi alcançável — vive dentro do `strategy.component` não roteado (ver acima), então
hoje o Quick Invest é de fato mobile-only.

#### Push honesto no web
A tela de Configurações agora informa que notificações requerem o app instalado, em vez de
oferecer cadência e alerta sem efeito para quem usa só o navegador. E o logout no app
desregistra o aparelho, que antes continuava recebendo o resumo da conta anterior.

#### Qualidade de dado (`GET /data-quality`)
Taxa de preenchimento por campo no universo, com o impacto de cada ausência descrito — a
instrumentação que faltava para distinguir "o modelo está errado" de "o dado não chegou".

---

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

---

## Score de oportunidades unificado, cadência de notificação e limpeza de "caixa disponível" nas Oportunidades (2026-08-19)

Pedido do usuário: usar todos os indicadores calculáveis no score de oportunidade, permitir configurar cadência de ajuste de carteira (diária/semanal/mensal) e considerar preferências de ativos/categorias na recomendação.

- **`opportunity_service.py` parou de usar um score ad-hoc** (`mos*60 + dy*1.5 + rsi_bonus*10 + trend_bonus`) e passou a chamar `scoring.py::score_opportunity()` — combina margem de segurança, qualidade (ROE/margem), endividamento, crescimento de receita, dividend yield e técnico, ponderados por perfil de risco (`OPPORTUNITY_WEIGHTS`). `score_company()`/`rank()` (baseados em P/L·P/VP) continuam no arquivo mas seguem sem nenhum consumidor real — candidatos a remoção numa próxima rodada se continuarem órfãos.
- **`PreferencesDb` ganhou** `risk_profile`, `preferred_categories`, `preferred_sectors`, `excluded_tickers` (boost de +5/+3 no score por categoria/setor preferido; exclusão remove o ticker da lista e do resumo de notificação) e `opportunities_frequency` (`off`/`daily`/`weekly`/`monthly`, substitui o booleano `notify_new_opportunities`). `notify_price_alerts` continua imediato (é alerta de risco, não sugestão de ajuste).
- **`notification_job.py`**: alertas de preço continuam a cada ciclo de 15min; o resumo de oportunidades só dispara quando a cadência configurada venceu desde `last_digest_sent_at`, agregando as melhores em um único push (antes eram até 3 pushes individuais por ciclo).
- **Vestígio morto removido**: `cash_available` de `PreferencesDb` nunca foi resettável de fato desde a remoção de 2026-08-12 (ver seção abaixo) — `PUT /preferences` nunca recebia esse campo, então ficava sempre em 0. Isso tornava `Opportunity.suggested_quantity`/`suggested_invest` e `OpportunitiesResponse.cash_available` permanentemente inertes (a condição `cash > 0` nunca era verdadeira), incluindo o bloco correspondente em `dashboard.component.html` que nunca renderizava. Removidos dos dois lados (backend e web) — a coluna `cash_available` na tabela `preferences` continua existindo (sem migração de drop), mas nada mais a lê para esse fim.

---

## Ajustes de usabilidade — caixa/metas/notificações/mercado/IA (2026-08-12)

Pedido do usuário para simplificar e corrigir usabilidade em mobile/web/backend:

- **"Caixa disponível" removida** — nunca ficava atualizada como preferência persistida. Quick invest e `/strategy` agora recebem o valor pontualmente na requisição (query param `cash_available` em `/strategy`, corpo em `/quick-invest`), não mais de preferences. `DashboardSummary.cash_available` removido da resposta do backend e dos models web/mobile.
- **Notificação de teste removida** (ver seção anterior); pushes reais ganharam campo `type` consistente (`price_alert`, `new_opportunity`) no payload `data`, preparando terreno para novos tipos.
- **Metas por categoria/setor** saíram do Dashboard e passaram a aparecer só em Ativos, que ganhou agrupamento por categoria/setor com indicador "atual X% · meta Y%" (mobile e web). Edição de metas continua em Configurações.
- **Autocomplete de ticker** ligado na busca do Mercado (mobile e web) e, na rodada seguinte (ver abaixo), também no diálogo de criar alerta de preço — reusando `TickerAutocompleteField`/`searchTickers()` já existentes, sem endpoint novo.
- **Estratégia de IA** (`analysis/strategy.py::build_investment_strategy`) deixou de escolher só a primeira oportunidade disponível por gap de alocação — agora usa o Gemini (`rank_opportunities_for_gap` em `llm/gemini_client.py`) para ponderar score/DY/margem de segurança/sentimento de notícias entre as candidatas do gap, com fallback determinístico (ordem por score) se a chamada falhar ou o Gemini estiver indisponível.
- **Regressão real encontrada e corrigida no mesmo dia**: `DashboardSummary.fromJson` no mobile ainda fazia cast não-nulo de `cash_available`, que o backend parou de enviar — quebrava Dashboard e Meus Ativos com `type Null is not a subtype of type num`. Motivou a rodada de testes de API abaixo.

---

## Robustez e usabilidade — testes de API, split do market, limpeza, evolução de patrimônio (2026-08-12)

- **Testes de API** — ver item 1 da lista de débito técnico, acima.
- **`market.component` quebrado em subcomponentes** — ver item 4 da lista de débito técnico, acima.
- **`opportunities.component` (web) removido** — código morto confirmado (só era exportado pelo barrel `components/index.ts`, sem nenhum consumidor real nas rotas ativas).
- **Gráfico de evolução de patrimônio**: dado já existia (`PortfolioSnapshot`, embutido em `GET /dashboard`/`GET /portfolio`, sem endpoint novo). Web trocou o SVG manual (`snapshotPath()`/`snapshotAreaPath()` em `ui-helper.service.ts`, removidos) por `PatrimonyChartComponent` (segue a skill `dataviz`: crosshair, tooltip, tabela alternativa para acessibilidade, cores 100% via tokens de tema). Mobile ganhou a mesma visualização do zero (não existia nada antes) via `fl_chart` em `dashboard_screen.dart`.

---

---

## Mobile — auto-login, splash animado, Configurações por módulos, diagnóstico de push (2026-08-11)

- **Auto-login corrigido**: o app sempre abria em `/login`, mesmo com sessão válida salva (`AuthService.readToken()` nunca era checado no boot). Novo `authStatusProvider` (`core/providers.dart`) lê o token salvo e, se existir, valida contra o novo endpoint `GET /auth/me` (também restaura o perfil do usuário sem precisar logar de novo). Nova `SplashScreen` (`features/auth/splash_screen.dart`) é a rota inicial (`/splash`) e decide automaticamente entre `/dashboard` (token válido) e `/login` (sem token ou token expirado/inválido — nesse caso desloga localmente).
- **Visual do login/splash**: novo `core/widgets/brand_background.dart` (glow radial nas cores da marca) e `core/widgets/brand_loading_indicator.dart` (logo pulsando, sem depender de pacote de animação) substituem o fundo liso e o `CircularProgressIndicator` genérico. Tagline trocada de "Análise de investimentos B3 na sua mão" (mencionava só B3) para "Ações, FIIs, cripto e renda fixa — tudo em um só assistente" (decisão do usuário, cobre o escopo real do app).
- **Configurações reorganizada em módulos** (`_SettingsCard`): Conta, Aparência, Preferências financeiras, Notificações, Metas de alocação por categoria, Metas de alocação por setor, Alertas de preço — cada um em um `Card` com cabeçalho ícone+título, substituindo a `ListView` plana de `Divider`s. Nenhuma lógica interna das seções (`_GoalsSection`, `_SectorGoalsSection`, `_AlertsSection`) foi alterada.
- **Diagnóstico de push**: novo botão "Enviar notificação de teste" no módulo Notificações, chamando `POST /notifications/test` (novo endpoint — busca os tokens do usuário atual via `list_device_tokens(user_id)` e usa `send_push` já existente). A resposta distingue os dois pontos de falha possíveis: `tokens_found == 0` → o token nunca foi registrado no servidor (permissão negada ou erro de rede no aparelho); `tokens_found > 0` mas nada chega → problema de credencial/entrega no servidor (conferir `FIREBASE_SERVICE_ACCOUNT_JSON` no Railway). `notifications_service.dart` agora guarda `permissionStatus`/`tokenRegistered`/`lastError` em vez de só logar com `debugPrint`. **Removido em 2026-08-12** (decisão do usuário: a integração já estava validada, o botão de teste não tinha mais utilidade) — `POST /notifications/test` e o botão não existem mais; `permissionStatus`/`tokenRegistered`/`lastError` permanecem, ainda usados pelo fluxo real de registro de push.
- **Bug real corrigido**: faltava `com.google.firebase.messaging.default_notification_channel_id` no `AndroidManifest.xml` — sem isso, pushes recebidos com o app em background caem no canal de fallback do FCM em vez do canal `fiance_default` já criado em `notifications_service.dart` (não impedia a entrega, mas descasava o canal/importância).
- **Ainda não verificado end-to-end**: se `FIREBASE_SERVICE_ACCOUNT_JSON` está de fato salvo no ambiente do Railway (só confirmamos que funciona com o `.env` local) — o botão de teste (removido em 2026-08-12, ver acima) era a ferramenta pra descobrir isso sem adivinhar; sem ele, essa verificação exigiria olhar os logs do backend em produção diretamente.

---

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

---

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

---

## Correções anteriores a 2026-08-10

Levantadas na primeira varredura do projeto (2026-07) e todas resolvidas depois:

| Limitação (registrada em 2026-07) | Status |
|---|---|
| BDR (ex. AAPL34) classificado como `br_stock`; units (SANB11, TAEE11, BPAC11...) classificadas como `fii` | ✅ **Corrigido.** `collectors/universal.py::detect_type()` testa BDR antes de FII; set `KNOWN_UNITS` trata as units conhecidas como `br_stock`; camada extra em `_fetch_brapi` reclassifica por nome (`UNIT/UNT/UNITS`) se necessário. |
| CDI fixo 13,5% no web vs 14,40% no backend | ✅ **Corrigido.** Ambos convergem via `GET /renda-fixa/taxas` → `collectors/rates.py` (BCB SGS real, fallback 14.40). O `signal(14.4)` no Angular é só valor inicial pré-fetch. |
| `fair_price` aplicando Graham em FII | ✅ **Corrigido.** FII usa exclusivamente `[bazin, pvp_fair]`; Graham só roda para ações BR/internacionais. |
| Fundamentos de BDR inconsistentes (LPA/VPA na escala do recibo, não da ação-mãe) | ✅ **Resolvido (validado com dado real em 2026-08-10).** Testado AAPL34 (BRAPI) vs AAPL (Finnhub): a BRAPI já retorna EPS escalado ao próprio preço da BDR (P/E implícito ≈33,8 vs P/E real da Apple ≈35,5 — coerente). `book_value` costuma vir `None` para BDRs na BRAPI (gap de dado, não erro de escala); `graham_fair_price()` já trata isso retornando `None` quando falta book_value, e o DCF segue funcionando só com EPS. Nenhuma correção de código necessária — a causa raiz (yfinance) já não existe mais. |
| Componentes compartilhados (RF form, allocation-view) não extraídos | ✅ **`market.component` corrigido em 2026-08-12** — quebrado em subcomponentes (`opportunities-list`, `dip-scanner`, `analyze-asset`, `renda-fixa`, `dip-analysis-modal`), sem mudança de comportamento. `quick-invest`/`investment-strategy` foram removidos de Mercado em 2026-08-19 (ver item novo abaixo), não existem mais como subcomponentes dessa tela. `assets.component.html`/`strategy.component.html` ainda têm formulários inline sem extração — não fizeram parte desta rodada. |
