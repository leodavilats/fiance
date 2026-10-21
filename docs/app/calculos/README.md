# O aplicativo — cálculos

Cada número que o app afirma, com entrada, fórmula, saída e **limitação**. O **código é a fonte de
verdade**; estes documentos são o espelho auditado, com âncora em cada fórmula. Se uma fórmula aqui
divergir do código, o código está certo e o documento tem um bug.
Última revisão: 2026-10-21

**A cotação de toda conta é o último fechamento** da base de mercado, lido pela API de dados, e não o
pregão em andamento; o Ibovespa é medido pelo BOVA11, porque a base não tem o índice
(`collectors/universal.py::fetch_ibov_history`).

**Nenhum número de posição antecipa retorno.** De 2011 a 2017, o veredito não ordenou o retorno dos
12 meses seguintes, nem com a taxa da ADR-028
([calibracao](../../pesquisa/estudos/calibracao.md),
[calibracao-com-a-taxa-nova](../../pesquisa/estudos/calibracao-com-a-taxa-nova.md)).

| Documento | O que calcula | Onde vive |
|---|---|---|
| [Preço justo](preco-justo.md) | Modelo por classe, taxa, faixa, confirmação, qualidade, margem de segurança, premissas e limitações | `analysis/fair_price.py` |
| [Score, veredito e falsificadores](score-e-veredito.md) | Score por perfil, bandas, etiqueta pela margem, confiança, falsificadores, varredura de quedas | `analysis/scoring.py`, `analysis/decision.py`, `analysis/falsifiers.py`, `services/dip_service.py` |
| [Carteira](carteira.md) | Saúde da carteira, projeção de patrimônio, rebalanceamento, renda fixa, proventos recebidos | `analysis/`, `services/dividends_service.py` |
| [Imposto](imposto.md) | Apuração mensal, day trade, isenção, compensação | `ledger/apuracao.py` |
| [Caixa, dívida e cascata](caixa.md) | Livre agora e sobra, régua de dívida, cascata da sobra | `cashflow/` |

---

## Onde cada limiar vive

| Limiar | Arquivo | Espelho |
|---|---|---|
| Bandas de score | `analysis/score_ruler.py` | `mobile/lib/core/score_ruler.dart` |
| Limiares de veredito | `analysis/decision.py` | — (a régua de margem do Dart é de exibição) |
| Premissas do preço justo | `analysis/fair_price.py` | — |
| Pesos por perfil | `analysis/scoring.py` | — |
| Alíquotas e isenção | `ledger/apuracao.py` | — |

**Mudar um limiar exige as duas plataformas, e o Python é o primeiro.** Réguas divergentes fazem a
tela dizer "boa oportunidade" sobre um número que o servidor classificou como neutro.
