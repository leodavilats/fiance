# Validação da base contra a brapi

**Status:** protocolo aceito em 2026-10-18; resultado abaixo, depois da execução.
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
- O token sai do `backend/.env`, que não vai para o git, e nunca é impresso.

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

*(preenchido depois da execução)*
