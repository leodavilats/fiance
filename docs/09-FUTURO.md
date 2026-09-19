# Futuro

**Fonte de verdade** do roadmap. Nada aqui existe — o que existe está em
[08-ESTADO](08-ESTADO.md).
Última revisão: 2026-09-13

As seções são rígidas e não se misturam. Um item só muda de seção por decisão explícita.

---

## Em desenvolvimento

**Nada.** Não há trabalho em curso neste momento.

---

## Planejado

Ordem definida em 2026-09-13. Os cinco primeiros são **recuperação e amadurecimento do que já
existe** — só o 7 e o 8 são construção nova.

### 1 · Livro-razão e importação de extrato no aplicativo

O razão é a fonte da carteira e do imposto, e **não tem nenhuma tela**. O backend está pronto e
testado: `POST /transactions`, `/transactions/import`, `/rebuild`, `/reconciliation`.

É o primeiro item porque o produto hoje entrega menos do que possui, e porque todo o resto —
proventos, apuração, sugestões — depende de o razão ser alimentável.

**Esforço:** telas novas sobre backend existente. Ver
[PARIDADE-WEB-APP](temporario/PARIDADE-WEB-APP.md).

### 2 · Tela de proventos

Ver de onde veio cada provento e lançar os recebidos. Hoje o aplicativo mostra proventos derivados no
caixa, mas não há como inspecionar a origem nem gerir os pendentes. `GET /dividends` e
`/dividends/pending` existem sem cliente.

### ~~3 · Oportunidades personalizadas~~ — parcialmente entregue em 2026-09-13

A frase-alvo, declarada pelo autor:

> *"PETR4 está 20% abaixo do preço justo e cabe na sua meta de renda, e você tem ITSA4 que está 20%
> acima — avalie se vale fazer o ajuste."*

**Entregue:** `/sobra/desvio` mostra o alvo da realocação com régua de score, as três razões, e o
perfil de risco que ordenou a lista. O perfil também aparece em `/descobrir`, com o glossário
dizendo o que ele muda.

**Falta, e depende do item 4:** a frase ainda não cita o preço justo do alvo nem a margem de
segurança dos dois lados — e citar isso com mais força exige confiar no número, que é o item
seguinte.

Esta é a hipótese de receita do produto. Ver
[ADR-006](decisoes/ADR-006-recomendacao-personalizada.md).

### 4 · Confiança no preço justo

O autor não confia no cálculo. A auditoria de 2026-09-13 encontrou quatro pontos concretos, todos em
[10-PROBLEMAS](10-PROBLEMAS.md):

- o "DCF" não é um DCF
- taxa de desconto fixa em 13% para qualquer empresa
- múltiplo de Graham não ajustado ao juro brasileiro
- `MIN_DATA_COMPLETENESS` declarado e nunca aplicado

O item 3 depende deste: recomendar com mais força um número em que não se confia aumenta o dano do
erro.

### 5 · Simplificar a linguagem da análise de ativo

Muitas siglas para um iniciante — e o iniciante é metade do público declarado. Trabalho de texto e
hierarquia, não de cálculo.

### 6 · Onboarding no aplicativo

`GET /onboarding` deriva o passo do que a pessoa já fez. Zero arquivos no cliente.

### 7 · Contas de desenvolvedor e publicação

Bloqueadores listados em [07-OPERACAO](07-OPERACAO.md): contas Google Play e Apple, um Mac, **Sign in
with Apple**, ficha de segurança de dados e um canal de atendimento publicado. A exclusão de conta
dentro do aplicativo saiu da lista em 2026-09-19.

⚠️ **O aplicativo nunca rodou em iOS**, nem em simulador. Publicar nas duas lojas significa descobrir
o comportamento em iOS do zero, e é o item de maior incerteza deste roadmap — pode custar horas ou
semanas, e não há como saber antes de executar.

### 8 · RevenueCat e cobrança real

O `billing/` atual tem só `FakeProvider` e será descartado. Ver
[ADR-008](decisoes/ADR-008-monetizacao-por-loja.md).

**Sem data.** Não há prazo de publicação definido.

---

## Considerado

Sem decisão, mas com interesse declarado.

| Item | Observação |
|---|---|
| **Opções e derivativos** | Tensiona o limite "não é ferramenta de trade" de [01-PRODUTO](01-PRODUTO.md) |
| **Controle de gastos completo** (tipo Mobills) | Aumentaria a atenção exigida de um público definido por não ter tempo |
| **Otimizador de carteira** (Sharpe, HRP, mínima volatilidade) | O diretório está vazio e será removido. Reconstruir é decisão nova — e é preciso responder se isso serve a quem não tem tempo |

---

## Ideia

Sem compromisso nenhum. Listado para não ser esquecido, e para não ser confundido com plano.

| Item | Observação |
|---|---|
| Day trade na apuração de IR | Alíquota de 20% e apuração própria. Tensiona o mesmo limite das opções |
| Open Finance | Resolveria a tensão central do produto — a atenção exigida — e é o item de maior esforço e maior regulação |
| Sair do Brasil / outros mercados | A premissa brasileira está em toda parte: IR, fuso, BRT, BRAPI, BCB |
| API para terceiros | `[EM DISCUSSÃO]` desde o início |

---

## Fora de escopo

Não é "ainda não": é **não**.

- Home broker, execução de ordem
- Ferramenta para profissional gerir carteira de terceiros
- Rede social de investidores
- Criptomoedas
- Ações internacionais diretas, fora de BDR
- Previdência
- Fiagro, Fi-Infra
- Curso ou conteúdo educacional
- Versão web — ver [ADR-003](decisoes/ADR-003-cliente-unico.md)

---

## Riscos

**Aquisição é o risco número um.** Sem gratuidade, sem landing page e sem presença em loja, não
existe superfície pela qual alguém descubra o produto. A decisão de não ter nada gratuito
([ADR-009](decisoes/ADR-009-trial-e-gratuidade.md)) aponta na direção oposta a esse risco, de forma
consciente e revisável.

**Sustentação do preço.** R$ 9,90 por mês, menos a comissão de loja de 15% a 30%, deixa cerca de
R$ 7 a R$ 8,40 por assinante. Contra isso: Railway, Postgres e a cota da BRAPI. O ponto de equilíbrio
não foi calculado.

**Dependência de fonte única.** A BRAPI é a única fonte de mercado. O disjuntor protege contra queda,
não contra descontinuação nem mudança de preço.

**Regulatório.** Registrado em [ADR-006](decisoes/ADR-006-recomendacao-personalizada.md).

**Um autor.** 37 mil linhas de código, 15 mil de teste, e uma pessoa. O sistema tem testes suficientes
para absorver isso, mas não tem quem o mantenha se o autor parar.
