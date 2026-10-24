# ADR-035 — O anual pode ser dividido em até 12x no cartão, como parcelamento e sem renovação automática

**Status:** ACEITO
**Data:** 2026-10-24
**Decidido por:** autor do projeto

## Contexto

O plano anual nasce como assinatura do Asaas com ciclo anual, que cobra o ano cheio de uma vez. O
autor quer que o anual possa ser dividido no cartão. A assinatura do Asaas não tem parcelas: o
cadastro dela não aceita nenhum campo de parcelamento, e o próprio Asaas trata assinatura (cobranças
ao longo do tempo) e parcelamento (uma operação dividida) como coisas diferentes.

## Problema

Como oferecer o anual em parcelas sem perder a renovação automática de quem não quer parcelar?

## Alternativas

1. **Anual só como parcelamento, de 1x a 12x.** Rejeitada: nenhum anual renovaria sozinho, e o
   anual perderia Pix e boleto.
2. **Parcelado que renova sozinho**, guardando o token do cartão e criando um parcelamento novo a
   cada ano. Rejeitada por ora: traz responsabilidade sobre dado de cartão e uma tela de cartão
   própria, no lugar da fatura do Asaas.
3. **Duas formas de pagar o anual.** À vista continua assinatura, com renovação automática; parcelado
   no cartão é um parcelamento, sem renovação.

## Decisão

A alternativa 3.

- **Mensal e anual à vista não mudam.**
- **O anual parcelado vai de 2x a 12x, só no cartão**, sem juros para quem paga: **o autor assume a
  taxa** do parcelamento. Boleto ou Pix parcelados virariam cobranças mensais sem garantia, o que é
  o mensal com desconto.
- **O ano conta do início**, não do vencimento de cada parcela. A primeira parcela confirmada libera
  o ano todo: no cartão, o valor inteiro é aprovado no limite do cliente de uma vez.
- **O parcelamento é uma compra só.** Estorno ou chargeback de qualquer parcela desfaz o ano
  inteiro. Pagamento de um parcelado já substituído é estornado inteiro.
- **Pago, o parcelado fica `quitada`**: não há recorrência a cancelar, e trocar de plano depois não
  mexe nele. Perto do vencimento, a pessoa gera a cobrança do próximo ano em Minha conta.

## Consequências

- Quem parcela renova à mão uma vez por ano. Sem e-mail enviado pelo serviço, o aviso é o cartão
  de situação de Minha conta, que já avisa a sete dias do vencimento.
- A taxa do parcelamento no cartão sai da receita do anual parcelado.
- A documentação do Asaas não diz se a fatura de um parcelamento no cartão criado sem os dados do
  cartão cobra todas as parcelas no cartão. O código conta com isso, e é o primeiro teste a fazer no
  sandbox.

## Referências

- [docs/dados](../dados/README.md#cobrança)
- [ADR-025](ADR-025-cobranca-da-api-de-dados.md), [ADR-034](ADR-034-cobranca-ligada-e-conferida.md)
