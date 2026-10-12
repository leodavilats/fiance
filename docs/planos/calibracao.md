# Plano — o preço justo do app, medido contra o que veio depois

**Estado:** `[ACEITO]` em 2026-10-12, pelo autor — antes da primeira execução

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
FII fica para depois, como no ranking.

| Período | Datas | Uso |
|---|---|---|
| Estudo | 2011-01 a 2018-12 | O balanço com data de entrega começa em 2010 |
| Validação | 2019-01 a 2022-12 | Uma vez por variação que passar no estudo |
| **Prova** | **2023-01 a 2025-09, lacrada** | O último mês com 12 meses de retorno à frente |

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
