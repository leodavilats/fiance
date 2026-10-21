# Carteira

Espelho auditado do código, que é a fonte de verdade: fórmula divergente é bug deste documento.

---

## Saúde da carteira

`analysis/portfolio_health.py` — de 0 a 100, sobre as posições de renda variável:

| Dimensão | Peso | Nota 100 → 0 |
|---|---|---|
| Concentração | 30% | maior posição de 10% a 40% do total |
| Concentração setorial | 20% | maior setor de 20% a 60% |
| Diversificação | 20% | categorias com valor, de 5 a 0 |
| Risco | 30% | fatia em veredito de venda, × 1,5 |

`_WEIGHTS` no mesmo arquivo. O risco lê a posição contra o preço justo, e não um retorno esperado: a
medida de 2026-10-12 não mostrou retorno menor acima dele.

---

## Projeção de patrimônio

`analysis/scenarios.py` — **três cenários, sempre**. Nunca um número único.

| Cenário | Fator | Racional |
|---|---|---|
| Conservador | 0,0 | A carteira não valoriza e os dividendos não crescem. Só o aporte trabalha. **É o único que não depende de previsão** |
| Base | 1,0 | As premissas informadas, aplicadas mês a mês |
| Otimista | 1,5 | As mesmas premissas multiplicadas por 1,5 |

O fator otimista de 1,5 **não é uma estimativa: é a largura escolhida para a faixa**, e o código diz
isso ao usuário com essas palavras.

`_low` e `_high` são campos **obrigatórios** de `PassiveIncomeMonth`: com default, existiria caminho
em que o número sai sozinho. `test/lint_ui_test.dart` recusa tela que exiba patrimônio ou renda
passiva projetados sem a faixa.

> Projeção não é previsão. A faixa mostra três contas com premissas diferentes, não a probabilidade
> de cada uma acontecer.


---

## Sugestões de rebalanceamento

`analysis/strategy.py` — `build_rebalance_suggestions`

Produz duas listas:

- **comprar**: por lacuna de alocação contra a meta, ordenada por score dentro da categoria
- **reduzir**: posições com veredito `SELL` ou `STRONG_SELL`, com destaque para as de categoria
  acima da meta

Cada sugestão carrega até 3 razões escritas.

Quando uma posição acima do preço justo tem para onde ir — um ativo abaixo do preço justo, de
categoria abaixo da meta, fora da carteira —, a sugestão traz a **frase do ajuste**
(`adjustment_sentence`): a margem do alvo e a da posição, as duas medidas contra a borda da faixa, e
se o preço do alvo cabe na meta de renda (`fits_income_goal`: preço ≤ `personal_ceiling`). Sem
yield declarado, a frase não fala de meta de renda. `realocar_para` leva também preço, faixa e
margem do alvo. A frase termina com "o preço justo descreve posição, não antecipa retorno": as
listas ordenam por posição, e a medida de 2026-10-12 não mostrou retorno maior abaixo do preço justo.

Na tela em `/sobra/desvio`: a frase em serifa, as razões, e o alvo com a faixa e a régua de score.

---

## Renda fixa

`analysis/renda_fixa_analysis.py` — acumula pela taxa contratada, por tipo de taxa, com o IPCA do
BCB para os indexados. Não é marcação a mercado. Compara com o CDI e projeta o valor no vencimento.

Tesouro Selic rende a Selic composta com a taxa informada (o ágio):
`(1 + selic) × (1 + taxa) − 1`. Taxa acima de 5% não é ágio: é a taxa anual inteira, gravada antes
de o app pedir só o ágio, e é lida como está (`AGIO_MAXIMO_TESOURO_SELIC`). O formulário recusa ágio
acima disso. Pós-fixado com % do CDI segue o CDI.

O valor atual é o **líquido se resgatasse hoje**, e o dia conta no fuso brasileiro. Dois impostos
saem do rendimento, nesta ordem:

```
iof       = rendimento × alíquota_iof(dias corridos)
ir        = (rendimento − iof) × alíquota_ir(dias corridos)
líquido   = rendimento − iof − ir
```

**IOF regressivo** (Decreto 6.306/2007, anexo): 96% no dia 1, 50% no dia 15, 3% no dia 29, zero do
dia 30 em diante. A tabela mora em `IOF_REGRESSIVO_PCT`. **O IOF vem antes do IR**, e a base do IR
é o que o IOF deixou.

**IR regressivo:** 22,5% até 180 dias, 20% até 360, 17,5% até 720, 15% depois.

| Tipo | IR | IOF |
|---|---|---|
| `cdb`, `lc`, `tesouro_selic`, `tesouro_ipca`, `tesouro_pre` | ✅ | ✅ |
| `lci`, `lca`, `cri`, `cra` | ❌ isentos | ✅ |

`isento_ir` declarado tira o IR, **nunca o IOF**. Poupança, isenta dos dois, não é tipo do modelo.
No comparador o prazo é de meses inteiros, então o IOF só aparece na posição com menos de 30 dias.

A curva de CDI é extrapolada da taxa de hoje (`cdi_basis`), então é **referência, não acumulado
histórico** — e o rótulo de fonte viaja até a tela.

---

## Proventos recebidos

`services/dividends_service.py`. A média mensal divide o que caiu nos últimos 12 meses pelo tempo
de carteira dentro do período, não pelos meses em que houve crédito:

```
início = máx(mín(primeiro lançamento do razão, primeiro crédito), hoje − 365 dias)
meses  = (hoje − início) em dias × 12 ÷ 365, limitado entre 1 e 12
média  = recebido nos 12 meses ÷ meses
```

Quem recebe duas vezes por ano vê a renda espalhada pelos doze meses, não por dois. Quem tem carteira
há dois meses tem a média sobre dois, e o mês corrente conta pelo que passou dele, não inteiro.
Crédito com data futura não zera o divisor: o mínimo é um mês. "Por ativo" soma todo o histórico
registrado, sem corte de 12 meses.
