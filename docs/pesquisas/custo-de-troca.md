# Plano — quanto custa trocar de papel na B3

**Estado:** `[ENCERRADO]` em 2026-10-19 — **o método não mediu spread**: mediu a volatilidade do dia, e a regra do protocolo não foi aplicada. Protocolo `[ACEITO]` pelo autor no mesmo dia, antes da execução

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

## Resultado — 2026-10-19: o método não mediu spread

Retrato de 2026-10-19, de 2005 a 2025. Custo por lado = metade do spread estimado + 0,031% de tarifa.

| Faixa | Ações: papéis-mês | Ações: custo por lado | FIIs: papéis-mês | FIIs: custo por lado |
|---|---|---|---|---|
| Abaixo de R$ 1 milhão | 16.496 | 0,54% | 14.228 | 0,32% |
| R$ 1 a 5 milhões | 9.681 | 0,49% | 4.029 | 0,24% |
| R$ 5 a 20 milhões | 10.579 | 0,49% | 688 | 0,17% |
| Acima de R$ 20 milhões | 17.195 | 0,43% | — | — |

**Pela regra, o custo padrão subiria para 0,45% por lado** (mediana das ações acima de R$ 5 milhões).
**A regra não foi aplicada**, porque a medida não passa numa conferência que se faz sem olhar
nenhum resultado de pesquisa:

- **O spread estimado quase não muda com a liquidez.** Os papéis de mais de R$ 20 milhões por dia
  saem com 0,80% de spread e os de menos de R$ 1 milhão, com 1,02%. Spread de verdade muda muito mais
  que isso entre um papel de bolsa inteira e um de pregão vazio
- **Nos papéis mais líquidos, a estimativa é cerca de 15 vezes o possível.** De 2022 em diante, a
  mediana mensal é 0,48% em PETR4, 0,35% em VALE3, 0,45% em ITUB4 e 0,56% em BBDC4. O spread
  mínimo de PETR4 é um centavo sobre um preço perto de R$ 30, uns 0,03%
- **A estimativa acompanha a volatilidade.** Entre os papéis de mais de R$ 20 milhões, a correlação de
  postos entre o spread estimado e a variação diária mediana do ano é 0,55

Corwin e Schultz separam spread de volatilidade supondo que a variação dentro do dia é pequena perto
do spread. Na B3, em papel líquido, é o contrário. O risco declarado ("ruidoso em dia de muita
volatilidade") era esse, e foi maior do que o protocolo previu.

**Desvio declarado:** o protocolo pedia a tarifa da B3 vigente em cada ano. A tabela oficial de ações à
vista não foi localizada; usou-se 0,031% em todos os anos (0,003756% de negociação + 0,0275% de
liquidação, para pessoa física, por fonte secundária: [Acionista](https://acionista.com.br/quais-tarifas-o-investidor-precisa-pagar/)).
É uma fração pequena do número medido, e não muda a conclusão.

**O que fica:** o custo das pesquisas segue em 0,25% por lado, e a pergunta continua aberta. Medir spread
exige dado de livro de ofertas ou de negócio a negócio, que a base não tem. **Se o autor preferir
aplicar a regra como escrita** (0,45% nas próximas pesquisas), ela só torna as conclusões encerradas mais
fortes, e nenhuma é revista.

Registro em `fiance-trend/backend/registro_custo.jsonl`; o resumo por faixa e por ano em
`fiance-trend/backend/resultados/custo_de_troca.json`.
