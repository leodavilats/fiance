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
| [taxa-de-desconto](taxa-de-desconto.md) | Com cada taxa candidata, quanto do mercado a faixa põe abaixo, dentro e acima? Não olha retorno | **Proposta**, aguarda aceite. Serve à ADR da A12 |
| [calibracao-com-a-taxa-nova](calibracao-com-a-taxa-nova.md) | Com a taxa da ADR, o veredito ordena o retorno? Uma variação | **Proposta**, só roda depois da ADR, e só se ela trocar a taxa |
| [filtro-de-risco](filtro-de-risco.md) | O filtro de tendência corta a queda na validação, e a que custo? | **Proposta**, aguarda aceite. Gasta a validação da pesquisa de carteira |
| [custo-de-troca](custo-de-troca.md) | Quanto custa trocar de papel, por faixa de liquidez? | **Proposta**, aguarda aceite. Descritiva, não revê conclusão encerrada |

Pesquisa nova começa por um arquivo novo aqui, com o protocolo, e só roda depois do aceite do autor.

**Ordem sugerida:** a taxa de desconto primeiro, porque destrava a ADR da A12, e o custo de troca junto,
porque não depende de nada. O filtro de risco é independente. A calibração com a taxa nova vem por
último, e talvez nem rode.

## Considerados e não propostos

- **Reversão em FII.** No [ranking](ranking.md), o topo perdeu do fundo de 2019 a 2022. O protocolo
  fechou esses sinais, e o sinal invertido é o mesmo sinal: com t de −1,39 no estudo, não há o que
  confirmar
- **Nova busca de retorno** (yield de FII, valor em outra régua, combinações). A [pesquisa de
  carteira](pesquisa.md) concluiu que procurar mais no mesmo estudo aumenta a chance de achar sorte. Uma
  busca nova só cabe num período que nenhuma pesquisa viu, e hoje o único é a prova
