# Plano — quanto custa trocar de papel na B3

**Estado:** `[PROPOSTO]` em 2026-10-19 — aguarda o aceite do autor; nada rodou

## A pergunta

> Quanto custa comprar ou vender um papel da B3, por faixa de liquidez, de 2005 a 2025, e o 0,25% por
> lado que as pesquisas usam está perto disso?

Toda pesquisa de carteira e de ranking depende do custo de troca: o giro consumiu a diferença em quase
todas. O custo usado (0,25% por lado na [pesquisa](pesquisa.md), 0,5% por troca no [ranking](ranking.md))
foi declarado, e não medido.

## O método — fixado antes

- **Spread estimado por Corwin e Schultz (2012)**, a partir da máxima e da mínima de dois pregões
  seguidos, na `cotacao` bruta. Estimativa negativa vira zero, como no artigo
- **Custo por lado = metade do spread + tarifa da B3** vigente no ano, com a tabela citada no resultado
- **Fora da conta:** par de pregões com evento no intervalo, dia com `salto_sem_evento` e dia em que o
  fechamento ou a média ficam fora da faixa entre mínima e máxima (a B3 publica dias assim, ver
  [11-DADOS-DE-MERCADO](../11-DADOS-DE-MERCADO.md))
- **Média mensal por papel**; mediana por faixa de liquidez e por ano

| Faixa (volume mediano de 63 pregões) | Ações | FIIs |
|---|---|---|
| Abaixo de R$ 1 milhão | ✓ | ✓ |
| R$ 1 a 5 milhões | ✓ | ✓ |
| R$ 5 a 20 milhões | ✓ | ✓ |
| Acima de R$ 20 milhões | ✓ | ✓ |

## O que o resultado pode mudar — e o que não pode

- **Se o custo mediano das ações acima de R$ 5 milhões passar de 0,25% por lado**, o custo padrão das
  próximas pesquisas sobe para o medido. Se for menor, o padrão fica: errar para o lado caro é
  conservador
- **Nenhuma conclusão encerrada é revista.** Custo maior só reforça o "não achei vantagem". Custo menor
  não reabre o teto: rodar de novo com custo menor é procurar até passar

## Risco declarado

- **Corwin-Schultz é ruidoso** em papel pouco líquido e em dia de muita volatilidade. Por isso a medida
  é a mediana, e por faixa
- **Não há livro de ofertas na base.** O spread é estimado pelo preço; o custo de impacto de uma ordem
  grande não entra
