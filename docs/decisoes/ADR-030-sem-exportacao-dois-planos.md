# ADR-030 — A base não é entregue em arquivo, e a API de dados fica com dois planos

**Status:** ACEITO
**Data:** 2026-10-21
**Decidido por:** autor do projeto
**Substitui em parte:** [ADR-025](ADR-025-cobranca-da-api-de-dados.md), no terceiro degrau

## Contexto

A [ADR-025](ADR-025-cobranca-da-api-de-dados.md) criou três planos pagos: Essencial, Pro e Quant. O
Quant se distinguia do Pro por três coisas — exportação da base, limites altos e contrato — e
custava a partir de R$ 490 por mês, sem anual.

A exportação nunca existiu: o plano tinha o recurso `exportacao`, o portal a anunciava como
"Exportação da base, sob contrato", e nenhuma rota a exigia nem a entregava.

## Problema

Entregar a base inteira em arquivo é o uso que mais pesa na licença do dado: a política de market
data da B3 trata redistribuição à parte, e a ODbL da CVM alcança a base derivada oferecida ao
público. Construir a exportação aumentaria o risco do maior bloqueador da venda
([ADR-024](ADR-024-api-de-dados.md)); manter o anúncio sem a rota é prometer o que não existe.

## Alternativas

1. **Construir a exportação.** Rejeitada pelo autor: a base não é entregue em arquivo.
2. **Manter o Quant sem exportação**, como um Pro com mais volume. Rejeitada: sem cliente nenhum, um
   terceiro plano público só para volume é complexidade sem demanda.
3. **Dois planos, Essencial e Pro, sem exportação em nenhum.**

## Decisão

A alternativa 3.

- **A base não é entregue em arquivo.** O acesso é pela API, consulta a consulta, e o portal diz isso
  na lista do que o serviço não tem.
- **Dois planos públicos:** Essencial e Pro, com os limites e preços da ADR-025.
- **O recurso `exportacao` sai** de todos os planos, inclusive `interno` e `convidado`.
- **Volume acima do Pro é contrato**, por um plano não listado criado quando houver o cliente, como
  `interno` e `convidado` já são — não por um plano público à espera dele.

## Consequências

- Migração `0003_sem_quant`: conta no Quant passa ao Pro, e o plano sai.
- Um teste confere que todo recurso oferecido por um plano é exigido por alguma rota — o defeito
  que deixou o Quant prometer a exportação.
- **Não exportar não impede copiar a base pela API.** No Pro, o limite por dia e o tamanho da página
  permitem baixar o histórico de cotações em poucas horas. Proteger a base é trabalho de limite e de
  termos de uso, e está em [04-PROBLEMAS](../04-PROBLEMAS.md#api-de-dados).

## Referências

- [docs/dados](../dados/README.md)
