# ADR-034 — A cobrança liga para o autor, o cadastro pede o endereço, e o Asaas é conferido

**Status:** ACEITO
**Data:** 2026-10-24
**Decidido por:** autor do projeto
**Ajusta:** [ADR-025](ADR-025-cobranca-da-api-de-dados.md), em quando ligar a cobrança, e
[ADR-031](ADR-031-assinatura-cria-a-conta.md), no que o cadastro pede

## Contexto

A [ADR-025](ADR-025-cobranca-da-api-de-dados.md) deixou a cobrança desligada até a licença da B3, o
CNPJ e os termos de uso. O autor a ligou em produção para pagar a própria assinatura e exercitar o
fluxo; ninguém mais usa. Rodando de verdade, o código mostrou quatro buracos:

- **Trocar de plano cancelava a assinatura antiga antes de criar a nova.** Se o Asaas recusasse a
  nova, o assinante ficava sem nenhuma.
- **Estorno e chargeback não tiravam o acesso.** O webhook só tratava a confirmação, e a conta
  seguia liberada até o `pago_ate`.
- **Webhook perdido era pagamento perdido.** Depois de 15 falhas seguidas, o Asaas interrompe a fila
  de webhooks e, passados 14 dias, apaga os eventos guardados.
- **O CPF ou CNPJ só era validado pelo Asaas**, depois de a conta e a chave estarem gravadas.

## Problema

Como deixar a cobrança confiável para quando abrir a terceiros, sem esperar a licença para corrigir
o que já está rodando, e pedindo só o dado que a cobrança usa?

## Alternativas

1. **Desligar de novo até a licença.** Rejeitada: o autor quer o fluxo exercitado, e os buracos
   continuariam lá para o dia de abrir.
2. **Corrigir só o webhook.** Rejeitada: o webhook é um aviso, não a fonte do estado. Sem conferir o
   Asaas, a fila interrompida perde pagamento do mesmo jeito.
3. **Tratar o Asaas como a fonte do estado de cada pagamento**, ouvido pelo webhook e conferido de
   tempos em tempos, e validar aqui o que der para validar.

## Decisão

A alternativa 3.

- **A cobrança fica ligada, e a abertura a terceiros continua esperando** licença, CNPJ e termos de
  uso. O portal está no ar com a assinatura aberta, mas ninguém é levado até ela.
- **O cadastro pede CEP e número do endereço**, obrigatórios, **e o celular, opcional.** Não espera a
  nota fiscal, que é quando algumas prefeituras exigem o endereço. Como o nome e o documento, esses
  dados vão só para o cliente do Asaas: a base guarda o nome e o e-mail da conta, nada mais. O portal
  diz isso ao lado do formulário. E-mail é pedido duas vezes: é para ele que o Asaas manda a
  cobrança, e a chave só aparece uma vez.
- **O CPF ou CNPJ é validado aqui, pelo dígito**, antes de qualquer gravação, inclusive o CNPJ com
  letras que a Receita emite desde julho de 2026. Vai ao Asaas sem máscara.
- **A assinatura nova nasce antes de a antiga cair.** A antiga fica `substituida` com
  `cancelamento_pendente`; se o Asaas não a cancelar na hora, a conferência tenta de novo.
- **Cada pagamento aplicado é gravado** (`acesso.pagamento`), com o período que cobre. O estado sai
  sempre da consulta ao Asaas, nunca do corpo do webhook. Pagamento estornado, em chargeback ou
  removido recua o `pago_ate` ao último pagamento que segue de pé, ou à véspera do vencimento dele
  se não houver outro. Estorno de um mês antigo não corta o mês pago depois.
- **Pagamento que chega de uma assinatura substituída é estornado sozinho.** Se o Asaas recusar o
  estorno, o evento fica com "estornar à mão" e aparece no console.
- **O serviço confere o Asaas a cada seis horas**, e o console confere na hora. A conferência aplica
  o pagamento confirmado que o webhook não trouxe, desfaz o que foi estornado e cancela a substituída
  pendente. Evento parado há mais de uma hora e estorno à mão aparecem em "Pede atenção".
- **`externalReference` é o id da conta**, no cliente e na assinatura, para o painel do Asaas
  apontar a conta daqui.

## Consequências

**Ganhos**

- Nenhuma troca de plano deixa o assinante sem assinatura
- O acesso acompanha o dinheiro também na volta: estorno e chargeback cortam
- Webhook perdido vira atraso de até seis horas, não pagamento perdido

**Custos aceitos**

- A conferência roda dentro do processo da API, numa thread: com mais de uma réplica, cada uma
  confere. É idempotente, então só gasta chamadas ao Asaas.
- O estorno sem pagamento anterior recua para a véspera do vencimento, e os três dias de tolerância
  ainda valem.
- Pedir endereço a quem só quer testar é atrito, aceito para não pedir de novo quando a nota fiscal
  vier.
- Renovar o mesmo plano ainda cobra no dia e descarta os dias que restavam; trocar de plano não
  desconta o restante do anterior. Fica para decidir.

## Referências

- [docs/dados](../dados/README.md#cobrança)
- [ADR-025](ADR-025-cobranca-da-api-de-dados.md), [ADR-031](ADR-031-assinatura-cria-a-conta.md),
  [ADR-033](ADR-033-conta-sem-pagamento-entra-em-minha-conta.md)
