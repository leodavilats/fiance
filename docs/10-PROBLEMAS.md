# Problemas conhecidos

**Fonte de verdade** do que está aberto. Só pendências: nada de histórico, nada de item resolvido.
Última verificação contra o código: **2026-09-13**
Itens 1 a 33 herdados da verificação de 2026-09-11; itens A a E da auditoria do motor de cálculo de
2026-09-13.

> **Ao fechar um item, apague-o daqui.** Item resolvido que fica é pior que item ausente, porque
> manda alguém refazer o que já existe. Este arquivo tem histórico de apodrecer: numa revisão de
> agosto, oito de 24 itens já estavam feitos.

---

## A · Motor de cálculo — auditoria de 2026-09-13

### A0 · O consenso pende para dividendo, e 54% da amostra sai como venda — **o mais grave**

Medido em produção em 2026-09-13, amostra de 33 ativos:

| Veredito | Ativos | % |
|---|---|---|
| SELL | 10 | 30% |
| STRONG_SELL | 8 | 24% |
| BUY | 6 | 18% |
| HOLD | 5 | 15% |
| UNKNOWN | 3 | 9% |
| STRONG_BUY | 1 | 3% |

**Mais da metade da amostra recebe sinal de venda**, e a margem de segurança se distribui de forma
bimodal, alinhada ao dividend yield:

| Pagam pouco dividendo | MOS | Pagam muito | MOS |
|---|---|---|---|
| WEGE3 (DY 1,9%) | **−308%** | PTBL3 | +72% |
| RADL3 | −190% | GRND3 | +61% |
| TOTS3 | −114% | CSAN3 | +59% |
| BPAC11 | −94% | PETR4 | +57% |

A causa é estrutural: para ação, o consenso é **Bazin + Graham**, e o DCF é descartado sempre que há
Bazin (item A4). Bazin é `dividendo médio ÷ 6%`, então empresa que retém lucro para crescer sai
sistematicamente "cara". O produto se apresenta como consenso de métodos e **opera, na prática, como
uma régua de dividendos**.

Isso atinge a tese do produto de frente: a pergunta é *"que ativo eu compro agora?"*, e a resposta
hoje é "quase nenhum, exceto os maiores pagadores de dividendo".

**Fechar é decisão de produto**, e as saídas não são excludentes: ponderar o consenso em vez de tirar
média simples; deixar o DCF participar junto com o Bazin; ou aplicar a faixa de validade de Graham
(item A6), que sozinha já removeria os casos mais extremos.

### A6 · Graham é aplicado fora da própria faixa de validade

`graham_fair_price` (`analysis/fair_price.py`) aplica `√(22,5 × LPA × VPA)` a qualquer empresa. Não
verifica nada além de LPA e VPA positivos.

Mas o glossário **promete ao usuário** que o método vale "para empresas com P/L ≤ 15 e P/VP ≤ 1,5".

WEGE3 tem P/L 34,6 e P/VP 11,5 — quase o dobro e quase oito vezes os limites —, e mesmo assim recebe
um preço justo de Graham de R$ 12,28 contra preço de R$ 51,49. Os dois métodos do consenso estão
fora da faixa em que fazem sentido, e nada no código percebe.

É o achado mais acionável do conjunto: a condição já está escrita, em português, na tela. Falta
implementá-la — e decidir o que fazer quando ela não é atendida (abster-se do método, ou abster-se do
veredito).

### A1 · O piso de completude — *resolvido em 2026-09-13, com ressalva*

O diagnóstico original estava incompleto. O piso **é aplicado**, no cliente:
`fiScoreBandFor` devolve a banda `insufficient` abaixo de 0,5, e as telas usam
(`mobile/lib/features/mes/widgets/feed_tiles.dart`). O que não existia era **consumidor no Python** —
a constante estava duplicada em `scoring.py` sem uso, e nada comparava os dois lados.

Resolvido movendo o limiar para `analysis/score_ruler.py` e criando
`tests/test_regua_nas_duas_plataformas.py`, que confronta os cinco limiares da régua com os do Dart.

**A ressalva que fica aberta:** o piso não é aplicado no backend de propósito. Aplicá-lo como
supressão eliminaria o score de toda ação sem fundamentos completos no perfil arrojado, cuja
completude típica é **0,35**. A leitura parcial declarada é melhor que tela vazia — mas isso é
remendo enquanto o item 29 não for resolvido.

### A2 · O "DCF" não é um DCF

`analysis/fair_price.py:184` desconta **lucro por ação**, não fluxo de caixa livre, e usa crescimento
de **receita** como proxy do crescimento de lucro. A taxa de desconto é fixa em 13% para qualquer
empresa — sem beta, sem WACC, sem prêmio por setor ou porte — e o P/L terminal é fixo em 15.

É uma heurística razoável com nome errado.

**Mitigado em 2026-09-13:** o glossário passou a chamá-lo de "lucros descontados" e a declarar as
três limitações — desconta lucro e não caixa, usa crescimento de receita como proxy, e a taxa de 13%
é igual para qualquer empresa.

**Segue aberto:** implementar um DCF de verdade, ou assumir a heurística e renomear o campo na API
(`dcf`) junto. Decisão de produto: muda o número que a pessoa vê.

### A3 · O múltiplo de Graham não é ajustado ao juro brasileiro

`√(22,5 × LPA × VPA)` usa a constante de 1949, do mercado americano. Em juro alto, ela é generosa —
e o Brasil passou a maior parte da década recente em juro alto. O método participa do consenso de
toda ação e de todo BDR.

**Mitigado em 2026-09-13:** o glossário declara a limitação. **Segue aberto:** ajustar o múltiplo à
Selic muda o preço justo de toda a base, e é decisão de produto.

### A4 · O DCF é descartado sempre que há Bazin, e isso não está documentado na interface

`fair_price.py:307`: `if bazin is not None: dcf = None`. Na prática, o DCF só participa do consenso de
uma ação que **não paga dividendos**.

**Mitigado em 2026-09-13:** o verbete do glossário diz a regra. **Segue aberto:** a tela ainda mostra
"consenso de 2 métodos" sem nomear quais — nomeá-los exige campo novo na resposta.

### A5 · O perfil de risco não afeta FIIs nem ETFs

`scoring.py:95-96`: `_FII_WEIGHTS` e `_ETF_WEIGHTS` são fixos e `profile` não entra no ramo. Quem tem
carteira de FIIs muda de conservador para arrojado e **nada acontece**.

Junto com o item 29, isto compromete a personalização que é a hipótese de receita do produto.

---

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
- **BDR sem VPA: 0 de 4.** Sem VPA não há Graham, e o consenso de BDR cai para **um método só**, o
  DCF. `consensus_methods: 1` em todos os quatro
- **ETF sem nada.** Confirma o item 28, e pior: o veredito sai `UNKNOWN` na rota pública, então nem
  o remendo por RSI está atuando ali

Repetir a medição: `GET /api/v1/data-quality` (exige sessão) ou amostrar
`GET /api/v1/public/asset/{ticker}`, que não exige.

### 29 · ~~Três das seis dimensões nunca têm dado~~ — **superado pela medição de 2026-09-13**

Este item descrevia o estado anterior a 2026-09-11 e **não vale mais para ações**: ROE, margem,
crescimento e D/E chegam em 80% a 100% da amostra, e o perfil de risco pondera o que deveria.

O que sobra dele, em forma menor: para **FII, BDR e ETF** as dimensões de fundamento continuam
vazias — por natureza da classe, não por falha de coleta. Isso está no item 3 e no A5.

### 28 · O ETF é estruturalmente mal avaliado, e o remendo tem consequência

Para `asset_type == "etf"` o único candidato a consenso é Bazin (`dividendo ÷ 0,04`); um ETF de
índice distribui na casa de 1% ao ano, então o preço justo sai em ~25% do preço e a margem de
segurança em −300%, sempre.

`opportunity_service` sobrescreve o veredito por RSI e tendência quando ele sai `UNKNOWN`, o que
produz duas coisas ruins: **o mesmo ETF recebe veredito diferente em `/descobrir` e em
`/ativo/:ticker`**, e o veredito por momentum sai **sem falsificador**, porque sem consenso não há
preço-limite.

Decidir o método — comparação com o índice, prêmio sobre valor patrimonial, ou abstenção explícita —
vem antes de mexer no falsificador.

### 1 · O caminho do Redis nunca rodou contra um servidor real fora do CI

Coberto: o contrato e a tradução do adaptador. Não coberto: rede instável, reconexão, failover.

### 4 · Universo hardcoded como fallback

`core/config.py::default_universe` mantém ~400 tickers, apesar de existir universo dinâmico via
BRAPI. Fallback defensivo intencional, mas extenso.

### 33 · A janela de pregão não conhece feriado da B3

`core/pregao.py` bloqueia a varredura em dia de feriado como se fosse pregão normal.

---

## C · Produto incompleto

### 30 · O passo de reserva da cascata é inalcançável

`cascata.montar` recebe `reserva_meses_alvo` e `reserva_atual`, a matemática está escrita e testada,
e **nenhuma rota passa os dois** — porque não há onde declarar quantos meses de gasto fixo a pessoa
quer guardar. Não há campo em `preferences`, em `goals`, em lugar nenhum.

A regra documentada ("a reserva vem depois da dívida cara, e só existe com alvo declarado") descreve
um passo que a Sobra **nunca mostra**.

Fechar é decisão de produto antes de código: quantos meses, contra qual base, e o que acontece com
quem não declara. Inventar "seis meses" é o número de mercado solto que a régua de dívida proíbe.

### 31 · A alocação-alvo cai no padrão e a tela não distingue

`GET /dashboard` monta as barras com `goal_service.get_goals()`, que devolve 30/35/15/15/5 quando nada
foi declarado. Quem nunca declarou meta vê barras "abaixo da meta" de uma meta que não escolheu, e o
alerta de rebalanceamento dispara sobre ela.

As metas **por setor** já distinguem (o `declared` da resposta); as de categoria não, e mudar isso
mexe no alerta do dashboard, no `whats_new` e no Quick Invest de uma vez.

### 15 · Sugestões seguidas dependem de lançamento manual

### 20 · A apuração de IR não cobre day trade nem IOF de renda fixa

### 27 · A cobrança é backend sem cliente

Existe a cerca, a régua de plano, o preço travado e o webhook — e nenhuma tela. Agravado pela decisão
de refazer tudo para RevenueCat ([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)): o que existe
hoje **não** será aproveitado.

### 16 · `detail_level` (Essencial / Completo / Avançado) não existe no backend

---

## D · Paridade perdida — o mais urgente

Nove funcionalidades que o backend serve e o aplicativo não alcança, todas por remoção do front web
em 2026-09-11. Inventário completo e com critério de morte em
[PARIDADE-WEB-APP](temporario/PARIDADE-WEB-APP.md).

O item mais grave: **o livro-razão, fonte da carteira e do imposto, não tem nenhuma tela**.

---

## E · Interface

### 7 · Três famílias de controle ainda são Material puro, com estilo só no tema

### 8 · A base do preço justo não chega às telas de posição da carteira

Em `/ativo` a cifra vem com "consenso de N métodos"; nas telas de posição, não.

### 9 · Falta a regra do alvo de toque de 44dp no Dart

### 10 · `/voce` são cinco entradas, e o desenho pede quatro eixos

### 11 · Dois comportamentos essenciais não têm componente

Faltam `Evidence` (o nível 2 da explicabilidade) e o par que o acompanha.

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

### 5 · A API de produção sobe sem esperar o CI

O serviço tem gatilho em `main` e `checkSuites: false`. Um commit vermelho vai ao ar — e o
pre-deploy é `python -m app.release`, então **uma migração ruim é aplicada antes de qualquer teste
terminar**. É o item de maior risco operacional da lista.

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

### Exclusão de conta não tem tela

Existe em `api/account.py`. As lojas exigem o caminho **dentro do aplicativo**.

### Não há contas de desenvolvedor, nem Mac

Ver [07-OPERACAO](07-OPERACAO.md).

---

## Armadilhas conhecidas

Não são bugs, mas mordem. Lista completa em [06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) e no
`CLAUDE.md`.
