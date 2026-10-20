# Pesquisas

Cada arquivo aqui é o **protocolo de uma pesquisa** e o resultado dela: a pergunta, o universo, os
períodos, a medida de acerto e o teto de variações, escritos e aceitos **antes** da primeira
execução.

**A regra é a das ADRs: o protocolo não se reescreve.** Depois de aceito, ele só ganha resultado,
adendo aceito antes de rodar, ou correção de erro declarada. Ajustar a régua depois de ver o
resultado é o que o protocolo existe para impedir. O registro de cada execução fica no
`fiance-trend/backend/` (`registro*.jsonl`), e só acrescenta.

| Pesquisa | Pergunta | Resultado |
|---|---|---|
| [pesquisa](pesquisa.md) | Alguma regra de seleção de carteira bate o CDI por 2 pontos, depois de custo e imposto? | Encerrada em 8 variações: não achei vantagem investível |
| [ranking](ranking.md) | Ordenar pela força da tendência diz quem rende mais no mês seguinte? | 6 variações, nenhuma passou: o ranking não informa |
| [calibracao](calibracao.md) | O veredito de preço justo do app ordena o retorno dos 12 meses seguintes? | Não ordenou (2011–2017); a calibração parou |
| [validacao-brapi](validacao-brapi.md) | Onde a base discorda de uma segunda fonte, e a discordância é erro nosso? | 25 eventos faltando, saltos sem marca e a estimativa de FII medida; a maior parte do resto é convenção da brapi. Depois das correções, 470 eventos batem (eram 426) e 29 seguem recusados (eram 65) |
| [taxa-de-desconto](taxa-de-desconto.md) | Com cada taxa candidata, quanto do mercado a faixa põe abaixo, dentro e acima? Não olha retorno | Taxa de hoje não passa (88% acima); Selic + 3 e IPCA+ longo passam por pouco, com mais de 70% acima. Serve à ADR da A12 |
| [calibracao-com-a-taxa-nova](calibracao-com-a-taxa-nova.md) | Com a taxa da ADR, o veredito ordena o retorno? Uma variação | Não passou: a ordem aparece (+1,1 ponto), mas com t de 0,18 e pouca amostra abaixo da faixa |
| [filtro-de-risco](filtro-de-risco.md) | O filtro de tendência corta a queda na validação, e a que custo? | Não confirmado: a pior queda ficou igual (−47,6%) e o retorno caiu 8,9 pontos ao ano |
| [custo-de-troca](custo-de-troca.md) | Quanto custa trocar de papel, por faixa de liquidez? | O método mediu volatilidade, não spread; o custo das pesquisas fica em 0,25% |

Pesquisa nova começa por um arquivo novo aqui, com o protocolo, e só roda depois do aceite do autor.

## Considerados e não propostos

- **Reversão em FII.** No [ranking](ranking.md), o topo perdeu do fundo de 2019 a 2022. O protocolo
  fechou esses sinais, e o sinal invertido é o mesmo sinal: com t de −1,39 no estudo, não há o que
  confirmar
- **Nova busca de retorno** (yield de FII, valor em outra régua, combinações). A [pesquisa de
  carteira](pesquisa.md) concluiu que procurar mais no mesmo estudo aumenta a chance de achar sorte. Uma
  busca nova só cabe num período que nenhuma pesquisa viu, e hoje o único é a prova
