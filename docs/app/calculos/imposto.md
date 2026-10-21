# Apuração de imposto

Espelho auditado do código, que é a fonte de verdade: fórmula divergente é bug deste documento.
`backend/app/ledger/apuracao.py` — projeção do razão, com o mês como unidade.

---

## Alíquotas

| Categoria | Alíquota | Isenção |
|---|---|---|
| `acoes_br` | 15% | R$ 20.000 em vendas no mês |
| `bdrs`, `etfs` | 15% | ❌ |
| `fiis` | 20% | ❌ |
| day trade, qualquer categoria | 20% | ❌ |

## Day trade

Compra e venda do mesmo ativo no mesmo dia. A projeção (`ledger/projection.py`) aparta a parte
casada antes de mexer na posição, e a apuração lê o que ela registrou
([ADR-020](../../decisoes/ADR-020-day-trade-apartado.md)):

```
casado    = mín(comprado no dia, vendido no dia)
resultado = casado × (preço médio de venda do dia − preço médio de compra do dia) − taxas casadas
taxas casadas = taxas de compra × casado/comprado + taxas de venda × casado/vendido
```

- **A sobra de compra entra no preço médio**; a parte casada não. **A sobra de venda é venda comum**
  contra o preço médio. A ordem de registro dentro do dia não muda nada
- **Conta própria por mês e categoria:** 20%, sem isenção, e o prejuízo de day trade só abate ganho
  de day trade da mesma categoria. O prejuízo comum também não abate day trade
- **A venda de day trade soma no volume da isenção** das operações comuns de `acoes_br`
- **IRRF:** 1% do resultado líquido positivo do dia, por categoria — o que a corretora retém. Ele se
  deduz do imposto de day trade do mês (`irrf_deducted`); o que sobra passa para os meses seguintes
  da mesma categoria. `ir_amount` é o imposto apurado; `ir_payable`, o que vai para o DARF
- **Corretora única:** o razão não guarda corretora, então compra numa e venda noutra no mesmo dia
  vira day trade
- A linha de Encerradas leva `day_trade` e o `id` da última venda do dia

## Ordem do cálculo, por mês, categoria e modalidade

1. Soma as vendas do mês e o resultado (`valor bruto − custo − taxas`)
2. Verifica a isenção — **só para `acoes_br` comum**, sobre o **volume vendido** (com o de day
   trade), não sobre o lucro
3. Se isento e com lucro: sem imposto
4. Se isento e com prejuízo: **o prejuízo não gera crédito compensável**
5. Se tributável: abate prejuízo acumulado da **mesma categoria e modalidade**
6. Aplica a alíquota sobre o que sobrou
7. No day trade, deduz o IRRF retido

**A isenção corta os dois lados.** É a regra que mais surpreende, e está no passo 4.

## O que não existe

Não há campo de imposto gravado numa venda. Gravá-lo fazia a ordem de registro dentro do mês mudar o
número, a isenção não ser reavaliada, e a venda vinda de `POST /transactions` não apurar nada.

O IR que aparece por linha em Encerradas é **rateio** do mês, e a tela diz isso.

## Limitações

- **Day trade assume corretora única** — o razão não guarda corretora nem hora
- **Três leituras conservadoras no day trade:** FII comum e day trade ficam em contas separadas (a
  Receita os junta), a venda casada conta no volume da isenção, e o IRRF só abate imposto de day
  trade da própria categoria. Cada uma pode mostrar imposto maior que o devido, nunca menor
- **Não emite DARF** — dá o número, não a guia
- Não gera informe para a declaração anual
- Não trata compensação entre categorias diferentes

A seção 4 dos `/termos` declara essas limitações ao usuário.
