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
| [011](ADR-011-preco-justo-e-faixa.md) | Preço justo como faixa; leitura de tendência declarada | `SUBSTITUÍDO EM PARTE` por 014 | 2026-09-19 |
| [012](ADR-012-o-alvo-e-de-quem-declara.md) | Sem alvo declarado não há julgamento | `ACEITO` | 2026-09-19 |
| [013](ADR-013-o-tecnico-nao-decide.md) | O técnico não decide, e a faixa carrega a própria incerteza | `SUBSTITUÍDO EM PARTE` por 014 | 2026-09-20 |
| [014](ADR-014-um-modelo-por-classe.md) | Um modelo por classe, e a faixa é das premissas dele | `SUBSTITUÍDO EM PARTE` por 015 | 2026-09-23 |
| [015](ADR-015-a-faixa-cobre-os-dois-cenarios.md) | A faixa da ação cobre os dois cenários de crescimento | `ACEITO` | 2026-09-25 |
| [016](ADR-016-a-confirmacao-da-acao-alarga-e-nao-derruba.md) | Na ação, o dividendo longe da faixa alarga a leitura, e não a derruba | `ACEITO` | 2026-09-25 |

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
