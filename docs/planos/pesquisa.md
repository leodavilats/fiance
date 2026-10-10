# Plano — pesquisa de carteira (`trend-backend/`)

**Estado:** motor, registro, relatório, momento 12–1 e valor + qualidade `[IMPLEMENTADO]` · **Escrito em:** 2026-10-10 · **Uso:** próprio do autor, não é produto

A pesquisa testa estratégias de carteira em horizonte de meses sobre a base do
[data-job](data-job.md). Este documento é o **protocolo**: foi escrito antes do primeiro resultado, e
mudar uma regra depois de ver um resultado invalida o resultado.

---

## A pergunta

Uma carteira de ações escolhida por regra fixa, rebalanceada uma vez por mês, **bate o CDI depois de
custos e imposto**, por margem que compense o risco, num período que a regra nunca viu?

A régua é o CDI, não o Ibovespa: o CDI é a alternativa sem risco e com liquidez diária.

## Os três períodos

| Período | Datas | Uso |
|---|---|---|
| Estudo | 2005-01 a 2018-12 | Criar e ajustar hipóteses, à vontade |
| Validação | 2019-01 a 2022-12 | Conferir o que sobreviveu ao estudo; poucas vezes |
| **Prova** | 2023-01 em diante | **Lacrada.** Abre uma vez por hipótese congelada |

- **A prova só roda para hipótese congelada** — parâmetros escritos no registro antes da abertura — e a
  abertura fica registrada. Abrir de novo a mesma hipótese exige forçar, e o forçar também fica no
  registro
- **Toda execução fica no registro** (`trend-backend/registro.jsonl`, só acrescenta): hipótese,
  parâmetros, período, resultado. O número de variações testadas é parte do resultado: com 200
  tentativas, uma passar é o esperado por sorte

## Regras da simulação

- **Rebalanceamento** no último pregão de cada mês, comprando e vendendo pelo fechamento do dia
- **Só o que se sabia na data.** Preço até o dia; balanço pela data de entrega à CVM, nunca pela data de
  referência
- **Universo com liquidez:** volume mediano dos últimos 63 pregões acima de R$ 5 milhões, preço acima de
  R$ 1 e ao menos 252 pregões de história. Quem saiu da bolsa está no universo enquanto negociou
- **Pesos iguais** entre os escolhidos; entre um rebalanceamento e outro, a carteira deriva com o preço
- **Retorno total**: preço ajustado mais provento na data ex (bruto — o imposto do JCP não é descontado)
- **Custo de 0,25% por lado** sobre o valor negociado (emolumentos e *spread*); configurável
- **Imposto de 15% sobre o ganho realizado** em cada venda, com prejuízo compensando ganho futuro. A
  isenção de vendas até R$ 20 mil por mês não entra: depende do tamanho da carteira e a favorece
- **Papel que deixa de negociar** fica com o último preço e vira caixa no rebalanceamento seguinte
- **Dia de salto sem evento** (`salto_sem_evento` na base): o retorno daquele dia conta como zero, e a
  quantidade de dias assim entra no relatório. Papel com salto desses nos 252 pregões anteriores fica
  fora da escolha daquele mês
- **Caixa rende CDI**

## O que o relatório mostra

Por período: retorno anual composto, contra o CDI no mesmo intervalo; volatilidade anual; pior queda
acumulada; índice de Sharpe sobre o CDI; fração dos meses acima do CDI; giro mensal; custo e imposto
pagos; dias de salto sem evento zerados.

## Hipóteses

Cada hipótese é um módulo em `trend-backend/pesquisa/hipoteses/`, com nome, parâmetros e a função que
pontua os papéis numa data. As primeiras, nesta ordem:

1. **Momento 12–1:** retorno dos últimos 12 meses, ignorando o último; compra os 20 maiores
2. **Valor + qualidade:** lucro sobre valor de mercado alto entre os de retorno sobre patrimônio alto
3. **A combinação** das duas

### O que valor + qualidade precisa da base

- **Lucro de 12 meses só com o que já tinha sido entregue:** no trimestre, acumulado do ano + último
  anual − acumulado do mesmo ponto do ano anterior; a disponibilidade é a **primeira** entrega do
  documento à CVM
- **Número de ações** de duas fontes: o FRE (quantidade integralizada, na data de aprovação do capital,
  de 2010 em diante) e a composição do capital na DFP e no ITR (de 2020 em diante, quando a CVM passou a
  publicá-la). Vale o registro mais recente em cada data. A data de aprovação vem antes da entrega do
  FRE: é uma antecipação pequena, aceita
- **Unidade:** valor de mercado abaixo de 2% do patrimônio é quantidade declarada em milhares (Gafisa), e
  é multiplicado por mil
- **Digitação:** quantidade que destoa por fator de 3 dos dois vizinhos, que concordam entre si, sai — o
  Banco do Brasil declara um décimo das ações no FRE de 2015, e sairia com P/L 0,5. Desdobramento muda a
  quantidade de vez e fica
- **Um papel por empresa**, o mais negociado nos últimos 63 pregões
- **Sem balanço antes de 2010**, a hipótese fica em caixa no começo do estudo e só investe de 2011 em diante

### Observação de diagnóstico (não é execução do registro)

De 2011 a 2018, **comprar todos os papéis do universo, em pesos iguais, rendeu 7,4% ao ano sem custo nem
imposto, contra 10,3% do CDI**. A bolsa inteira perdeu do CDI nesse trecho; uma hipótese que perde do CDI
ali precisa ser comparada também com esse mercado, e não só com o CDI.

## Acesso à base

A pesquisa roda sobre um **retrato**: a série ajustada e o CDI exportados para Parquet em
`trend-backend/.retratos/<data>/` (fora do Git). O mesmo retrato reproduz o mesmo resultado, e a data
do retrato vai para o registro.

```bash
cd trend-backend
python -m pesquisa retrato --pelo-railway     # pela CLI do Railway, sem expor o banco (~2 min)
python -m pesquisa rodar --hipotese momento_12_1 --periodo estudo
python -m pesquisa relatorio                 # relatorio.html, com as curvas e as carteiras
```

`--pelo-railway` usa `railway ssh` no `postgres-mercado` e não exige porta pública nem senha. Sem a
opção, o retrato lê `PESQUISA_DATABASE_URL`, que só existe se um dia o banco ganhar acesso externo
com um usuário do papel `mercado_leitura`.

## Resultados

Os resultados ficam em `trend-backend/registro.jsonl`, e não neste documento: o registro é a fonte, com
cada execução e o retrato usado.
