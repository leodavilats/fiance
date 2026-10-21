# ADR-025 — A API de dados é paga, sem plano gratuito, em três degraus

**Status:** SUBSTITUÍDO EM PARTE por [ADR-030](ADR-030-sem-exportacao-dois-planos.md) — o Quant e a exportação
**Data:** 2026-10-14
**Decidido por:** autor do projeto

## Contexto

A `fiance-dados` ([ADR-024](ADR-024-api-de-dados.md)) nasceu com três planos: `interno`, `convidado`
e `gratuito`. O autor não quer nada gratuito. O app já segue essa linha
([ADR-009](ADR-009-trial-e-gratuidade.md)).

O que a base tem de raro não é a cotação do dia, que se acha em muitos lugares. Raros são o
histórico com as empresas que saíram da bolsa, a série ajustada com os eventos conferidos pelo preço
e o balanço como se sabia na data. Quem precisa disso costuma testar estratégia, e paga por não ter
de montar a base.

## Problema

Como cobrar sem plano gratuito, de modo que o preço acompanhe o valor, e sem cobrar antes de a
licença permitir?

## Alternativas

1. **Cobrança por chamada.** Rejeitada: quem testa estratégia faz rajadas, e a conta sai
   imprevisível para os dois lados.
2. **Um plano só.** Rejeitada: quem quer a cotação do dia pagaria pelo histórico inteiro, ou quem
   quer o histórico pagaria pouco demais.
3. **Degraus por recurso, mensais ou anuais, com o caro no que é raro.**

## Decisão

A alternativa 3.

- **Três planos pagos:** Essencial (cotação, proventos, retrato e macro dos últimos dois anos),
  Pro (histórico inteiro, série ajustada, balanço por data, informe de FII) e Quant (tudo, limites
  altos e exportação, sob contrato). Os preços — R$ 49, R$ 149 e a partir de R$ 490 por mês, com
  anual de dez meses — são **hipótese**, e mudam sem ADR.
- **O plano diz o que libera** (`recursos`): uma rota fora dele responde 403, e um plano pago sem
  pagamento em dia responde 402, com três dias de tolerância.
- **`interno` e `convidado` ficam, sem cobrança e fora da página.** Convite é o modo de testar.
- **Cobrança pelo Asaas** (Pix, boleto e cartão, assinatura recorrente), atrás de
  `COBRANCA_ATIVA`. O titular de um pagamento sai da assinatura que nós criamos, nunca do corpo do
  webhook; o pagamento é reconsultado no Asaas antes de liberar; cada evento entra uma vez só.
- **A cobrança fica desligada até haver licença da B3, CNPJ e termos de uso.** Até lá, o portal
  mostra os planos e o acesso é por convite. Contrato e pagamento por fora entram pela
  administração (`pago_ate`).

## Consequências

**Ganhos**

- Nenhuma conta usa o serviço sem que o autor saiba por quê
- O preço segue o que é difícil de achar em outro lugar
- A cobrança está pronta para ligar sem mudar código

**Custos aceitos**

- Sem gratuito, há menos gente experimentando. O convite cobre isso, à mão
- Um plano pago na página pede termos de uso e nota fiscal, que ainda não existem
- Os preços são palpite até haver o primeiro cliente
