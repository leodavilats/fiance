# Preço justo

Espelho auditado do código, que é a fonte de verdade: fórmula divergente é bug deste documento.
`backend/app/analysis/fair_price.py`

---

Cada classe tem **um modelo principal**, a faixa é a sensibilidade dele às premissas, e **outro
insumo confirma ou não**. Não há mínimo e máximo de métodos que medem coisas diferentes, nem média
deles. Ver [ADR-014](../../decisoes/ADR-014-um-modelo-por-classe.md). `analysis/fair_price.py`

## Por classe de ativo

| Classe | Principal | Confirmação | Por quê |
|---|---|---|---|
| Ação | lucro distribuível descontado | dividendo recorrente | o lucro é o que gera valor; o dividendo diz se ele vira caixa |
| FII | distribuição recorrente ÷ yield exigido | VPA | a lei obriga a distribuir 95% do resultado de caixa: a distribuição **é** o fluxo |
| BDR | **nenhum** | — | a única taxa disponível é em reais, e o lucro não é |
| ETF | **nenhum** | — | o preço acompanha o valor do que o fundo carrega |
| Qualquer outra | **nenhum** | — | não há modelo declarado para ela; o modelo de ação só vale para `br_stock` |

## A taxa

```
d_ação = juro real do Tesouro IPCA+ mais longo à venda + meta de inflação (3%) + 5 pontos
g_T    = meta de inflação (3%) + 1,5% de crescimento real       = 4,5%
y_FII  = máx(Selic média de 10 anos − meta de inflação, 3%) + 3 pontos
```

**A taxa de ação** é a taxa de venda do Tesouro IPCA+ (sem juros semestrais) de vencimento mais longo
à venda no último dia da base, lida pela `fiance-dados` (`collectors/juro_real.py`), mais a meta de
inflação e o prêmio ([ADR-028](../../decisoes/ADR-028-taxa-de-acao-pelo-juro-real-do-tesouro.md)). **Custo
de capital é taxa de longo prazo**, e o juro real que o mercado cobra hoje por prazo longo é o que
mais se aproxima dele; a Selic média de 10 anos + 5, a taxa de antes, punha 88% das ações acima da
faixa na mediana de 2011 a 2025 ([pesquisa/taxa-de-desconto](../../pesquisa/estudos/taxa-de-desconto.md)). **Sem
título à venda, ou com a base fora do ar e sem cache, a ação fica sem juro** e o método se cala: não
há volta para a Selic. As premissas de ação trazem `rate_base: ipca_longo`, a taxa do título
(`real_rate_pct`) e o vencimento dele (`real_rate_maturity`), e não trazem `selic_pct`.

**O yield de FII** segue saindo da Selic média de 10 anos, da série mensal 4189 do SGS
(`collectors/rates.py::_selic_media`). Sem a série, entra a Selic do dia, e `premises.rate_base` diz
qual base foi usada. As premissas
também carregam a origem da taxa (`rate_source`, que pode ser `bcb_cache_vencido` ou, na ação,
`base_cache_vencido`), a Selic usada no FII
(`selic_pct`), o momento da leitura (`rates_as_of`) e a data de referência da janela de dividendos
(`reference_date`). **Com juros
estimados (`source: estimativa`), o FII não tem avaliação** — `analysis/fair_price.py::rates_for_valuation`.
Selic zero, na média e no dia, conta como ausência de juro.

## O modelo de ação

```
V(d, g) = Σ_{t=1..5} LPA_n·(1+g)^t·q ÷ (1+d)^t
        + LPA_n·(1+g)^5·(1+g_T)·(1 − g_T/ROE) ÷ ((d − g_T)·(1+d)^5)

q = 1 − g/ROE          (o que pode ser distribuído sem deixar de crescer)
g = mín(ROE × (1 − payout), 20%)
payout = dividendo recorrente ÷ LPA_n, entre 0 e 1
```

`analysis/fair_price.py::earnings_value` e `_earnings_lens`.

- **Só se desconta o que pode ser distribuído.** Somar o lucro inteiro e ainda crescer por
  reinvestimento contava duas vezes o lucro retido. Em regime estável esta é a mesma equação do P/VP
  justificado, `VPA·(ROE − g) ÷ (d − g)` — banco sai avaliado pelo mesmo modelo.
- **Crescer só cria valor quando o ROE passa da taxa.** Com ROE perto de `d`, o valor quase não muda
  com o payout — é o comportamento correto.
- **O terminal sai da mesma taxa**, por Gordon. O P/L terminal implícito cai quando o juro sobe.
- **LPA normalizado** (`normalized_eps`): média dos 3 últimos exercícios, escalada pela razão entre
  lucros — `LPA × média(lucro anual) ÷ lucro de 12 meses`. Em unit, lucro ÷ número de ações não é o
  LPA da unit. Com menos de 3 exercícios, usa o LPA de 12 meses e a qualidade sai frágil. Com o
  LPA e o lucro-base de sinais opostos, ou lucro-base zero, **não há LPA normalizado**: um dos dois
  está errado, e o principal cala com `sem_dado`.
- **ROE normalizado** (`normalized_roe`): média do lucro sobre média do patrimônio, nos mesmos 3
  exercícios alinhados por data. Sem série, o ROE informado. Patrimônio médio negativo: sem ROE.

## O modelo de FII

```
V = distribuição recorrente ÷ y_FII
```

`analysis/fair_price.py::_dividend_lens`.

**Premissa implícita:** `y_FII` é juro real, e a distribuição é nominal. O quociente só é coerente se
a distribuição crescer com a inflação, como o aluguel de um FII de tijolo.

**FII de papel exige yield nominal:** `y_FII + meta de inflação`. A distribuição dele já traz a
correção monetária dos recebíveis, e o principal não cresce com ela. A leitura de papel vale para a
lista de referência em `analysis/fii_segments.py::PAPER_FIIS`, com data de revisão, e
`premises.fii_segment` diz qual foi usada ([ADR-019](../../decisoes/ADR-019-fii-de-papel-exige-yield-nominal.md)). **A CVM informa segmento e mandato**, e a
base os guarda em `mercado.fii_mensal`, mas o código ainda usa a lista.

## O dividendo recorrente

```
cada ano completo da janela de 5 anos limitado a 2 × a mediana dos outros
média   = média desses anos
último  = máx(último ano completo, últimos 12 meses)
recorrente = mín(média, último)
corte   = último < 50% da média
```

`analysis/fair_price.py::recurring_dividend`. Contínuo — 2,9× e 3,1× a mediana dão o mesmo
resultado. **Pega corte**, que é a armadilha de dividendo. Não apaga uma mudança de política para
cima, como fazia a troca da série inteira pela mediana. **Na ação, o corte age duas vezes:**
rebaixa a qualidade para frágil e, por baixar o payout, aumenta o crescimento que o modelo atribui
ao lucro retido. Ano sem pagamento dentro da série conta como zero; sem nenhum ano completo, vale
a soma dos últimos 12 meses. O ano civil é o brasileiro (`core/brt.py`): às 22h de 31 de dezembro,
o ano ainda não fechou.

**Provento que não chegou não é provento zero.** Quando a fonte falha e não há cache, nem vencido, a
coleta devolve `None`, e não lista vazia (`collectors/universal.py::fetch_dividends`). O principal
cala com `sem_dado`: sem o histórico, o payout é desconhecido, e tratá-lo como zero poria o
crescimento no máximo. A empresa que de fato não paga chega com lista vazia e cresce pelo ROE.

## A faixa

```
com(d') = V(d', g, q = 1 − g/ROE)                o crescimento que o lucro retido sustenta
sem(d') = V(d', 0, q = 1)                        sem crescer, distribuindo todo o lucro

piso    = mín(com(d + 1 ponto), sem(d + 1 ponto))    FII: D ÷ (y + 1 ponto)
teto    = máx(com(d − 1 ponto), sem(d − 1 ponto))    FII: D ÷ (y − 1 ponto)
central = com(d)                                     FII: D ÷ y
posição = (preço − piso) ÷ (teto − piso), quando o preço está dentro
```

**Sem crescimento é sem retenção**, pela mesma identidade `g = ROE × retenção` do modelo
([ADR-015](../../decisoes/ADR-015-a-faixa-cobre-os-dois-cenarios.md)). Quando o ROE não paga a taxa, crescer consome valor e `sem` passa de `com`. Por isso a faixa é o
envelope dos dois cenários, e não um deles em cada ponta. `premises.growth_creates_value` diz qual
é o caso, e a razão avisa quando crescer consome valor. A ordem `piso < central < teto` vale nos dois
regimes: `piso ≤ com(d+1) < com(d) < com(d−1) ≤ teto`.

É **incerteza real sobre o valor** — o que acontece se a premissa mais discutível errar —, e não a
distância entre métodos com alvos diferentes. `principal_value` carrega o valor central, e não decide
sozinho. `independent_inputs` diz se ele tem confirmação por outro insumo (2) ou não (1).

## A confirmação

| Classe | Leitura | Não se aplica quando |
|---|---|---|
| Ação | `D × (1 + g_c) ÷ (d − g_c)`, com `g_c = mín(g, g_T)` | menos de 3 anos completos **com pagamento**; payout abaixo de 25% |
| FII | VPA | sem VPA |

A concordância é `dentro` da faixa, `fora_ate_30` ou `fora_mais_30`. **A confirmação não define
borda**: ela entra na qualidade.

A distância da concordância se mede contra a borda atravessada: abaixo do piso, `(piso − v) ÷ piso`;
acima do teto, `(v − teto) ÷ teto`. É convenção diferente da margem, que acima do teto divide pelo
preço. Exatamente 30% ainda é `fora_ate_30`.

## Qualidade

| `band_quality` | Quando |
|---|---|
| `fragil` | lucro de menos de 3 exercícios, ou instável (LPA de 12m fora de metade a dobro do normalizado, ou ano com prejuízo); FII com menos de 3 anos completos com distribuição; corte de distribuição; **no FII**, VPA a mais de 30% da faixa |
| `ampla` | sem confirmação; confirmação fora da faixa por até 30%; **na ação**, dividendo a mais de 30% da faixa; **na ação**, teto acima de 1,5× o piso |
| `firme` | nenhum dos anteriores |
| `sem_faixa` | não há modelo principal |

Na ação, o dividendo longe da faixa **alarga, e não derruba**: a confirmação usa a mesma taxa e um
crescimento tirado do principal, e a distância dela é quase função do payout — abaixo de 45%, longe;
de 60% para cima, dentro. No FII, o VPA é insumo independente, e discordar é evidência
([ADR-016](../../decisoes/ADR-016-a-confirmacao-da-acao-alarga-e-nao-derruba.md)).

`quality_reasons` diz, em frase, o que a definiu. `independent_inputs` é 1 ou 2: o insumo do
principal e, se houver, o da confirmação.

## Silêncio com motivo

`methods[]` traz cada leitura com `role` — `principal`, `confirmacao`, `indicador`, `inaplicavel` — e
`status`:

| Estado | Significa |
|---|---|
| `ok` | a leitura existe |
| `inaplicavel` | não descreve esta classe de ativo |
| `sem_dado` | o insumo não veio da fonte |
| `lucro_negativo` | o LPA normalizado é negativo — informação, não ausência |
| `roe_insuficiente` | o ROE não passa do crescimento de longo prazo: crescer consome valor |
| `sem_juro` | não há juro de referência real |
| `pouco_distribuido` | o dividendo não mede a capacidade de quem distribui menos de 25% do lucro |
| `taxa_implausivel` | a taxa menos o choque não passa do crescimento de longo prazo |

Na ação, o motor confere **nesta ordem** — LPA, juro, ROE, taxa, proventos — e grava só o primeiro
motivo que falha (`_earnings_lens`). Empresa em prejuízo e sem juro de referência aparece como
`lucro_negativo`.

## Indicadores que não decidem

`indicators[]`, fora da faixa:

| Indicador | O que é |
|---|---|
| `graham` | `√(22,5 × LPA_n × VPA)`: o preço-limite do critério defensivo, com `passes`. Dentro do próprio filtro ele sempre fica acima do preço — por isso não pode ser borda |
| `preco_teto_pessoal` | `dividendo recorrente ÷ yield que a pessoa declarou`. É meta de renda, não preço justo: mudar a meta muda o teto, e não a faixa |
| `pvp` | preço sobre valor patrimonial |

## Margem de segurança

```
preço < piso          →  margem = (piso − preço) ÷ piso       (a favor)
piso ≤ preço ≤ teto   →  margem = 0                          (não há margem)
preço > teto          →  margem = (teto − preço) ÷ preço      (contra)
```

As duas pontas medem a mesma distância em escala logarítmica: +30% e −30% correspondem ao mesmo
afastamento. `fair_price.py::margin_of_safety_in_band`

O campo exibido tem quatro casas. **A etiqueta compara a margem com nove** (`margin_exact`): com
quatro, um preço a 29,996% do piso já saía "bem abaixo", acima do gatilho que a tela anunciava. Nove
casas tiram o ruído de ponto flutuante, e no preço exato do gatilho a etiqueta já é a nova.

**A margem descreve posição, não antecipa retorno.** Medido em 2026-10-12, com o modelo do app e só o
que se sabia em cada data, nas ações de 2011 a 2017: retorno médio em 12 meses de 4,0% abaixo da
faixa, 5,3% dentro e 3,0% acima; abaixo menos acima, t de −0,09. O veredito não ordenou o retorno
([pesquisa/calibracao](../../pesquisa/estudos/calibracao.md)). Com a taxa da ADR-028, a ordem aparece, mas sem
força: +1,1 ponto, t de 0,18 ([pesquisa/calibracao-com-a-taxa-nova](../../pesquisa/estudos/calibracao-com-a-taxa-nova.md)).

## Premissas

| Premissa | Valor | Configurável |
|---|---|---|
| Base da taxa de ação | Tesouro IPCA+ mais longo à venda + meta de inflação | ❌ |
| Base do yield de FII | Selic média de 10 anos | ❌ |
| Prêmio de ação | 5 pontos | ❌ |
| Meta de inflação | 3% | ❌ |
| Crescimento real de longo prazo | 1,5% | ❌ |
| Teto de crescimento | 20% ao ano | ❌ |
| Anos explícitos | 5 | ❌ |
| Choque de taxa na faixa | ±1 ponto | ❌ |
| Prêmio de FII / piso de juro real | 3 pontos / 3% | ❌ |
| Exercícios do LPA normalizado | 3 | ❌ |
| Limite de ano extraordinário / corte | 2× a mediana dos outros / 50% da média | ❌ |
| Yield da meta pessoal | 6% ação, 10% FII | ✅ por usuário — só no preço-teto |

## Limitações — leia antes de confiar no número

1. **Não é fluxo de caixa livre.** Desconta o lucro distribuível; capex, capital de giro e dívida
   líquida por empresa não existem na fonte.
2. **O prêmio é o mesmo para toda empresa.** Sem beta nem estrutura de capital, diferenciar seria
   inventar.
3. **O ROE do terminal é o normalizado de hoje.** Empresa de ROE muito alto sai generosa no longo
   prazo; a concorrência tende a reduzi-lo.
4. **Os parâmetros não têm calibração empírica.** Medido em 2026-10-12: o veredito não ordenou o
   retorno, e a calibração parou antes de mexer em parâmetro ([pesquisa/calibracao](../../pesquisa/estudos/calibracao.md)).
   A taxa mudou depois por outro critério, a distribuição da régua, e nem com ela o veredito ordena
   o retorno ([pesquisa/calibracao-com-a-taxa-nova](../../pesquisa/estudos/calibracao-com-a-taxa-nova.md)).
5. **FII de papel fora da lista de referência parece barato.** A lista é mantida à mão; fundo que
   não está nela é lido como tijolo, e a distribuição com correção monetária sai capitalizada por
   juro real.
6. **VPA de FII é laudo, com defasagem.** Em FoF, ele já carrega o desconto dos fundos investidos.
7. **Quem cresce o dividendo com a inflação sai cerca de 9% abaixo do último ano**, pelo mínimo
   entre a média e o mais recente.
8. **Cíclica em ciclo longo** ainda pode ter três exercícios de pico; a normalização suaviza, não
   resolve.
9. **±15% e ±30% são convenção declarada**, não fronteira medida. A mudança de etiqueta é degrau:
   o falsificador de preço mostra a que distância ela está.
