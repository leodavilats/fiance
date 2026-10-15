# Estado do sistema

**Fonte de verdade** para a pergunta *"isto existe?"*. Nenhum outro documento responde isso.
Última revisão: 2026-10-12 · Escopo: todo o produto

Se um documento descrever uma funcionalidade e este arquivo disser que ela não existe, **este
arquivo vence**.

---

## Vocabulário de estado

| Marcador | Significa | Critério |
|---|---|---|
| `[ATUAL]` | Funciona e é usado com dado real | Alguém usa de verdade |
| `[IMPLEMENTADO]` | Existe no código, sem uso real | Testes passam, ninguém exercita |
| `[SEM CLIENTE]` | Backend vivo, o aplicativo não alcança | Rota existe, tela não |
| `[PLANEJADO]` | Decidido, não construído | Tem lugar em [09-FUTURO](09-FUTURO.md) |
| `[EM DISCUSSÃO]` | Sem decisão | Precisa de decisão |
| `[ABANDONADO]` | Existiu, saiu | Com data e commit |
| `[DESCONHECIDO]` | Nunca observado | Não se sabe se funciona |

`[SEM CLIENTE]` existiu porque o front web saiu em 2026-09-11 e levou junto o único consumidor de
várias rotas. Chegou a zero em 2026-09-26; o marcador fica para a próxima vez que uma rota nascer sem
tela.

---

## Quem usa o sistema

**Uma pessoa: o autor**, com carteira e gastos reais, diariamente. Não há outros usuários, não há
aplicativo publicado em loja, e não existe conta de desenvolvedor Google Play ou Apple.

| Plataforma | Estado |
|---|---|
| Android | `[ATUAL]` — instalado no aparelho do autor, em uso diário |
| iOS | `[DESCONHECIDO]` — **nunca executado**, nem em simulador |

O aplicativo iOS nunca rodou. Todo o comportamento descrito neste documento foi observado em
Android. Ver [10-PROBLEMAS](10-PROBLEMAS.md), seção H.

Isso significa que `[ATUAL]` aqui quer dizer *"exercitado por um usuário real"* — não *"validado em
escala"*. Nenhuma funcionalidade deste sistema foi submetida a mais de um usuário.

---

## O ciclo do dinheiro

A navegação do aplicativo é o encadeamento do produto, e o resto deste documento segue a mesma
ordem:

```
 /mes                    /sobra                   /patrimonio
 o que entrou      →     o que sobra        →     onde está aplicado
 e o que saiu            e para onde vai
                                                  /descobrir
                                                  o que comprar
```

Deslizar na horizontal troca de aba. O gesto tem esse significado só no nível da raiz: dentro de um
card de ativo ele continua sendo vender e remover.

---

## Caixa — `/mes`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Lançamento de entrada e saída | `[ATUAL]` | `cashflow/entries.py` | `month/cash_entry_sheet.dart` |
| Projeção do mês (entrou, saiu, comprometido, livre agora) | `[ATUAL]` | `cashflow/month.py` | `month/month_screen.dart` |
| Estimativa de gasto variável a partir de meses fechados | `[ATUAL]` | `cashflow/month.py` | idem |
| Molde de mês (prévia e commit) | `[ATUAL]` | `cashflow/template.py` | `month/month_template_sheet.dart` |
| Dívidas e classificação por custo | `[ATUAL]` | `cashflow/debt.py` | `month/debts_screen.dart` |
| Proventos derivados do razão, montados na leitura | `[ATUAL]` | `cashflow_service` | feed |
| Feed do mês | `[ATUAL]` | — | `month/feed_screen.dart` |

---

## Sobra — `/sobra`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Cascata: dívida cara → aporte | `[ATUAL]` | `cashflow/cascata.py` | `surplus/surplus_screen.dart` |
| Passo de reserva na cascata | `[IMPLEMENTADO]` | idem | ✅ alvo em meses declarado em `/voce/investir`; saldo vem da renda fixa de liquidez diária |
| Faixa piso/teto da sobra | `[ATUAL]` | `cashflow/month.py` | idem |
| Desvio de alocação | `[ATUAL]` | `analysis/strategy.py` | `surplus/allocation_drift_screen.dart` |
| Sugestões de aporte por categoria | `[ATUAL]` | `analysis/strategy.py` | `/sobra`, com os três primeiros destinos na própria aba; `/sobra/aporte` para a ordem inteira e a simulação |
| Maiores desvios de alocação na própria Sobra | `[ATUAL]` | `analysis/strategy.py` | `surplus/surplus_screen.dart` |

---

## Patrimônio — `/patrimonio`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Posições e composição | `[ATUAL]` | `storage/portfolio_store.py` | `patrimony/` |
| Marcação a mercado | `[ATUAL]` | `collectors/universal.py` | idem |
| Operações encerradas | `[ATUAL]` | `ledger/apuracao.py` | `patrimony/widgets/patrimony_closed_trades.dart` |
| Renda fixa (CDB, LCI, LCA, LC, CRI, CRA, Tesouro Selic/IPCA+/Pré) | `[ATUAL]` | `analysis/renda_fixa_analysis.py` | `assets/fixed_income_screen.dart` |
| Saúde da carteira | `[ATUAL]` | `analysis/portfolio_health.py` | feed |
| Projeção de patrimônio e renda passiva, em faixa | `[IMPLEMENTADO]` | `analysis/scenarios.py` | `/patrimonio/projecao` |

---

## Descobrir — `/descobrir`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Oportunidades com score e veredito | `[ATUAL]` | `services/opportunity_service.py` | `market/opportunities_tab.dart` |
| Preço justo por modelo de classe, faixa das premissas | `[ATUAL]` | `analysis/fair_price.py` | idem e `market/asset_detail_sheet.dart` — BDR e ETF saem "Sem preço justo" ([ADR-014](decisoes/ADR-014-um-modelo-por-classe.md)). Descreve posição, não antecipa retorno: de 2011 a 2017 o veredito não ordenou o retorno ([pesquisas/calibracao](pesquisas/calibracao.md), [10-PROBLEMAS](10-PROBLEMAS.md) A12) |
| Preço-teto da meta de renda | `[ATUAL]` | `analysis/fair_price.py::_indicators` | `market/asset_detail_sheet.dart` |
| Score personalizado por perfil de risco | `[ATUAL]` | `analysis/scoring.py` | idem — ações e FIIs; BDR com os pesos da ação e sem a margem; ETF não tem score |
| Falsificadores do veredito | `[ATUAL]` | `analysis/falsifiers.py` | `market/asset_detail_sheet.dart` |
| Linguagem da análise para iniciante: sigla com explicação ao lado, verbete ao toque, número em português | `[IMPLEMENTADO]` | `analysis/decision.py`, `analysis/texto.py` | `market/asset_detail_sheet.dart` e `core/glossary.dart` |
| Análise de ativo individual | `[ATUAL]` | `services/` | `market/asset_detail_sheet.dart` — a folha é a análise; `/ativo/:ticker` mostra menos e deixou de ser oferecida por botão |
| Quedas: recorte de quem caiu da máxima de 52 semanas, com a leitura de valor | `[IMPLEMENTADO]` | `services/dip_service.py` | `/descobrir/quedas` — [ADR-018](decisoes/ADR-018-a-queda-e-recorte-e-nao-veredito.md) |
| Comparador de ativos | `[ATUAL]` | — | `/descobrir/comparar` |
| Comparador renda fixa × bolsa | `[ATUAL]` | `services/income_compare_service.py` | `tools/income_compare_view.dart` |
| Calculadora de renda fixa | `[ATUAL]` | `analysis/renda_fixa_analysis.py` | `tools/tools_views.dart` |
| Setores | `[ATUAL]` | `analysis/sectors.py` | — |
| Benchmark CDI/Selic/IPCA | `[ATUAL]` | `collectors/rates.py` | — |
| Sugestões de rebalanceamento, com o alvo da realocação | `[ATUAL]` | `analysis/strategy.py` | `surplus/allocation_drift_screen.dart` |
| Perfil de risco visível onde ele ordena | `[ATUAL]` | `analysis/scoring.py` | `/descobrir` e `/sobra/desvio` |
| Sugestões seguidas, derivadas da compra no razão | `[IMPLEMENTADO]` | `services/followed_service.py` | `/patrimonio/seguidas`; a folha de compra do Descobrir registra |

---

## Livro-razão e imposto

A camada mais bem construída do sistema: o razão é a fonte da carteira e do imposto. Tem tela desde
2026-09-13 (`/patrimonio/razao`), e importação, conferência e reconstrução desde 2026-09-26.

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Razão como fonte única; posição é projeção | `[ATUAL]` | `ledger/projection.py` | `patrimony/ledger_screen.dart` |
| Registro de lançamento | `[IMPLEMENTADO]` | `services/ledger_service.py` | ✅ `/patrimonio/razao` |
| Comprar direto do Descobrir, com o preço de agora | `[IMPLEMENTADO]` | `POST /transactions` (`buy`) | `market/buy_sheet.dart` |
| Apagar lançamento, com reprojeção | `[IMPLEMENTADO]` | idem | ✅ idem |
| Eventos corporativos pela interface | `[IMPLEMENTADO]` | `ledger/entries.py` | ✅ idem |
| Importação de extrato (prévia + commit) | `[IMPLEMENTADO]` | `importing/` | ✅ `/patrimonio/razao/importar` — colar; anexar arquivo não |
| Reconstrução da projeção | `[IMPLEMENTADO]` | `POST /transactions/rebuild` | ✅ `/patrimonio/razao/conferir` |
| Reconciliação projeção × razão | `[IMPLEMENTADO]` | `GET /transactions/reconciliation` | ✅ idem, com posição sem lançamento levada ao razão |
| Apuração mensal de IR | `[IMPLEMENTADO]` | `ledger/apuracao.py` | parcial |
| Compensação de prejuízo por categoria | `[IMPLEMENTADO]` | `ledger/apuracao.py` | ❌ |
| Isenção mensal de R$ 20 mil | `[IMPLEMENTADO]` | `ledger/apuracao.py` | — |
| Proventos recebidos: registrar, listar, apagar | `[IMPLEMENTADO]` | `api/dividends.py` | `patrimony/dividends_screen.dart` |
| Proventos: sugestões do calendário | `[IMPLEMENTADO]` | `services/dividend_calendar_service.py` | ✅ `/patrimonio/proventos`, colapsado |
| Direito a provento provado pela data-com | `[ATUAL]` | `services/dividend_calendar_service.py` | ✅ bloco "Aguardando sua confirmação" — medição de 2026-09-25 sobre a BRAPI, então a fonte: 0 de 3.659 proventos sem data-com; o indeterminado vem de declaração de posição que absorveu a história |
| Razão: filtro por tipo, período e ativo, com paginação | `[ATUAL]` | `GET /transactions` | ✅ `/patrimonio/razao` |

**O que o IR cobre:** swing trade de ações, BDRs, ETFs (15%) e FIIs (20%), com compensação de
prejuízo e isenção mensal; day trade a 20%, apurado à parte, com IRRF de 1% e premissa de
corretora única. **O que não cobre:** emissão de DARF, informe anual.

---

## Conta, sessão e preferências

| Funcionalidade | Estado | Onde vive |
|---|---|---|
| Login com Google | `[ATUAL]` | `POST /auth/google` — botão no aplicativo |
| Login com Apple | `[IMPLEMENTADO]` | `POST /auth/apple` — servidor pronto; o botão depende da conta de desenvolvedor Apple |
| Sessão: acesso 1h, refresh 30d rotacionado | `[ATUAL]` | `api/auth.py` |
| Revogação por dispositivo e por conta | `[IMPLEMENTADO]` | `session_cuts` |
| Exclusão e exportação de conta | `[IMPLEMENTADO]` | `api/account.py` — ✅ `/voce/conta`, exclusão com frase de confirmação e exportação pela folha de compartilhamento |
| Importação da exportação, com prévia | `[IMPLEMENTADO]` | `services/account_import_service.py` — ✅ `/voce/conta/importar`, só em conta sem dados financeiros ([ADR-021](decisoes/ADR-021-a-exportacao-volta-para-conta-vazia.md)) |
| Preferências (perfil de risco, yields, nível de detalhe, tema) | `[ATUAL]` | `api/preferences.py` |
| Metas, com alvo declarado distinto do padrão | `[ATUAL]` | `api/goals.py` — sem declaração, nada cobra desvio |
| Alertas de preço | `[ATUAL]` | `api/alerts.py` |
| Notificações push | `[ATUAL]` | `notifications/` |
| Onboarding derivado | `[IMPLEMENTADO]` | `api/onboarding.py` — ✅ `/voce/comecar` |
| Telemetria com dicionário fechado | `[ATUAL]` | `core/events.py` — o aplicativo envia por `mobile/lib/core/product_events.dart`, conferido contra o catálogo |
| Rotas de administrador | `[IMPLEMENTADO]` | `require_admin` |
| Rota pública sem titular | `[IMPLEMENTADO]` | `GET /public/asset/{ticker}` |
| Páginas jurídicas (`/termos`, `/privacidade`, `/aviso-cvm`) | `[ATUAL]` | `api/legal.py` |
| Backup lógico: exportar, restaurar, reaplicar exclusões | `[IMPLEMENTADO]` | `backend/app/backup.py` — runbook em [07-OPERACAO](07-OPERACAO.md); roda à mão, sem agendamento nem backup automático — risco aceito em 2026-10-12 |

**Não existe senha no sistema.** O login é Google (e Apple, quando o botão chegar). Não há "esqueci minha senha"
porque não há senha.

---

## Monetização

Nada cobra dinheiro hoje. A cerca de plano está **desligada** (`ENTITLEMENTS_ENABLED=false`).

| Funcionalidade | Estado | Observação |
|---|---|---|
| Cerca de plano | `[IMPLEMENTADO]` | Desligada. Nunca exercitada |
| Trial de 14 dias na primeira posição salva | `[IMPLEMENTADO]` | Ver [ADR-009](decisoes/ADR-009-trial-e-gratuidade.md) |
| Indicação com crédito | `[IMPLEMENTADO]` | Nunca usada |
| Cobrança (`backend/app/payments/`, `api/billing.py`) | `[IMPLEMENTADO]` | Só `FakeProvider`, sem tela. Será refeito para RevenueCat, e o que existe não será aproveitado — [ADR-008](decisoes/ADR-008-monetizacao-por-loja.md) |
| RevenueCat | `[PLANEJADO]` | Decidido, não iniciado |

---

## Dados externos

| Fonte | Estado | Fornece |
|---|---|---|
| Base de mercado própria (`postgres-mercado`, pelo `data-job/`) | `[ATUAL]` | Preço de fechamento, fundamentos, proventos, histórico de ações, FIIs, BDRs, ETFs. Substituiu a BRAPI em 2026-10-12 ([ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)) |
| BCB SGS | `[ATUAL]` | CDI, Selic, IPCA |
| Serviço `data-job` | `[ATUAL]` | Cron `0 2 * * 2-6` (UTC, 23h de Brasília) no Railway; arquivo bruto guardado no volume `/bruto`; cada rodada registrada em `mercado.rodada` — [11-DADOS-DE-MERCADO](11-DADOS-DE-MERCADO.md), [07-OPERACAO](07-OPERACAO.md) |
| Leitura do app: `mercado.ativo_hoje` e `mercado.fundamento_app` | `[ATUAL]` | Visões materializadas que a `dados-api` entrega e o backend consome em `/v1/retratos` (`collectors/mercado.py`): cotação, cadastro, quantidade de ações e proventos de 12 meses por ativo; resultado e balanço por empresa. Junto com `mercado.cotacao` (histórico) e `mercado.provento` (sem `cvm_estimado`) |
| B3 COTAHIST, pelo `data-job/` | `[ATUAL]` | Cotação diária bruta do mercado à vista, de 2005 em diante, no `postgres-mercado` de produção, atualizada por cron depois de cada pregão. O backend lê por `ativo_hoje` e `mercado.cotacao`; a pesquisa e o painel, direto — [11-DADOS-DE-MERCADO](11-DADOS-DE-MERCADO.md) |
| CVM cadastro e FCA, e emissores da B3, pelo `data-job/` | `[ATUAL]` | Empresa por CNPJ e a ligação do código de emissor do ISIN ao CNPJ, com o método. O backend lê nome, setor e CNPJ por `ativo_hoje`; a pesquisa e o painel, direto |
| CVM DFP e ITR, pelo `data-job/` | `[ATUAL]` | Balanço, resultado e fluxo de caixa de 2010 em diante, por documento, versão e data de entrega: 6,3 milhões de linhas no `postgres-mercado`. O backend lê por `fundamento_app`; a pesquisa, pelas visões de fundamento |
| BCB SGS, pelo `data-job/` | `[IMPLEMENTADO]` | CDI e Selic diários, meta da Selic e IPCA mensal de 2005 em diante, e a Selic mensal (SGS 4189) desde 2000, no `postgres-mercado`. Lido pela pesquisa; o backend segue lendo o BCB por conta própria (`backend/app/collectors/rates.py`) |
| Visões de fundamento no `postgres-mercado` | `[ATUAL]` | Receita, EBIT, lucro, patrimônio, caixa e dívida por documento, sobre as demonstrações brutas — [11-DADOS-DE-MERCADO](11-DADOS-DE-MERCADO.md). O backend lê o recorte `fundamento_app`; a pesquisa e o painel, as visões inteiras |
| Proventos, eventos em ações e série ajustada, pelo `data-job/` | `[ATUAL]` | Da B3, por emissor, toda sexta; eventos conferidos pelo preço antes de ajustar, e o que falta na B3 inferido com preço, número de ações e IPE (21 em 2026-10-10); `mercado.serie_papel` com preço ajustado, retorno total e saltos sem explicação marcados; FIIs, ETFs e BDRs em `mercado.serie_fundo`, com eventos completos, rendimentos recentes da B3 acumulados desde out/2026 e, para FII, o histórico desde 2016 estimado pelo informe mensal da CVM; PTAX e preços e taxas do Tesouro Direto desde 2005. O backend lê `mercado.provento`, sem a origem `cvm_estimado`; série ajustada, PTAX e Tesouro, só a pesquisa e o painel |
| Capital social do FRE, pelo `data-job/` | `[ATUAL]` | Quantidade de ações integralizadas por data de aprovação, de 2010 em diante, para o que a composição do capital não cobre (antes de 2020). Entra no valor de mercado do app, pela quantidade de ações de `ativo_hoje` |
| Pesquisa de carteira, em `trend-backend/` | `[IMPLEMENTADO]` | Uso próprio: motor de simulação mensal com custo e imposto, prova lacrada, registro e relatório HTML; 8 variações testadas e busca encerrada sem vantagem investível — [pesquisas/pesquisa](pesquisas/pesquisa.md). Ranking de tendência: 6 variações, 3 em ações e 3 em FIIs, nenhuma passou no estudo — o ranking não informa — [pesquisas/ranking](pesquisas/ranking.md) |
| API de dados (`dados-api/`) | `[IMPLEMENTADO]` | Contas por convite, chaves com hash, planos com limite por minuto e por dia, histórico por plano, uso por chave e por dia, rotas `/v1` de ativos, cotação, série ajustada, proventos, eventos, demonstrações como se sabia na data, informe de FII, BCB e Tesouro; administração em `/admin`. Sem cobrança — [ADR-024](decisoes/ADR-024-api-de-dados.md) |
| Painel `trend` (API no `trend-backend`, front no `trend-frontend`) | `[IMPLEMENTADO]` | Caminho, coleta, ativos de todas as classes, dólar e Tesouro, ranking, pesquisa e documentos, com senha, no serviço `trend` do Railway |
| Alertas de coleta no painel | `[IMPLEMENTADO]` | Falha de etapa na última rodada (`mercado.rodada`), rodada parada há mais de 80 h ou sem terminar, cotação com mais de 2 dias úteis sem pregão novo — `trend-backend/api/alertas.py` |
| Calibração do preço justo, em `trend-backend/` | `[IMPLEMENTADO]` | Uso próprio: o veredito do app, com só o que se sabia na data, contra o retorno dos 12 meses seguintes. Encerrada em 2026-10-12: de 2011 a 2017, o veredito não ordenou o retorno — [pesquisas/calibracao](pesquisas/calibracao.md), [10-PROBLEMAS](10-PROBLEMAS.md) A12 |

Proteções ativas: disjuntor por fonte, cache com idade, faixa de plausibilidade, coleta em lote,
portão de pregão. Detalhes em [03-ARQUITETURA](03-ARQUITETURA.md).

---

## `[ABANDONADO]`

| Item | Quando | Referência |
|---|---|---|
| **Front Angular — a interface web inteira** | 2026-09-11 | commit `3a922a6` · [ADR-003](decisoes/ADR-003-cliente-unico.md) |
| Landing page, `POST /public/interest`, sitemap, og-image | 2026-09-11 | commit `3a922a6` |
| Renderização no servidor e E2E de navegador | 2026-09-11 | commit `3a922a6` |
| Criptomoedas | antes de 2026-09 | Nenhum vestígio no código |
| Ações internacionais diretas (fora de BDR) | antes de 2026-09 | — |
| Finnhub, CoinGecko, Gemini, yfinance, Alpha Vantage | antes de 2026-09 | Restaram BRAPI (até 2026-10-12) e BCB |
| BRAPI | 2026-10-12 | Trocada pela base própria — [ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md) |
| Otimizador (`optimizer/`, `OptimizationStrategy`) | 2026-09-13 | commit `88c18c5` · [ADR-010](decisoes/ADR-010-remover-otimizador.md) |
| Diagnóstico de queda por notícia (Google News) | 2026-09-25 | [ADR-018](decisoes/ADR-018-a-queda-e-recorte-e-nao-veredito.md) — a queda virou recorte |
| Veredito por tendência (`basis = trend`) e os nomes antigos das etiquetas | 2026-09-25 | [ADR-013](decisoes/ADR-013-o-tecnico-nao-decide.md) |
| Técnico como dimensão do score | 2026-09-25 | [ADR-017](decisoes/ADR-017-o-score-nao-le-o-tecnico.md) |
| Liquidez no score de FII | 2026-09-25 | [ADR-019](decisoes/ADR-019-fii-de-papel-exige-yield-nominal.md) |
| Densidade de tela | 2026-09-26 | substituída pelo nível de detalhe (migração `0011_nivel_de_detalhe`) |
| Dados de demonstração (`/demo/portfolio`, `/demo/assets`) | 2026-09-26 | Era vitrine da web e ficou sem cliente desde 2026-09-11 |

Sobrou da web: `mobile/web/index.html`, scaffold padrão do Flutter. Não é uma interface.

---

## Resumo por estado

Contado nas tabelas deste arquivo em 2026-10-12, uma linha por item.

| Estado | Linhas |
|---|---|
| `[ATUAL]` | 52 |
| `[IMPLEMENTADO]` | 34 |
| `[DESCONHECIDO]` | 1 — iOS |
| `[SEM CLIENTE]` | **0** — ver [historico/PARIDADE-WEB-APP-2026-09](historico/PARIDADE-WEB-APP-2026-09.md) |
| `[PLANEJADO]` | 1 aqui; o resto em [09-FUTURO](09-FUTURO.md) |
| `[ABANDONADO]` | 14 |

O `[SEM CLIENTE]` chegou a zero em 2026-09-26: as nove lacunas abertas pela saída da web têm tela,
e a demonstração, que era vitrine dela, saiu do backend. O número que importa agora é o
`[IMPLEMENTADO]`: o que existe e ninguém exercita com dado real, porque não há aplicativo em loja.
