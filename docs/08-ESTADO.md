# Estado do sistema

**Fonte de verdade** para a pergunta *"isto existe?"*. Nenhum outro documento responde isso.
Última revisão: 2026-09-13 · Escopo: todo o produto

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

`[SEM CLIENTE]` existe porque o front web saiu em 2026-09-11 e levou junto o único consumidor de
várias rotas. É a categoria mais importante deste documento hoje, e a que deve encolher primeiro.

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

---

## Caixa — `/mes`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Lançamento de entrada e saída | `[ATUAL]` | `cashflow/entries.py` | `mes/lancar_sheet.dart` |
| Projeção do mês (entrou, saiu, comprometido, livre agora) | `[ATUAL]` | `cashflow/month.py` | `mes/mes_screen.dart` |
| Estimativa de gasto variável a partir de meses fechados | `[ATUAL]` | `cashflow/month.py` | idem |
| Molde de mês (prévia e commit) | `[ATUAL]` | `cashflow/template.py` | `mes/molde_sheet.dart` |
| Dívidas e classificação por custo | `[ATUAL]` | `cashflow/debt.py` | `mes/dividas_screen.dart` |
| Proventos derivados do razão, montados na leitura | `[ATUAL]` | `cashflow_service` | feed |
| Feed do mês | `[ATUAL]` | — | `mes/feed_screen.dart` |

---

## Sobra — `/sobra`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Cascata: dívida cara → aporte | `[ATUAL]` | `cashflow/cascata.py` | `sobra/sobra_screen.dart` |
| Passo de reserva na cascata | `[IMPLEMENTADO]` | idem | ❌ **inalcançável** — falta onde declarar o alvo ([10-PROBLEMAS](10-PROBLEMAS.md), item 30) |
| Faixa piso/teto da sobra | `[ATUAL]` | `cashflow/month.py` | idem |
| Desvio de alocação | `[ATUAL]` | `analysis/strategy.py` | `sobra/desvio_screen.dart` |
| Sugestões de aporte por categoria | `[ATUAL]` | `analysis/strategy.py` | `/sobra/aporte` |

---

## Patrimônio — `/patrimonio`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Posições e composição | `[ATUAL]` | `storage/portfolio_store.py` | `patrimonio/` |
| Marcação a mercado | `[ATUAL]` | `collectors/universal.py` | idem |
| Operações encerradas | `[ATUAL]` | `ledger/apuracao.py` | `patrimonio_closed_trades.dart` |
| Renda fixa (CDB, LCI, LCA, LC, CRI, CRA, Tesouro Selic/IPCA+/Pré) | `[ATUAL]` | `analysis/renda_fixa_analysis.py` | `assets/fixed_income_screen.dart` |
| Saúde da carteira | `[ATUAL]` | `analysis/portfolio_health.py` | feed |
| Projeção de patrimônio e renda passiva, em faixa | `[IMPLEMENTADO]` | `analysis/scenarios.py` | `/patrimonio/projecao` |

---

## Descobrir — `/descobrir`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Oportunidades com score e veredito | `[ATUAL]` | `services/opportunity_service.py` | `market/opportunities_tab.dart` |
| Preço justo por consenso de métodos | `[ATUAL]` | `analysis/fair_price.py` | idem |
| Score personalizado por perfil de risco | `[ATUAL]` | `analysis/scoring.py` | idem — **só ações e BDRs**, ver [10-PROBLEMAS](10-PROBLEMAS.md) |
| Falsificadores do veredito | `[ATUAL]` | `analysis/falsifiers.py` | `market/asset_detail_sheet.dart` |
| Análise de ativo individual | `[ATUAL]` | `services/` | `market/asset_detail_sheet.dart` — a folha é a análise; `/ativo/:ticker` mostra menos e deixou de ser oferecida por botão |
| Quedas (dip scanner) | `[IMPLEMENTADO]` | `analysis/dip_analysis.py` | `/descobrir/quedas` |
| Comparador de ativos | `[ATUAL]` | — | `/descobrir/comparar` |
| Comparador renda fixa × bolsa | `[ATUAL]` | `services/income_compare_service.py` | `tools/income_compare_view.dart` |
| Calculadora de renda fixa | `[ATUAL]` | `analysis/renda_fixa_analysis.py` | `tools/tools_views.dart` |
| Setores | `[ATUAL]` | `analysis/sectors.py` | — |
| Benchmark CDI/Selic/IPCA | `[ATUAL]` | `collectors/rates.py` | — |
| Sugestões de rebalanceamento, com o alvo da realocação | `[ATUAL]` | `analysis/strategy.py` | `sobra/desvio_screen.dart` |
| Perfil de risco visível onde ele ordena | `[ATUAL]` | `analysis/scoring.py` | `/descobrir` e `/sobra/desvio` |
| Ativos seguidos | `[SEM CLIENTE]` | `api/followed.py` | ❌ |

---

## Livro-razão e imposto

A camada mais bem construída do sistema, e a **menos acessível**: o razão é a fonte da carteira e do
imposto, e não tem nenhuma tela no aplicativo.

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Razão como fonte única; posição é projeção | `[ATUAL]` | `ledger/projection.py` | `patrimonio/razao_screen.dart` |
| Registro de lançamento | `[IMPLEMENTADO]` | `services/ledger_service.py` | ✅ `/patrimonio/razao` |
| Apagar lançamento, com reprojeção | `[IMPLEMENTADO]` | idem | ✅ idem |
| Eventos corporativos pela interface | `[IMPLEMENTADO]` | `ledger/entries.py` | ✅ idem |
| Importação de extrato (prévia + commit) | `[SEM CLIENTE]` | `importing/` | ❌ |
| Reconstrução da projeção | `[SEM CLIENTE]` | `POST /transactions/rebuild` | ❌ |
| Reconciliação projeção × razão | `[SEM CLIENTE]` | `GET /transactions/reconciliation` | ❌ |
| Apuração mensal de IR | `[IMPLEMENTADO]` | `ledger/apuracao.py` | parcial |
| Compensação de prejuízo por categoria | `[IMPLEMENTADO]` | `ledger/apuracao.py` | ❌ |
| Isenção mensal de R$ 20 mil | `[IMPLEMENTADO]` | `ledger/apuracao.py` | — |
| Proventos recebidos: registrar, listar, apagar | `[IMPLEMENTADO]` | `api/dividends.py` | `patrimonio/proventos_screen.dart` |
| Proventos: sugestões do calendário | `[IMPLEMENTADO]` | `services/dividend_calendar_service.py` | ✅ `/patrimonio/proventos` |

**O que o IR cobre:** swing trade de ações, BDRs, ETFs (15%) e FIIs (20%), com compensação de
prejuízo e isenção mensal. **O que não cobre:** day trade, emissão de DARF, informe anual.

---

## Conta, sessão e preferências

| Funcionalidade | Estado | Onde vive |
|---|---|---|
| Login com Google | `[ATUAL]` | `POST /auth/google` |
| Sessão: acesso 1h, refresh 30d rotacionado | `[ATUAL]` | `api/auth.py` |
| Revogação por dispositivo e por conta | `[IMPLEMENTADO]` | `session_cuts` |
| Exclusão e exportação de conta | `[IMPLEMENTADO]` | `api/account.py` |
| Preferências (perfil de risco, yields, densidade) | `[ATUAL]` | `api/preferences.py` |
| Metas | `[ATUAL]` | `api/goals.py` |
| Alertas de preço | `[ATUAL]` | `api/alerts.py` |
| Notificações push | `[ATUAL]` | `notifications/` |
| Onboarding derivado | `[SEM CLIENTE]` | `api/onboarding.py` |
| Telemetria com dicionário fechado | `[IMPLEMENTADO]` | `core/events.py` |
| Rotas de administrador | `[IMPLEMENTADO]` | `require_admin` |
| Rota pública sem titular | `[IMPLEMENTADO]` | `GET /public/asset/{ticker}` |
| Páginas jurídicas (`/termos`, `/privacidade`, `/aviso-cvm`) | `[ATUAL]` | `api/legal.py` |
| Dados de demonstração | `[SEM CLIENTE]` | `api/demo.py` |

**Não existe senha no sistema.** O login é exclusivamente Google. Não há "esqueci minha senha"
porque não há senha.

---

## Monetização

Nada cobra dinheiro hoje. A cerca de plano está **desligada** (`ENTITLEMENTS_ENABLED=false`).

| Funcionalidade | Estado | Observação |
|---|---|---|
| Cerca de plano | `[IMPLEMENTADO]` | Desligada. Nunca exercitada |
| Trial de 14 dias na primeira posição salva | `[IMPLEMENTADO]` | Ver [ADR-009](decisoes/ADR-009-trial-e-gratuidade.md) |
| Indicação com crédito | `[IMPLEMENTADO]` | Nunca usada |
| Cobrança (`billing/`) | `[ABANDONADO na direção]` | Só `FakeProvider`. Será refeito para RevenueCat — [ADR-008](decisoes/ADR-008-monetizacao-por-loja.md) |
| RevenueCat | `[PLANEJADO]` | Decidido, não iniciado |

---

## Dados externos

| Fonte | Estado | Fornece |
|---|---|---|
| BRAPI | `[ATUAL]` | Preço, fundamentos, dividendos, histórico de ações, FIIs, BDRs, ETFs |
| BCB SGS | `[ATUAL]` | CDI, Selic, IPCA |

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
| Finnhub, CoinGecko, Gemini, yfinance, Alpha Vantage | antes de 2026-09 | Restaram BRAPI e BCB |
| `backend/app/optimizer/` | a remover | Diretório vazio · [ADR-010](decisoes/ADR-010-remover-otimizador.md) |
| `OptimizationStrategy` (Sharpe, HRP, mín. volatilidade) | a remover | Enum órfão em `models/enums.py` |

Sobrou da web: `mobile/web/index.html`, scaffold padrão do Flutter. Não é uma interface.

---

## Resumo por estado

| Estado | Quantidade aproximada |
|---|---|
| `[ATUAL]` | ~30 funcionalidades |
| `[IMPLEMENTADO]` | ~14 |
| `[SEM CLIENTE]` | **5** — ver [PARIDADE-WEB-APP](temporario/PARIDADE-WEB-APP.md) |
| `[PLANEJADO]` | ver [09-FUTURO](09-FUTURO.md) |
| `[ABANDONADO]` | 8 blocos |

O número que importa é o `[SEM CLIENTE]`: **cinco funcionalidades que o backend serve e o aplicativo
não alcança**, todas por perda de paridade em 2026-09-11 — eram nove, e quatro saíram da lista em
2026-09-13: livro-razão, eventos corporativos, proventos e o alvo da realocação. Enquanto ele não chegar a zero, o produto
entrega menos do que possui.
