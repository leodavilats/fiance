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

Pesquisa nova começa por um arquivo novo aqui, com o protocolo, e só roda depois do aceite do autor.
