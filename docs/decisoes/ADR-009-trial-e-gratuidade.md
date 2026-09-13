# ADR-009 — Nada gratuito; trial de 14 dias na primeira posição salva

**Status:** ACEITO
**Data:** 2026-09-13
**Decidido por:** autor do projeto

## Contexto

O produto será pago, por assinatura de até R$ 9,90 por mês, com o objetivo inicial de cobrir o custo
de operação. A cerca de plano está construída e **desligada**
(`ENTITLEMENTS_ENABLED=false`).

Duas perguntas precisavam de resposta antes de ligá-la: **o que fica de graça** e **quando o relógio
começa a contar**.

## Problema

### O que fica de graça

Um modelo freemium exige escolher o que a versão gratuita entrega. Entregar pouco não demonstra
valor; entregar muito remove a razão de pagar.

### Quando o trial começa

Se o trial começa no **cadastro**, alguém pode gastar os 14 dias sem nunca ter salvo uma posição — e
perder o período de avaliação sem jamais ter visto o produto funcionando, porque sem carteira não há
o que analisar.

Se começa na **primeira posição salva**, o relógio só corre quando há o que avaliar.

Há um detalhe que o código já resolve e que precisa estar escrito: `start_trial` é chamado na
primeira posição salva **sem consultar `ENTITLEMENTS_ENABLED`**. Toda conta com carteira já carrega
um `trial_ends_at`, muitos deles no passado. Ligar a flag sem uma âncora derrubaria a base inteira
para Free num instante, sem volta pelo código.

## Alternativas

**Gratuidade:** (a) nada de graça; (b) carteira e caixa livres, análise paga; (c) leitura livre,
escrita paga.

**Início do trial:** (d) no cadastro; (e) na primeira posição salva.

## Decisão

**Nada gratuito permanente. Trial de 14 dias, começando na primeira posição salva.**

A decisão sobre o início do trial foi reconsiderada durante a entrevista de 2026-09-13: a preferência
inicial era o cadastro, e mudou para a primeira posição ao se examinar a consequência. Isso
**preserva** o invariante existente, e nenhuma mudança de código é necessária.

Três regras sustentam isso:

- **Nada é cercado antes da primeira posição salva.** `entitlement.check` libera tudo enquanto a
  carteira estiver vazia, e nem grava evento de paywall: cercar quem ainda não tem o que analisar é
  cobrar antes de entregar
- "Free com carteira" só existe **depois** de o trial acabar
- **`ENTITLEMENTS_ENABLED_AT` é obrigatória** quando a flag é ligada, e a ausência falha alto no
  startup. O relógio conta do **mais tarde** entre qualificar e a cerca subir

## Consequências

**Ganhos**

- O período de avaliação só corre quando há algo a avaliar
- Ligar a cerca não derruba ninguém de surpresa
- Nenhuma mudança de código: a implementação já é esta

**Custos aceitos, e um deles é grande**

- **Sem gratuidade, não há superfície de descoberta.** Somado à remoção da landing page
  ([ADR-003](ADR-003-cliente-unico.md)) e à ausência de presença em loja, não existe hoje caminho
  pelo qual alguém conheça o produto sem pagar
- Isso aponta na direção **oposta** ao risco número um declarado pelo autor: *ninguém usar /
  aquisição*
- 14 dias é pouco para um produto cujo valor aparece na comparação entre meses — a estimativa de
  gasto variável precisa de meses fechados para existir, e quem acaba de começar não os tem

**Revisão:** esta decisão deve ser revista se a aquisição se mostrar o gargalo, e antes de ligar
`ENTITLEMENTS_ENABLED`. As alternativas (b) e (c) continuam disponíveis e não exigem mudança
estrutural — a régua de plano é dado em `entitlement/plans.py`.

## Referências

- [01-PRODUTO](../01-PRODUTO.md), [09-FUTURO](../09-FUTURO.md)
- `backend/app/entitlement/`
