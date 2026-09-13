# ADR-008 — Monetização por loja via RevenueCat; `billing/` atual descartado

**Status:** ACEITO
**Data:** 2026-09-13
**Decidido por:** autor do projeto

## Contexto

O sistema tem uma camada de cobrança construída: `api/billing.py`, `payments/billing.py`,
`payments/provider.py`, tabelas de assinatura e de sessão de checkout, webhook com verificação de
assinatura, idempotência por `processed_webhooks`, e preço travado por assinante.

Com a decisão de cliente único distribuído por loja ([ADR-003](ADR-003-cliente-unico.md)), a cobrança
passa a acontecer **dentro do aplicativo**.

## Problema

**O modelo implementado é incompatível com compra por loja.**

O `billing/` atual pressupõe checkout na web: o servidor abre uma sessão, devolve uma URL, o usuário
paga fora do aplicativo, e o provedor avisa por webhook.

Em compra dentro do aplicativo é o oposto: **a loja processa o pagamento** e o servidor **valida um
recibo**. Não há URL de checkout, e o titular não vem de uma sessão que o servidor abriu.

Há também um fato que a auditoria de 2026-09-13 expôs: `payments/provider.py` contém apenas o
`PaymentProvider` (protocolo) e um **`FakeProvider`**. Nunca houve provedor real. O checkout devolve
`https://checkout.local/...`. **É andaime, não integração.**

## Alternativas

1. **Adaptar** o `billing/` atual para validação de recibo
2. Integrar diretamente com as APIs de Google Play e App Store
3. **RevenueCat**, descartando o `billing/` atual
4. Cobrança fora da loja

A alternativa 4 é proibida pelas regras das lojas para conteúdo digital consumido no aplicativo. A 2
significa manter duas integrações, cada uma com renovação, reembolso, período de graça e mudança de
plano — muito para um autor só.

## Decisão

**RevenueCat, compra dentro do aplicativo. O `billing/` atual é descartado, não adaptado.**

Descartar em vez de adaptar porque o que existe pressupõe um fluxo que deixou de valer, e porque não
há integração real para preservar — apenas o `FakeProvider`.

**O que deve sobreviver à reescrita**, por serem decisões boas independentes do provedor:

| O quê | Por quê |
|---|---|
| Preço travado como **dado** (`price_cents`, `locked`) | Preço de fundador é promessa pública, não memória |
| Idempotência de webhook | Evento repetido é normal, não exceção |
| **Titular vem da sessão, nunca do corpo** | A rota do webhook é pública; a assinatura protege a integridade da mensagem, não a autoridade sobre quem ela nomeia |
| Cerca de plano isolada em `entitlement/` | Ver [03-ARQUITETURA](../03-ARQUITETURA.md) |

O último item é o mais importante: **a cerca de plano não muda.** `entitlement/` não sabe quem é o
provedor de pagamento, e não deve passar a saber.

## Consequências

**Ganhos**

- Uma integração em vez de duas, com renovação, reembolso e período de graça tratados pelo provedor
- A cerca de plano, que é a parte difícil, já está construída e testada

**Custos aceitos**

- Dependência de um terceiro entre o produto e a receita
- Custo do RevenueCat sobre uma assinatura de até R$ 9,90, **somado** à comissão de loja de 15% a
  30%
- Trabalho jogado fora: o `billing/` atual sai inteiro
- **Nada disso pode começar antes das contas de desenvolvedor**, que não existem — ver
  [09-FUTURO](../09-FUTURO.md), item 7

## Referências

- [ADR-009](ADR-009-trial-e-gratuidade.md), [ADR-003](ADR-003-cliente-unico.md)
- `backend/app/payments/`, `backend/app/entitlement/`
