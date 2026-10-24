# Estado do sistema

**Fonte de verdade** para a pergunta *"isto existe?"*, em todas as partes. Nenhum outro documento
responde isso.
Última revisão: 2026-10-24 · Escopo: app, base de mercado, API de dados e laboratório

Se um documento descrever uma funcionalidade e este arquivo disser que ela não existe, **este
arquivo vence**.

---

## Vocabulário de estado

| Marcador | Significa | Critério |
|---|---|---|
| `[ATUAL]` | Funciona e é usado com dado real | Alguém usa de verdade |
| `[IMPLEMENTADO]` | Existe no código, sem uso real | Testes passam, ninguém exercita |
| `[SEM CLIENTE]` | Backend vivo, o aplicativo não alcança | Rota existe, tela não |
| `[PLANEJADO]` | Decidido, não construído | Tem lugar em [05-FUTURO](05-FUTURO.md) |
| `[EM DISCUSSÃO]` | Sem decisão | Precisa de decisão |
| `[ABANDONADO]` | Existiu, saiu | Com data e commit |
| `[DESCONHECIDO]` | Nunca observado | Não se sabe se funciona |

`[SEM CLIENTE]` existiu porque o front web saiu em 2026-09-11 e levou junto o único consumidor de
várias rotas. Chegou a zero em 2026-09-26; o marcador fica para a próxima vez que uma rota nascer sem
tela.

---

---

## Quem usa o sistema

**Uma pessoa: o autor**, diariamente, com carteira e gastos reais. Nada está aberto ao público
([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)).

| Parte | Quem usa | Onde roda |
|---|---|---|
| App | O autor. Nada publicado em loja, nenhuma conta de desenvolvedor | Android `[ATUAL]`, no aparelho do autor. iOS `[DESCONHECIDO]` — **nunca executado**, nem em simulador |
| Base de mercado | Os dois produtos e o laboratório | Railway, cron diário |
| API de dados | O app, com a chave `interno`; convidados, sem cobrança; o autor, com a cobrança pelo Asaas | `https://fiance-dados.up.railway.app` |
| Laboratório | O autor | `https://fiance-trend.up.railway.app`, com senha |

`[ATUAL]` aqui quer dizer *"exercitado por um usuário real"* — não *"validado em escala"*. Todo
comportamento do app foi observado em Android. Ver [04-PROBLEMAS](04-PROBLEMAS.md#app).

---

## App

### O ciclo do dinheiro

A navegação do aplicativo é o encadeamento do produto, e o resto desta seção segue a mesma ordem:

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

### Caixa — `/mes`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Lançamento de entrada e saída | `[ATUAL]` | `cashflow/entries.py` | `month/cash_entry_sheet.dart` |
| Projeção do mês (entrou, saiu, comprometido, livre agora) | `[ATUAL]` | `cashflow/month.py` | `month/month_screen.dart` |
| Estimativa de gasto variável a partir de meses fechados | `[ATUAL]` | `cashflow/month.py` | idem |
| Molde de mês (prévia e commit) | `[ATUAL]` | `cashflow/template.py` | `month/month_template_sheet.dart` |
| Dívidas e classificação por custo | `[ATUAL]` | `cashflow/debt.py` | `month/debts_screen.dart` |
| Proventos derivados do razão, montados na leitura | `[ATUAL]` | `cashflow_service` | `month/month_screen.dart` |

---

### Sobra — `/sobra`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Cascata: dívida cara → aporte | `[ATUAL]` | `cashflow/cascata.py` | `surplus/surplus_screen.dart` |
| Passo de reserva na cascata | `[IMPLEMENTADO]` | idem | ✅ alvo em meses declarado em `/voce/investir`; saldo vem da renda fixa de liquidez diária |
| Faixa piso/teto da sobra | `[ATUAL]` | `cashflow/month.py` | idem |
| Desvio de alocação | `[ATUAL]` | `analysis/strategy.py` | `surplus/allocation_drift_screen.dart` |
| Sugestões de aporte por categoria | `[ATUAL]` | `analysis/strategy.py` | `/sobra`, com os três primeiros destinos na própria aba; `/sobra/aporte` para a ordem inteira e a simulação |
| Maiores desvios de alocação na própria Sobra | `[ATUAL]` | `analysis/strategy.py` | `surplus/surplus_screen.dart` |

---

### Patrimônio — `/patrimonio`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Posições e composição | `[ATUAL]` | `storage/portfolio_store.py` | `patrimony/` |
| Marcação a mercado | `[ATUAL]` | `collectors/universal.py` | idem |
| Operações encerradas | `[ATUAL]` | `ledger/apuracao.py` | `patrimony/widgets/patrimony_closed_trades.dart` |
| Renda fixa (CDB, LCI, LCA, LC, CRI, CRA, Tesouro Selic/IPCA+/Pré) | `[ATUAL]` | `analysis/renda_fixa_analysis.py` | `assets/fixed_income_screen.dart` |
| Saúde da carteira | `[ATUAL]` | `analysis/portfolio_health.py` | `patrimony/widgets/portfolio_health.dart` |
| Projeção de patrimônio e renda passiva, em faixa | `[IMPLEMENTADO]` | `analysis/scenarios.py` | `/patrimonio/projecao` |

---

### Descobrir — `/descobrir`

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Oportunidades com score e veredito | `[ATUAL]` | `services/opportunity_service.py` | `market/opportunities_tab.dart` |
| Preço justo por modelo de classe, faixa das premissas | `[ATUAL]` | `analysis/fair_price.py` | idem e `market/asset_detail_sheet.dart` — BDR e ETF saem "Sem preço justo" ([ADR-014](decisoes/ADR-014-um-modelo-por-classe.md)). Taxa de ação pelo juro real do Tesouro IPCA+ mais longo, pela `fiance-dados` ([ADR-028](decisoes/ADR-028-taxa-de-acao-pelo-juro-real-do-tesouro.md)); yield de FII pela Selic média. Descreve posição, não antecipa retorno: de 2011 a 2017 o veredito não ordenou o retorno, nem com a taxa nova ([pesquisa/calibracao](pesquisa/estudos/calibracao.md), [pesquisa/calibracao-com-a-taxa-nova](pesquisa/estudos/calibracao-com-a-taxa-nova.md)) |
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

### Livro-razão e imposto

A camada mais bem construída do app: o razão é a fonte da carteira e do imposto. Na tela ele se
chama **Lançamentos** (`/patrimonio/razao`), com importação, conferência e reconstrução.

| Funcionalidade | Estado | Onde vive | Tela |
|---|---|---|---|
| Razão como fonte única; posição é projeção | `[ATUAL]` | `ledger/projection.py` | `patrimony/ledger_screen.dart` |
| Registro de lançamento | `[IMPLEMENTADO]` | `services/ledger_service.py` | ✅ `/patrimonio/razao` |
| Comprar direto do Descobrir, com o preço de agora | `[IMPLEMENTADO]` | `POST /transactions` (`buy`) | `market/buy_sheet.dart` |
| Apagar lançamento, com reprojeção | `[IMPLEMENTADO]` | idem | ✅ idem |
| Eventos corporativos pela interface | `[IMPLEMENTADO]` | `ledger/entries.py` | ✅ idem |
| Importação de extrato (prévia + commit) | `[IMPLEMENTADO]` | `importing/` | ✅ `/patrimonio/razao/importar` — colar; anexar arquivo não |
| Importação do extrato de movimentação da B3 (.xlsx) | `[IMPLEMENTADO]` | `importing/b3.py`, `services/b3_import_service.py` | ✅ `/patrimonio/razao/importar/b3` — anexar o arquivo |
| Reconstrução da projeção | `[IMPLEMENTADO]` | `POST /transactions/rebuild` | ✅ `/patrimonio/razao/conferir` |
| Reconciliação projeção × razão | `[IMPLEMENTADO]` | `GET /transactions/reconciliation` | ✅ idem, com posição sem lançamento levada ao razão |
| Apuração mensal de IR | `[IMPLEMENTADO]` | `ledger/apuracao.py` | parcial |
| Compensação de prejuízo por categoria | `[IMPLEMENTADO]` | `ledger/apuracao.py` | ❌ |
| Isenção mensal de R$ 20 mil | `[IMPLEMENTADO]` | `ledger/apuracao.py` | — |
| Proventos recebidos: registrar, listar, apagar | `[IMPLEMENTADO]` | `api/dividends.py` | `patrimony/dividends_screen.dart` |
| Proventos: sugestões do calendário | `[IMPLEMENTADO]` | `services/dividend_calendar_service.py` | ✅ `/patrimonio/proventos`, colapsado |
| Direito a provento provado pela data-com | `[ATUAL]` | `services/dividend_calendar_service.py` | ✅ bloco "Aguardando sua confirmação" — medição de 2026-09-25 sobre a BRAPI, então a fonte: 0 de 3.659 proventos sem data-com; o indeterminado vem de declaração de posição que absorveu a história |
| Razão: filtro por tipo, período e ativo, com paginação | `[ATUAL]` | `GET /transactions` | ✅ `/patrimonio/razao` |

**O extrato da B3** traz compra e venda como "Transferência - Liquidação", na data da liquidação: a
operação entra no pregão de dois pregões antes, pelo calendário de `core/pregao.py`. JCP, dividendo e
rendimento entram nos proventos recebidos com o valor líquido. "Atualização" não é lançamento: confere
a quantidade da B3 contra o razão e avisa se não bater. Linha que casa com lançamento existente (mesmo
ativo, tipo e quantidade, até dois pregões e 2% de preço) vem desmarcada. **Não cobre:** custos de
corretagem e emolumentos, que o extrato não tem; desdobramento, grupamento, bonificação e
transferência entre corretoras, que ficam de fora com aviso; renda fixa.

**O que o IR cobre:** swing trade de ações, BDRs, ETFs (15%) e FIIs (20%), com compensação de
prejuízo e isenção mensal; day trade a 20%, apurado à parte, com IRRF de 1% e premissa de
corretora única. **O que não cobre:** emissão de DARF, informe anual.

---

### Conta, sessão e preferências

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
| Alertas de preço | `[ATUAL]` | `api/alerts.py` — o disparo entra também na caixa de avisos, com ou sem push |
| Notificações push | `[ATUAL]` | `notifications/` |
| Caixa de avisos, com lido e não lido | `[IMPLEMENTADO]` | `services/inbox_service.py` — ✅ `/mes/avisos`, sino com contador ([ADR-027](decisoes/ADR-027-caixa-de-avisos-guardada.md)) |
| Onboarding derivado | `[IMPLEMENTADO]` | `api/onboarding.py` — ✅ `/voce/comecar` |
| Telemetria com dicionário fechado | `[ATUAL]` | `core/events.py` — o aplicativo envia por `mobile/lib/core/product_events.dart`, conferido contra o catálogo |
| Rotas de administrador | `[IMPLEMENTADO]` | `require_admin` |
| Rota pública sem titular | `[IMPLEMENTADO]` | `GET /public/asset/{ticker}` |
| Páginas jurídicas (`/termos`, `/privacidade`, `/aviso-cvm`) | `[ATUAL]` | `api/legal.py` |
| Backup lógico: exportar, restaurar, reaplicar exclusões | `[IMPLEMENTADO]` | `backend/app/backup.py` — runbook em [07-OPERACAO](07-OPERACAO.md); roda à mão, sem agendamento nem backup automático — risco aceito em 2026-10-12 |

**Não existe senha no sistema.** O login é Google (e Apple, quando o botão chegar). Não há "esqueci minha senha"
porque não há senha.

---

### Monetização do app

Nada cobra dinheiro hoje. A cerca de plano está **desligada** (`ENTITLEMENTS_ENABLED=false`).

| Funcionalidade | Estado | Observação |
|---|---|---|
| Cerca de plano | `[IMPLEMENTADO]` | Desligada. Nunca exercitada |
| Trial de 14 dias na primeira posição salva | `[IMPLEMENTADO]` | Ver [ADR-009](decisoes/ADR-009-trial-e-gratuidade.md) |
| Indicação com crédito | `[IMPLEMENTADO]` | Nunca usada |
| Cobrança (`backend/app/payments/`, `api/billing.py`) | `[IMPLEMENTADO]` | Só `FakeProvider`, sem tela. Será refeito para RevenueCat, e o que existe não será aproveitado — [ADR-008](decisoes/ADR-008-monetizacao-por-loja.md) |
| RevenueCat | `[PLANEJADO]` | Decidido, não iniciado |

---

### Dados de mercado no app

| Fonte | Estado | Fornece |
|---|---|---|
| Leitura de mercado pela API de dados | `[ATUAL]` | `collectors/mercado.py` — `/v1/ativos`, `/v1/retratos` em lotes de 50, cotações e proventos (sem `cvm_estimado`); `collectors/juro_real.py` — `/v1/tesouro`, para a taxa de ação. Chave do plano `interno`, pela rede privada |
| BCB SGS, direto | `[ATUAL]` | CDI, Selic, IPCA e a Selic mensal (4189), lidos pelo backend no BCB, sem passar pela base (`collectors/rates.py`) |

Proteções ativas: disjuntor por fonte, cache com idade, faixa de plausibilidade, coleta em lote,
cache que vence na carga da base. Detalhes em [app/arquitetura](app/arquitetura.md).

### `[SEM CLIENTE]`

| Rota | Onde vive | Observação |
|---|---|---|
| `GET /whats-new` | `api/whats_new.py` | Substituída pela caixa de avisos ([ADR-027](decisoes/ADR-027-caixa-de-avisos-guardada.md)); o app não a chama desde 2026-10-18 |
| `GET /activity` | `api/transactions.py` | Idem: "O que aconteceu" virou redirecionamento para `/mes/avisos` |

---

## Base de mercado

O que o `data-job/` coleta e entrega no schema `mercado`. Como cada dado é tratado:
[base/](base/README.md).

| Fonte ou peça | Estado | O quê |
|---|---|---|
| Base de mercado própria (`postgres-mercado`, pelo `data-job/`) | `[ATUAL]` | Preço de fechamento, fundamentos, proventos, histórico de ações, FIIs, BDRs, ETFs. Substituiu a BRAPI em 2026-10-12 ([ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)) |
| Serviço `data-job` | `[ATUAL]` | Cron `0 2 * * 2-6` (UTC, 23h de Brasília) no Railway; arquivo bruto guardado no volume `/bruto`; cada rodada registrada em `mercado.rodada` — [base/](base/README.md), [07-OPERACAO](07-OPERACAO.md) |
| B3 COTAHIST, pelo `data-job/` | `[ATUAL]` | Cotação diária bruta do mercado à vista, de 2005 em diante, no `postgres-mercado` de produção, atualizada por cron depois de cada pregão. O backend lê por `ativo_hoje` e `mercado.cotacao`; a pesquisa e o painel, direto — [base/](base/README.md) |
| CVM cadastro e FCA, e emissores da B3, pelo `data-job/` | `[ATUAL]` | Empresa por CNPJ e a ligação do código de emissor do ISIN ao CNPJ, com o método. O backend lê nome, setor e CNPJ por `ativo_hoje`; a pesquisa e o painel, direto |
| CVM DFP e ITR, pelo `data-job/` | `[ATUAL]` | Balanço, resultado e fluxo de caixa de 2010 em diante, por documento, versão e data de entrega: 6,7 milhões de linhas do exercício corrente, consolidadas no `postgres-mercado`. O backend lê por `fundamento_app`; a pesquisa, pelas visões de fundamento |
| BCB SGS, pelo `data-job/` | `[IMPLEMENTADO]` | CDI e Selic diários, meta da Selic e IPCA mensal de 2005 em diante, e a Selic mensal (SGS 4189) desde 2000, no `postgres-mercado`. Lido pela pesquisa; o backend segue lendo o BCB por conta própria (`backend/app/collectors/rates.py`) |
| Visões de fundamento no `postgres-mercado` | `[ATUAL]` | Receita, EBIT, lucro, patrimônio, caixa e dívida por documento, sobre as demonstrações brutas — [base/](base/README.md). O backend lê o recorte `fundamento_app`; a pesquisa e o painel, as visões inteiras |
| Proventos, eventos em ações e série ajustada, pelo `data-job/` | `[ATUAL]` | Da B3, por emissor, toda sexta, com cada parcela na sua data de pagamento; eventos conferidos pelo preço na medida do tamanho deles ([ADR-026](decisoes/ADR-026-confirmacao-do-evento-pelo-tamanho.md)), e o que falta na B3 inferido com preço e prova da CVM — composição do capital, FRE e IPE para ações, cotas do informe mensal para FII; `mercado.serie_papel` com preço ajustado, retorno total e saltos sem explicação marcados — acima de 50% ou perto de um fator comum, e só o evento que ajustou a série apaga a marca; FIIs, ETFs e BDRs em `mercado.serie_fundo`, com eventos completos, rendimentos recentes da B3 desde out/2025 (12 meses antes da primeira coleta) e, para FII, rendimento e amortização dos avisos do FundosNet desde nov/2016, e o mês sem aviso nem B3 estimado pelo informe mensal da CVM; PTAX e preços e taxas do Tesouro Direto desde 2005. O backend lê `mercado.provento`, sem a origem `cvm_estimado`; o Tesouro IPCA+ mais longo, para a taxa de ação; série ajustada, PTAX e o resto do Tesouro, só a pesquisa e o painel |
| Capital social do FRE, pelo `data-job/` | `[ATUAL]` | Quantidade de ações integralizadas por data de aprovação, de 2010 em diante, para o que a composição do capital não cobre (antes de 2020). Entra no valor de mercado do app, pela quantidade de ações de `ativo_hoje`, e como prova do número de ações na inferência de eventos |

---

## API de dados

| Item | Estado | O quê |
|---|---|---|
| API de dados (`fiance-dados/`) | `[IMPLEMENTADO]` | Contas por convite e, com a cobrança aberta, pela assinatura no portal ([ADR-031](decisoes/ADR-031-assinatura-cria-a-conta.md)), chaves com hash, Minha conta por e-mail e senha ([ADR-036](decisoes/ADR-036-conta-entra-com-email-e-senha.md)), planos com limite por minuto e por dia, histórico por plano, uso por chave e por dia, rotas `/v1` de ativos, cotação, série ajustada, proventos, eventos, demonstrações como se sabia na data, informe de FII, BCB e Tesouro; administração em `/admin`, portal em `/` e console em `/console`, com a fumaça de cada plano. Planos Essencial e Pro, sem gratuito e sem exportação da base; cobrança pelo Asaas ligada em produção, usada só pelo autor, com estorno que recua o acesso e conferência do Asaas a cada seis horas — [ADR-024](decisoes/ADR-024-api-de-dados.md), [ADR-025](decisoes/ADR-025-cobranca-da-api-de-dados.md), [ADR-030](decisoes/ADR-030-sem-exportacao-dois-planos.md), [ADR-034](decisoes/ADR-034-cobranca-ligada-e-conferida.md) |

O que cada plano libera, e o que ainda não tem rota, em [dados/](dados/README.md).

---

## Laboratório

| Item | Estado | O quê |
|---|---|---|
| Pesquisa de carteira, em `fiance-trend/backend/` | `[IMPLEMENTADO]` | Uso próprio: motor de simulação mensal com custo e imposto, prova lacrada, registro e relatório HTML; 8 variações testadas e busca encerrada sem vantagem investível — [pesquisa/pesquisa](pesquisa/estudos/pesquisa.md). Ranking de tendência: 6 variações, 3 em ações e 3 em FIIs, nenhuma passou no estudo — o ranking não informa — [pesquisa/ranking](pesquisa/estudos/ranking.md) |
| Painel `fiance-trend` (API no `fiance-trend/backend`, front no `fiance-trend/frontend`) | `[IMPLEMENTADO]` | Caminho, coleta, ativos de todas as classes (retorno total e preço, com período e zoom), dólar e Tesouro, estudos, ranking, pesquisa e documentos, com senha, no serviço `fiance-trend` do Railway |
| Alertas de coleta no painel | `[IMPLEMENTADO]` | Falha de etapa na última rodada (`mercado.rodada`), rodada parada há mais de 80 h ou sem terminar, cotação com mais de 2 dias úteis sem pregão novo — `fiance-trend/backend/api/alertas.py` |
| Validação da base contra a brapi, em `fiance-trend/backend/` | `[IMPLEMENTADO]` | Uso próprio: eventos, preço do último ano e proventos comparados com uma segunda fonte, que só aponta; erro nosso é o que a fonte primária confirma. Executada e revalidada em 2026-10-18: eventos que batem de 426 para 470 depois das correções — [pesquisa/validacao-brapi](pesquisa/estudos/validacao-brapi.md) |
| Calibração do preço justo, em `fiance-trend/backend/` | `[IMPLEMENTADO]` | Uso próprio: o veredito do app, com só o que se sabia na data, contra o retorno dos 12 meses seguintes. Encerrada em 2026-10-12: de 2011 a 2017, o veredito não ordenou o retorno — [pesquisa/calibracao](pesquisa/estudos/calibracao.md). Refeita em 2026-10-19 com a taxa da ADR-028: a ordem aparece, sem força — [pesquisa/calibracao-com-a-taxa-nova](pesquisa/estudos/calibracao-com-a-taxa-nova.md) |
| Estudos de 2026-10-19, em `fiance-trend/backend/` | `[IMPLEMENTADO]` | Uso próprio, um comando cada: distribuição do veredito por taxa, sem olhar retorno ([pesquisa/taxa-de-desconto](pesquisa/estudos/taxa-de-desconto.md)); filtro de tendência na validação, não confirmado ([pesquisa/filtro-de-risco](pesquisa/estudos/filtro-de-risco.md)); custo de troca por Corwin-Schultz, que mediu volatilidade e não spread ([pesquisa/custo-de-troca](pesquisa/estudos/custo-de-troca.md)) |

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

---

## Resumo por estado

Contado nas tabelas deste arquivo em 2026-10-21, uma linha por item.

| Estado | Linhas |
|---|---|
| `[ATUAL]` | 51 |
| `[IMPLEMENTADO]` | 39 |
| `[DESCONHECIDO]` | 1 — iOS |
| `[SEM CLIENTE]` | 2 — sobras da caixa de avisos |
| `[PLANEJADO]` | 1 aqui; o resto em [05-FUTURO](05-FUTURO.md) |
| `[ABANDONADO]` | 14 |

O número que importa é o `[IMPLEMENTADO]`: o que existe e ninguém exercita com dado real, porque não
há aplicativo em loja nem cliente pagante da API.
