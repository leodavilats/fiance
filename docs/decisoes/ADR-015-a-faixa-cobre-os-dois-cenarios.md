# ADR-015 — A faixa da ação cobre os dois cenários de crescimento

**Status:** ACEITO · substitui em parte a [ADR-014](ADR-014-um-modelo-por-classe.md) — a faixa da
ação; o resto da ADR-014 segue valendo
**Data:** 2026-09-25
**Decidido por:** autor do projeto, que escolheu a alternativa 2 entre as apresentadas pela
auditoria

## Contexto

A [auditoria da especificação do preço justo](../historico/AUDITORIA-DO-PRECO-JUSTO-2026-09-25.md), de
2026-09-25, marcou como bloqueador o item R-001. Pela ADR-014, a faixa da ação vai "do cenário sem
crescimento e com 1 ponto a mais de taxa ao cenário com crescimento e 1 ponto a menos". A intenção
se sustenta. A implementação do piso, não.

## Problema

O piso zerava o crescimento, mas mantinha a fração distribuível do cenário com crescimento,
`q = 1 − g/ROE`. A empresa retinha lucro e não crescia com ele. Isso contradiz a identidade
`g = ROE × retenção`, que o próprio modelo principal usa: crescimento zero é retenção zero.

Com ROE de 15%, sem dividendo e d = 15%, `q` é zero. O fluxo explícito do piso sumia, e o piso era
só o valor terminal: **R$ 3,03, contra um central de R$ 6,97**. No cenário coerente, o piso seria
R$ 6,09. A faixa media a penalidade de reter sem crescer, e não a incerteza da premissa. A razão
teto/piso ficava entre 1,7 e 3,0 nos casos comuns, e "firme", que exige no máximo 1,5, era quase
inalcançável para ação que cresce.

A garantia de que o piso nunca passava do teto dependia dessa incoerência. Quando ROE < d, crescer
destrói valor, e o cenário sem crescimento coerente vale **mais** que o com crescimento: com ROE de
6%, R$ 4,36 contra um teto de R$ 2,91.

## Alternativas

1. **Manter os números e renomear o piso** para "retém sem crescer". Não há risco numérico, mas a
   faixa continua medindo a penalidade da retenção.
2. **Dois cenários coerentes, e a faixa é o envelope deles.** Sem crescimento, a empresa distribui
   todo o lucro. Piso é o menor dos dois cenários a d + 1 ponto; teto é o maior dos dois a
   d − 1 ponto.
3. **Só corrigir a fração distribuível do piso**, sem o envelope. Rejeitada: com ROE < d, o piso
   passaria do teto.

## Decisão

A alternativa 2.

```
com(d') = V(d', g, q = 1 − g/ROE)
sem(d') = V(d', 0, q = 1)

piso    = mín(com(d + 1 ponto), sem(d + 1 ponto))
teto    = máx(com(d − 1 ponto), sem(d − 1 ponto))
central = com(d)
```

A ordem continua garantida: `piso ≤ com(d+1) < com(d) = central < com(d−1) ≤ teto`.

O central não muda: ele é o cenário com o crescimento que o lucro retido sustenta. Muda só o que a
faixa diz ser a incerteza sobre ele.

`premises.value_without_growth` passa a ser `sem(d)`, e `premises.growth_creates_value` diz se
`com(d) > sem(d)`. Quando crescer consome valor, a razão diz isso, e o falsificador de crescimento
não aparece: se o crescimento não se confirmar, o valor sobe.

## Consequências

Medido em 2026-09-25 sobre os mesmos dados, antes e depois: 31 ativos pela coleta real, BRAPI e
SGS, com Selic média de 10 anos de 9,48%.

| Qualidade | Antes | Depois |
|---|---|---|
| Firme | 5 | 5 |
| Ampla | 13 | 10 |
| Frágil | 8 | 11 |
| Sem faixa | 5 | 5 |

| Etiqueta | Antes | Depois |
|---|---|---|
| No preço justo | 13 | 12 |
| Abaixo | 1 | 2 — entra CMIG4 |
| Acima | 5 | 7 |
| Bem acima | 7 | 5 — saem RADL3 e SANB11 |
| Sem preço justo | 5 | 5 |

Entre as 20 ações com faixa, as de razão teto/piso acima de 1,5 caíram de **12 para 5**. Os pisos
subiram de zero (RENT3 e VIVT3, que já não cresciam) a 59% (SUZB3). FII, BDR e ETF não mudam.

**Ganhos**

- A faixa da ação passa a medir a incerteza da premissa de crescimento, nos dois sentidos
- A regra de largura volta a discriminar
- Com ROE abaixo da taxa, a tela diz que crescer consome valor, em vez de tratar o crescimento como
  a hipótese otimista

**Custos aceitos**

- **Três ações caem para frágil sem que nenhum dado tenha mudado**: CMIG4, ITUB4 e RADL3. O piso
  subiu, e a confirmação por dividendo ficou a mais de 30% abaixo dele. É o item R-002 da auditoria,
  agora medido: na amostra, payout abaixo de 45% leva a confirmação para longe da faixa, e payout
  acima de 60% a traz para dentro. A concordância é quase função do payout, e não evidência
  independente. **Segue aberto**, para decisão própria.
- Mais ações saem "abaixo do preço justo" quando o mercado precifica pouco crescimento

## Referências

- `backend/app/analysis/fair_price.py` · `backend/app/analysis/falsifiers.py` ·
  `backend/app/analysis/decision.py`
- `backend/tests/test_faixa_coerente.py`
- [AUDITORIA-DO-PRECO-JUSTO](../historico/AUDITORIA-DO-PRECO-JUSTO-2026-09-25.md), itens R-001 e R-002 ·
  [04-CALCULOS](../04-CALCULOS.md)
