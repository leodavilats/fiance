# fiance-dados

O que o produto é, para quem e por quanto vem de [docs/dados/](../../docs/dados/README.md). Aqui está
só como isso vira anúncio.

## Para quem

Quem testa estratégia ou analisa empresa com dado da B3 e da CVM: investidor quantitativo, analista,
desenvolvedor. Nos vídeos curtos, o espectador típico é **quem já tentou montar um backtest com
planilha ou dado de site** e desconfiou do resultado.

## A promessa

**A base que você montaria, se tivesse um ano livre — com o que é difícil de achar organizado.**

## As três mensagens

Cada peça carrega **uma** delas. A dor vem antes da API.

| Mensagem | A dor | A prova na tela |
|---|---|---|
| **Quem saiu da bolsa está no histórico** | Backtest só com as empresas que sobreviveram parece ótimo e é mentira — viés de sobrevivência | Cotação desde 2005 de uma empresa que deixou a B3 |
| **O ajuste é conferido pelo preço** | Série com salto de desdobramento ou grupamento faz o backtest "ganhar" num dia que não existiu | Série crua com o salto e a ajustada, lado a lado |
| **O balanço como se sabia na data** | Usar em janeiro um lucro publicado em março é olhar o futuro — e o backtest acerta tudo | A mesma demonstração antes e depois da entrega, com `sabido_em` |

Mensagens de apoio, para peças de 60–90 s:

- **A idade do dado está dita:** `/v1/atualidade` mostra até quando vai cada série.
- **Tudo vem de fonte pública:** B3, CVM, BCB e Tesouro, e o bruto é guardado.
- **Mais do que ação:** informe mensal de FII, proventos, séries do BCB, Tesouro Direto.
- **O próprio autor usa:** o app dele lê a base por esta API, com os mesmos limites de um cliente.

## Oferta

| Plano | Por mês | O que muda |
|---|---|---|
| Essencial | R$ 49 | O básico, com 730 dias de histórico |
| Pro | R$ 149 | Histórico inteiro, série ajustada, balanço por data (`sabido_em`), informe de FII |

O anual custa dez meses. Sem plano gratuito. A chamada leva ao portal, na âncora `#planos`.

**A venda só fecha com a cobrança ligada.** Hoje ela está desligada até a licença da B3, a leitura da
ODbL da CVM, CNPJ e termos de uso ([04-PROBLEMAS](../../docs/04-PROBLEMAS.md)). Peça com preço só vai ao
ar depois disso.

## Pastas

| Pasta | O quê |
|---|---|
| [roteiros/](roteiros/MODELO.md) | Um arquivo por peça, a partir do modelo |
| `prompts/` | Prompts de Veo e Nano Banana por peça (a criar com os roteiros) |
| `midia/` | Capturas, clipes, exportações — fora do Git |
