# Plano — o ranking de tendência (`fiance-trend/backend/`)

**Estado:** `[CONCLUÍDO]` em 2026-10-12 — **o ranking de tendência não informa** (6 variações, nenhuma
passou no estudo). Protocolo `[ACEITO]` pelo autor no mesmo dia, antes da primeira execução · **Etapa 2 de**
[plataforma](../../historico/PLATAFORMA-2026-10.md)

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
de classe. **ETFs e BDRs ficam de fora** — poucos papéis líquidos antes de 2019 para medir ordem. Com o teto
usado, não entram com estes sinais.

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
histórico de acerto do ranking mês a mês. **Não vai para o app** ([plataforma](../../historico/PLATAFORMA-2026-10.md)).

## Adendo — FIIs com períodos próprios

**Estado:** `[ACEITO]` em 2026-10-12, pelo autor, antes de qualquer sinal rodar em FII. Para escolher os períodos,
olhou-se só o tamanho do universo mês a mês, nunca um retorno ou um sinal.

| | FIIs |
|---|---|
| Liquidez mínima | **R$ 500 mil** de volume mediano em 63 pregões — com ela, há 20 fundos ou mais em todo mês desde jan/2019 |
| Estudo | 2019-01 a 2022-12 (48 meses) |
| Validação | 2023-01 a 2024-12 (24 meses) |
| **Prova** | **2025-01 em diante, lacrada** |
| Sinais | Os mesmos três, com os mesmos parâmetros e na mesma ordem — nada é reajustado para FII |
| Variações | As 3 que sobraram do teto de 6 |
| Medida | A mesma, com as três condições juntas |

**Risco declarado:** 48 meses de estudo é pouco. Um t de 2 com essa amostra exige um sinal forte; um
sinal fraco e real pode não aparecer. É o preço de não ter mercado de FII líquido antes de 2019.

## Resultado em ações — 2026-10-12: nenhum sinal passou no estudo

| # | Sinal | Correlação de postos | t | Acerto do topo | Diferença líquida ao ano | Giro |
|---|---|---|---|---|---|---|
| 1 | Momento ajustado ao risco | 0,030 | 1,56 | 57% | +3,9 pontos | 54% |
| 2 | Distância da média de 200 | 0,017 | 0,93 | 60% | +3,4 pontos | 83% |
| 3 | Inclinação vezes R² | 0,032 | **1,87** | 58% | +3,3 pontos | 62% |

155 meses (2006–2018), 77 ações por mês em média. Registro em `fiance-trend/backend/registro_ranking.jsonl`.

- **Os três apontam na mesma direção, e nenhum com força estatística.** O topo vence o fundo em 57% a
  60% dos meses e paga a troca, mas a correlação mês a mês oscila tanto que o t não chega a 2. Pelo
  protocolo, isso é "não informa": a validação fica lacrada
- **A inclinação vezes R² chegou mais perto** (t de 1,87). Ajustar a janela até passar é exatamente o que
  o teto existe para impedir — a variação não se repete
- **As 3 variações que sobram do teto são dos FIIs**, pelo adendo acima

## Resultado em FIIs — 2026-10-12: nenhum sinal passou, e a tendência se inverte

| # | Sinal | Correlação de postos | t | Acerto do topo | Diferença líquida ao ano | Giro |
|---|---|---|---|---|---|---|
| 4 | Momento ajustado ao risco | 0,038 | 1,04 | 40% | −9,1 pontos | 66% |
| 5 | Distância da média de 200 | −0,040 | −1,39 | 38% | −15,3 pontos | 93% |
| 6 | Inclinação vezes R² | −0,003 | −0,10 | 49% | −11,7 pontos | 69% |

47 meses (2019–2022), 56 fundos por mês em média.

- **Em FII, o topo do ranking perdeu do fundo na maioria dos meses.** O fundo que mais subiu tende a
  devolver no mês seguinte — o contrário de tendência. Com 47 meses, nem isso tem força estatística
- **O giro é alto e a troca custa caro:** a diferença líquida fica entre −9 e −15 pontos ao ano

## Conclusão — 2026-10-12: o ranking de tendência não informa

As 6 variações do teto foram usadas: 3 em ações, 3 em FIIs, nenhuma passou no estudo. A validação e a
prova seguem lacradas e não serão abertas para estes sinais. Rodar mais exige `--forcar`, e fica no
registro.

O que fica para o uso: a tendência no painel é **contexto de risco** — o filtro da
[primeira pesquisa](pesquisa.md) cortou as quedas grandes pela metade —, e não ordem de compra.

## Adendo — 2026-10-19: o corte de risco não se confirmou fora do estudo

O [filtro de risco](filtro-de-risco.md) mediu o filtro na validação (2019–2022): a pior queda ficou
igual à de quem ficou comprado (−47,6%), e o retorno caiu 8,9 pontos ao ano. **O corte das quedas pela
metade só foi visto no estudo.** A tendência no painel segue como contexto, e não como proteção.
