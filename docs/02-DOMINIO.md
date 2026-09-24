# Domínio

**Fonte de verdade** para o vocabulário e as regras de negócio. Os enums são derivados do código.
Última revisão: 2026-09-13

Leia antes de tocar em `ledger/`, `cashflow/` ou `analysis/`.

---

## Glossário

Termos que o código presume conhecidos e que não são óbvios.

**Livro-razão** — a lista de lançamentos (compra, venda, provento, evento corporativo). É a **fonte
da verdade** da carteira. `ledger/`

**Projeção** — qualquer número reconstruído a partir do razão: a posição atual, o preço médio, a
apuração de imposto. Projeção nunca é gravada como verdade independente; é recalculada.

**Falsificador** — a condição conferível que mudaria o veredito. Para um veredito de preço, é o
preço em que ele vira outro: *"se cair para R$ 28,40, fica abaixo do preço justo"*. Sai por álgebra dos limiares
de margem de segurança, não de opinião. Existe para que um julgamento seja verificável em vez de
confiável. `analysis/falsifiers.py`

**Provento derivado** — provento que aparece no caixa **sem estar gravado na tabela de caixa**. Ele
já é lançamento do razão; a camada de serviço o soma em memória na leitura. Existe para tornar
impossível, por construção, contar o mesmo dinheiro duas vezes. O tipo recusa categoria `provento`
sem `derived=True`, e recusa `derived` em qualquer outra categoria.

**Modelo principal** — o método que descreve o fluxo da classe: lucro distribuível descontado para
ação, distribuição recorrente capitalizada para FII. BDR e ETF não têm.

**Faixa de preço justo** — o modelo principal da premissa pessimista à otimista: sem crescimento e
com 1 ponto a mais de taxa, até com crescimento e 1 ponto a menos. É incerteza sobre o valor, e não
distância entre métodos que medem coisas diferentes.

**Confirmação** — a leitura por outro insumo: o dividendo recorrente na ação, o VPA no FII. Diz se a
faixa se sustenta, e entra na qualidade — nunca na borda.

**Margem de segurança** — distância do preço de mercado até a **borda** da faixa: sobre o piso
quando o preço está abaixo dele, sobre o próprio preço quando está acima do teto, e zero dentro da
faixa. As duas pontas medem a mesma distância.

**Sem preço justo** — o que o produto diz sobre ativo sem modelo principal (BDR, ETF) ou sem o dado
que o modelo exige (lucro, ROE, juro). A tendência continua na tela, como contexto, e nunca decide.

**Preço-teto da meta** — até que preço a distribuição recorrente rende o yield que a pessoa
declarou. É meta de renda, não valor: mudar a meta muda o teto, e não a faixa.

**Qualidade da faixa** — `firme`, `ampla`, `fragil` ou `sem_faixa`. Diz se dá para confiar na faixa,
e não onde ela está. Com `fragil`, a etiqueta não passa de abaixo ou acima do preço justo.

**Gatilho e premissa** — o gatilho é o preço em que a etiqueta muda; a premissa é a condição
econômica que sustenta o preço justo. Atravessar um gatilho reclassifica; refutar uma premissa
derruba a tese. A resposta separa os dois em `kind`.

**Cascata da sobra** — a ordem em que o dinheiro que sobra é destinado: dívida cara, depois reserva,
depois aporte. Pode terminar sem aporte, e isso é sucesso.

**Livre agora** — **fato**: entrou, menos saiu, menos o comprometido e datado. Alimenta `/mes`.

**Sobra piso / sobra teto** — **projeção**: o livre agora menos o gasto variável ainda esperado.
Alimenta `/sobra`. A diferença entre livre agora e sobra *é* a estimativa.

**Competência (caixa)** — o dia do **pagamento**, não do vencimento. Conta de agosto paga em
setembro é de setembro.

**Apuração mensal** — o cálculo de imposto do mês, por categoria. A unidade é o mês, sempre.

**Desvio de alocação** — diferença entre a alocação atual e a meta declarada, por categoria.

**Classe de dívida** — `cara`, `administrável` ou `sem taxa`. Sai da comparação entre a taxa da
dívida e o que a carteira da pessoa rende. Não existe campo "caro" declarado.

**Taxa de virada** — a taxa em que uma dívida deixa de ser cara. É o falsificador da régua de
dívida.

---

## Classes de ativo

Vocabulário fechado, em `models/enums.py`.

| Tipo (`AssetType`) | Categoria (`AssetCategory`) | Suportado |
|---|---|---|
| `br_stock` | `acoes_br` | ✅ |
| `bdr` | `bdrs` | ✅ |
| `fii` | `fiis` | ✅ |
| `etf` | `etfs` | ✅ |
| `renda_fixa` | `renda_fixa` | ✅ |

**Renda fixa** (`RendaFixaType`): `cdb`, `lci`, `lca`, `lc`, `cri`, `cra`, `tesouro_selic`,
`tesouro_ipca`, `tesouro_pre`. Tipo de taxa: `pre_fixado`, `pos_fixado`, `hibrido`.

**Fora de escopo:** cripto, ações internacionais diretas, previdência, Fiagro/Fi-Infra, opções e
derivativos. Ver [09-FUTURO](09-FUTURO.md) para o que é ideia e o que é considerado.

---

## Regras do livro-razão

**O razão é a fonte; a posição é projeção dele.** A escrita grava só lançamento e reconstrói a linha
de posição a partir dele. Não há espelhamento entre duas verdades.

**Toda escrita passa por `ledger_service` e reprojeta.** `record_entry`, `record_entries`,
`delete_entry`, `import_entries` são a porta única. Escrever direto no store faz a carteira não
mudar — e o usuário não saber.

**Preço médio segue a convenção brasileira:** venda reduz quantidade e custo, nunca a média.

**Comprar não é declarar posição.** Uma compra (`buy`) soma à posição e recalcula a média; uma
declaração (`adjust`, via `POST /portfolio/position`) diz "eu tenho isto" e ancora a linha do tempo.
Usar declaração onde cabia compra apaga o histórico e faz o imposto da venda futura sair errado —
por isso o botão do Descobrir registra compra.

**Uma declaração de posição ancora a linha do tempo, e a assimetria é proposital.** O que vier
depois se aplica em cima. O que tem data anterior e **soma** posição (compra, bonificação,
transferência de entrada) já está dentro do que foi declarado, e é descartado com aviso — senão
declarar 100 hoje e importar o extrato do ano passado daria 200. O que tem data anterior e **reduz**
continua valendo: é a venda retroativa contra posição declarada hoje, que o produto suporta.

**Evento corporativo é lançamento**, não correção manual: `split`, `bonus`, `amortization`.
Desdobramento sem ajuste é imposto errado.

**Valor negativo não é lançamento, é sinal trocado.** Entrada e saída se distinguem por tipo.

**Importação é prévia e commit:** tolerante com a forma, intolerante com ambiguidade; o erro diz a
linha; a gravação é atômica; duplicidade é apresentada para decisão, nunca silenciada.

**Provento por calendário é sugestão, nunca lançamento.** Toda ressalva ali erra para mais, então
nada vem pré-selecionado e não existe "aceitar todos".

---

## Regras de imposto

A apuração é projeção do razão, e a unidade é o mês. Não existe campo de imposto gravado numa venda:
guardá-lo fazia a ordem de registro dentro do mês mudar o número.

| Regra | Valor |
|---|---|
| Alíquota ações, BDRs, ETFs | 15% |
| Alíquota FIIs | 20% |
| Isenção mensal | R$ 20.000 em vendas, **só** para `acoes_br` |
| Compensação de prejuízo | Por categoria, sem prazo |
| Fuso | Brasileiro (`core/brt.py`), não UTC |

**Isenção corta os dois lados:** prejuízo apurado em mês isento **não** gera crédito compensável.

**O IR por linha em Encerradas é rateio do mês**, e a tela diz isso. O número que se paga está na
apuração mensal.

**Não cobre:** day trade, emissão de DARF, informe anual. O texto de `/aviso-cvm` declara isso.

---

## Regras do caixa

**Toda escrita passa por `cashflow_service`:** `registrar`, `registrar_varias`, `editar`,
`marcar_paga`, `apagar`.

**Competência é o dia do pagamento.** Conta não paga conta no mês do vencimento, e é o que forma o
comprometido.

**Entrada não tem vencimento.** Dinheiro que se recebe não é obrigação a cumprir.

**Provento não se lança no caixa — é derivado do razão.** Se a pessoa pudesse lançá-lo também,
contaria duas vezes e inflaria a renda do mês e a sobra junto.

**Fato e projeção não se misturam.** `livre_agora` é fato; `sobra_piso`/`sobra_teto` é projeção. Um
número que às vezes é fato e às vezes é projeção seria a pior das duas coisas.

**Sem mês fechado não há estimativa, e ausência não vira zero.** A estimativa sai só do histórico da
própria pessoa, até 3 meses fechados. Sem base, a sobra é o próprio livre agora — tratar "não sei"
como "não vai sair nada" daria sobra otimista justamente a quem começou agora.

**Pagamento de dívida sai do caixa e não é consumo.** Se entrasse na base de estimativa, a rotina
pareceria custar o que a dívida custa.

### Vocabulário de categorias

| Bloco | Valores |
|---|---|
| Despesa | `moradia`, `contas_da_casa`, `mercado`, `transporte`, `saude`, `educacao`, `lazer`, `cuidados_pessoais`, `divida`, `outros` |
| Entrada | `salario`, `decimo_terceiro`, `ferias`, `renda_variavel`, `provento`, `reembolso`, `outros` |
| Fixas | `moradia`, `contas_da_casa`, `educacao` |
| Variáveis | `mercado`, `transporte`, `saude`, `lazer`, `cuidados_pessoais`, `outros` |
| Fora da base de renda | `provento`, `reembolso` |

Categoria fora do vocabulário devolve 422. `cashflow/entries.py`

---

## Regras de dívida

**Dívida se classifica por custo, nunca por tipo.** Consignado a 0,4% ao mês e consignado a 3,5% não
são a mesma decisão.

A referência é o que **a carteira da pessoa** rende; sem carteira, o CDI do BCB. Dívida cara é a que
custa mais que a referência.

**Sem taxa informada não há classe.** O produto não estima taxa de rotativo, que varia por banco e
por dia.

**Taxa anual vira mensal por juros compostos, nunca dividindo por doze.** Dividir superestima a
referência e afrouxa a régua: 12% ao ano dão 0,9489% ao mês, não 1,0%. O erro cairia do lado de não
avisar.

Tipos: `rotativo_cartao`, `cheque_especial`, `credito_pessoal`, `financiamento_imovel`,
`financiamento_veiculo`, `parcelamento`, `outros`.

---

## Regras da cascata

**Ordem: dívida cara → reserva → aporte.**

**A reserva vem depois da dívida cara, e só existe com alvo declarado.** A reserva existe para a
pessoa não precisar tomar dívida cara; quem já a tem não precisa se proteger do risco de contraí-la.
O alvo é em meses do **próprio** gasto fixo, declarado pela pessoa — o produto não inventa seis
meses.

**A cascata pode terminar sem passo de aporte, e isso é sucesso.** É por isso que o destino se chama
`Sobra`, e não `Aporte`.

Cada passo carrega o motivo e o falsificador. `cashflow/cascata.py`

---

## Unidades

Erro de unidade é o defeito mais caro deste domínio, porque não quebra nada.

| Grandeza | Unidade | Onde se converte |
|---|---|---|
| `roe`, `profit_margin`, `revenue_growth`, `debt_to_equity` | **percentual** (20.0 = 20%) | `collectors/universal._ratio_to_pct` |
| Crescimento e ROE no modelo de lucro | **fração** (0.15 = 15%) | `analysis/fair_price.py::normalized_roe` |
| Yield desejado | **fração** (0.06 = 6%) | `analysis/fair_price.py` |
| Margem de segurança | fração (0.15 = 15%) | `analysis/fair_price.py` |
| Dividend yield no score | percentual | `analysis/scoring.py` |
| Taxa de dívida | percentual ao mês | `cashflow/debt.py` |

**Dinheiro fiscal é `Decimal`; dinheiro de tela é `float`.** Escala e arredondamento só em
`core/money.py`, meio para cima. Nunca construa `Decimal` a partir de `float` sem passar por texto —
use `money()`. Colunas monetárias são `Money`; agregação é `sum_money()`, nunca `func.sum()`.
