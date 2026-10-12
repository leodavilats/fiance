# Plano — o ranking de tendência (`trend-backend/`)

**Estado:** `[ACEITO]` em 2026-10-12, pelo autor — antes da primeira execução · **Etapa 2 de** [plataforma](plataforma.md)

## A pergunta

> Ordenar os ativos de uma classe pela força da tendência, no último pregão do mês, diz quais vão render
> mais **no mês seguinte**?

Não é a pergunta da [primeira pesquisa](pesquisa.md), que era "uma carteira bate o CDI". Aqui o que se
mede é a **ordem**: se o topo do ranking rende mais que o fundo, de forma consistente e fora da
amostra, o ranking informa — mesmo que nenhuma carteira montada com ele bata o CDI.

## Universo — um ranking por classe

| Classe | Desde | Liquidez mínima (volume mediano de 63 pregões) |
|---|---|---|
| Ações | 2005 | R$ 5 milhões |
| FIIs | 2010 | R$ 1 milhão |

Fora a liquidez, o universo segue as regras da primeira pesquisa: 252 pregões de história, preço acima
de R$ 1 e nenhum salto sem evento no último ano.

**FIIs adiados — decidido em 2026-10-12, antes de qualquer execução.** O mercado de FII era pequeno
demais antes de 2019: com R$ 1 milhão de piso, nenhum mês do estudo (2010–2018) tem 20 fundos; com
R$ 100 mil, só 64 de 108 meses, com quintos de 4 fundos. FIIs ganham períodos próprios num adendo,
escrito antes de rodar qualquer sinal neles, e usam as 3 variações que sobrarem do teto.

Classes não se misturam: uma ação e um FII não têm a mesma volatilidade, e o ranking viraria um ranking
de classe. **ETFs e BDRs ficam de fora** nesta etapa — poucos papéis líquidos antes de 2019 para medir
ordem. Entram quando a validação tiver amostra.

## A medida de acerto — fixada antes da primeira execução

A cada fim de mês: o ranking pelo sinal, e o retorno total de cada ativo no mês seguinte.

| Medida | O que é | Para passar no estudo |
|---|---|---|
| **IC** | Correlação de postos (Spearman) entre o sinal e o retorno do mês seguinte, média dos meses | **≥ 0,03, com t ≥ 2** |
| **Acerto do topo** | Meses em que o quinto mais bem colocado rende mais que o quinto pior | **≥ 55%** |
| **Diferença líquida** | Retorno do quinto do topo menos o do fundo, ao ano, descontado o giro a 0,5% por troca | **> 0** |

**As três juntas.** IC alto com diferença líquida negativa é ranking que acerta e não paga a troca.

## Os períodos são os mesmos — e o estudo já foi visto

Estudo 2005–2018, validação 2019–2022, **prova 2023 em diante, lacrada**. A validação também segue
fechada: a primeira pesquisa não abriu nenhuma das duas.

**Risco declarado:** o estudo de ações já foi olhado com momento e filtro de tendência. Um sinal parecido
com os de lá não é descoberta nova. Por isso a régua é a validação, não o estudo.

## Teto e régua

- **Teto: 6 variações**, somando as duas classes. Variação é um par sinal + parâmetros numa classe
- **Passar no estudo libera a validação**, uma vez por variação. Passar na validação libera a prova, uma vez
- **Se nada passar a validação dentro do teto, a conclusão é "o ranking não informa"**, e fica registrada
  — como a da primeira pesquisa

## Sinais candidatos, na ordem em que entram

1. **Momento ajustado ao risco** — retorno de 12 meses sem o último, dividido pela volatilidade diária
   anualizada do mesmo período
2. **Distância da média de 200 pregões**, em desvios-padrão
3. **Inclinação da reta do log do preço em 126 pregões, vezes o R²** — tendência que é reta, não salto

Cada candidato numa classe é uma variação. A ordem acima é a ordem de gasto do teto.

## Regras

- **Só o preço até o dia.** O sinal usa o preço ajustado por evento, **sem provento** — o rendimento de
  FII estimado pela CVM só se sabe semanas depois do mês, e usá-lo no sinal seria olhar o futuro. O
  **alvo** (retorno do mês seguinte) usa o retorno total
- **Dia de salto sem evento** conta como retorno zero, no sinal e no alvo
- **Ativo que deixa de negociar** no mês seguinte sai daquele mês, com aviso no relatório
- **Mínimo de 20 ativos no universo do mês**; mês com menos não entra na média
- **Toda execução vai para o `registro.jsonl`**, com a classe, como na primeira pesquisa

## O que sai, se passar

No painel: o ranking do último fim de mês por classe, a posição e o percentil de cada ativo, e o
histórico de acerto do ranking mês a mês. **Não vai para o app** ([plataforma](plataforma.md)).
