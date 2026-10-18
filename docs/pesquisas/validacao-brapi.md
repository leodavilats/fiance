# Validação da base contra a brapi

**Status:** executada em 2026-10-18. Resultado abaixo.
**Pergunta:** onde a base própria discorda de uma segunda fonte, e a discordância é erro nosso?

## Por que, e o limite do que se conclui

A base é a fonte do app e da `fiance-dados`. Até aqui ela foi conferida contra ela mesma — o preço
confirma o evento, o informe confirma o FII. Uma segunda fonte, independente na montagem, acha o que
a conferência interna não vê: o evento que a B3 não publicou, o provento que não chegou, o dia que
falta.

**A brapi não vira fonte.** A ADR-022 a tirou do produto; nada do que ela diz entra no schema
`mercado`, nem preenche lacuna. Ela só aponta onde olhar. Uma divergência só vira erro nosso quando
a fonte primária confirma — o COTAHIST da B3, que já está na base, ou a CVM. O que só a brapi diz
fica registrado como **não confirmado**.

Discordar não prova erro de nenhum lado: a brapi também monta dado de terceiros, e a série ajustada
dela segue outra convenção (o `adjustedClose` desconta provento; o nosso ajuste é só por evento). Por
isso a comparação de preço usa o `close` da brapi, ajustado só por evento, como o nosso
`fechamento_ajustado`.

## Plano disponível

Plano Startup da brapi, medido antes do protocolo com três requisições:

- preço diário: **só o último ano** (`range=max` é recusado);
- eventos (`stockDividends`) e proventos (`cashDividends`): **o histórico inteiro**, mesmo com
  `range=1y`; ETF e BDR vêm sem provento;
- dez tickers por requisição; 150 mil por mês, das quais o autor dispõe de 100 mil.

## Universo e coleta

- Todo ticker em `mercado.ativo_hoje` na data da coleta: ações, FIIs, ETFs e BDRs.
- Uma requisição por lote de dez: `range=1y&interval=1d&dividends=true`. Cerca de 200 requisições.
- **Teto: 1.000 requisições.** Passou disso, a coleta para e o protocolo ganha adendo antes de
  continuar.
- A resposta bruta fica em disco (`fiance-trend/backend/.brapi/`, fora do git) e a comparação roda sobre
  ela, sem gastar requisição de novo. A base é lida no mesmo dia, de produção, só leitura.
- O token sai do `.env` do backend, que não vai para o git, e nunca é impresso.

## Comparações e réguas

As réguas abaixo foram fixadas antes de ver qualquer comparação, e não mudam depois dela.

### 1. Eventos — desdobramento, grupamento e bonificação

- Chave: emissor e classe do ticker; da brapi, só os rótulos `DESDOBRAMENTO`, `GRUPAMENTO` e
  `BONIFICACAO`, com data-com (`lastDatePrior`) de 03/01/2005 em diante.
- O nosso lado: `mercado.evento` (qualquer status) e `mercado.evento_inferido`.
- **Batem** quando a data-com difere em até 5 dias corridos e o multiplicador em até 1%.
- Categorias: bate; fator difere; **só na brapi**; só nossa; nossa recusou (está em `evento` com
  status diferente de confirmado).
- Para cada evento **só na brapi**, a conferência primária: a razão entre o fechamento da véspera e o
  do pregão seguinte, no nosso COTAHIST, a até 10% do fator. Passou: **lacuna confirmada pelo
  preço**. Não passou, ou sem pregão: não confirmada.

### 2. Preço do último ano

- Ação: `close` da brapi contra `fechamento_ajustado` de `serie_papel`, pelo ticker e pela data.
  FII: contra `serie_fundo`. ETF e BDR: contra o fechamento bruto de `cotacao`.
- Um dia **bate** quando a razão está a até 0,5% de 1.
- Um ticker **diverge** quando menos de 98% dos dias comparados batem, ou quando algum dia passa
  de 5%.
- Também se contam os pregões que só um lado tem.

### 3. Proventos

- Ações e FIIs, data-com de 03/01/2005 em diante. O nosso lado sem `cvm_estimado`.
- Compara-se a **soma por data-com** (dividendo, JCP, rendimento e o que mais houver em dinheiro),
  porque os rótulos não coincidem entre as fontes.
- **Batem** quando a diferença é de até 1% ou de até R$ 0,0001 por cota.
- Categorias: bate; valor difere; só na brapi; só nossa.

### 4. A estimativa do rendimento de FII

- Para os FIIs, nos meses antes de outubro de 2025 em que o nosso rendimento é `cvm_estimado`: a
  estimativa do mês contra a soma do rendimento da brapi com data-com no mesmo mês.
- Só descreve: mediana e percentil 90 do erro relativo, e a fração a até 10%. Não há régua de
  aprovação; o número entra no 10-PROBLEMAS para dar tamanho à lacuna declarada.

### Fora desta rodada

Fundamentos (o plano dá cinco anos de demonstração anual): a CVM já é a fonte primária. Fica para um
adendo, se esta rodada achar motivo.

## O que acontece com o resultado

- Cada divergência **confirmada pela fonte primária** vira item no 10-PROBLEMAS ou correção no
  data-job, com a fonte primária como prova.
- A correção nunca copia o número da brapi.
- O resultado agregado entra aqui; as listas por ticker ficam em `fiance-trend/backend/.brapi/`, fora do
  git, porque carregam dado da brapi.
- O registro da execução acrescenta uma linha a `fiance-trend/backend/registro_validacao.jsonl`.

## Resultado

Execução de 2026-10-18: 1.949 tickers, **195 requisições** (0,2% da cota), 9 tickers sem resposta.
Duas linhas no `registro_validacao.jsonl`: a primeira com o erro de janela declarado abaixo.

**Correção declarada.** Na primeira passada, a base foi exportada com 400 dias de preço e a brapi
devolve um ano: 88 mil dias apareceram como "só nossa" sem ser. A comparação passou a olhar só a
janela que a brapi devolveu. A régua não mudou.

**Limite declarado da régua de confirmação.** A folga de 10% na razão de preço, herdada da inferência
de eventos, não separa uma bonificação de 2% a 10% de um dia comum: para fator 1,1, a razão 1,0 já
passa. Os 52 eventos "confirmados pelo preço" estão abaixo separados pelo tamanho do fator, e só os
grandes contam como confirmados.

### 1. Eventos (data-com desde 2005)

| Categoria | Eventos |
|---|---|
| Batem | 426 |
| Só na brapi | 88 — 52 passam a régua; **25 com fator ≥ 1,5 ou ≤ 0,67 confirmados pelo preço** |
| Nossa recusou (a brapi tem, o nosso preço não confirmou) | 65 — 48 divergentes, 17 sem preço |
| Fator difere | 2 (BRSR3 e ETER3, 2007) |
| Só nossa | 269 — 172 de BDR, 54 de FII, 21 de ação, várias de outubro de 2026 |

Os 25 confirmados são **lacunas reais da série ajustada**: MGLU3 (2015, 2017 e 2019), BBDC4 (2005,
2:1), GGBR3/4 e GOAU3/4 (bonificação de 50% em 2005 e 2006), BBDC3/4 (2008), RCSL3/4 (2010), COGN3
(2013 e 2014), SBSP3 (2013), RIAA3 e AZEV3 (2019), RCSL4 e ECOM3 (2024), IFCM3 (2025) e K1LA34
(2026). As bonificações pequenas que só a brapi lista — Itaú, Bradesco e Itaúsa, de 2% a 10%, de 2009
a 2025 — a régua não decide; o "só nossa" é, em geral, lacuna da brapi, que quase não lista evento de
FII.

### 2. Preço do último ano

1.903 tickers comparados; **176 divergem**: 133 BDR (desvio espalhado, sinal de outra fonte de preço),
8 ETF, 14 FII e 21 ações. Nas ações e nos FIIs, quatro padrões:

- **Convenção:** antes de uma bonificação que os dois lados têm (ITSA3/4, KLBN4/11, RADL3), a razão é
  exatamente o fator — a brapi não leva a bonificação ao preço passado.
- **Atraso da brapi:** grupamentos de outubro de 2026 (ENJU3, RCSL3/4) ainda não aplicados por ela.
- **Evento que o nosso preço recusou, com o salto na série e sem marca:** BTYU11 (+8.066% num dia),
  SEQL3 (+797%), PDGR3 (+74%). A B3 publicou o grupamento; a razão observada ficou fora dos 10%, e
  com evento no intervalo o `salto_sem_evento` não marca.
- **Razão ×2, ×0,5 ou ×1/3 sem evento em lista nenhuma:** 11 FIIs e 5 ações. Na nossa série, alguns
  aparecem como queda de 42% a 49% sem marca (CACR11, LPLP11, DAMT11) — abaixo do limiar de 50%.

Pregões só na brapi: 9.661, dos quais 2.168 de ações e FIIs repetem o fechamento anterior (dia sem
negócio preenchido por ela). Só nossos: 4.876, todos de BDR.

### 3. Proventos (desde 2005, sem estimados)

| Categoria | Datas-com |
|---|---|
| Batem | 14.280 |
| Só na brapi | 17.841 — cerca de 17.200 são de FII antes de outubro de 2025, a lacuna declarada; 632 de ações e 127 de FII depois de outubro de 2025 |
| Valor difere | 898 |
| Só nossa | 258 |

Dos 898 valores diferentes, **517 são convenção da brapi**: 273 por lote de mil ações (2005 a 2015)
e 244 em que ela junta parcelas. As parcelas foram conferidas na B3, pela lista que traz data de
pagamento: dos 54 grupos repetidos verificáveis desde 2025, **44 são parcelas reais**, com datas de
pagamento distintas — a nossa soma está certa. Em 10 (B3SA, entre outros) a B3 lista mais parcelas do
que o nosso histórico. Ficam 381 diferenças sem explicação única, para conferência caso a caso.

De passagem: as parcelas repetidas recebem, todas, a última data de pagamento (CMIG, 22/09/2026: as
duas com 30/12/2027, quando uma é 30/06/2027).

### 4. A estimativa do rendimento de FII

15.068 meses de 275 FIIs: erro mediano de **0,78%**, percentil 90 de **31,8%**, e **79,4%** dos meses
a até 10%. A estimativa acerta o mês típico e erra feio em um de cada dez.

### O que vira trabalho

Confirmado pela fonte primária e aberto no [10-PROBLEMAS](../10-PROBLEMAS.md): os eventos grandes que
faltam, o salto sem marca quando o evento foi recusado, a queda de quase 50% abaixo do limiar, as
parcelas que faltam e a data de pagamento das parcelas. Nada da brapi entrou na base.
