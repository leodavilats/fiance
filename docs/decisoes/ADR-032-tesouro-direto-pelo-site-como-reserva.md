# ADR-032 — Com o Tesouro Transparente fora, o retrato do dia vem do site do Tesouro Direto

**Status:** ACEITO
**Data:** 2026-10-24
**Decidido por:** autor do projeto

## Contexto

O `PrecoTaxaTesouroDireto.csv` do Tesouro Transparente é a fonte do Tesouro Direto desde 2005.
Desde a rodada de 22/10/2026, o site inteiro responde 429 a qualquer cliente que não seja
navegador: está atrás da proteção anti-robô do F5 BIG-IP, que exige executar um desafio em
JavaScript. A etapa do Tesouro falhou em duas rodadas seguidas, e a `tesouro` parou.

## Problema

Como manter a `tesouro` em dia sem depender de um arquivo que pode ficar inacessível por script?

## Alternativas

1. **Imitar navegador.** Rejeitada: exige Chromium no container e uma disputa com uma proteção que
   o Tesouro ligou de propósito e que muda sem aviso.
2. **Taxas indicativas da ANBIMA.** Rejeitada: são do mercado secundário, sem o spread de compra e
   venda do Tesouro Direto.
3. **API de terceiro (brapi).** Rejeitada: deriva do mesmo CSV e põe um terceiro entre a base e a
   fonte.
4. **JSON do site do Tesouro Direto como reserva.** `/o/rentabilidade/investir` e `/resgatar`
   respondem a cliente comum, com taxa e preço de cada título à venda e de cada título resgatável.

## Decisão

A alternativa 4, só quando o CSV falha por rede. O CSV segue como fonte principal.

- **Fonte própria:** `tesouro_direto_site`, com os dois lados guardados juntos como bruto. A origem
  de cada linha da `tesouro` se lê pela `coleta`.
- **Mesmo vocabulário:** o nome do site perde o ano ("Tesouro IPCA+ 2032" → "Tesouro IPCA+") e a
  taxa sai do texto do indexador ("IPCA + 6,72%" → 6,72).
- **O site não publica o PU base:** `pu_base` fica nulo.
- **Quando o CSV volta, ele sobrescreve** o retrato do site pela mesma chave.

## Consequências

- O site traz a última marcação do dia (18h); o CSV, a da manhã. Até o CSV voltar, o valor do dia é
  o de fechamento.
- O site só tem o dia corrente: rodada perdida vira buraco até o CSV voltar.
- É um endpoint sem contrato, como os da B3 ([04-PROBLEMAS](../04-PROBLEMAS.md#base-de-mercado)). O
  anterior (`treasurybondsinfo.json`) já responde 410. Formato mudado é recusado, não gravado.

## Referências

- [docs/base](../base/README.md#fontes-conferidas)
- [ADR-022](ADR-022-dados-de-mercado-coletados-em-lote.md)
