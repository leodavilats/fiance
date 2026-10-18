# ADR-027 — Os avisos são guardados numa caixa, com lido e não lido

**Status:** ACEITO
**Data:** 2026-10-18
**Decidido por:** autor do projeto

## Contexto

O que o aplicativo tinha a dizer à pessoa saía de três lugares que se sobrepunham:

- o sino do `Mês` abria "O que mudou", um painel que repetia o patrimônio, a meta e a nota da
  carteira, com os avisos no meio;
- dentro dele, "O que aconteceu" mostrava **os mesmos** avisos;
- `/voce/avisos` ligava e desligava alerta e resumo.

Os avisos eram recalculados a cada abertura (`GET /whats-new`, no máximo cinco), sem data, sem marca
de leitura e sem passado: o que a pessoa não viu no dia sumia quando o assunto saía da conta. O sino
não tinha contador, e o alerta de preço disparado só existia como push — quem negou a permissão de
notificação nunca o recebia.

## Problema

Como entregar o aviso de forma que ele tenha data, possa ser lido depois e não se repita?

## Alternativas

1. **Reorganizar a tela e guardar a leitura no aparelho.** Rejeitada: continua sem data e sem
   histórico, e a mesma pessoa vê contadores diferentes em dois aparelhos.
2. **Guardar cada aviso enviado como push.** Rejeitada: deixa de fora quem não tem push, e o que o
   cálculo de "o que mudou" produz entre dois ciclos do job.
3. **Uma caixa guardada, alimentada pelo cálculo de sempre, com identidade por assunto.**

## Decisão

A alternativa 3.

- **A tabela é `inbox_items`**, por usuário. Cada aviso guarda o texto do momento em que chegou, a
  data de chegada e a de leitura.
- **Cada aviso calculado tem um assunto estável** (`topic`): a categoria e o sentido do desvio, os
  ativos acima do preço justo, as aplicações que vencem, o ativo em destaque.
- **O mesmo assunto não entra duas vezes no mesmo período**: semana para patrimônio e oportunidade,
  mês para veredito, meta e prejuízo a compensar; vencimento, alerta de preço disparado e resumo são
  eventos únicos. A caixa não insiste — o que continua verdade não volta a cada abertura.
- **A caixa se atualiza** ao ser aberta (`GET /inbox`) e no ciclo de snapshot de cada conta; o alerta
  de preço e o resumo entram pelo job de notificações, com ou sem push.
- **Falha ao calcular não esvazia a caixa**: o que já está guardado continua aparecendo.
- **No aplicativo**, o sino tem contador e abre `/mes/avisos`, agrupado por chegada e filtrável por
  tipo. Tocar num aviso o marca como lido e leva à ação dele. O painel que ficava no meio saiu: meta
  de renda e nota da carteira foram para `Patrimônio`, a próxima ação já mora no desvio da `Sobra`, e
  os destaques, no `Descobrir`.

## Consequências

**Ganhos**

- Um lugar só para o que o sistema tem a dizer, com data e passado
- O alerta de preço chega a quem não aceitou push
- O contador do sino é o mesmo em qualquer aparelho

**Custos aceitos**

- Mais uma tabela por usuário (`USER_SCOPED_MODELS`), fora da importação de conta: os avisos voltam a
  ser gerados
- `GET /inbox` recalcula a caixa e entra na lista de rotas caras
- O texto guardado é o do momento: um aviso de vencimento diz "em 20 dias" mesmo lido uma semana depois
