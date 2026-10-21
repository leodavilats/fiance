# O aplicativo

Um dos dois produtos do fiance: **onde está cada ativo, e por quê**, para quem tem salário e pouco
tempo. `backend/` (FastAPI e Postgres) e `mobile/` (Flutter, o único cliente). Contrato de trabalho:
[backend/CLAUDE.md](../../backend/CLAUDE.md) e [mobile/CLAUDE.md](../../mobile/CLAUDE.md).

| Quero saber | Leia |
|---|---|
| Para quem, o que entrega, o que não é, como se paga | [produto](produto.md) |
| O que significa esse termo, qual é a regra | [dominio](dominio.md) |
| Como é montado, sessão, segurança, cache, dados de mercado | [arquitetura](arquitetura.md) |
| Como esse número é calculado, e no que não confiar | [calculos/](calculos/README.md) |
| O que uma tela precisa respeitar | [interface](interface.md) |
| Armadilhas, testes de arquitetura, revisão de telas | [desenvolvimento](desenvolvimento.md) |
| Variáveis, sinais de fonte caída, publicação nas lojas | [operacao](operacao.md) |
| O que existe, em que estado | [03-ESTADO](../03-ESTADO.md#app) |
| O que está aberto | [04-PROBLEMAS](../04-PROBLEMAS.md#app) |

O app lê dado de mercado só pela [API de dados](../dados/README.md), com a mesma chave e os mesmos
limites que um terceiro teria.
