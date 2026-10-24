# ADR-033 — A conta sem pagamento entra em Minha conta, e o painel segue a situação dela

**Status:** ACEITO
**Data:** 2026-10-24
**Decidido por:** autor do projeto
**Ajusta:** [ADR-031](ADR-031-assinatura-cria-a-conta.md), no que a chave faz antes do pagamento

## Contexto

A [ADR-031](ADR-031-assinatura-cria-a-conta.md) fez a conta nascer na assinatura, com a chave
travada em 402 até o pagamento. Mas as rotas `/v1/conta` usavam a mesma autenticação dos dados, e
o 402 valia também para elas. Quem acabava de assinar não entrava em Minha conta; quem tinha a
assinatura vencida não entrava para renovar, e o cadastro o mandava de volta a Minha conta. O link
de pagamento aparecia uma vez só, e o botão do plano abria um formulário de login.

## Problema

Como o painel serve a quem ainda não pagou, a quem venceu e a quem está em dia, sem abrir os dados
a quem não pagou?

## Alternativas

1. **Manter o 402 em tudo e mandar o link por e-mail.** Rejeitada: o serviço não envia e-mail, e
   quem venceu continuaria sem renovar.
2. **Uma tela só, com abas "Entrar" e "Criar conta".** Rejeitada: o botão do plano cairia numa
   aba que a pessoa ainda precisa escolher.
3. **Separar a conta dos dados.** As rotas `/v1/conta` aceitam a chave sem pagamento; o 402 fica nas
   rotas de dados.

## Decisão

A alternativa 3.

- **Entrar na conta não exige pagamento** e não conta na cota do dia. Chave revogada ou conta
  desativada continuam recebendo 401.
- **`aguardando_pagamento` separa quem assinou e não pagou** de `sem_pagamento`, quem venceu.
- **O `/v1/conta` traz a assinatura atual**, com o link da cobrança em aberto consultado no Asaas.
  Asaas fora do ar vira `pagar_em_indisponivel`, não ausência de cobrança.
- **Renovar ou trocar de plano reaproveita o cliente do Asaas**: nome e CPF ou CNPJ só na primeira
  assinatura.
- **O portal tem `#assinar` para quem chega e `#conta` para quem tem chave.** O cadastro entra
  direto na conta, e um cartão de situação mostra o próximo passo: pagar, renovar ou nada.

## Consequências

- Abrir Minha conta consulta o Asaas quando há cobrança a pagar: o painel depende da resposta dele
  para mostrar o link.
- Quem perde a chave antes de pagar continua preso aos sete dias da ADR-031: sem e-mail verificado,
  liberar o e-mail deixaria um terceiro derrubar o boleto de outra pessoa.

## Referências

- [docs/dados](../dados/README.md#contas)
- [ADR-025](ADR-025-cobranca-da-api-de-dados.md), [ADR-031](ADR-031-assinatura-cria-a-conta.md)
