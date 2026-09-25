# Auditoria da especificação do preço justo

> ## ⏳ DOCUMENTO TEMPORÁRIO
>
> **Critério de morte:** quando os 18 itens estiverem riscados, **apague este arquivo**, remova a
> linha do índice em [README](../README.md) e a subseção correspondente em
> [10-PROBLEMAS](../10-PROBLEMAS.md).
>
> Ele existe para que o fluxo introduzido pela [ADR-014](../decisoes/ADR-014-um-modelo-por-classe.md),
> que vai da classe do ativo à etiqueta, tenha os seus defeitos de especificação listados num lugar
> só, e não numa conversa.

Levantado em **2026-09-25**, sobre o commit `53a6796` e o fluxo que [04-CALCULOS](../04-CALCULOS.md)
desenha na seção *Veredito*. A pergunta não foi qual metodologia é melhor. Foi se as regras
existentes são coerentes, determinísticas, completas e implementáveis sem interpretação. Cada item
foi conferido contra o código. Onde a resposta dependia de comportamento, o motor foi executado.

**Ao fechar um item, risque-o com a data**, como em [PARIDADE-WEB-APP](PARIDADE-WEB-APP.md). A
numeração não muda, porque ela é referência daqui para fora.

---

## Como ler

| Campo | O que responde |
|---|---|
| **Severidade** | `bloqueador` · `crítico` · `atenção` · `latente` (defeito sem caminho que chegue a ele hoje) · `documentação` |
| **Natureza** | `incoerência`: a regra contradiz outra regra do mesmo modelo · `lacuna`: um estado sem saída correta · `ambiguidade`: o diagrama permite duas leituras · `nomenclatura` · `metodológico`: escolha, não erro |
| **Lote** | Em que lote de ataque o item entra (ver *Os quatro lotes*) |

Uma escolha metodológica não é tratada como erro. São escolhas, e ficam fora deste inventário:

- o prêmio de 5 pontos;
- o g_T de 4,5%;
- o teto de 20% no crescimento;
- o juro real por subtração;
- o choque de ±1 ponto;
- a tolerância de 30% e a largura de 1,5×.

A calibração empírica de todos eles é o item A8 de [10-PROBLEMAS](../10-PROBLEMAS.md).

---

## O que está correto

Para que ninguém refaça essa verificação:

- **Nenhum ramo divide por zero nem tem Gordon inválido.** A guarda `d − 1 ponto > g_T` de
  `_earnings_lens` cobre o valor central, o piso e o teto. Na confirmação, `d − g_c ≥ 1%`. No FII,
  `y ≥ 6%`, logo `y − 1 ponto ≥ 5%`.
- **A fronteira de 4,5% é exata.** Em ponto flutuante, `0.03 + 0.015 == 0.045`.
- **A margem é simétrica em escala multiplicativa.** `+30%` quer dizer preço ≤ 0,7 × piso;
  `−30%` quer dizer preço ≥ teto ÷ 0,7.
- **Qualidade, confiança e etiqueta são determinísticas**, com precedência explícita: se houver
  alguma razão de frágil, a qualidade é frágil; senão, se houver alguma de ampla, é ampla; senão, é
  firme.
- **O técnico não entra na leitura de valor.** Tendência e RSI ficam de fora da margem, da etiqueta e
  da confiança (`backend/app/analysis/decision.py::_context_reasons`). Fora dela, eles entram no
  score, que é o item R-016.

---

## O que foi medido

Todas as medições usam LPA = 1 e d = 15%, calculadas com `earnings_value` do próprio código
(`backend/app/analysis/fair_price.py`). Os valores estão em reais por ação e podem ser repetidos.

### O piso "sem crescimento" retém lucro sem crescer

Colunas "hoje": o piso usa g = 0, mas mantém a fração distribuível `δ = 1 − g/ROE`.

Colunas "coerente": sem crescimento, a empresa distribui tudo (`δ = 1`). O piso é o menor dos dois
cenários a d + 1 ponto, e o teto é o maior dos dois a d − 1 ponto.

| ROE | Payout | g | Central | Piso hoje | Teto hoje | Razão hoje | Piso coerente | Teto coerente | Razão coerente |
|---|---|---|---|---|---|---|---|---|---|
| 15% | 0% | 15,0% | 6,97 | 3,03 | 8,04 | 2,66 | 6,09 | 8,04 | 1,32 |
| 15% | 50% | 7,5% | 7,02 | 4,67 | 7,84 | 1,68 | 6,30 | 7,84 | 1,24 |
| 20% | 40% | 12,0% | 8,61 | 4,66 | 9,70 | 2,08 | 6,63 | 9,70 | 1,46 |
| 30% | 30% | 20,0% | 12,36 | 4,77 | 14,03 | 2,94 | 6,95 | 14,03 | 2,02 |
| 30% | 80% | 6,0% | 8,78 | 6,30 | 9,73 | 1,55 | 6,95 | 9,73 | 1,40 |
| 10% | 20% | 8,0% | 4,83 | 3,03 | 5,47 | 1,80 | 4,31 | 6,58 | 1,53 |
| 10% | 60% | 4,0% | 5,55 | 4,34 | 6,12 | 1,41 | 5,08 | 6,58 | 1,29 |
| 6% | 30% | 4,2% | 2,65 | 2,06 | 2,91 | 1,41 | 2,43 | 4,86 | 2,00 |

Com ROE 15% e sem dividendo, a fração distribuível é zero. O fluxo explícito do piso é nulo, e o
piso de hoje é só o valor terminal.

Quando ROE < d, crescer destrói valor. Nesse caso, o cenário sem crescimento **coerente** fica
**acima** do teto de hoje (ROE 6%: 4,36 contra 2,91). A garantia atual de que o piso nunca passa do
teto só existe por causa da incoerência.

### A confirmação da ação diverge por construção

A confirmação `D(1+g_c)/(d−g_c)` distribui, para sempre, a fração observada `D/LPA`. O terminal do
principal distribui `1 − g_T/ROE`. As duas frações só coincidem quando g = g_T:

| ROE | Payout | Confirmação | Faixa hoje | Distância | Qualidade |
|---|---|---|---|---|---|
| 30% | 30% | 2,99 | 4,77 – 14,03 | 37% abaixo do piso | frágil |
| 6% | 90% | 6,29 | 4,03 – 4,61 | 36% acima do teto | frágil |
| 10% | 60% | 5,67 | 4,34 – 6,12 | dentro | firme |

Nos dois primeiros casos, nenhum dado discorda. A qualidade vira frágil porque as duas fórmulas
embutem frações distribuídas diferentes.

### Dividendo que não chegou vira crescimento máximo

Quando a chamada falha, `_brapi_raw` devolve `{}`, o mesmo retorno de uma resposta sem resultado.
`_dividends_brapi` transforma isso em `[]` (`backend/app/collectors/universal.py`). Com a lista
vazia, `_earnings_lens` calcula o payout como `(D ou 0) ÷ LPA = 0`, e o crescimento vira
`g = mín(ROE; 20%)`, que é o máximo possível. `fetch_dividends` não guarda lista vazia em cache,
então a chamada seguinte tenta de novo, mas a avaliação daquela rodada já saiu.

---

## Os quatro lotes

| Lote | O que é | Itens | Natureza |
|---|---|---|---|
| **A** | Estados e guardas | R-003, R-006, R-007, R-008, R-009, R-011, R-012, R-013, R-017 | Correção direta, sem ADR |
| **B** | Ausência não vira zero | R-004, R-005, R-010 | Correção direta; toca o coletor |
| **C** | A faixa coerente | R-001, R-002, R-014, R-018 | Emenda à ADR-014 antes de código |
| **D** | Contrato e produto | R-015, R-016 | Contrato regravado; decisão de produto |

**Ordem sugerida: A → B → C → D.** A e B não dependem de metodologia e restauram invariantes do
[CLAUDE.md](../../CLAUDE.md). C muda o que a faixa mede em quase toda a base de ações. R-002 e R-014
só se decidem **depois** de C1, porque o piso novo já muda a concordância e a largura.

**Restrição de todos os lotes: o app mostra o código cru de um motivo que ele não conhece.**
`methodStatusLabel` (`mobile/lib/core/score_ruler.dart`) devolve o próprio código no `default`. Como
o cliente chega pela loja, um status novo, como `dado_inconsistente`, aparece como texto técnico nas
versões antigas. Por isso, os lotes A e B **reaproveitam `sem_dado` e `inaplicavel`** e mudam só a
nota. O mesmo mapa ainda traduz `destoa_dos_demais` e `fora_da_faixa`, que o backend não produz
mais, e `basisLabel` ainda trata `trend`: vocabulário sem produtor.

---

## Lote A · Estados e guardas

### R-007 · ~~Classe desconhecida cai no modelo de ação~~ — **corrigido em 2026-09-25**

Severidade **crítico** · Natureza `lacuna` · Lote A

O diagrama tem quatro saídas para a classe. O código tem três: `fair_price_from_inputs` manda para o
modelo de ação tudo o que não é `fii`, `etf` ou `bdr`. `renda_fixa`, que existe em
`backend/app/models/enums.py`, ou uma classe nova, recebe desconto de lucros.

Nenhum caminho atual passa `renda_fixa`, porque `_fetch_sync` só coleta as quatro classes. O
defeito é de contrato, e o custo de correção é quase zero.

- **Ataque:** trocar `elif asset_type not in _NO_METHOD_NOTE` por `elif asset_type == "br_stock"`.
  Em `_no_band_methods`, usar uma nota padrão para classe fora do mapa: "esta classe não tem método
  de preço justo". O status continua `inaplicavel`.
- **Teste:** `renda_fixa` e `"xyz"` saem sem faixa, com todos os métodos `inaplicavel` e a nota
  preenchida.

### R-011 · ~~LPA positivo com lucro de 12 meses negativo produz faixa~~ — **corrigido em 2026-09-25**

Severidade atenção · Natureza `lacuna` · Lote A

Quando os sinais divergem, `normalized_eps` devolve o LPA bruto e marca instável. Um dado
contraditório vira faixa frágil, em vez de silêncio com motivo.

- **Ataque:** `NormalizedEarnings` ganha `inconsistent=True` e LPA_n nulo. `_earnings_lens`
  responde `sem_dado` com a nota "o LPA e o lucro dos últimos 12 meses têm sinais opostos". LPA = 0
  continua em `lucro_negativo`.
- **Teste:** `normalized_eps(1.0, [10, 10, 10], -5)` cai em `sem_dado` com essa nota.

### R-017 · ~~A janela de anos usa UTC~~ — **corrigido em 2026-09-25**

Severidade atenção · Natureza `lacuna` · Lote A

`_now()` usa `datetime.now(UTC)`. Entre 21h e 24h (BRT) de 31/12, o "último ano completo" já é o
ano seguinte.

- **Ataque:** `_now()` passa a devolver `now_brt()` de `backend/app/core/brt.py`. `analysis/` pode
  importar `core/`; o invariante proíbe só `storage/`.
- **Teste:** com referência em 31/12/2026 às 22h (BRT), o último ano completo é 2025.

### R-006 · ~~Faixa com preço ausente sai como "Sem preço justo"~~ — **corrigido em 2026-09-25**

Severidade **latente** · Natureza `lacuna` · Lote A

Com faixa e sem preço, `decide()` devolve UNKNOWN "Sem preço justo", com `basis=band` e confiança de
0,45 ou 0,70. O rótulo nega um preço justo que existe.

Hoje nenhum caminho chega aqui: `_fetch_brapi` descarta o snapshot sem preço, e os três chamadores
de `decide()` passam o preço do snapshot.

- **Ataque:** `confidence_from_evidence` devolve 0 quando `fair.margin_of_safety is None`. Com faixa
  e sem preço, a razão passa a ser "Sem cotação: a faixa é de R$ X a R$ Y, e não há preço para
  comparar". Antes de trocar o rótulo, conferir se o app mostra o `label` da API ou traduz o
  `verdict`.
- **Teste:** `decide(fair_com_faixa, None, None)` dá confiança 0.

### R-003 · ~~O diagrama exige 3 exercícios e depois classifica o lucro curto~~ — **corrigido em 2026-09-25**

Severidade atenção · Natureza `ambiguidade` · Lote A

A pré-condição da ação diz "LPA normalizado de 3 exercícios". A qualidade diz "lucro curto é
frágil". Se a pré-condição valesse, o lucro curto seria inalcançável. O código não exige os 3
exercícios: com menos, usa o LPA bruto e marca frágil.

- **Ataque:** tirar "de 3 exercícios" da pré-condição no diagrama de
  [04-CALCULOS](../04-CALCULOS.md). Sem mudança de código.

### R-008 · ~~Selic zero e `taxa_implausivel` não estão no diagrama~~ — **corrigido em 2026-09-25**

Severidade documentação · Natureza `ambiguidade` · Lote A

`rates_for_valuation` trata Selic = 0 como ausência (`sem_juro`). Entre 0 e 0,5%, `_earnings_lens`
gera `taxa_implausivel`, que o diagrama não tem.

- **Ataque:** acrescentar o nó e o motivo ao diagrama.

### R-009 · ~~A ordem dos motivos difere do diagrama~~ — **corrigido em 2026-09-25**

Severidade documentação · Natureza `ambiguidade` · Lote A

O código testa LPA, juro, ROE e taxa, e registra só o primeiro motivo que falha. O diagrama lista
LPA, ROE e juro. O resultado é o mesmo, mas o motivo exibido depende da ordem.

- **Ataque:** fixar no diagrama a ordem do código.

### R-012 · A margem é arredondada antes do limiar

Severidade documentação · Natureza `lacuna` · Lote A

`margin_of_safety_in_band` arredonda a 4 casas, e `_verdict_from_mos` compara o valor arredondado.
Os preços-gatilho saem da fórmula exata. Com piso de R$ 100, o preço de R$ 70,004 já sai "bem
abaixo", enquanto o gatilho anuncia R$ 70,00. O efeito é de no máximo 0,005 ponto.

- **Ataque:** `verdict_for` recalcula a margem sem arredondar, a partir de preço, piso e teto; o
  campo exibido continua com 4 casas. Vale fazer só se o PR já estiver mexendo em `decide`.

### R-013 · ~~Duas convenções de distância acima do teto~~ — **corrigido em 2026-09-25**

Severidade documentação · Natureza `ambiguidade` · Lote A

`_agreement` divide pelo teto. `margin_of_safety_in_band` divide pelo preço. Os mesmos "30%" têm
sentidos diferentes nas duas regras.

- **Ataque:** documentar as duas convenções em [04-CALCULOS](../04-CALCULOS.md).

---

## Lote B · Ausência não vira zero

### R-005 · Dividendo que não chegou vira payout zero e crescimento máximo

Severidade **crítico** · Natureza `lacuna` · Lote B

Ver a medição acima. Viola "falha de rede não vira ausência". Há um segundo efeito, separado: um
corte baixa o payout e sobe g. O corte age duas vezes, na qualidade e na premissa. Com ROE 15%, D
passando de 0,50 para 0,25 leva o teto de 7,84 para 7,98 e o piso de 4,67 para 3,85.

- **Ataque:**
  1. `_dividends_brapi` devolve `None` quando a chamada falhou e `[]` quando a resposta chegou sem
     proventos. Para distinguir os dois casos, `_brapi_raw` precisa sinalizar a falha, por um
     sentinela, ou reaproveitando `_guardar_raw(base, None)`, que já marca a resposta sem resultado.
  2. `fetch_dividends` degrada como `_degradar` em `backend/app/collectors/rates.py`: cache válido,
     depois cache vencido com `cache.get_with_age`, e só então `None`. A lista vazia também passa a
     ir para o cache.
  3. `compute_fair_price_inputs` aceita `dividends: list | None` e grava `dividends_known`. Sem esse
     dado, `_earnings_lens` responde `sem_dado` com a nota "o histórico de proventos não chegou: sem
     ele não há como separar o que a empresa distribui do que retém".
- **Alcance:** `get_dividends` em `backend/app/repositories/asset_repository.py` e os cinco pontos
  que o chamam: `backend/app/services/asset_service.py`, `backend/app/services/dip_service.py` (duas
  vezes), `backend/app/services/dividend_calendar_service.py` e
  `backend/app/services/opportunity_service.py`. Onde a lista é iterada, `None` precisa de
  tratamento explícito, e não de um `or []` silencioso.
- **Teste:** BRAPI falhando no dividendo, com o snapshot válido, deixa o principal em `sem_dado`, e
  não em g = mín(ROE; 20%). Com o cache vencido presente, sai a faixa normal.
- **Fica como está:** a empresa que de fato não paga continua com g = mín(ROE; 20%). Isso é a
  identidade funcionando, não uma ausência. O efeito duplo do corte vai para a emenda da ADR-014
  (lote C).

### R-004 · "Recorrente" e "3 anos de dividendo" não medem o que dizem

Severidade atenção · Natureza `ambiguidade` · Lote B

`recurring_dividend` aceita só os últimos 12 meses quando não há ano completo: um FII com um
pagamento recebe faixa (frágil). `_complete_years` preenche com zero os anos sem pagamento. Então
`complete_years` mede a extensão da série desde o primeiro pagamento, e não os anos pagos. Uma ação
que pagou 2 vezes em 5 anos passa no filtro de 3 anos da confirmação.

- **Ataque:** `RecurringDividend` e `FairPriceInputs` ganham `paid_years`, o número de anos da
  janela com valor maior que zero. O campo precisa de valor padrão, porque `opportunity_service`
  serializa `fair_inputs`. O filtro de `_stock_confirmation` e o frágil do FII em `_quality` passam
  a usar `paid_years`.
- **Decisão de produto:** o FII só com os 12 meses continua com faixa frágil ou passa a ficar sem
  valor?
- **Efeito:** ações com série falhada perdem a confirmação e passam de firme para ampla.

### R-010 · A taxa e a data de referência não são gravadas

Severidade atenção · Natureza `lacuna` · Lote B

`rates_for_valuation` aceita `bcb_cache_vencido` e avalia com ele. As premissas não gravam a origem,
a idade nem a Selic usada: `selic_pct` existe em `ValuationRates` e é descartado. A data de
referência da janela de dividendos também não fica registrada. Sem isso, não dá para reproduzir o
resultado nem mostrar a idade da taxa.

- **Ataque:** `get_rates` grava `fetched_at`, e `ValuationRates` carrega `source` e `fetched_at`.
  As premissas ganham `rate_source`, `selic_pct`, `rates_age_s` e `reference_date`. `premises` é um
  dicionário, então chaves novas não quebram o `fromJson` do Dart. Na tela, o precedente é a regra
  de `formatAge` para preço.

---

## Lote C · A faixa coerente

Pede uma emenda à [ADR-014](../decisoes/ADR-014-um-modelo-por-classe.md) antes de código, a
atualização de [04-CALCULOS](../04-CALCULOS.md) e a amostra de 2026-09-23 rodada de novo, antes e
depois.

### R-001 · O piso "sem crescimento" retém lucro sem crescer

Severidade **bloqueador** · Natureza `incoerência` · Lote C

Ver a medição acima. O piso contradiz a identidade `g = ROE × retenção`, que o próprio principal
usa. Em vez da incerteza de taxa e crescimento, a faixa mede a penalidade de reter sem crescer. Com
d = 15%, a razão teto/piso fica entre 1,7 e 3,0, e "firme" é quase inalcançável para ação que
cresce.

- **Opção A, recomendada:** calcular dois cenários coerentes em cada taxa. *Sem crescimento* é
  `earnings_value(eps, 1.0, 0.0, d', roe)`; *com crescimento* é
  `earnings_value(eps, δ, g, d', roe)`. Piso é o menor dos dois a d + 1 ponto; teto é o maior dos
  dois a d − 1 ponto. O central não muda. A ordem piso < central < teto continua garantida:
  piso ≤ com(d+1) < com(d) = central < com(d−1) ≤ teto. A asserção de
  `backend/tests/test_fair_price.py` sobrevive.
- **Opção B:** manter os números e renomear o piso para "retém sem crescer", na ADR e no texto da
  premissa. Não há risco numérico, mas a faixa continua medindo a penalidade.
- **Arrastos da opção A:**
  - `value_without_growth` passa a usar δ = 1.
  - `_growth_falsifier`, em `backend/app/analysis/falsifiers.py`, só dispara quando o cenário sem
    crescimento fica abaixo do central; hoje ele pressupõe isso.
  - `_premise_reason`, em `backend/app/analysis/decision.py`, precisa de texto condicional para
    ROE < d: "aqui crescer consome valor".
  - Os testes que fixam valores de faixa mudam. Os de `backend/tests/test_revisao_do_valuation.py`
    são relativos e tendem a sobreviver.
- **Efeito:** em empresas que retêm muito, o piso sobe de 30% a 100%, e mais ativos passam a sair
  "abaixo do preço justo". Quando ROE < d, o teto passa a ser o cenário que distribui tudo, e o
  central fica perto do piso.
- **Validação:** a distribuição por qualidade e por etiqueta na amostra, antes e depois. Os dois
  números vão para a ADR.

### R-002 · A confirmação da ação não é independente

Severidade **crítico** · Natureza `incoerência` · Lote C

Ver a medição acima. `_stock_confirmation` compartilha d e g_c com o principal, e D já entra no
payout do principal. A regra diz "confirmação por outro insumo", e em parte não é. A divergência
estrutural rebaixa para frágil sem que nenhum dado discorde.

**Decidir só depois de R-001.** Com o piso coerente, ROE 30% e payout 30% continuam longe (2,99
contra piso de 6,95). ROE 6% e payout 90% passam de longe para perto (6,29 contra teto de 4,86, a
29%).

- **Opção A:** na ação, confirmação longe rebaixa para ampla, não para frágil. É uma condição em
  `_quality`, restrita a `principal == PRINCIPAL_EARNINGS`.
- **Opção B:** manter a regra e declarar na ADR que a divergência é esperada quando g é diferente
  de g_T.
- **Fora de escopo:** reformular a confirmação para usar a mesma fração distribuída na
  perpetuidade. Seria outro método.

### R-014 · A regra de largura não discrimina

Severidade atenção · Natureza `incoerência` · Lote C

No FII, a razão teto/piso é `(y + 1)/(y − 1)`, no máximo 1,4 com y = 6%: a regra de 1,5× nunca
dispara. Na ação, ela dispara quase sempre, em parte por causa de R-001.

- **Ataque:** em `_quality`, restringir a regra a `principal == PRINCIPAL_EARNINGS`. O comportamento
  não muda, mas a regra fica explícita. Medir de novo o limiar de 1,5× depois de R-001.

### R-018 · D ÷ y supõe distribuição que acompanha a inflação

Severidade documentação · Natureza `metodológico` · Lote C

y é juro real (`máx(Selic − meta; 3%) + 3 pontos`) e D é nominal. O quociente só é coerente se a
distribuição crescer com a inflação. A premissa existe e não está escrita. Ela conversa com o item
A7 (FII de papel) de [10-PROBLEMAS](../10-PROBLEMAS.md).

- **Ataque:** declarar a premissa na emenda à ADR-014, junto com o efeito duplo do corte de R-005.

---

## Lote D · Contrato e produto

### R-015 · Nomes de campo que não dizem o que guardam

Severidade documentação · Natureza `nomenclatura` · Lote D

Em `FairPriceResult`:

- `bazin` guarda o Gordon de dividendos na ação e D/y no FII. Nenhum dos dois é Bazin; o Bazin de
  verdade é `personal_ceiling`.
- `consensus` guarda o valor central do principal.
- `avg_dividend_5y` e `dy_5y` guardam o recorrente, isto é, mín(média; último).

Quem consome o campo pelo nome o interpreta errado.

- **Ataque:** acrescentar `principal_value`, `confirmation_value`, `dividend_recurring` e
  `dividend_yield_recurring`, mantendo os nomes antigos como alias, em
  `backend/app/models/analysis.py`. O `fromJson` de `mobile/lib/core/models.dart` lê o campo novo
  como opcional, com fallback para o antigo, e `mobile/lib/core/glossary.dart` acompanha. O contrato
  é regravado no mesmo commit (`python -m tests.contrato_das_rotas`). Os aliases saem depois que a
  versão da loja que lê os campos novos estiver em uso.

### R-016 · O técnico pesa no score

Severidade atenção · Natureza `ambiguidade` · Lote D

`_score_technical`, em `backend/app/analysis/scoring.py`, põe RSI e tendência no score. O score
alimenta `is_highlight`, a ordenação de Descobrir e as faixas "Evitar agora" e "Excelente entrada"
(`backend/app/analysis/score_ruler.py`). Sem faixa, os pesos se redistribuem pelas dimensões que
sobram, e ETF e BDR ganham score sem preço justo.

A etiqueta cumpre "análise técnica não decide". O ranking e o destaque, não. E "Evitar agora" é uma
ordem, não uma posição.

- **Opção A:** tirar a dimensão `technical` dos pesos de ação e deixar o score nulo quando não há
  faixa. As faixas de score mudam nas duas plataformas, primeiro no Python
  (`mobile/lib/core/design_tokens.dart`).
- **Opção B:** escrever uma ADR dizendo que o score é ranking, e não leitura de valor, e revisar os
  rótulos à luz de "a etiqueta descreve posição".
- **Antes de decidir:** medir na amostra quantos ativos mudam de faixa de score.
