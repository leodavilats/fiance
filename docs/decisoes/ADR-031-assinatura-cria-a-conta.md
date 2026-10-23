# ADR-031 — Com a cobrança aberta, assinar cria a conta e entrega a chave na hora

**Status:** ACEITO
**Data:** 2026-10-23
**Decidido por:** autor do projeto
**Substitui em parte:** [ADR-024](ADR-024-api-de-dados.md), no cadastro por convite

## Contexto

A [ADR-024](ADR-024-api-de-dados.md) fez a conta nascer só pela administração, e a
[ADR-025](ADR-025-cobranca-da-api-de-dados.md) pôs a assinatura dentro de "Minha conta": para
assinar, a pessoa precisava de uma chave, e a chave só vinha por convite. Com a cobrança aberta,
quem chega pela página de planos não tem como pagar sem antes falar com o autor.

## Problema

Como deixar quem chega assinar sozinho — clicar, pagar, usar — sem verificação de e-mail, que o
serviço não tem, e sem que um cadastro alheio prenda o e-mail de alguém?

## Alternativas

1. **Manter o convite.** Rejeitada pelo autor: a assinatura tem de ser automática.
2. **Chave só depois do pagamento.** Rejeitada: no boleto, a confirmação leva dias, e a chave
   teria de ir por e-mail, que o serviço não envia.
3. **Chave na hora, travada até pagar.** A conta nasce no plano escolhido, sem `pago_ate`, e a
   chave responde 402 até o Asaas confirmar.

## Decisão

A alternativa 3, em `POST /v1/assinatura`, sem chave, só com a cobrança aberta.

- **O pagamento é o que libera**, pela mesma regra do 402 que já valia
  ([docs/dados](../dados/README.md#regras)). A chave aparece uma vez, na resposta.
- **E-mail de conta existente é recusado** (409): quem já tem conta assina em "Minha conta", com
  a chave. Convidado, interno e conta paga nunca são tocados pelo cadastro.
- **Cadastro que nunca pagou não prende o e-mail.** Quem assina de novo com ele recebe a conta, e
  as chaves antigas caem. Enquanto houver assinatura de até sete dias aguardando pagamento, o
  e-mail fica com ela: um terceiro não derruba o boleto de quem acabou de assinar.
- **Cinco cadastros por hora por endereço**, além das três assinaturas por dia por conta.

## Consequências

- O e-mail continua sem verificação: quem paga com o e-mail de outra pessoa fica com a conta. O
  pagamento identifica o pagador no Asaas, e o caso se resolve pela administração.
- Conta criada e nunca paga fica na base, sem uso: some da lista só se for desativada à mão.
- A abertura a terceiros segue esperando licença, CNPJ e termos de uso
  ([04-PROBLEMAS](../04-PROBLEMAS.md#api-de-dados)); esta decisão só vale com `COBRANCA_ATIVA`.

## Referências

- [docs/dados](../dados/README.md#contas)
- [ADR-024](ADR-024-api-de-dados.md), [ADR-025](ADR-025-cobranca-da-api-de-dados.md)
