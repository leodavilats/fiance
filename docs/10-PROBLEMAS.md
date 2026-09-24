# Problemas conhecidos

**Fonte de verdade** do que está aberto. Só pendências: nada de histórico, nada de item resolvido.
Última verificação contra o código: **2026-09-23**
Itens 1 a 33 herdados da verificação de 2026-09-11; itens A a E da auditoria do motor de cálculo de
2026-09-13. A0, 28, 30 e 31 saíram em 2026-09-19 — ver
[ADR-011](decisoes/ADR-011-preco-justo-e-faixa.md) e
[ADR-012](decisoes/ADR-012-o-alvo-e-de-quem-declara.md). A2, A3, A4 e A6 saíram em 2026-09-23, e
A7 a A9 entraram — ver [ADR-014](decisoes/ADR-014-um-modelo-por-classe.md).

> **Ao fechar um item, apague-o daqui.** Item resolvido que fica é pior que item ausente, porque
> manda alguém refazer o que já existe. Este arquivo tem histórico de apodrecer: numa revisão de
> agosto, oito de 24 itens já estavam feitos.

---

## A · Motor de cálculo

Os itens remanescentes da auditoria de **2026-09-13**. A de **2026-09-20**, que inventariou os
40 problemas do caminho do preço ao veredito, foi fechada no mesmo dia
([ADR-013](decisoes/ADR-013-o-tecnico-nao-decide.md)) e virou registro em
[historico/AUDITORIA-DO-VEREDITO-2026-09-20](historico/AUDITORIA-DO-VEREDITO-2026-09-20.md).

### A5 · O perfil de risco não afeta FIIs nem ETFs

`scoring.py:95-96`: `_FII_WEIGHTS` e `_ETF_WEIGHTS` são fixos e `profile` não entra no ramo. Quem tem
carteira de FIIs muda de conservador para arrojado e **nada acontece**.

Junto com o item 29, isto compromete a personalização que é a hipótese de receita do produto.

### A7 · FII de papel parece barato

O FII de papel distribui como rendimento a correção monetária dos CRIs. A distribuição sobe com a
inflação sem que o valor suba, e o principal perde valor real. O modelo de FII trata tudo como
tijolo, cuja distribuição cresce com o aluguel. Na amostra de 2026-09-23, MXRF11 foi o único ativo a
sair "abaixo do preço justo".

**Segue aberto:** a BRAPI não entrega o subtipo do fundo. Resolver exige uma classificação mantida
à mão ou outra fonte, e um yield exigido nominal para papel.

### A8 · Os parâmetros do preço justo não têm calibração empírica

Prêmio de 5 pontos, 3 pontos de FII, 1,5% de crescimento real, teto de 20%, choque de ±1 ponto e
bandas de ±15% e ±30% são convenções declaradas. Validá-los exige retorno à frente por faixa de
margem, fora da amostra, com fundamentos **como estavam na data** e sem viés de sobrevivência.

**Segue aberto:** a BRAPI não entrega fundamento *point-in-time*. Os dados abertos da CVM
(DFP/ITR) entregariam, mas o invariante "só BRAPI e BCB SGS" teria de ser revisto. Decisão de
produto.

### A9 · BDR não tem leitura de valor

Por decisão da ADR-014: a única taxa disponível é em reais, e descontar lucro em dólar pela Selic
fazia todo BDR parecer caro (cerca de 0,67× o valor numa taxa em dólar). O LPA que a BRAPI entrega
para BDR já vem por BDR e em reais — a escala está certa, a moeda da taxa não.

**Segue aberto:** exige juro em dólar, fora das duas fontes permitidas.

## B · Dado e fonte

### 3 · Cobertura dos fundamentos — **medida em 2026-09-13**

Amostra de 33 ativos em produção, pela rota pública. Presentes / total:

| Classe | n | ROE | Margem | Cresc. | D/E | VPA | LPA | Val. mercado |
|---|---|---|---|---|---|---|---|---|
| Ação grande | 8 | 7 | 8 | 8 | 6 | 8 | 8 | 8 |
| Ação média | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 4 |
| Ação pequena | 5 | 3 | 4 | 4 | 4 | 4 | 5 | 5 |
| Banco | 4 | 2 | 4 | 4 | **0** | 4 | 4 | 2 |
| FII | 5 | 0 | 0 | 0 | 0 | 5 | 0 | **0** |
| BDR | 4 | 0 | 0 | 0 | 0 | **0** | 4 | 4 |
| ETF | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Para ação, a cobertura é boa** — 80% a 100% nos quatro campos de fundamento. O problema que o item
29 descrevia **não existe mais para ações**; ele descrevia o estado anterior a 2026-09-11.

O que a medição encontrou de novo:

- **Banco sem D/E: 0 de 4.** Conhecido e deliberado
- **FII sem valor de mercado: 0 de 5.** `_FII_WEIGHTS` dá 15% do peso à liquidez, que vem de
  `market_cap` — então todo FII perde essa dimensão e é pontuado só por margem e dividendos
- **BDR sem VPA: 0 de 4.** Desde 2026-09-23 BDR não tem preço justo por decisão de método (A9), e
  não por falta de dado
- **ETF sem nada.** Nenhum método se aplica, e o produto diz "Sem preço justo"
  ([ADR-014](decisoes/ADR-014-um-modelo-por-classe.md))
- **Banco sem ROE.** O Itaú não preenche `netIncome`; desde 2026-09-23 o coletor lê
  `netIncomeApplicableToCommonShares`, e sem ROE a ação não tem preço justo. Repetir a medição

Repetir a medição: `GET /api/v1/data-quality` (exige sessão) ou amostrar
`GET /api/v1/public/asset/{ticker}`, que não exige.

### 29 · ~~Três das seis dimensões nunca têm dado~~ — **superado pela medição de 2026-09-13**

Este item descrevia o estado anterior a 2026-09-11 e **não vale mais para ações**: ROE, margem,
crescimento e D/E chegam em 80% a 100% da amostra, e o perfil de risco pondera o que deveria.

O que sobra dele, em forma menor: para **FII, BDR e ETF** as dimensões de fundamento continuam
vazias — por natureza da classe, não por falha de coleta. Isso está no item 3 e no A5.

### 1 · O caminho do Redis nunca rodou contra um servidor real fora do CI

Coberto: o contrato e a tradução do adaptador. Não coberto: rede instável, reconexão, failover.

### 4 · Universo hardcoded como fallback

`core/config.py::default_universe` mantém ~400 tickers, apesar de existir universo dinâmico via
BRAPI. Fallback defensivo intencional, mas extenso.

### 33 · A janela de pregão não conhece feriado da B3

`core/pregao.py` bloqueia a varredura em dia de feriado como se fosse pregão normal.

---

## C · Produto incompleto

### 34 · O calendário de proventos só prova o direito quando a fonte publica a data-com

Desde 2026-09-15 o coletor carrega `lastDatePrior`, e com ela o razão prova quem tinha a posição na
data-com. Quando a fonte não publica a data-com, ou quando uma declaração de posição absorveu a
história anterior, o direito fica `indeterminado` e a sugestão vai para o calendário colapsado. Não
há como saber quantos proventos caem em cada caso sem medir contra a fonte real.

### 15 · Sugestões seguidas dependem de lançamento manual

### 20 · A apuração de IR não cobre day trade nem IOF de renda fixa

### 27 · A cobrança é backend sem cliente

Existe a cerca, a régua de plano, o preço travado e o webhook — e nenhuma tela. Agravado pela decisão
de refazer tudo para RevenueCat ([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)): o que existe
hoje **não** será aproveitado.

### 16 · `detail_level` (Essencial / Completo / Avançado) não existe no backend

---

## D · Paridade perdida — o mais urgente

Nove funcionalidades ficaram sem cliente com a remoção do front web em 2026-09-11. **Quatro seguem
abertas:** importação de extrato, ativos seguidos, onboarding, e reconciliação com reconstrução.
Inventário completo e com critério de morte em
[PARIDADE-WEB-APP](temporario/PARIDADE-WEB-APP.md).

A mais grave é a **importação de extrato**: o razão ganhou tela em 2026-09-13, e alimentá-lo
continua sendo um lançamento de cada vez.

---

## E · Interface

### 7 · Duas famílias de controle ainda são Material puro, com estilo só no tema

`Switch` e `Slider`. A ficha saiu em 2026-09-15 — `FiChoiceChip` —, e `ExpansionTile` foi substituído
onde o produto usava caixa expansível.

### 8 · ~~A base do preço justo não chega às telas de posição da carteira~~ — **resolvido em 2026-09-15**

O card de posição deixou de ter gaveta própria de razões e passou a abrir `/ativo/:ticker`, que já
traz a cifra com a base.

### 9 · Falta a regra do alvo de toque de 44dp no Dart

### 10 · ~~`/voce` são cinco entradas, e o desenho pede quatro eixos~~ — **resolvido em 2026-09-15**

`/voce` virou índice de `investir`, `avisos`, `aparencia` e `conta`, e cada linha carrega o estado
atual.

### 11 · Falta o componente de evidência

Falta `Evidence`, o nível 2 da explicabilidade. O par que revelava detalhe foi construído em
2026-09-15: `FiDisclosure` e `FiGroupDisclosure`.

### 12 · A régua de afirmação anula `allocated_cash` e deixa a subtração de pé

### 17 · A régua não cobre o score em linha densa, e ali ele sai só como selo

### 26 · A aparência nos dois temas nunca foi conferida num aparelho

O contraste é verificado por máquina; a aparência não.

### 25 · A acessibilidade foi coberta por verificação, não por auditoria — e a verificação encolheu

---

## F · Teste, automação e operação

### 13 · Não existe mais teste de ponta a ponta

O que havia rodava no navegador e saiu com o front web.

### 14 · As regras de interface que só rodavam no front não foram portadas

Três não têm equivalente no Dart: **gráfico sem tabela equivalente**, **destino de navegação
inexistente** *(esta foi portada — regra 13 do lint)* e **controle montado à mão**.

### 6 · Rótulo e régua são escritos dos dois lados — os números já são comparados, os textos não

Desde 2026-09-13, `tests/test_regua_nas_duas_plataformas.py` confronta os **cinco limiares
numéricos** da régua de score entre `analysis/score_ruler.py` e `mobile/lib/core/product_rules.dart`,
com o Python como fonte.

**O que ainda não é comparado:** os rótulos das bandas ("Excelente entrada", "Boa oportunidade"…),
o vocabulário de veredito e os rótulos de categoria. Continuam escritos duas vezes, e nada impede que
o Dart chame de "Boa oportunidade" o que o Python chama de outra coisa.

### 18 · O contrato das rotas guarda campo que sai, não campo que entra

### 45 rotas sem contrato de resposta

`SEM_MODELO_HOJE = 45` em `tests/test_contrato_das_rotas.py`. Metade das rotas devolve `dict` solto,
sem `response_model` — o FastAPI não pode conferir, e o contrato não as cobre. A catraca impede
crescer; não faz o número cair.

### 24 · A paginação das listas com agregado limita o payload, não a consulta

### 23 · Token de push é reatribuído a quem o registrar

### Não existe rotina de backup própria nem restauração testada

O backup é o do provedor. Nunca foi exercitado.

### 21 · O mobile nunca teve um release de verdade

Não existe chave de assinatura, e nenhum evento de telemetria foi visto em produção.

---

## G · Código morto a remover

| Item | Ação |
|---|---|
| `api/demo.py` — sem cliente desde 2026-09-11 | Decidir |

`optimizer/`, `OptimizationStrategy` e a duplicata de `MIN_DATA_COMPLETENESS` foram removidos em
2026-09-13 ([ADR-010](decisoes/ADR-010-remover-otimizador.md) e item A1).

---

## H · Pré-requisitos de loja não atendidos

### Sign in with Apple não existe

A App Store exige quando há login social de terceiros. O sistema só tem Google. É um segundo provedor
de identidade, não uma configuração.

### Não há contas de desenvolvedor, nem Mac

Ver [07-OPERACAO](07-OPERACAO.md).

---

## Armadilhas conhecidas

Não são bugs, mas mordem. Lista completa em [06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) e no
`CLAUDE.md`.
