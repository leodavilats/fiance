# Plano — o preço justo do app, medido contra o que veio depois

**Estado:** `[ENCERRADO]` em 2026-10-12 — **o veredito não ordena o retorno**, e a calibração parou
no protocolo, sem variação rodada. Protocolo `[ACEITO]` pelo autor no mesmo dia, antes da primeira execução

## A pergunta

> Ação que o app diria estar **abaixo do preço justo** rendeu mais, nos 12 meses seguintes, que ação
> **acima do preço justo** — com o veredito calculado só com o que se sabia na data?

É a pergunta que o item *Calibração empírica do preço justo* de [09-FUTURO](../09-FUTURO.md) deixou
aberta. Ela vem **antes** de calibrar: se o modelo como está não ordena o retorno, ajustar parâmetro é
procurar acaso. Se ordenar, a calibração escolhe entre poucos valores, com teto.

## O modelo é o do app, sem cópia

A pesquisa chama `backend/app/analysis/fair_price.py::compute_fair_price` e
`decision.py` como o app chama. Mudar o modelo no app muda a pesquisa; não há segunda versão da
fórmula para divergir.

## Só o que se sabia na data

- **Preço:** fechamento do último pregão do mês
- **Balanço:** DFP e ITR pela **data de entrega** à CVM, nunca pela data de referência
- **Proventos:** com data-com até o dia; o estimado pela CVM não entra, como no app
- **Juro:** a Selic média de 10 anos até a data (`rates_for_valuation`), da série do BCB na base
- **Ações:** FRE pela data de aprovação

## Universo e períodos

Ações com volume mediano de R$ 5 milhões em 63 pregões, as regras da [primeira pesquisa](pesquisa.md).
**Units ficam de fora:** a quantidade de ações por unit não é dado da base, e o app a deduz do preço
das ações que compõem a unit — o que, no passado, só existiria com as duas cotações em todo mês.
FII fica para depois, como no ranking.

| Período | Datas | Uso |
|---|---|---|
| Estudo | 2011-01 a 2018-12 | O balanço com data de entrega começa em 2010. Vereditos até dez/2017 |
| Validação | 2019-01 a 2022-12 | Uma vez por variação que passar no estudo |
| **Prova** | **2023-01 a 2025-09, lacrada** | O último mês com 12 meses de retorno à frente |

**O retorno à frente fica dentro do período.** O veredito de dez/2017 é o último do estudo, porque
o de 2018 seria medido com retorno de 2019 — da validação. Na validação, o último é dez/2021.

## A medida — fixada antes

A cada fim de mês, as ações do universo se dividem pelo veredito: **abaixo**, **dentro** e **acima**
da faixa. Sem faixa (sem preço justo), fica de fora. Mede-se o retorno total dos 12 meses seguintes,
média simples de cada grupo.

| Medida | Para passar no estudo |
|---|---|
| Abaixo menos acima, ao ano | **≥ 3 pontos** |
| t dessa diferença, com Newey-West de 11 defasagens (as janelas de 12 meses se sobrepõem) | **≥ 2** |
| Ordem | **abaixo > dentro > acima** na média do período |
| Amostra | Pelo menos 10 ações em **abaixo** e em **acima** em 80% dos meses |

As quatro juntas.

## Primeiro o modelo como está; depois, no máximo 4 variações

**Execução 0:** os parâmetros de hoje. Ela conta no teto e responde se o modelo informa.

Só se a execução 0 passar no estudo a calibração continua, com **teto de 4 variações**, uma de cada
vez e nesta ordem:

1. Prêmio de risco de 4 pontos (hoje 5)
2. Prêmio de risco de 6 pontos
3. Crescimento real de longo prazo de 1% (hoje 1,5%)
4. Crescimento real de longo prazo de 2%

A melhor no estudo vai para a validação, uma vez. Passando, vai para a prova, uma vez. Só então o
parâmetro muda no app — com ADR, porque é decisão de produto.

**Se a execução 0 não passar, a conclusão é "o veredito não ordena o retorno"**, e fica registrada.
Isso não tira o preço justo do app — ele descreve posição, não promete retorno ([ADR-014](../decisoes/ADR-014-um-modelo-por-classe.md)) —, mas muda
o que o app pode dizer dele, e vira item no [10-PROBLEMAS](../10-PROBLEMAS.md).

## Risco declarado

- **Ações de 2011 a 2018 perderam do CDI** — a primeira pesquisa mostrou. Isso afeta os três grupos
  igual; a medida é a diferença entre eles, não contra o CDI
- **12 meses à frente sobrepostos** inflariam o t sem a correção de Newey-West
- **Balanço reapresentado:** a base guarda só os números da versão mais recente de cada documento
  (ADR-022). Uma reapresentação posterior entra como se fosse sabida antes — viés pequeno e declarado

## Resultado — 2026-10-12: o veredito não ordena o retorno

Execução 0, o modelo como está, no estudo (vereditos de jan/2011 a dez/2017, 84 meses):

| Grupo | Retorno médio em 12 meses | Ações por mês |
|---|---|---|
| Abaixo do preço justo | 4,0% | 2,8 |
| Dentro | 5,3% | 3,3 |
| Acima | 3,0% | 48,8 |
| Sem faixa | — | 38,5 |

- **Não passou em nenhuma das quatro condições.** Abaixo menos acima, nos meses com os dois grupos:
  −0,7 ponto, t de Newey-West de −0,09. A ordem não aparece (dentro rendeu mais que abaixo). E o
  grupo abaixo nunca teve 10 ações num mês
- **Com o juro da época, o modelo chama quase a bolsa inteira de cara.** A taxa de desconto é a
  Selic média de 10 anos mais 5 pontos — 16% a 19% de 2011 a 2017. Com ela, 9 em cada 10 ações com
  faixa ficavam acima do preço justo, e as poucas abaixo não renderam mais que as outras
- **Pelo protocolo, a calibração para aqui.** As variações de prêmio e crescimento só rodariam se o
  modelo como está passasse; ajustar parâmetro até o resultado aparecer é o que o teto existe para
  impedir. A validação e a prova seguem lacradas
- **A primeira execução usou a janela errada** (o estudo da pesquisa de carteira, de 2005), por erro
  de código; ficou no registro e foi refeita com `--forcar` na janela do protocolo. Como não havia
  balanço antes de 2010, os números dos dois grupos não mudaram

Registro em `fiance-trend/backend/registro_calibracao.jsonl`; mês a mês em
`fiance-trend/backend/resultados/calibracao_0_estudo.json`. O que isso muda no app está em
[10-PROBLEMAS](../10-PROBLEMAS.md), item A12.

## O que mudou no app

Em 2026-10-12, saíram "oportunidade forte", "excelente oportunidade de entrada",
"indica forte potencial", "preço com desconto" e "potencial de valorização" das frases do servidor; a
frase de ajuste ganhou "o preço justo descreve posição, não antecipa retorno"; e a explicação do
preço justo e o verbete de margem de segurança dizem o resultado da medida. O nome "Oportunidades"
fica, por decisão do autor.

**Aberto:** ADR sobre a taxa de desconto ([10-PROBLEMAS](../10-PROBLEMAS.md), item A12).
