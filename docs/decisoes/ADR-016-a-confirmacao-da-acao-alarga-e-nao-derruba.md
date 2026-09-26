# ADR-016 — Na ação, o dividendo longe da faixa alarga a leitura, e não a derruba

**Status:** ACEITO · substitui em parte a [ADR-014](ADR-014-um-modelo-por-classe.md) — a regra de
qualidade para a confirmação da ação; o resto segue valendo
**Data:** 2026-09-25
**Decidido por:** autor do projeto, que escolheu a alternativa 1 entre as apresentadas pela
auditoria

## Contexto

Pela ADR-014, confirmação a mais de 30% da faixa torna a qualidade frágil, e frágil nunca passa de
"abaixo" ou "acima" do preço justo. A
[auditoria de 2026-09-25](../historico/AUDITORIA-DO-PRECO-JUSTO-2026-09-25.md) registrou no item R-002 que,
na ação, a confirmação não é independente do principal. A
[ADR-015](ADR-015-a-faixa-cobre-os-dois-cenarios.md) deixou o item aberto como custo declarado.

## Problema

A confirmação da ação, `D × (1 + g_c) ÷ (d − g_c)`, usa a mesma taxa `d` do principal e um
crescimento `g_c` tirado dele. O dividendo `D` já entra no payout que define esse crescimento. Na
perpetuidade, a confirmação distribui a fração observada `D ÷ LPA`, e o principal distribui
`1 − g_T ÷ ROE`. As duas só coincidem quando o crescimento é o de longo prazo.

Medido em 2026-09-25 sobre 31 ativos reais, a concordância é quase função do payout:

| Payout | Ativos | Concordância |
|---|---|---|
| abaixo de 45% | BBAS3, CMIG4, EQTL3, ITUB4, RADL3 | a mais de 30% do piso |
| entre 45% e 60% | B3SA3, ITSA4, KLBN11, PETR4, WEGE3 | fora, a até 30% |
| 60% ou mais | ABEV3, BBDC4, EGIE3, SANB11, TAEE11, VALE3 | dentro |
| 100%, com ROE abaixo da taxa | RENT3, VIVT3 | acima do teto: o principal distribui só `1 − g_T ÷ ROE` na perpetuidade |

"Frágil" deveria dizer que a evidência é fraca. Aqui dizia que o payout é baixo. Com a faixa da
ADR-015, CMIG4, ITUB4 e RADL3 caíram para frágil sem que nenhum dado discordasse.

## Alternativas

1. **Na ação, confirmação longe da faixa conta como "ampla", e não como "frágil".** A distância
   continua declarada (`agreement`, `methods_disagree`) e continua pesando contra "firme".
2. **Manter a regra** e declarar na ADR que a divergência é esperada quando o crescimento não é o
   de longo prazo.
3. **Reformular a confirmação** para distribuir na perpetuidade a mesma fração que o principal.
   Rejeitada: seria outro método, e não uma correção.

## Decisão

A alternativa 1, só para a ação. **No FII continua frágil:** lá a confirmação é o VPA, insumo
independente da distribuição, e discordar dela em mais de 30% é evidência.

`_quality`, em `backend/app/analysis/fair_price.py`, decide pelo `principal`. A razão explica por
que a distância alarga, em vez de só dizer que ela existe.

## Consequências

Na mesma amostra, com a faixa da ADR-015:

| Qualidade | Antes | Depois |
|---|---|---|
| Firme | 5 | 5 |
| Ampla | 10 | 14 |
| Frágil | 11 | 7 |

CMIG4, ITUB4, RADL3 e VIVT3 passam de frágil a ampla. Os 7 que seguem frágeis estão assim por
evidência dos dados: corte de distribuição (BBAS3, PETR4, PRIO3) ou lucro instável (EQTL3,
KLBN11, SUZB3, VALE3). RADL3 e VIVT3 voltam a "Bem acima do preço justo": com margem de −30% ou
pior, o limite de etiqueta dos frágeis era o que os segurava.

**Custo aceito:** a confirmação da ação deixa de poder rebaixar a leitura sozinha. Ela ainda
impede "firme" quando fica fora da faixa. A confiança máxima de quem tem confirmação longe passa de
baixa para média.

## Referências

- `backend/app/analysis/fair_price.py` · `backend/tests/test_confirmacao_que_nao_e_independente.py`
- [AUDITORIA-DO-PRECO-JUSTO](../historico/AUDITORIA-DO-PRECO-JUSTO-2026-09-25.md), item R-002 ·
  [04-CALCULOS](../04-CALCULOS.md)
