# ADR-011 — O preço justo é uma faixa, e o que não tem método diz que não tem

**Status:** SUBSTITUÍDO EM PARTE pela [ADR-014](ADR-014-um-modelo-por-classe.md) — a faixa passou a
ser das premissas de um modelo por classe, e a leitura de tendência saiu
**Data:** 2026-09-19
**Decidido por:** autor do projeto

**Nota (2026-09-25):** os campos legados `consensus`, `consensus_methods`, `bazin` e `dcf` saíram da
resposta no commit `f8c2609`; a consequência que os mantinha não vale mais.

## Contexto

O preço justo saía como **média aritmética** dos métodos aplicáveis ao ativo: Bazin, Graham e lucros
descontados para ação; Bazin e VPA para FII; Bazin sozinho para ETF.

Em 2026-09-13, medindo 33 ativos em produção, 55% recebia sinal de venda. O remédio aplicado no mesmo
dia foi **abster-se** quando os métodos discordassem por 2× ou mais.

A medição de **2026-09-19**, sobre 35 ativos, mostrou o que o remédio custou:

| | |
|---|---|
| Ações na amostra | 22 |
| Ações sem veredito (`UNKNOWN`) | **11** |
| ETFs com preço justo | **0 de 4** — `consensus: null`, `consensus_methods: 0` |

Metade das ações passou a não ter leitura nenhuma. E WEGE3, que motivou a auditoria, continuava
`STRONG_SELL` com confiança 0,75: Bazin R$ 12,94, lucros descontados R$ 23,77, média R$ 18,36, preço
R$ 51,78 — dispersão 1,84, logo abaixo do corte, então o veredito saía.

## Problema

**A média é de estimadores que não medem a mesma coisa.**

- **Bazin** é `dividendo médio ÷ yield exigido`. Não estima o negócio: diz a que preço aquele fluxo
  de dividendo entrega o yield que *você* pediu. É um teto de compra para um objetivo de renda.
- **Graham** olha lucro e patrimônio, e só vale dentro da própria faixa (P/L 15, P/VP 1,5).
- **Lucros descontados** olham crescimento.

Somar os três e dividir por três produz um número que nenhum deles sustenta — e a "dispersão" que
disparava a abstenção era apenas o sintoma disso. Pior: a abstenção calava justamente onde os métodos
tinham mais a dizer, porque discordância entre métodos **é informação**, não ausência dela.

Havia um segundo caso, de outra natureza: o **ETF de índice**, para o qual nenhum método se aplica —
não há LPA, VPA nem dividendo que os sustente. Ali o produto tinha uma régua escondida: o
`opportunity_service` sobrescrevia o veredito por RSI e tendência, e a tela de análise não. O mesmo
ETF saía `Comprar (momentum)` no Descobrir e `Sem dados suficientes` na análise, e o veredito por
momentum não trazia falsificador nenhum.

## Alternativas

1. **Faixa no lugar da média**, com o veredito saindo da posição do preço nela
2. **Bazin só em ativo de renda**, gatilhado por um limiar de yield histórico
3. **Manter a abstenção**, aceitando metade da base sem veredito
4. Ponderar o consenso por classe de empresa

A 2 exigiria um limiar inventado — o mesmo tipo de número de mercado solto que a régua de dívida
proíbe. A 4 é a 2 com mais parâmetros arbitrários. A 3 é o estado que a medição condenou.

## Decisão

**O preço justo sai como faixa**, do método mais conservador ao mais otimista, e **a margem de
segurança é medida contra a borda**:

```
preço < piso   →  margem = (piso - preço) / piso      (a favor)
preço na faixa →  margem = 0                           (não há margem)
preço > teto   →  margem = (teto - preço) / teto       (contra)
```

Isso segue a regra que a projeção de patrimônio já obedece — *faixa, nunca número único* — e tem três
consequências que resolvem o problema na raiz:

- **Comprar exige preço abaixo do método mais pessimista.** É mais conservador que comparar com a
  média, e é conservador do lado certo.
- **Faixa larga vira sinal, não silêncio.** Quando os métodos discordam muito, o preço tende a cair
  dentro da faixa, e "dentro da faixa" é uma leitura legítima: não há margem a favor nem contra.
- **A abstenção por dispersão sai.** O `methods_disagree` continua na resposta e explica a largura,
  mas não cala mais o veredito.

**Para o ativo sem método nenhum, a leitura vem da tendência — e se declara como tal.** A decisão
ganhou o campo `basis`: `band` quando vem da faixa, `trend` quando vem de médias móveis e RSI. O
remendo saiu do `opportunity_service` e a regra passou a viver em `decide()`, um lugar só, de modo
que as duas telas dizem o mesmo. O falsificador de uma leitura de tendência é a **própria tendência
virar** — específico e conferível, e não o falsificador genérico que o invariante proíbe.

### O que a decisão não faz

Não conserta o que a auditoria chamou de A2 e A3: os lucros descontados continuam descontando lucro
e não caixa, com taxa fixa de 13% e P/L terminal 15, e o múltiplo de Graham continua sendo a
constante de 1949. A faixa **mostra** esse desacordo em vez de escondê-lo numa média, o que é
diferente de resolvê-lo.

## Consequências

Efeito medido na amostra de 2026-09-19:

| Ativo | Antes | Depois |
|---|---|---|
| TAEE11 | `UNKNOWN` (dispersão 2,42) | faixa R$ 60,32–146,03, preço R$ 41,91 → margem +30% |
| WEGE3 | `STRONG_SELL`, margem −182% contra a média | faixa R$ 12,94–23,77 → margem −118% contra o teto |
| LREN3 | `UNKNOWN` (dispersão 2,34) | faixa R$ 11,36–26,59, preço R$ 11,17 → margem +1,7% |
| BOVA11 | `UNKNOWN` na análise, `Comprar (momentum)` no Descobrir | mesma leitura de tendência nas duas |

**Ganhos**

- Nenhuma ação com método aplicável fica sem leitura
- A leitura fica mais conservadora do lado da compra, que é onde o erro custa dinheiro
- ETF passa a ter uma única leitura, nomeada, e com o que a derruba

**Custos aceitos**

- **A tela mostra dois números onde mostrava um.** É mais para ler, e é o preço de não fingir
  precisão que não existe
- `consensus` continua na resposta como média dos métodos, agora sem decidir nada. Fica porque o
  contrato de rota o guarda e o aplicativo em loja ainda pode lê-lo
- Ativo com um método só tem faixa de um ponto — e aí a leitura volta a depender de um número só,
  o que a tela declara por `N método na faixa`

## Referências

- `backend/app/analysis/fair_price.py` — `margin_of_safety_in_band`, `fair_low`, `fair_high`
- `backend/app/analysis/decision.py` — `BASIS_BAND`, `BASIS_TREND`, `_verdict_from_trend`
- `test_consenso_que_nao_e_consenso.py` e `test_etf_sem_metodo.py`, removidos pela ADR-014
- [04-CALCULOS](../04-CALCULOS.md) · [ADR-006](ADR-006-recomendacao-personalizada.md)
