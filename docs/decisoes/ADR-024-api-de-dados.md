# ADR-024 — A base de mercado vira um serviço de dados, separado do laboratório

**Status:** ACEITO
**Data:** 2026-10-14
**Decidido por:** autor do projeto

## Contexto

A base própria de mercado ([ADR-022](ADR-022-dados-de-mercado-coletados-em-lote.md)) tem o que
poucos vendem organizado: histórico desde 2005 com as empresas que saíram da bolsa, balanço com a
data em que foi entregue à CVM, série ajustada com os eventos conferidos pelo preço, proventos com
data de pagamento, informe mensal de FII, Tesouro Direto e as séries do BCB.

Hoje três coisas leem essa base, cada uma do seu jeito: o backend do app (conexão direta,
`collectors/mercado.py`), a pesquisa (retrato exportado) e o painel do autor (`trend-backend/api`).
O `trend-backend` mistura laboratório — pesquisa, protocolos, experimentos — com a API do painel.

O autor quer duas frentes: o app como está, com melhorias, e a base de dados oferecida a terceiros,
com contas e chaves — para usar, e um dia vender junto com o app.

## Problema

Vender ou mesmo expor dado exige um serviço estável, versionado e com controle de acesso. O
laboratório precisa do contrário: liberdade para quebrar e experimentar. No mesmo serviço, um
compromete o outro.

E a licença não está resolvida. A política comercial de market data da B3 (out/2024) deixa
distribuir dado de fim de dia obtido pelas plataformas da B3, mas ser distribuidor exige contrato; o
preço vem do arquivo COTAHIST, e proventos e eventos de endpoints não documentados do site da B3. Os
dados abertos da CVM são ODbL: uso comercial com atribuição, e base derivada oferecida ao público
pode ter de seguir a mesma licença.

## Alternativas

1. **Expor a base pelo `trend-backend`.** Rejeitada: laboratório e produto no mesmo serviço.
2. **Esperar a resposta da B3 para começar.** Rejeitada pelo autor: no pior caso, o serviço fica
   de uso interno, e ele já vale por isso.
3. **Um serviço próprio de dados, construído para o público desde o primeiro dia.**

## Decisão

A alternativa 3.

- **`dados-api/` é um serviço novo**, só leitura sobre o schema `mercado` (papel `mercado_leitura`),
  com o próprio schema `acesso` no mesmo Postgres para contas, chaves, planos e uso. Não escreve em
  `mercado`, e o data-job não sabe que ele existe.
- **Construído para o público:** contas, chaves por conta (só o hash é guardado), planos com limite
  por minuto e por dia, histórico limitado por plano, uso contado por chave e por dia, revogação de
  chave, rotas de administração separadas, documentação OpenAPI, versão na URL (`/v1`), paginação
  por cursor, e atribuição das fontes em toda resposta.
- **Cadastro por convite primeiro.** Conta nasce pela administração; a própria conta gerencia as
  suas chaves. Cadastro aberto exige verificação de e-mail e vem depois, quando houver para quem.
- **O app vira o primeiro cliente.** Hoje o backend lê o banco direto; migrar para a API é o passo
  seguinte, e prova o serviço com uso real antes de qualquer terceiro.
- **O laboratório fica no `trend-backend`**, com o painel do autor, livre para experimentar.
- **Cobrar de terceiros depende da licença.** Até a resposta da B3 e a leitura da ODbL, só contas
  internas e convidadas sem cobrança. Se a B3 recusar, o serviço fica de uso interno, e o que vem
  só da CVM, do BCB e do Tesouro pode ser revisto à parte.
- **A fase continua pessoal** ([ADR-023](ADR-023-fase-pessoal-primeiro.md)): o serviço é construído
  pronto para o público, mas abrir é decisão própria, com backup e o item A12 resolvidos antes.

## Consequências

**Ganhos**

- Um contrato de leitura só, versionado, para o app, o painel e terceiros
- O laboratório pode mudar sem quebrar quem consome dado
- O produto de dados existe pronto quando a licença permitir

**Custos aceitos**

- Mais um serviço no Railway, e mais uma suíte para manter
- Um serviço público com um autor só: disponibilidade e correção do dado viram compromisso
- Dado com lacunas declaradas ([base/](../base/README.md)) passa a ter
  cliente — a lacuna precisa estar na documentação da API, não só na nossa

## Referências

- [Política Comercial de Market Data B3 (out/2024)](https://www.b3.com.br/data/files/6D/77/9D/65/0AB929106EEC8429AC094EA8/Politica%20Comercial%20de%20Market%20Data%20v3.0.4.1.pdf)
- [Portal de dados abertos da CVM](https://dados.cvm.gov.br/)
- [base/](../base/README.md) · [ADR-022](ADR-022-dados-de-mercado-coletados-em-lote.md) · [ADR-023](ADR-023-fase-pessoal-primeiro.md)
