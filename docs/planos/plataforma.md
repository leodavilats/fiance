# Plano — a plataforma de dados, tendência e painel

**Estado:** `[PLANEJADO]` · **Decidido em:** 2026-10-12, pelo autor, a partir de um questionário

A plataforma tem três partes e um consumidor:

| Parte | Pasta | Papel |
|---|---|---|
| Coleta | `data-job/` | Tudo o que negocia na bolsa, tratado e guardado no `postgres-mercado` |
| Tendência | `trend-backend/` | Ranking dos ativos por força de tendência, com acerto medido antes de usar |
| Painel | `trend-frontend/` | O caminho, os dados e o ranking organizados para o autor |
| Consumidor | `backend/` e `mobile/` | O app fiance passa a ler **só o dado** da base própria, sem BRAPI |

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

O preço bruto de tudo já está no COTAHIST (5.171 ISINs). O que falta é o tratamento por classe:

| Classe | Falta | Fonte |
|---|---|---|
| ETFs | Série ajustada e eventos de cota; a maioria reinveste, e o preço já é quase o retorno total | COTAHIST, B3 |
| Dólar | PTAX diária | BCB SGS (série 1), já é fonte |
| Tesouro Direto | Preços e taxas históricos de cada título | Tesouro Transparente, dados abertos |
| FIIs | Rendimentos mensais, eventos de cota, ligação com o fundo | CVM, informe mensal de FII; B3 |
| BDRs | Proventos e eventos; **sem balanço**, porque a CVM não publica demonstrações de empresa estrangeira | B3 |

A série ajustada (`mercado.serie_papel`) passa a cobrir as classes novas com a mesma regra: preço por
cota ajustado por evento conferido pelo preço, provento na data ex, retorno total.

**Feito (2026-10-12):** eventos de cota e rendimentos recentes de FIIs, ETFs e BDRs, e a série ajustada
deles (`mercado.serie_fundo`); PTAX (série 1 do BCB) e Tesouro Direto (`mercado.tesouro`); o histórico
de rendimentos de FII desde 2016, estimado pelo informe mensal da CVM. **Lacuna declarada:** proventos
de BDR e ETF antes de out/2026.

Ordem sugerida: ETFs e dólar/Tesouro primeiro — são os instrumentos e o histórico longo que a
tendência usa —, depois FIIs, depois BDRs.

## Etapa 2 — a tendência como ranking

Um ranking dos ativos por força de tendência, recalculado todo fim de mês. Antes da primeira
execução, um protocolo novo (como o de [pesquisa](pesquisa.md)) fixa:

- **a medida de acerto do ranking** — por exemplo, se o quinto mais bem colocado rende mais que o quinto
  pior no mês seguinte, de forma consistente, fora da amostra;
- **o teto de variações e a régua;**
- **o universo** — por classe ou entre classes.

A validação (2019–2022) e a prova (2023 em diante) continuam lacradas para isso. O que a primeira pesquisa
ensinou entra como ponto de partida: escolher ações não bateu o CDI depois de custo, e o filtro de
tendência cortou as quedas grandes pela metade.

## Etapa 3 — o painel organizado

O painel mostra o caminho (este plano e o estado de cada etapa), a saúde da coleta, os dados por ativo
de todas as classes e o ranking com o histórico de acerto.

## Etapa 4 — o app sem BRAPI

O backend do fiance passa a ler o `postgres-mercado` com um usuário do papel `mercado_leitura`, e a BRAPI
sai. Exige a [ADR-022](../decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md) aceita e as mudanças
que ela lista.

**Consequência visível:** a cotação do app passa a ser a do último fechamento, e não a do pregão em
andamento. A idade continua carimbada na tela.

**A etapa 4 depende só da etapa 1.** Pode vir antes da 2 e da 3, se o custo ou a dependência da BRAPI
apertarem.
