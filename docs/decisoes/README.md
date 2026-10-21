# Decisões arquiteturais

Uma decisão entra aqui quando é **cara de reverter** ou quando alguém, daqui a seis meses, olharia o
código e perguntaria *"por que assim?"*.

O porquê vive aqui. O código diz **o quê**; a ADR diz **por quê**, e o que se aceitou perder em
troca. É por isso que justificativa não vai em comentário de código — ver
[06-DESENVOLVIMENTO](../06-DESENVOLVIMENTO.md).

---

## Índice

| # | Decisão | Status | Data |
|---|---|---|---|
| [001](ADR-001-matematica-pura.md) | Matemática pura separada da persistência | `ACEITO` | 2026-09-13 *(retroativa)* |
| [002](ADR-002-razao-fonte-unica.md) | Livro-razão como fonte única da carteira | `ACEITO` | ~2026-08 |
| [003](ADR-003-cliente-unico.md) | Flutter como cliente único; web descontinuada | `ACEITO` | 2026-09-11 |
| [004](ADR-004-dinheiro-decimal.md) | Dinheiro fiscal em `Decimal`, dinheiro de tela em `float` | `ACEITO` | ~2026-07 |
| [005](ADR-005-cache-trocavel.md) | Cache no banco da aplicação, com backend trocável | `ACEITO` | ~2026-09 |
| [006](ADR-006-recomendacao-personalizada.md) | Recomendação personalizada como alvo, sem parecer jurídico | `ACEITO` | 2026-09-13 |
| [007](ADR-007-nivel-de-afirmacao.md) | Nível de afirmação como configuração, não código | `ACEITO` | ~2026-08 |
| [008](ADR-008-monetizacao-por-loja.md) | Monetização por loja via RevenueCat; `billing/` descartado | `ACEITO` | 2026-09-13 |
| [009](ADR-009-trial-e-gratuidade.md) | Nada gratuito; trial de 14 dias na primeira posição salva | `ACEITO` | 2026-09-13 |
| [010](ADR-010-remover-otimizador.md) | Remover `optimizer/` e o enum de estratégias | `ACEITO` | 2026-09-13 |
| [011](ADR-011-preco-justo-e-faixa.md) | Preço justo como faixa; leitura de tendência declarada | `SUBSTITUÍDO EM PARTE` por 014 | 2026-09-19 |
| [012](ADR-012-o-alvo-e-de-quem-declara.md) | Sem alvo declarado não há julgamento | `ACEITO` | 2026-09-19 |
| [013](ADR-013-o-tecnico-nao-decide.md) | O técnico não decide, e a faixa carrega a própria incerteza | `SUBSTITUÍDO EM PARTE` por 014 | 2026-09-20 |
| [014](ADR-014-um-modelo-por-classe.md) | Um modelo por classe, e a faixa é das premissas dele | `SUBSTITUÍDO EM PARTE` por 015, 016 e 028 | 2026-09-23 |
| [015](ADR-015-a-faixa-cobre-os-dois-cenarios.md) | A faixa da ação cobre os dois cenários de crescimento | `ACEITO` | 2026-09-25 |
| [016](ADR-016-a-confirmacao-da-acao-alarga-e-nao-derruba.md) | Na ação, o dividendo longe da faixa alarga a leitura, e não a derruba | `ACEITO` | 2026-09-25 |
| [017](ADR-017-o-score-nao-le-o-tecnico.md) | O score de oportunidade não lê o técnico — estende 013 | `ACEITO` | 2026-09-25 |
| [018](ADR-018-a-queda-e-recorte-e-nao-veredito.md) | A queda é recorte de Descobrir, e não veredito — estende 013 | `ACEITO` | 2026-09-25 |
| [019](ADR-019-fii-de-papel-exige-yield-nominal.md) | FII de papel exige yield nominal, por uma classificação mantida no código — complementa 014 | `ACEITO` | 2026-09-25 |
| [020](ADR-020-day-trade-apartado.md) | Day trade é apartado na projeção, e apurado em conta própria | `ACEITO` | 2026-09-25 |
| [021](ADR-021-a-exportacao-volta-para-conta-vazia.md) | A exportação da conta volta, e só para conta sem dados financeiros | `ACEITO` | 2026-09-28 |
| [022](ADR-022-dados-de-mercado-coletados-em-lote.md) | Dados de mercado coletados em lote, por um job dono do próprio schema | `ACEITO` | 2026-10-09, aceita em 2026-10-12 |
| [023](ADR-023-fase-pessoal-primeiro.md) | Fase pessoal primeiro; público depois | `ACEITO` | 2026-10-12 |
| [024](ADR-024-api-de-dados.md) | A base de mercado vira um serviço de dados, separado do laboratório | `ACEITO` | 2026-10-14 |
| [025](ADR-025-cobranca-da-api-de-dados.md) | A API de dados é paga, sem plano gratuito, em três degraus | `SUBSTITUÍDO EM PARTE` por 030 | 2026-10-14 |
| [026](ADR-026-confirmacao-do-evento-pelo-tamanho.md) | O preço confirma o evento na medida do tamanho dele | `ACEITO` | 2026-10-18 |
| [027](ADR-027-caixa-de-avisos-guardada.md) | Os avisos são guardados numa caixa, com lido e não lido | `ACEITO` | 2026-10-18 |
| [028](ADR-028-taxa-de-acao-pelo-juro-real-do-tesouro.md) | A taxa exigida de ação sai do juro real do Tesouro | `ACEITO` | 2026-10-19 |
| [029](ADR-029-documentacao-por-parte.md) | A documentação se organiza por parte, e o app deixa de ser o eixo | `ACEITO` | 2026-10-21 |
| [030](ADR-030-sem-exportacao-dois-planos.md) | A base não é entregue em arquivo, e a API de dados fica com dois planos | `ACEITO` | 2026-10-21 |

---

## Notas de contexto

- **Nomes, 2026-10-14:** o serviço e a pasta `dados-api` passaram a `fiance-dados`; `trend`,
  `trend-backend/` e `trend-frontend/` passaram a `fiance-trend`, `fiance-trend/backend/` e
  `fiance-trend/frontend/`. As ADRs 022 a 024 usam os nomes antigos.

O texto de uma ADR não muda. Quando um fato posterior muda o peso de uma premissa, a nota fica aqui,
datada, e a ADR continua como foi escrita.

**2026-10-12**

- **006** — a frase-alvo é anterior à medida do preço justo; reexaminar antes da fase pública
  ([ADR-023](ADR-023-fase-pessoal-primeiro.md), [calibracao](../pesquisa/estudos/calibracao.md),
  [04-PROBLEMAS](../04-PROBLEMAS.md) A12). A frase do app ganhou "o preço justo descreve posição, não
  antecipa retorno".
- **008 e 009** — valem para a fase pública, adiada pela [ADR-023](ADR-023-fase-pessoal-primeiro.md).
- **011 e 014** — tratam "abaixo do preço justo" como lado de compra e justificam a Selic média de 10
  anos; a medida de 2011–2017 mostrou que o veredito não ordenou o retorno e que, com essa média, 9 em
  10 ações ficavam acima da faixa ([calibracao](../pesquisa/estudos/calibracao.md), A12). A afirmação da 014 de
  que validar exige dado point-in-time "que a BRAPI não entrega" foi resolvida pela base própria.
- **017, 018 e 019** — as premissas "a BRAPI não entrega…" e o invariante "só BRAPI e BCB SGS" foram
  trocados pela [ADR-022](ADR-022-dados-de-mercado-coletados-em-lote.md). Na 019, o informe mensal da
  CVM (`mercado.fii_mensal`) traz segmento e mandato do FII: a lista mantida à mão deve ser revista.
  Na 017, BDR segue sem balanço, porque a CVM não publica demonstração de empresa estrangeira.
- **022** — a condição "a BRAPI só sai quando proventos tiverem fonte" foi cumprida com os endpoints
  da B3; o backend já migrou (cotação do último fechamento, `as_of` às 18h BRT). O consumo é pela
  conexão do Railway com `SET ROLE mercado_leitura`, sem usuário próprio.

**2026-10-21**

- **Documentação por parte** ([ADR-029](ADR-029-documentacao-por-parte.md)) — as ADRs citam
  documentos pelos nomes antigos: 01-PRODUTO é hoje [01-VISAO](../01-VISAO.md) e
  [app/produto](../app/produto.md); 03-ARQUITETURA, [02-ARQUITETURA](../02-ARQUITETURA.md) e
  [app/arquitetura](../app/arquitetura.md); 08-ESTADO, 09-FUTURO e 10-PROBLEMAS são 03, 05 e 04;
  11-DADOS-DE-MERCADO é [base/](../base/README.md). Os links foram corrigidos; o texto, não.
- **Itens de problema citados que já fecharam** — a A12 (005, 006, 011, 014, 023, 024) fechou com a
  [ADR-028](ADR-028-taxa-de-acao-pelo-juro-real-do-tesouro.md); a seção D (002) fechou em 2026-09-26,
  quando a paridade com a web se completou; o item 1 (005), o Redis com timeout, em 2026-09-25; o item
  14 (003) e o "FII de papel" (014) não estão mais abertos.
- **022 e 024** — o backend não lê o banco de mercado: lê pela `fiance-dados`, com a chave do plano
  `interno`. O "passo seguinte" da 024 já foi dado.
- **025** — o Quant e a exportação saíram pela [ADR-030](ADR-030-sem-exportacao-dois-planos.md).

---

## Formato

```markdown
# ADR-XXX — Título

**Status:** PROPOSTO | ACEITO | SUBSTITUÍDO por ADR-YYY | REVOGADO
**Data:**
**Decidido por:**

## Contexto
## Problema
## Alternativas
## Decisão
## Consequências
## Referências
```

**Status muda; texto não.** Uma decisão revista ganha ADR nova que substitui a anterior — a antiga
fica, marcada. Reescrever a história apaga a razão de a decisão ter parecido certa na época, que é
exatamente o que se quer saber depois.

## Datas aproximadas

As ADRs 002, 004, 005 e 007 documentam decisões **já tomadas e em vigor**, escritas retroativamente
em 2026-09-13. A data é aproximada, inferida do histórico. Estão aqui porque são caras de reverter e
ninguém saberia o motivo olhando só o código.
