# Plano — a plataforma de dados, tendência e painel

**Estado:** `[IMPLEMENTADO]` · **Decidido em:** 2026-10-12, pelo autor, a partir de um questionário ·
**Fase:** pessoal, a plataforma é ferramenta do autor ([ADR-023](../decisoes/ADR-023-fase-pessoal-primeiro.md))

| Etapa | Estado | Onde está |
|---|---|---|
| 1 · Coleta de tudo o que negocia | `[IMPLEMENTADO]` | Ações, FIIs, ETFs, BDRs, PTAX e Tesouro Direto na base, todo dia útil |
| 2 · Tendência como ranking | `[CONCLUÍDO]` | Teto de 6 variações usado, nenhuma passou: o ranking não informa. A tendência fica como contexto de risco. [Protocolo e resultado](ranking.md) |
| 3 · Painel organizado | `[IMPLEMENTADO]` | Caminho, coleta, ativos de todas as classes, dólar e Tesouro, ranking e pesquisa |
| 4 · App sem BRAPI | `[IMPLEMENTADO]` | ADR-022 aceita em 2026-10-12. O backend lê `mercado.ativo_hoje`; a BRAPI saiu do código |
| Calibração do preço justo | `[ENCERRADO]` | O veredito do app não ordenou o retorno de 2011 a 2017; a calibração parou no protocolo. A taxa de desconto segue aberta em [10-PROBLEMAS](../10-PROBLEMAS.md), A12. [Protocolo e resultado](calibracao.md) |

A plataforma tem três partes e um consumidor:

| Parte | Pasta | Papel |
|---|---|---|
| Coleta | `data-job/` | Tudo o que negocia na bolsa, tratado e guardado no `postgres-mercado` |
| Pesquisa | `trend-backend/` | Pesquisa de carteira, ranking e calibração, cada um com protocolo, e a API do painel |
| Painel | `trend-frontend/` | O caminho, os dados e o ranking organizados para o autor |
| Consumidor | `backend/` e `mobile/` | O app fiance lê **só o dado** da base própria, sem BRAPI |

## Decisões do questionário

- **Todas as classes entram no data-job:** ações, FIIs, ETFs, BDRs, dólar e Tesouro Direto
- **A tendência é um ranking dos ativos**, e não promessa de retorno. A medida de acerto é escrita no
  protocolo antes da primeira execução
- **O app recebe só o dado** — cotação, proventos, fundamentos, eventos — e nenhum sinal de tendência
- **O fiance é de uso pessoal durante os testes e público depois.** Por isso as regras de produto valem
  desde já: indicar compra ou venda ao público é atividade de analista credenciado pela CVM
  ([ADR-006](../decisoes/ADR-006-recomendacao-personalizada.md)), e o técnico não decide no app
  ([ADR-013](../decisoes/ADR-013-o-tecnico-nao-decide.md)). O ranking fica no painel do autor

## Etapa 1 — o data-job com tudo o que negocia

O preço bruto de tudo está no COTAHIST (5.171 ISINs). O tratamento por classe, feito em 2026-10-12:

| Classe | Feito | Lacuna | Fonte |
|---|---|---|---|
| ETFs | Série ajustada e eventos de cota (`mercado.serie_fundo`) | Proventos antes de out/2026; a maioria reinveste, e o preço já é quase o retorno total | COTAHIST, B3 |
| Dólar | PTAX diária | — | BCB SGS (série 1) |
| Tesouro Direto | Preços e taxas de cada título desde 2005 (`mercado.tesouro`) | — | Tesouro Transparente |
| FIIs | Eventos de cota, rendimentos recentes e, desde 2016, rendimento estimado pelo informe mensal | Antes de 2016; amortização só pela B3 | CVM, informe mensal de FII; B3 |
| BDRs | Eventos e proventos recentes | Proventos antes de out/2026; **sem balanço**, porque a CVM não publica demonstrações de empresa estrangeira | B3 |

A série ajustada das classes novas segue a regra de `mercado.serie_papel`: preço por cota ajustado por
evento conferido pelo preço, provento na data ex, retorno total. O detalhe está em [data-job](data-job.md).

## Etapa 2 — a tendência como ranking

Um ranking por classe, pela força da tendência no fim do mês, medido contra o retorno do mês seguinte
com protocolo fixado antes da primeira execução: correlação de postos, acerto do topo e diferença
líquida, teto de 6 variações. Em ações, a validação (2019–2022) e a prova (2023 em diante) ficaram
lacradas; os FIIs tiveram períodos próprios, num adendo escrito antes de rodar (estudo 2019–2022,
validação 2023–2024, prova 2025 em diante).

**Resultado (2026-10-12): o ranking não informa.** As 6 variações foram usadas, 3 em ações e 3 em FIIs,
e nenhuma passou no estudo; em FII, a tendência se inverteu. A tendência fica no painel como contexto
de risco. Protocolo e números em [ranking](ranking.md).

## Etapa 3 — o painel organizado

O painel mostra o caminho (este plano e o estado de cada etapa), a saúde da coleta, os dados por ativo
de todas as classes e o ranking com o histórico de acerto.

**Feito (2026-10-12):** a página inicial é o Caminho — os números da base por classe, os proventos por
origem e este plano. Ativos de todas as classes, com a tela de fundo e BDR marcando o rendimento
estimado; dólar e Tesouro; o ranking com a correlação de cada mês e a diferença acumulada entre topo e
fundo. O ranking do último fim de mês não aparece: nenhum sinal passou no protocolo.

## Etapa 4 — o app sem BRAPI

O backend do fiance lê o `postgres-mercado` pela conexão do Railway, assumindo o papel
`mercado_leitura` (`SET ROLE`, sem usuário nem senha próprios), e a BRAPI saiu. A
[ADR-022](../decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md) foi aceita em 2026-10-12.

**Consequência visível:** a cotação do app é a do último fechamento, e não a do pregão em andamento. A
idade continua carimbada na tela. O Ibovespa é medido pelo BOVA11, porque a base não tem o índice.
