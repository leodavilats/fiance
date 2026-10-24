# Como cada dado é tratado

Regras que os dados ensinaram, com o que foi medido. O que a base guarda está no [README](../README.md).

---

## A base, e como foi aceita na carga inicial

COTAHIST de 2005 em diante, cadastro e FCA, DFP e ITR de 2010 em diante, BCB SGS.

**Conferido na carga inicial (2026-10-09):**

- A série da PETR4 de 2005 a hoje bate, em 5 datas sorteadas, com o fechamento publicado pela B3
- Uma empresa que saiu da bolsa tem cotação até a saída
- Uma troca de ticker (`VVAR3` → `VIIA3` → `BHIA3`) aparece como **um** ativo
- Lucro líquido e patrimônio da PETR4 em 2024 batem com a DFP publicada
- Rodar o `diario` duas vezes seguidas não muda nenhuma linha
- O volume de `demonstracao_linha` está medido, e cabe no plano do banco
- `ruff` e `pytest` no CI, como os do backend

## Visões de fundamento

`mercado.fundamento_resultado` (por documento e período) e `mercado.fundamento_balanco` (por
documento) leem as linhas brutas sem copiar nada; corrigir uma regra é uma migração.

O código da conta muda com o plano da empresa — o lucro dos controladores é `3.11.01` na Petrobras e
`3.09.01` no Itaú —, e a descrição das contas fixas da CVM é estável. As visões casam pela descrição,
com as variações medidas sobre os 22.837 documentos carregados.

| Coluna | Regra |
|---|---|
| `receita` | Receita de venda; em banco, receita da intermediação; em seguradora, receita das operações |
| `ebit` | Resultado antes do financeiro e dos tributos — **vazio em banco e seguradora**, onde não significa o mesmo |
| `lucro_controladores` | Atribuído aos sócios da controladora; sem consolidado, o lucro do período inteiro |
| `divida_bruta` | Soma de *Empréstimos e Financiamentos* no circulante e no não circulante — vazia em banco |
| `patrimonio_controladores` | Patrimônio menos a participação dos não controladores |

Cobertura nas DFPs: lucro 100%, receita 99,8%, EBIT 93,3%, ativo e patrimônio 100%, caixa 98,1%,
dívida 92,7%. Em 2024, Petrobras: lucro dos controladores R$ 36,6 bi e dívida bruta R$ 373 bi; Itaú:
lucro R$ 41,1 bi e patrimônio R$ 211 bi — como publicados.

**O ITR traz o resultado do trimestre e o acumulado no ano**, cada um com o seu início de exercício.
O lucro de 12 meses é conta de quem lê (o backend e a pesquisa): acumulado do ano + último anual − acumulado do mesmo ponto
do ano anterior.

## Série contínua de um papel — `mercado.cotacao_papel`

A troca de ticker cria ISIN novo: VVAR3, VIIA3 e BHIA3 são três ISINs da mesma empresa. A visão costura
as cotações por **CNPJ e classe da ação** (ON, PN, PNA, PNB…, UNT), e só com código BDI de ação —
recibo e direito de subscrição (ITSA9, BBDC10) têm espécie ON ou PN e ficam de fora. Em produção: 841
papéis de 543 empresas; a Casas Bahia sai contínua de 2012 a hoje.

**Restam algumas centenas de dias com duas cotações para o mesmo papel**, de tickers especiais
negociados como lote padrão (AZUL97–99, BEES11, JBDU11/12, BPAC13). Nesses dias, a pesquisa fica com
a de maior volume.

O preço é o **bruto**. Desdobramento, grupamento e provento entram na série ajustada
(`mercado.serie_papel`).

## Ligação do ativo à empresa

O ISIN carrega o código do emissor na B3 (posições 3 a 6). Ele é ligado a um CNPJ por três vias, nesta
ordem, e o método fica gravado para a pesquisa filtrar por confiança:

1. **FCA** — o ticker que a própria empresa declara à CVM. Vence a B3 quando divergem (JBSS, EMBR,
   TUPY, ENAT), porque é o CNPJ que entrega os balanços
2. **B3** — a lista de emissores listados hoje, num endpoint não documentado do site da B3. Cobre o
   que o FCA deixa em branco: o BTG Pactual declara o ticker como `000000`
3. **Nome** — o nome resumido do COTAHIST como prefixo da razão social ou do nome comercial no
   cadastro da CVM, só entre empresas com registro vigente no período de pregão, e só com um
   candidato. É a via de quem saiu da bolsa e ficou sem ticker no FCA (Souza Cruz, BR Properties)

O campo *mercado* do FCA não é confiável — a Brisanet declara BRST3 como balcão — e não é usado.

Em produção, com o histórico inteiro, são 726 emissores de ação: 450 pelo FCA, 41 pela B3, 109 pelo
nome, 126 sem CNPJ — na maioria, empresas que saíram da bolsa antes de 2010, antes do FCA. Uma amostra de 15 ligações por nome estava correta, inclusive empresas renomeadas depois de
sair (BR Insurance → Alper, Abril Educação → Somos). Sem o endpoint da B3, cerca de 30 emissores
listados hoje ficariam sem CNPJ; o resto não depende dele.

## Eventos e proventos

**Fonte: os endpoints do site da B3**, decidida em 2026-10-10 depois de comparar com a BRAPI gratuita:

| | B3 | BRAPI gratuita |
|---|---|---|
| Custo | Grátis | Só PETR4, VALE3, ITUB4, MGLU3 sem token |
| Quem saiu da bolsa | Cobre (Souza Cruz até 2015, Cetip, BR Properties) | Não |
| Valor | Limpo nos casos conferidos | Conta o mesmo provento duas vezes (Itaú: bruto + líquido) |
| Data de pagamento | Não | Sim |
| Formalidade | Não documentada | API comercial |

Por emissor, toda sexta (e na primeira carga): o histórico de proventos em dinheiro e os eventos em
ações. Cada coleta **substitui** os proventos e eventos daquele emissor; resposta sem nome de pregão
não substitui nada.

**Regras que os dados ensinaram:**

- **Provento antigo vem por lote de mil** (`quotedPerShares` = 1000): o valor por ação é o valor dividido
- **Parcela não é duplicata.** A Cemig paga o mesmo JCP em duas datas, com o mesmo valor: as duas linhas
  entram
- **A busca de proventos é pelo nome de pregão, exato**, e a B3 grafa o mesmo emissor de dois jeitos
  ("AMBEV S/A" no cadastro, "AMBEV SA" nos proventos): tentam-se as variantes
- **Parcela de provento:** o histórico da B3 não traz data de pagamento e repete a linha a cada
  parcela; a lista recente traz uma data por parcela. As duas se casam pela ordem da data, uma a uma, e
  a parcela que só a lista recente mostra entra como `b3_recente` (desde 2026-10-18; antes, todas as
  parcelas ficavam com a última data, e a de FII com o mesmo valor era barrada como repetida)
- **O fator do evento:** desdobramento e bonificação dão o percentual de ações a mais (100 = 1 para 2);
  grupamento dá o multiplicador (0,1 = 10 para 1)
- **Evento é conferido pelo preço** antes de ajustar: a razão entre o fechamento até a data-com e a
  abertura seguinte, com o preço por ação (dividido pelo fator de cotação), tem de bater com o
  multiplicador na medida do tamanho dele ([ADR-026](../decisoes/ADR-026-confirmacao-do-evento-pelo-tamanho.md)):
  evento grande confirma a até metade da distância, em log, entre o fator e 1; evento de até 25% vale
  pela publicação, a menos que o preço o desminta por mais de 25%. Eventos do mesmo dia se combinam — o Bradesco fez ×50 e ×0,02 em 2009.
  Em 24 empresas, 36 de 40 bateram; os 4 restantes eram o Itaú de 2011 (a B3 lista só o grupamento de
  um grupamento seguido de desdobramento), a Renner de 2005 e um papel que ficou 866 dias sem negociar

| Status | Ajusta? |
|---|---|
| `confirmado` | Sim |
| `sem_preco` — sem pregão em volta para conferir | Sim |
| `divergente` — o preço desmente | Não; vai para a quarentena |
| `nao_ajusta` — cisão, resgate | Não |

**`mercado.serie_papel`** (visão materializada, recalculada no fim de cada rodada): por papel e dia, o
fechamento por ação, o fator de ajuste, o fechamento ajustado, o provento na data ex (o primeiro pregão
depois da data-com, na escala do preço ajustado) e o retorno total do dia. Nos dias com duas cotações
para o mesmo papel, fica a de maior volume.

**A lista de eventos da B3 não é completa.** A Méliuz (CASH3, set/2021), o Banco Inter (BIDI4, mai/2021),
a Kepler Weber (KEPL3, mai/2022) e a Gafisa (GFSA3, set/2022) desdobraram ou grupuram sem o evento
aparecer — o preço salta 82%, 67%, 66% e 849% num dia. A série **não inventa o evento**: a coluna
`salto_sem_evento` marca a variação acima de 50%, ou com a razão de preço a até 10% de um fator comum (2, 3, 4, 5, 6, 8, 10, 20, 25, 50, 100, 200, 1000 ou o inverso), quando nenhum evento **que ajustou a série** — da mesma classe, confirmado ou inferido — está no intervalo; evento recusado pelo preço não esconde o salto (desde 2026-10-18, migração 0021), e `dias_desde_anterior`
expõe o retorno que atravessa meses sem pregão. Em 2026-10-10: 1.907 dias marcados, 110 deles em papéis
com volume acima de R$ 10 milhões desde 2010 — e parte desses é movimento real (Americanas, jan/2023).

**Evento inferido** (`mercado.evento_inferido`). Um salto sem evento vira evento só com três evidências:

1. a razão de preço (fechamento anterior ÷ abertura) a até 10% de um fator comum — 2, 3, 4, 5, 6, 8, 10,
   20, 25, 50, 100, 200, 1000 ou o inverso;
2. a razão do número de ações (`mercado.composicao_capital`, do trimestre anterior para o seguinte) a
   até 10% **do mesmo fator**;
3. um documento no IPE da CVM (`mercado.ipe_documento`) que fale em desdobramento ou bonificação (ou
   grupamento, no sentido oposto) entre 120 dias antes e 10 dias depois.

Kepler (3 para 1) e Méliuz (6 para 1) passam. A Gafisa de 2022 não: o grupamento foi de 10 para 1, mas veio
junto com aumento de capital, e preço e ações apontam para 1/8 e 1/9 — fica marcada, e não ajustada errado.
Os fatores 7, 9 e 12 ficam fora da lista por isso. Na primeira rodada, em 2026-10-10, 21 eventos foram
inferidos — Banco Inter (1 para 3), Méliuz (1 para 6), Kepler (1 para 3), Oi e PDG (grupamentos) entre eles —, e os
papéis líquidos com salto marcado desde 2010 caíram de 110 para 104: o resto é, em boa parte, movimento real. O inferido cede a vez ao evento da B3 a até 10 dias,
para não ajustar duas vezes.

**O FRE como segunda fonte de ações** (desde 2026-10-18). A composição do capital só existe de 2020 em
diante, e o IPE, de 2015. O histórico do capital integralizado no FRE (`mercado.capital_social`, de 2010
em diante) dá a quantidade de ações depois de cada aprovação, e entra quando a composição falta:

- **Antes de 2015**, sem IPE, bastam o preço e o FRE: a mudança aprovada entre 200 dias antes e 30
  depois do salto, a até 10% do mesmo fator comum — ou, se o FRE for exato a 1%, **qualquer fator
  inteiro**, como o 7 para 1 da ECOM3. Um FRE exato não tem a ambiguidade da Gafisa.
- **De 2015 em diante**, o documento no IPE continua obrigatório, e o FRE só corrobora: até 15% do
  fator e até 120 dias depois — a emissão junto do desdobramento e o registro tardio da aprovação
  cabem (MGLU3 em 2017, ×8,81; em 2019, registrado 98 dias depois).

Medido antes de aplicar: 41 eventos novos, entre eles MGLU3 (2015, 2017 e 2019), WEGE3 (2015), CIEL3
(2014), PRIO3 (2019), RADL3 (2010), COGN3 (2013), RIAA3, AZEV3 e ECOM3. Ficam de fora o que não tem prova
na CVM — antes de 2010 (Gerdau e Bradesco de 2005 a 2008) — e a bonificação pequena, que o FRE mostra
mas sem a data-com.

**FII pelas cotas do informe** (desde 2026-10-18). Fundo não entrega documento ao IPE, e o FRE é de
companhia. A segunda prova é a quantidade de cotas emitidas no informe mensal da CVM
(`mercado.fii_mensal`), do mês anterior à data-com para o mês do salto, com até três meses entre os
dois informes: preço e cotas no mesmo fator comum a 10%, ou qualquer fator inteiro com as cotas
exatas a 1%. A `serie_fundo` lê o evento inferido pelo CNPJ do fundo no informe. Medido antes: 19
eventos — a maioria 10 para 1 com as cotas exatas (HGBS11, RBRF11, MCHY11, SADI11), mais BCFF11 (8),
NCHB11 (9) e RBFF11 (5). De 481 saltos marcados em FII, 237 não têm informe dos dois lados — antes
de 2016, ou fundo sem informe —, e ficam marcados.

A composição do capital vem dos arquivos de DFP e ITR já guardados; o número de ações tem unidade
inconsistente entre empresas (a Gafisa declara em milhares), o que não afeta a razão, mas afeta qualquer
uso absoluto.

**Fundos e BDRs** (espécie `CI` ou `DR*`, qualquer que seja o BDI: até out/2022 o BDR era BDI 02) entram pela
**`mercado.serie_fundo`**, com a mesma regra, por código do emissor no ISIN e classe da cota. A B3 dá
os eventos de cota completos, mas o histórico de proventos só de companhia: de fundo e BDR, só os
recentes — cerca de 12 meses antes da primeira coleta, em out/2026. Esses se **acumulam** a cada coleta (`provento.origem = 'b3_recente'`) e nunca são
apagados; o histórico de companhia (`b3_historico`) substitui tudo o que veio da B3 para o emissor.
Entram os fundos e BDRs negociados nos últimos dois anos.

**O rendimento e a amortização de FII de nov/2016 em diante vêm dos avisos do FundosNet**, o sistema da
B3 em que o administrador publica o aviso aos cotistas (`origem = 'fundosnet'`): valor por cota, data-base
como data-com e data de pagamento. Só conta o aviso ativo — a versão substituída e o aviso cancelado têm
os proventos apagados a cada rodada. O que a B3 já deu entre os recentes, com valor a até 1%, fica com
a B3; aviso repetido do mesmo fundo, dia, tipo e valor conta uma vez. A cota cujo ISIN nunca negociou
fica de fora.

**O rendimento de FII sem aviso nem B3 é estimado** pelo informe mensal da CVM (2016 em diante): o
yield do mês vezes o valor patrimonial da cota, com data-com no último dia do mês de referência
(`origem = 'cvm_estimado'`). Conferido em 2024: HGLG11 e KNRI11 batem no centavo; MXRF11 erra até 10%
num mês. No mês em que a B3 ou o FundosNet deram o pago, o estimado sai da série; `provento_estimado` marca o dia que
usou estimativa.

**Limites declarados:**

- **Rendimento antigo de ETF, Fiagro e BDR não existe na base**, nem o de FII antes de nov/2016. O que
  é anterior aos recentes trazidos pela primeira coleta (out/2026) só entra se vier de outra fonte
- **Data de pagamento só nos proventos recentes e nos de FII.** O histórico da B3 não a traz; os
  recentes trazem (`provento.data_pagamento`), e ela preenche também a linha do histórico de mesmo valor
  e data-com. Os recentes cobrem cerca de 12 meses antes da primeira coleta (out/2026): antes de
  out/2025, o provento de companhia, ETF e BDR fica sem data de pagamento; o de FII a tem pelo aviso
- **Provento bruto.** O JCP tem imposto retido na fonte, e o retorno total não o desconta
- **Cisão e redução de capital não ajustam** (Itaú/XP em 2021): o preço cai sem que a série saiba por quê
- **Emissor que a B3 não encontra fica sem proventos** — a ALL, incorporada pela Rumo em 2015

## O que o app lê

O app lê a base **pela API de dados**, nunca pelo banco: `backend/app/collectors/mercado.py` busca
`/v1/ativos`, `/v1/retratos` (que entrega `ativo_hoje` e as demonstrações), cotações e proventos — sem
a origem `cvm_estimado`, que a API só entrega a pedido —, e `collectors/juro_real.py` busca o Tesouro
IPCA+ mais longo em `/v1/tesouro`, para a taxa de ação. CDI, Selic e IPCA o backend lê direto no BCB
(`collectors/rates.py`). Os índices (P/L, P/VP, ROE, yield) seguem regra do backend; a base entrega
só números brutos.

**Decidido:** ativo que a base não tem — não negociou nos últimos 30 dias, é Fiagro, ou nunca entrou —
**o app não mostra**: o coletor não devolve snapshot, e não há fonte de reserva. A cotação é a do
último fechamento, com a idade carimbada; o Ibovespa é medido pelo BOVA11, porque a base não tem o
índice.
