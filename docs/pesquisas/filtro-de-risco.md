# Plano — o filtro de tendência corta a queda fora da amostra?

**Estado:** `[ENCERRADO]` em 2026-10-19 — **não confirmado**: fora do estudo, o filtro não cortou a queda e custou 8,9 pontos ao ano. Protocolo `[ACEITO]` pelo autor no mesmo dia, antes da execução, gastando a validação

## A pergunta

> O filtro de tendência, aplicado ao PIBB11, corta a pior queda num período em que nunca foi olhado,
> e quanto retorno isso custa?

É o único efeito que a [pesquisa de carteira](pesquisa.md) achou em todas as variações em que o filtro
entrou: a pior queda caiu de −50% a −61% para −20% a −32%. O painel já usa a tendência como **contexto de
risco** ([ranking](ranking.md), conclusão), mas esse uso hoje se apoia só no período de estudo, que foi
olhado à vontade.

Não é uma busca de retorno. A pesquisa de carteira está encerrada e continua encerrada.

## O que roda — duas execuções, sem nada novo

| Execução | O quê |
|---|---|
| Filtrado | A variação 8 da pesquisa (PIBB11 com filtro), com a **assinatura e os parâmetros do `registro.jsonl`**, sem mudar nada |
| Comprado sempre | PIBB11 o tempo todo, com o mesmo custo e o mesmo imposto |

As regras da simulação são as da pesquisa de carteira.

## Período: a validação, uma vez

**2019-01 a 2022-12.** Nenhuma hipótese da pesquisa de carteira passou no estudo, então essa validação
nunca seria aberta para retorno. Usá-la aqui gasta a validação **para esta pergunta**, uma vez, e isso é
decisão do autor. A prova (2023 em diante) segue lacrada.

## A medida — fixada antes

| Medida | Para confirmar |
|---|---|
| Pior queda do filtrado | **Até 2/3 da pior queda do comprado sempre** (corta pelo menos um terço) |
| Volatilidade anual | **Menor** que a do comprado sempre |
| Retorno anual, filtrado menos comprado sempre | **≥ −3 pontos**: o preço máximo aceito pelo seguro |

**As três juntas confirmam.** Sem as três, a conclusão é "não confirmado fora do estudo", e o texto de
contexto de risco do painel passa a dizer que o efeito só foi visto no estudo.

## Risco declarado

- **Uma queda domina o período.** Março de 2020 é quase certamente a pior queda dos dois lados. O
  relatório mostra também a segunda pior queda e o número de meses fora do mercado
- **Filtro de tendência perde em mercado que cai e volta rápido.** Se o filtro sair depois da queda e
  voltar depois da alta, a pior queda pode cair e o retorno pode cair mais. A terceira condição
  existe para isso
- **Quatro anos é pouco.** A confirmação diz que o efeito sobreviveu a um período novo, não que ele é
  garantido

## Resultado — 2026-10-19: não confirmado

Validação, jan/2019 a dez/2022, 48 meses, retrato de 2026-10-19, assinatura `1be95b0b042a`:

| | Filtrado | Comprado sempre | Condição |
|---|---|---|---|
| Pior queda | −47,6% | −47,6% | Até 2/3 da do comprado: **não** |
| Segunda pior queda | −10,4% | −26,6% | — |
| Volatilidade anual | 23,7% | 28,4% | Menor: **sim** |
| Retorno anual | −5,0% | +3,9% | Diferença ≥ −3 pontos: **não** (−8,9) |
| Meses fora do mercado | 20 de 48 | 0 | — |
| CDI no período | 6,3% ao ano | 6,3% ao ano | — |

- **A queda de 2020 passou inteira por dentro do filtro.** Ela foi do topo de 23/01 ao fundo de
  23/03. O filtro estava comprado no fim de fevereiro e só saiu em 31/03, com o fundo já passado. Um
  filtro que olha uma vez por mês não sai de uma queda que dura semanas
- **Depois, saiu na recuperação.** Ficou fora de abril a maio de 2020, quando o mercado subia, e quase
  todo o tempo de setembro de 2021 a dezembro de 2022. A segunda pior queda caiu, mas o retorno foi
  junto
- **Pelo protocolo, o corte de risco só foi visto no estudo.** Esta validação não diz que o filtro
  nunca funciona; diz que ele não é uma propriedade garantida, e que depende do ritmo da queda

Registro em `fiance-trend/backend/registro_filtro.jsonl`; o resumo em
`fiance-trend/backend/resultados/filtro_de_risco.json`. A prova segue lacrada.
