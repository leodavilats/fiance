# Caixa, dívida e cascata

Espelho auditado do código, que é a fonte de verdade: fórmula divergente é bug deste documento.

---

## Caixa: livre agora e sobra

`cashflow/month.py`

```
livre_agora  = entrou − saiu − comprometido            ← FATO
sobra_piso   = livre_agora − gasto_variável_esperado_alto   ← PROJEÇÃO
sobra_teto   = livre_agora − gasto_variável_esperado_baixo  ← PROJEÇÃO
```

**A estimativa sai de até 3 meses fechados da própria pessoa** (`MESES_DE_BASE = 3`), sobre as
categorias variáveis. Sem base, `tem_faixa` é falso e a sobra é o próprio `livre_agora`.

Categorias fora da base: `provento` e `reembolso` não são renda recorrente; `divida` não é consumo.

---

## Régua de dívida

`cashflow/debt.py`

```
classe = CARA          se taxa_mensal > referência
       = ADMINISTRÁVEL se taxa_mensal ≤ referência
       = SEM_TAXA      se a taxa não foi informada
```

**Referência**, em ordem: o retorno mensal da carteira da pessoa → o CDI do BCB → sem referência,
sem classe.

**`taxa_de_virada` = a referência.** É o falsificador: a taxa em que o veredito muda.

**Conversão de taxa anual para mensal é por juros compostos:**

```
mensal = (1 + anual)^(1/12) − 1
```

Dividir por 12 superestima a referência e **afrouxa** a régua — 12% ao ano dariam 1,0% em vez de
0,9489%, e uma dívida a 0,97% ao mês sairia como administrável. O erro cairia do lado de não avisar.

---

## Cascata da sobra

`cashflow/cascata.py` — ordem fixa, cada passo com motivo e falsificador.

**1 · Dívida cara** — enquanto houver saldo classificado como caro, ele vem antes de tudo. O motivo
compara a taxa da dívida com o que a carteira rende, e nomeia a fonte da referência.

**2 · Reserva** — só existe com **alvo declarado em meses do próprio gasto fixo**. O gasto fixo sai
da média dos últimos 3 meses das categorias fixas realizadas. O produto não inventa seis meses.

O alvo em meses é declarado em `preferences.reserve_months_target`, e **nada mais é declarado**: a
base é o gasto fixo do próprio caixa, e a reserva atual é a renda fixa de **liquidez diária** —
papel preso até o vencimento não cobre emergência. Sem alvo, o passo não aparece. Ver
[ADR-012](../../decisoes/ADR-012-o-alvo-e-de-quem-declara.md).

**3 · Aporte** — o que sobrou. Se houver meta de alocação, a ordem sai pelo desvio; sem meta, pelo
score.

**A cascata pode terminar sem passo de aporte, e isso é sucesso.** Com dívida cara consumindo a
sobra inteira, a resposta certa é não aportar.
