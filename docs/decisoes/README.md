# Decisões arquiteturais

Uma decisão entra aqui quando é **cara de reverter** ou quando alguém, daqui a seis meses, olharia o
código e perguntaria *"por que assim?"*.

O porquê vive aqui. O código diz **o quê**; a ADR diz **por quê**, e o que se aceitou perder em
troca. É por isso que justificativa não vai em comentário de código — ver
[06-DESENVOLVIMENTO](../06-DESENVOLVIMENTO.md).

---

## Índice

| # | Decisão | Status | Data |
|---|---|---|---|
| [001](ADR-001-matematica-pura.md) | Matemática pura separada da persistência | `ACEITO` | 2026-09-13 *(retroativa)* |
| [002](ADR-002-razao-fonte-unica.md) | Livro-razão como fonte única da carteira | `ACEITO` | ~2026-08 |
| [003](ADR-003-cliente-unico.md) | Flutter como cliente único; web descontinuada | `ACEITO` | 2026-09-11 |
| [004](ADR-004-dinheiro-decimal.md) | Dinheiro fiscal em `Decimal`, dinheiro de tela em `float` | `ACEITO` | ~2026-07 |
| [005](ADR-005-cache-trocavel.md) | Cache no banco da aplicação, com backend trocável | `ACEITO` | ~2026-09 |
| [006](ADR-006-recomendacao-personalizada.md) | Recomendação personalizada como alvo, sem parecer jurídico | `ACEITO` | 2026-09-13 |
| [007](ADR-007-nivel-de-afirmacao.md) | Nível de afirmação como configuração, não código | `ACEITO` | ~2026-08 |
| [008](ADR-008-monetizacao-por-loja.md) | Monetização por loja via RevenueCat; `billing/` descartado | `ACEITO` | 2026-09-13 |
| [009](ADR-009-trial-e-gratuidade.md) | Nada gratuito; trial de 14 dias na primeira posição salva | `ACEITO` | 2026-09-13 |
| [010](ADR-010-remover-otimizador.md) | Remover `optimizer/` e o enum de estratégias | `ACEITO` | 2026-09-13 |

---

## Formato

```markdown
# ADR-XXX — Título

**Status:** PROPOSTO | ACEITO | SUBSTITUÍDO por ADR-YYY | REVOGADO
**Data:**
**Decidido por:**

## Contexto
## Problema
## Alternativas
## Decisão
## Consequências
## Referências
```

**Status muda; texto não.** Uma decisão revista ganha ADR nova que substitui a anterior — a antiga
fica, marcada. Reescrever a história apaga a razão de a decisão ter parecido certa na época, que é
exatamente o que se quer saber depois.

## Datas aproximadas

As ADRs 002, 004, 005 e 007 documentam decisões **já tomadas e em vigor**, escritas retroativamente
em 2026-09-13. A data é aproximada, inferida do histórico. Estão aqui porque são caras de reverter e
ninguém saberia o motivo olhando só o código.
