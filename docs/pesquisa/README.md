# Laboratório — `fiance-trend`

**Fonte de verdade** para o que se mediu, com que protocolo, e o que deu; e para o que o laboratório
é. Ferramenta do autor, **fora dos dois produtos**
([ADR-023](../decisoes/ADR-023-fase-pessoal-primeiro.md)): nada daqui chega ao app nem à API de dados
sem passar por decisão.
Última revisão: 2026-10-21

---

## Para que existe

Antes de um produto afirmar algo — que um ativo está barato, que uma regra seleciona melhor, que uma
taxa é a certa —, a afirmação é medida contra o histórico da [base](../base/README.md), com só o que
se sabia em cada data. O laboratório é onde essa medida acontece, e o painel é onde o autor acompanha
a base e os estudos.

| Parte | O quê | Onde |
|---|---|---|
| Pesquisa | Retrato da base em Parquet, motor de simulação mensal com custo e imposto, ranking, calibração do preço justo do app, e um módulo por estudo; um comando cada (`python -m pesquisa <estudo>`) | `fiance-trend/backend/pesquisa/` |
| Registro | Uma linha por execução, só com acréscimo, por estudo; resultado em JSON ao lado | `fiance-trend/backend/registro*.jsonl`, `fiance-trend/backend/resultados/` |
| API do painel | Leitura direta da base como `mercado_leitura`, os registros de carteira e de ranking, os documentos e os alertas de coleta | `fiance-trend/backend/api/` |
| Painel | Base (caminho, coleta, ativos de todas as classes, dólar e Tesouro), estudos (índice, ranking, pesquisa de carteira) e documentos, com senha | `fiance-trend/frontend/src/` |

**A calibração importa o motor do app** (`app.analysis.fair_price`): o veredito medido é o mesmo que
o app mostra, e mudar o backend pode quebrar a suíte do laboratório.

**Só dois dos oito registros têm tela** — carteira e ranking. Os outros estudos aparecem no painel
pelo texto do protocolo.

## Variáveis

| Variável | Default | Para quê |
|---|---|---|
| `DATABASE_URL` | **obrigatória** | O `postgres-mercado`, lido como `mercado_leitura` |
| `TREND_USUARIO` | **obrigatória** | Usuário do painel |
| `TREND_SENHA` | **obrigatória** | Senha do painel; definida no Railway, nunca no repositório |
| `TREND_DOCS` | `docs/` da raiz | Onde ler os documentos exibidos no painel |
| `TREND_PESQUISA` | `fiance-trend/backend/` | Onde ler os resultados da pesquisa |
| `TREND_FRONT` | `fiance-trend/frontend/dist` | O front compilado que a API serve |

A CLI da pesquisa, rodada à mão, lê a base por `PESQUISA_DATABASE_URL` ou, com `--pelo-railway`,
pelo `railway ssh` (`pesquisa/retrato.py`).


## O protocolo

Cada arquivo em [estudos/](estudos/) é o **protocolo de uma pesquisa** e o resultado dela: a
pergunta, o universo, os períodos, a medida de acerto e o teto de variações, escritos e aceitos
**antes** da primeira execução.

**A regra é a das ADRs: o protocolo não se reescreve.** Depois de aceito, ele só ganha resultado,
adendo aceito antes de rodar, ou correção de erro declarada. Ajustar a régua depois de ver o
resultado é o que o protocolo existe para impedir. No código, a regra vira teto de variações, prova
lacrada e `--forcar` gravado no registro.

**Períodos:** estudo de 2005 a 2018, validação de 2019 a 2022, prova de 2023 em diante
(`pesquisa/periodos.py`); estudos com balanço ou FII declaram os seus. A prova não foi aberta por
nenhum estudo.

## Estudos

| Pesquisa | Pergunta | Resultado |
|---|---|---|
| [pesquisa](estudos/pesquisa.md) | Alguma regra de seleção de carteira bate o CDI por 2 pontos, depois de custo e imposto? | Encerrada em 8 variações: não achei vantagem investível |
| [ranking](estudos/ranking.md) | Ordenar pela força da tendência diz quem rende mais no mês seguinte? | 6 variações, nenhuma passou: o ranking não informa |
| [calibracao](estudos/calibracao.md) | O veredito de preço justo do app ordena o retorno dos 12 meses seguintes? | Não ordenou (2011–2017); a calibração parou |
| [validacao-brapi](estudos/validacao-brapi.md) | Onde a base discorda de uma segunda fonte, e a discordância é erro nosso? | 25 eventos faltando, saltos sem marca e a estimativa de FII medida; a maior parte do resto é convenção da brapi. Depois das correções, 470 eventos batem (eram 426) e 29 seguem recusados (eram 65) |
| [taxa-de-desconto](estudos/taxa-de-desconto.md) | Com cada taxa candidata, quanto do mercado a faixa põe abaixo, dentro e acima? Não olha retorno | Taxa de hoje não passa (88% acima); Selic + 3 e IPCA+ longo passam por pouco, com mais de 70% acima. Serviu à [ADR-028](../decisoes/ADR-028-taxa-de-acao-pelo-juro-real-do-tesouro.md) |
| [calibracao-com-a-taxa-nova](estudos/calibracao-com-a-taxa-nova.md) | Com a taxa da ADR, o veredito ordena o retorno? Uma variação | Não passou: a ordem aparece (+1,1 ponto), mas com t de 0,18 e pouca amostra abaixo da faixa |
| [filtro-de-risco](estudos/filtro-de-risco.md) | O filtro de tendência corta a queda na validação, e a que custo? | Não confirmado: a pior queda ficou igual (−47,6%) e o retorno caiu 8,9 pontos ao ano |
| [custo-de-troca](estudos/custo-de-troca.md) | Quanto custa trocar de papel, por faixa de liquidez? | O método mediu volatilidade, não spread; o custo das pesquisas fica em 0,25% |

Pesquisa nova começa por um arquivo novo em `estudos/`, com o protocolo, e só roda depois do aceite do autor.

## Considerados e não propostos

- **Reversão em FII.** No [ranking](estudos/ranking.md), o topo perdeu do fundo de 2019 a 2022. O protocolo
  fechou esses sinais, e o sinal invertido é o mesmo sinal: com t de −1,39 no estudo, não há o que
  confirmar
- **Nova busca de retorno** (yield de FII, valor em outra régua, combinações). A [pesquisa de
  carteira](estudos/pesquisa.md) concluiu que procurar mais no mesmo estudo aumenta a chance de achar sorte. Uma
  busca nova só cabe num período que nenhuma pesquisa viu, e hoje o único é a prova
