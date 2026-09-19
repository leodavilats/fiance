# ADR-012 — O alvo é de quem declara

**Status:** ACEITO
**Data:** 2026-09-19
**Decidido por:** autor do projeto

## Contexto

Dois lugares do produto tratavam um número do produto como se fosse escolha da pessoa.

**A reserva de emergência.** `cascata.montar` recebe `reserva_meses_alvo` e `reserva_atual`, a
matemática está escrita e testada desde sempre, e **nenhuma rota passava os dois** — não havia onde
declarar quantos meses guardar. A regra documentada descrevia um passo que a Sobra nunca mostrou.

**A alocação-alvo.** `goal_service.get_goals()` devolvia 30/35/15/15/5 quando nada fora declarado, e
quatro consumidores tratavam isso como meta: o painel desenhava barras "abaixo da meta", o alerta de
rebalanceamento disparava, o `whats_new` acusava desvio. As metas **por setor** já distinguiam o caso
(`declared` na resposta); as de categoria, não.

## Problema

São o mesmo problema com duas caras: **o produto inventava o objetivo de outra pessoa**.

No caso da reserva, o custo era omissão — um passo pronto que ninguém via. No caso da meta, o custo
era pior: o produto **cobrava** a pessoa por não cumprir um alvo que ela nunca escolheu, e oferecia o
botão "Ajustar meta" para uma meta que não era dela.

A tentação, nos dois casos, era escolher um número: "seis meses de reserva" é o padrão de mercado, e
30/35/15/15/5 é uma alocação defensável. Mas a régua de dívida do próprio produto já proíbe isso em
outro contexto — *dívida se classifica por custo, nunca por tipo; sem taxa informada não há classe* —
e a razão é a mesma: um número plausível apresentado como conclusão é pior que a ausência dele,
porque não se pode conferir.

## Decisão

**Sem declaração, não há alvo — e sem alvo, não há julgamento.**

**Reserva.** Declara-se **só o número de meses**, em `preferences.reserve_months_target`. Os outros
dois lados já existem e não se declaram de novo:

- a **base** é o gasto fixo do próprio caixa, que `gasto_fixo_mensal` já calcula;
- o **saldo** é a renda fixa de **liquidez diária**, que o sistema já modela — papel preso até o
  vencimento não cobre emergência, então não conta.

Nulo é o estado normal, não um valor faltando: sem alvo, a cascata não mostra o passo.

**Meta de alocação.** `GET /goals` passa a carregar `declared`, como as metas por setor já faziam.
Quem julga passa por `goals_for_judgement()`, que devolve lista vazia quando nada foi declarado — e
aí o alvo sai `null`, o delta sai `null`, e o alerta de rebalanceamento não dispara. A composição
continua sendo mostrada, porque ela é fato; o que sai é o julgamento sobre ela.

O padrão 30/35/15/15/5 **continua existindo** como ponto de partida oferecido na tela de metas, agora
dizendo o que é: *"Este é o ponto de partida do produto, e não a sua escolha. Enquanto for assim,
nada no aplicativo cobra desvio contra ele."*

## Consequências

**Ganhos**

- O passo da reserva deixa de ser código inalcançável depois de meses testado e nunca exibido
- Ninguém é cobrado por um objetivo que não escolheu
- O `declared` das metas por setor, que existia no modelo Dart **sem nenhum consumidor**, ganhou um

**Custos aceitos**

- Quem nunca declarou meta perde o alerta de rebalanceamento que recebia. É a intenção: o alerta era
  sobre um alvo alheio
- A reserva depende de a pessoa cadastrar renda fixa com liquidez diária. Quem guarda reserva fora do
  sistema verá o passo pedir mais do que precisa — e a alternativa, um saldo declarado à mão, é um
  número que envelhece sozinho e que ninguém volta para atualizar
- Uma coluna nova (`reserve_months_target`), com migração `0010_alvo_de_reserva`

## Referências

- `backend/app/cashflow/cascata.py` · `backend/app/api/cashflow.py`
- `backend/app/services/goal_service.py` — `goals_for_judgement()`
- `backend/tests/test_alvo_de_reserva.py`, `backend/tests/test_meta_declarada.py`
- [02-DOMINIO](../02-DOMINIO.md) · [ADR-011](ADR-011-preco-justo-e-faixa.md)
