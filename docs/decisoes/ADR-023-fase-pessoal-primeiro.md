# ADR-023 — Fase pessoal primeiro: o fiance serve ao autor antes de servir ao público

**Status:** ACEITO
**Data:** 2026-10-12
**Decidido por:** autor do projeto, entre 2026-10-09 e 2026-10-12

## Contexto

Até setembro de 2026 o fiance era desenhado como produto pago de loja: assinatura de até R$ 9,90
([ADR-008](ADR-008-monetizacao-por-loja.md), [ADR-009](ADR-009-trial-e-gratuidade.md)), aquisição
como o risco número um, publicação nas lojas e cobrança no roadmap.

Em outubro o autor mudou a pergunta. A prioridade passou a ser **usar o sistema para investir o
próprio dinheiro**, com dado próprio e com qualquer ideia de estratégia medida antes de usar. Nas
palavras do autor: *"de início, durante teste, apenas pessoal. Mas no futuro para o público"*.

Disso saíram, em poucos dias:

- a coleta própria de dados de mercado ([ADR-022](ADR-022-dados-de-mercado-coletados-em-lote.md)) e a
  saída da BRAPI;
- a plataforma de pesquisa e o painel do autor ([plano da plataforma](../historico/PLATAFORMA-2026-10.md));
- três pesquisas com protocolo, todas sem vantagem a explorar: seleção de carteira
  ([pesquisa](../pesquisas/pesquisa.md)), ranking de tendência ([ranking](../pesquisas/ranking.md)) e o
  preço justo do próprio app ([calibracao](../pesquisas/calibracao.md)).

## Problema

Os documentos de produto, o roadmap e os riscos ainda descreviam o fiance como algo a vender agora.
Quem lesse decidiria prioridades pela régua errada: lojas e cobrança antes do que o autor usa, e
aquisição como o risco do momento.

## Alternativas

1. **Seguir para as lojas** como planejado. Rejeitada pelo autor: o sistema ainda não provou que
   serve a quem o usa, e a medida do preço justo mostrou um limite que precisa ser resolvido antes.
2. **Abandonar o produto público.** Rejeitada: o público continua no horizonte.
3. **Fase pessoal primeiro, público depois.**

## Decisão

A alternativa 3.

- **Hoje o fiance tem um usuário: o autor.** A régua de prioridade é o que serve a ele para investir
  e acompanhar o dinheiro, com dado confiável e sem prometer o que não se mediu.
- **A fase pública tem data nenhuma.** Publicação nas lojas, cobrança (ADR-008 e ADR-009), aquisição
  e o que só bloqueia a publicação ficam num bloco próprio do roadmap e dos problemas, sem prioridade
  agora. As duas ADRs continuam `ACEITO`: valem quando a fase pública começar.
- **As regras de produto valem desde já.** O app não indica compra nem venda
  ([ADR-006](ADR-006-recomendacao-personalizada.md)), o técnico não decide
  ([ADR-013](ADR-013-o-tecnico-nao-decide.md)), e o preço justo descreve posição, não antecipa
  retorno — a medida de 2026-10-12 mostrou que ele não antecipou.
- **A plataforma é ferramenta do autor, fora do produto.** `data-job/` alimenta o app; `trend-backend/`
  e `trend-frontend/` (o painel em `trend.up.railway.app`) são de uso do autor. O painel é web, e isso
  não contradiz a [ADR-003](ADR-003-cliente-unico.md): o cliente do fiance continua sendo só o
  Flutter. A tendência e o ranking ficam no painel e não vão para o app.
- **Antes de abrir ao público, revisar:** backup dos bancos (hoje nenhum, risco aceito em
  [07-OPERACAO](../07-OPERACAO.md)), o item A12 de [10-PROBLEMAS](../10-PROBLEMAS.md), e a frase-alvo da
  ADR-006 à luz da medida do preço justo.

## Consequências

**Ganhos**

- A prioridade de cada documento passa a ser a mesma: o que serve ao autor agora
- O custo de operar cai: a fonte de mercado é zero, e não há loja nem cobrança para manter

**Custos aceitos**

- O produto não gera receita, e o ponto de equilíbrio não importa enquanto a fase durar
- Sem uso público, não há retorno de outras pessoas sobre o que serve ou não
- O risco de um autor só cresce: ninguém mais usa, ninguém mais olha

## Referências

- [01-PRODUTO](../01-PRODUTO.md) · [09-FUTURO](../09-FUTURO.md) · [plano da plataforma](../historico/PLATAFORMA-2026-10.md)
