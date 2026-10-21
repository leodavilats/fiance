# ADR-029 — A documentação se organiza por parte, e o app deixa de ser o eixo

**Status:** ACEITO
**Data:** 2026-10-21
**Decidido por:** autor do projeto

## Contexto

A documentação foi escrita em 2026-09-13, quando o fiance era um app: backend e cliente Flutter. Os
documentos numerados respondiam perguntas do app — o 01 descrevia o produto, o 08 seguia a navegação
(`/mes`, `/sobra`, `/patrimonio`), o 05 era a interface do Flutter.

Em outubro vieram três partes que não são o app: a base de mercado (`data-job/`,
[ADR-022](ADR-022-dados-de-mercado-coletados-em-lote.md)), o laboratório (`fiance-trend/`,
[ADR-023](ADR-023-fase-pessoal-primeiro.md)) e a API de dados (`fiance-dados/`,
[ADR-024](ADR-024-api-de-dados.md)), que é um segundo produto, com planos pagos
([ADR-025](ADR-025-cobranca-da-api-de-dados.md)). Elas entraram como apêndices: a API de dados era
"a segunda frente" no fim do 01 e uma seção de variáveis no 07; o laboratório não tinha documento;
o estado das três cabia numa tabela chamada "Dados externos".

## Problema

Quem lesse a documentação concluiria que o fiance é um app com acessórios, e decidiria prioridade
por essa régua. A API de dados, que tem preço e terceiros como público, não tinha um lugar que
dissesse o que ela é. E o que existia sobre cada parte estava espalhado por quatro arquivos.

## Alternativas

1. **Manter a numeração por assunto**, reescrevendo cada documento para cobrir as quatro partes.
   Rejeitada: documentos como domínio, cálculos e interface só existem para o app, e ficariam com
   três seções vazias.
2. **Uma pasta por parte, inclusive estado, problemas e futuro.** Rejeitada: a pergunta "isto
   existe?" passaria a ter quatro respostas, e a regra de um documento por pergunta se perderia.
3. **Híbrido:** o que vale para todas as partes na raiz, numerado; o que é de uma parte só, na pasta
   dela.

## Decisão

A alternativa 3, com as quatro partes em peso igual e **dois produtos lado a lado**: o app e a API
de dados.

- **Na raiz:** visão da plataforma (01), arquitetura entre as partes (02), estado (03), problemas
  (04), futuro (05), desenvolvimento (06) e operação (07). Estado, problemas e futuro têm uma seção
  por parte.
- **Por parte:** `app/` (produto, domínio, arquitetura interna, cálculos, interface, desenvolvimento e
  operação do app), `dados/`, `base/` e `pesquisa/` (o laboratório e os protocolos, em
  `pesquisa/estudos/`).
- **Um documento de pasta não diz se algo existe nem o que falta:** aponta para o 03, o 04 e o 05.
- **As ADRs ficam juntas**, numeradas em sequência única. Os links delas foram corrigidos para os
  caminhos novos; o texto, não.

## Consequências

- Os caminhos mudaram. O painel do laboratório lista documentos por caminho
  (`fiance-trend/backend/api/arquivos.py`), e mudou junto.
- Os documentos de cálculo do app foram divididos por assunto em `app/calculos/`.
- O histórico (`historico/`) não foi tocado e cita os nomes antigos — o checador de links o ignora.
- Os protocolos de pesquisa citam o "10-PROBLEMAS" e o "08-ESTADO" na prosa; protocolo não se
  reescreve, e os nomes de hoje são 04-PROBLEMAS e 03-ESTADO.

## Referências

- [docs/README](../README.md) — o mapa de qual arquivo responde o quê
- [01-VISAO](../01-VISAO.md)
