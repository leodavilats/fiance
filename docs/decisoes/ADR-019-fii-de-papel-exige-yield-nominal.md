# ADR-019 — FII de papel exige yield nominal, por uma classificação mantida no código

**Status:** ACEITO · complementa a [ADR-014](ADR-014-um-modelo-por-classe.md) no modelo de FII
**Data:** 2026-09-25
**Decidido por:** autor do projeto, que delegou a escolha do caminho

## Contexto

Pela ADR-014, o preço justo de FII é `distribuição recorrente ÷ y`, com `y` = juro real de longo
prazo + 3 pontos de prêmio. Capitalizar por juro real supõe que a distribuição cresce com a
inflação, como o aluguel de um FII de tijolo.

## Problema

O FII de papel distribui como rendimento a correção monetária dos recebíveis (CRIs). A distribuição
sobe com a inflação sem que o principal suba. Capitalizá-la por juro real conta a inflação duas
vezes, e todo FII de papel parecia barato. Na amostra de 2026-09-23, MXRF11 foi o único ativo a
sair "abaixo do preço justo".

A BRAPI não entrega o tipo do fundo. O setor que ela informa para FII é "Finance" ou
"Miscellaneous", sem relação com papel ou tijolo.

## Alternativas

1. **Manter tudo como tijolo** e declarar a limitação. O erro fica.
2. **Inferir o tipo pelo nome ou pelo dividend yield.** Seria inventar dado.
3. **Uma lista de FIIs de papel mantida no código**, com data de revisão, como a tradução de setores
   em `analysis/sectors.py`. É dado de referência declarado, e não fonte externa.

## Decisão

A alternativa 3. `analysis/fii_segments.py::PAPER_FIIS` lista os fundos de papel (recebíveis
imobiliários) de maior liquidez, com `PAPER_REVIEWED_ON`. Para eles, o yield exigido é **nominal**:

```
y_papel = máx(Selic média de 10 anos − meta de inflação, 3%) + 3 pontos + meta de inflação
```

A premissa `fii_segment` diz qual leitura foi usada, e a razão exibida explica por que o yield inclui
a inflação. FII fora da lista segue lido como tijolo, com `fii_segment = nao_classificado`.

## Consequências

Na amostra de 2026-09-25, MXRF11 passa de "Abaixo do preço justo" (faixa R$ 11,16 a R$ 13,80,
preço R$ 9,10) para "No preço justo" (faixa R$ 8,68 a R$ 10,19), com qualidade **firme**: o VPA, que
é insumo independente, cai dentro da faixa nova. Os FIIs de tijolo não mudam.

**Custos aceitos**

- A lista envelhece: fundo novo ou que mude de estratégia não entra sozinho. A revisão é manual, e a
  data fica no código
- FII de papel fora da lista continua parecendo barato. A limitação fica declarada em
  [04-CALCULOS](../04-CALCULOS.md)
- Fundo híbrido é classificado pela maior parte da carteira

## Referências

- `backend/app/analysis/fii_segments.py` · `backend/app/analysis/fair_price.py::_dividend_lens`
- `backend/tests/test_fii_de_papel.py`
