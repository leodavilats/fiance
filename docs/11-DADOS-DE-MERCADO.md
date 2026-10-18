# Dados de mercado — o data-job

**Fonte de verdade** do que o `data-job/` coleta, como trata cada dado e o que entrega no schema
`mercado`. O porquê está na [ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md); o
estado de cada parte, no [08-ESTADO](08-ESTADO.md).
Última revisão: 2026-10-12

O data-job coleta dados de mercado de fontes oficiais, guarda o arquivo como veio e grava a versão
interpretada no schema `mercado` do Postgres. Ele é a base de três consumidores:

- **`backend/`** — o aplicativo, que lê a base pela conexão do Railway com `SET ROLE mercado_leitura`
- **`fiance-dados/`** — a base como serviço, com contas e chaves ([ADR-024](decisoes/ADR-024-api-de-dados.md))
- **a pesquisa de carteira** — uso próprio do autor, em horizonte de meses, que precisa de histórico
  longo, empresas que saíram da bolsa e fundamento como se sabia na data

---

## Fontes conferidas

As primeiras, baixadas e abertas em 2026-10-09; as demais, quando entraram na coleta.

| Fonte | Endereço | Formato | O que se viu |
|---|---|---|---|
| **B3 COTAHIST** | `https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_{A2025 \| M092026 \| D08102026}.ZIP` | Texto de largura fixa, 245 posições, Latin-1 | O diário de 08/10/2026 tem 17.546 linhas — inclui opções, termo e fracionário — e saiu com carimbo 20:42. Cada linha traz o ISIN (`BRPETRACNPR6`), o código BDI e o tipo de mercado |
| **CVM DFP** | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/ | ZIP anual de CSVs `;`, Latin-1 | O de 2025 tem 12,8 MB e 19 arquivos (284 MB descompactado). O índice traz `VERSAO` e `DT_RECEB`; as demonstrações trazem `CD_CONTA`, `VL_CONTA`, `ESCALA_MOEDA` (`MIL`) e `ORDEM_EXERC` (`ÚLTIMO`, `PENÚLTIMO`) |
| **CVM ITR** | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/ | O mesmo da DFP, por trimestre | — |
| **CVM FCA** | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/ | ZIP anual | `valor_mobiliario` liga CNPJ a `Codigo_Negociacao`, com início e fim de negociação |
| **CVM informe mensal de FII** | https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/ | ZIP anual, 2016 → 2026 | Segmento, mandato, valor patrimonial da cota, cotas emitidas e yield do mês |
| **CVM FRE** | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/ | ZIP anual, 2010 em diante | Capital social: quantidade de ações integralizadas, em unidades, na data de aprovação |
| **CVM IPE** | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ | ZIP anual, 2005 em diante | Índice de fatos relevantes, comunicados e atas, com categoria e assunto |
| **CVM cadastro** | https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv | CSV | Companhias abertas, inclusive canceladas |
| **BCB SGS** | `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados`, por `datajob/fontes/bcb_sgs.py` | JSON, em janelas de até 10 anos | — |
| **Tesouro Transparente** | `PrecoTaxaTesouroDireto.csv`, nos dados abertos do Tesouro | CSV | Taxas e preços de cada título do Tesouro Direto, 2005 em diante |
| **B3 — emissores** | `sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies` | JSON, não documentado | Emissores listados hoje, com CNPJ |
| **B3 — proventos e eventos** | o mesmo proxy, `GetListedCashDividends` e `GetListedSupplementCompany` | JSON, não documentado | Proventos em dinheiro e eventos em ações por emissor |

**Duas descobertas que mudam o desenho:**

1. **A CVM guarda só os números da última versão.** No índice da DFP de 2025, 75 companhias têm mais
   de uma versão, mas nenhuma tem mais de uma versão na DRE consolidada. O valor original de um
   balanço reapresentado não existe no arquivo. No histórico, o fundamento entra com a data de entrega
   da **primeira** versão e os números da **última** — uma aproximação, declarada. Do primeiro download
   em diante, o bruto guardado preserva cada versão.
2. **O plano de contas muda com o tipo de empresa.** Em banco, a conta `3.01` é *Receitas de
   Intermediação Financeira*. Por isso o data-job grava as linhas como a CVM publica, e o mapeamento
   para lucro, patrimônio e receita é uma camada separada, testada por tipo de empresa.

---

## Princípios

Os da [ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md), aplicados:

| Princípio | Como fica |
|---|---|
| Bruto antes de interpretar | Todo arquivo vai para o armazenamento com o hash no nome antes do parser |
| Rodar duas vezes dá o mesmo resultado | `INSERT … ON CONFLICT` pela chave natural; hash conhecido é pulado |
| Fundamento nunca sobrescrito | Chave inclui `versao`; a versão nova é linha nova |
| Preço bruto e evento separados | `cotacao` é como a B3 publicou; `evento` guarda o fator; o ajustado é *view* |
| Identidade estável | `ativo` pelo ISIN; `ticker` com vigência; `empresa` pelo CNPJ |
| Quarentena | Linha implausível vai para `quarentena` com fonte, chave e motivo |
| Registro | Toda execução é uma linha de `coleta`, aberta no início e fechada no fim |
| Falha não apaga | Cada arquivo grava numa transação; erro desfaz o arquivo, não a base |

---

## Estrutura

```
data-job/
  pyproject.toml          # ruff e pytest, mesma configuração do backend
  requirements.txt
  alembic.ini
  migrations/             # tabela de versão dentro do schema mercado
  datajob/
    __main__.py           # CLI
    config.py             # DATABASE_URL e DATAJOB_BRUTO_DIR, sem default
    armazenamento.py      # bruto em diretório; o bucket do Railway entra aqui
    coleta.py             # registro da execução, pulo por hash, transação por arquivo
    esquema.py            # tabelas de mercado
    fontes/
      b3_cotahist.py      # cotações
      b3_emissores.py     # emissores listados
      b3_proventos.py     # proventos e eventos
      bcb_sgs.py          # séries do BCB
      cvm_cadastro.py     # companhias abertas
      cvm_fca.py          # valor mobiliário e ticker declarado
      cvm_demonstracoes.py  # DFP e ITR
      cvm_fre.py          # capital social
      cvm_ipe.py          # documentos do IPE
      cvm_fii.py          # informe mensal de FII
      tesouro_direto.py   # Tesouro Direto
      cvm_comum.py        # leitura comum aos arquivos da CVM
  tests/
    fixtures/             # trechos pequenos de arquivos reais
```

A plausibilidade fica em cada fonte, porque a regra depende do arquivo. O data-job não importa o
backend, para não arrastar a configuração dele.

### Produção

Serviço `data-job` no projeto `fiance` do Railway, ambiente `production`:

| Item | Valor |
|---|---|
| Fonte | `main`, diretório `/data-job`, reconstrói só com mudança em `/data-job/**` |
| Banco | `postgres-mercado`, só do data-job — `DATABASE_URL` referencia o id dele |
| Bruto | Volume `data-job-bruto` em `/bruto` |
| Antes de cada deploy | `python -m alembic upgrade head` |
| Execução | `python -m datajob diario`, sem reinício: roda e termina |
| Agenda | `0 2 * * 2-6` (UTC): 23h de Brasília, depois de cada pregão de segunda a sexta |

**Para rodar fora da agenda:** tirar o cron do serviço e fazer uma implantação **nova**
(`railway up --service data-job`), e depois devolver o cron com outra implantação nova. O *redeploy*
do Railway reaproveita a configuração da implantação anterior, cron incluído: com ele, o container
fica em `created` esperando o horário, e nada roda.

O `diario` busca o que falta desde o último pregão gravado: os anuais de 2005 em diante com o banco
vazio, o anual do ano quando a lacuna passa de dez dias, e os diários no resto. O arquivo que a B3
ainda não publicou responde 404 e fica para a rodada seguinte.

### Leitura

O papel `mercado_leitura` (sem login) lê todo o schema, inclusive tabelas futuras, e não escreve. A
`fiance-dados` e o painel `fiance-trend` usam a conexão que o Railway dá ao `postgres-mercado` e, a cada
conexão aberta, assumem o papel com `SET ROLE mercado_leitura` e transação só de leitura. **Não há
usuário próprio nem senha nova.** O backend do app não lê o banco: lê pela `fiance-dados`
([ADR-024](decisoes/ADR-024-api-de-dados.md)).

### Como rodar

```bash
cd data-job
export DATABASE_URL=postgresql://...  DATAJOB_BRUTO_DIR=/caminho/do/bruto
python -m alembic upgrade head
python -m datajob cotahist --ano 2025
```

Os testes de gravação rodam contra um Postgres descartável, indicado em `DATAJOB_TEST_DATABASE_URL`;
eles **apagam o schema `mercado`** desse banco a cada teste. No CI é um serviço do job *Data-job*.

### Medido em 2026-10-09

- O ano de 2025 inteiro tem 3.174.698 registros, dos quais 335.874 do mercado à vista. Entrou em 1min30s
  num Postgres local, e regravar a partir do bruto não baixa nada
- 20 anos de cotação à vista devem ficar na casa de 6 a 7 milhões de linhas
- **A B3 publica preço médio fora da faixa do dia.** Na BMKS3, em 08/10/2026, abertura, máxima,
  mínima e fechamento são 376,02 e a média é 380,78. A média não é conferida contra a faixa;
  abertura e fechamento são
- **O registro final muda de convenção.** Os anuais de 2005 e 2015 declaram o total de linhas, com
  cabeçalho e final; o de 2025 e o diário de 2026 declaram só as cotações. As duas são aceitas, e
  qualquer outra diferença recusa o arquivo
- **Os 22 anuais, de 2005 a 2026, passam pela interpretação**, com 3,4 milhões de cotações à vista no
  total. A quarentena tem 351 linhas em 2005 — tickers com sufixo `B`, do balcão organizado, cujo
  último preço não respeita a faixa do dia — e de 0 a 13 nos demais anos
- **Até meados dos anos 2000 há cotação por lote de mil** (`fator_cotacao` 1000 e 100000). O preço
  por ação é o preço dividido pelo fator, e o fator fica gravado por isso
- **A B3 recusa (403) o User-Agent padrão do `urllib`**; o do `httpx` passa

---

## Schema `mercado`

As colunas finais são as das migrações. O que importa decidir agora é a chave e o que cada tabela
guarda.

| Tabela | Chave | Guarda |
|---|---|---|
| `empresa` | `cnpj` | Cadastro da CVM: código CVM, razão social, setor, situação, registro e cancelamento — inclui as canceladas |
| `valor_mobiliario` | `(cnpj, data_referencia, versao, tipo, classe, codigo)` | FCA de 2010 em diante: o que cada empresa declara negociar, com o ticker quando preenchido |
| `emissor_b3` | `codigo` | Lista de emissores listados na B3, com CNPJ e código CVM |
| `emissor` | `codigo` | Derivada: o código de emissor do ISIN (`BRPETRACNPR6` → `PETR`) ligado a um CNPJ, e o método |
| `ativo` | `isin` | Nome resumido, espécie, código BDI, primeiro e último pregão. A classe (ação, FII, ETF, BDR) não é coluna: sai da espécie e do BDI em `ativo_hoje` |
| `ticker` | `(codigo, isin)` | Primeiro e último pregão. Um código reaproveitado por outro ISIN é outra linha |
| `cotacao` | `(isin, data)` | Abertura, máxima, mínima, fechamento, média, negócios, quantidade, volume, fator de cotação — tudo bruto, `NUMERIC` |
| `documento` | `id`; único em `(cnpj, tipo, data_referencia, versao)` | Tipo (DFP, ITR), data de entrega, id CVM — todas as versões do índice |
| `demonstracao_linha` | `(documento_id, demonstracao, inicio_exercicio, fim_exercicio, conta)` | Descrição, valor em reais (a escala já aplicada), consolidado ou individual, conta fixa. No balanço, início = fim |
| `indicador` | `(serie, data)` | Séries do BCB SGS de 2005 em diante: CDI diário (12), Selic diária (11), meta da Selic (432), IPCA mensal (433), dólar PTAX de venda (1); Selic mensal anualizada (4189) desde 2000, para a média de 10 anos que o app usa como juro |
| `tesouro` | `(titulo, vencimento, data)` | Taxas e preços unitários de compra e venda do Tesouro Direto de 2005 em diante, do Tesouro Transparente. Título fora de venda fica sem taxa e preço de compra |
| `coleta` | `id` | Fonte, arquivo, hash, início, fim, linhas lidas, gravadas, em quarentena, status, erro |
| `rodada` | `id` | Cada execução do data-job: início, fim e as etapas que falharam, com o erro. O painel `fiance-trend` alerta a partir dela |
| `fii_mensal` | `(emissor, classe, referencia)` | Informe mensal de FII da CVM, 2016 em diante: CNPJ, nome, segmento, mandato, valor patrimonial da cota, patrimônio, cotas emitidas e yield do mês — a base do P/VP |
| `quarentena` | `id` | Coleta, chave da linha, motivo, conteúdo bruto |
| `provento` | `id` | Por emissor e classe: data-com, tipo, valor por ação, aprovação, `origem` (`b3_historico`, `b3_recente`, `cvm_estimado`) e `data_pagamento`, quando a fonte dá |
| `evento` | `id` | Desdobramento, grupamento e bonificação da B3: ISIN, data-com, fator, multiplicador, status da conferência pelo preço e razão observada |
| `evento_inferido` | `(cnpj, classe, data_com)` | Salto sem evento que virou evento: multiplicador, razão observada e o documento do IPE que o sustenta |
| `ipe_documento` | `(protocolo, versao)` | Índice do IPE da CVM: CNPJ, entrega, referência, categoria, tipo, espécie, assunto, link |
| `composicao_capital` | `documento_id` | Ações ordinárias, preferenciais, total e em tesouraria, da DFP e do ITR |
| `capital_social` | `(cnpj, data_referencia, versao, data_aprovacao)` | Ações ON, PN e total, do FRE |

**Visões.** `fundamento_resultado` e `fundamento_balanco` (comuns) leem as linhas da demonstração;
`cotacao_papel` costura as cotações por CNPJ e classe. As materializadas são recalculadas no fim de
cada rodada:

| Visão materializada | Chave | Guarda |
|---|---|---|
| `serie_papel` | papel e dia | Ação: fechamento por ação, fator de ajuste, ajustado, provento na data ex, retorno total, saltos marcados |
| `serie_fundo` | emissor, classe e dia | O mesmo para FII, ETF e BDR |
| `ativo_hoje` | `codigo` | O que o app lê: um ticker negociado nos últimos 30 dias por linha, com classe (`stock`, `fii`, `etf`, `bdr`; Fiagro fora), preço do último fechamento e o anterior, faixa de 52 semanas, volume médio, nome, setor ou segmento, CNPJ, ações, valor patrimonial da cota e proventos de 12 meses |
| `fundamento_app` | `(cnpj, tipo, data_referencia, versao)` | O que o app lê de fundamento: receita, lucro dos controladores, patrimônio e dívida bruta do período de cada documento |

**O que entra da CVM:** balanço ativo e passivo (BPA, BPP), resultado (DRE) e fluxo de caixa (DFC,
direto e indireto), da DFP de 2010 em diante e do ITR de 2011 em diante, com três recortes medidos em
2026-10-10:

| Recorte | Linhas (DFP + ITR) |
|---|---|
| Tudo | 35 milhões |
| Só o exercício corrente (`ÚLTIMO`), consolidado | 6,7 milhões |
| Isso, só empresas ligadas a uma ação | 5,1 milhões |

- **Só o exercício corrente.** O `PENÚLTIMO` é o ano anterior reapresentado dentro do documento
  novo: é metade das linhas, e o ano anterior já está no documento dele
- **Consolidado, e individual só quando o documento não tem consolidado**
- **Só empresas em `emissor`.** Quando a ligação melhora, `reprocessar --fonte cvm_dfp` (e `cvm_itr`)
  traz o resto do bruto guardado, sem baixar
- **Linhas repetidas e idênticas viram uma** — CPX Distribuidora e Salta Educação publicam a mesma conta
  duas vezes na DFP de 2024. Repetida com valor diferente vai para a quarentena
- **Moeda sempre real, escala em mil ou unidade**; outra coisa vai para a quarentena
- **Rotina:** com o banco vazio, todos os anos; depois, o ano corrente e o anterior. Reapresentação de
  um ano mais antigo só entra por `reprocessar` ou carga manual do ano

**O que entra do COTAHIST:** só o mercado à vista (`TPMERC = 010`), lote padrão. Fracionário, opções e
termo ficam no bruto e fora da tabela.

---

## CLI

```bash
python -m datajob cotahist --ano 2024            # um ano
python -m datajob cotahist --dia 2026-10-08      # um pregão
python -m datajob cotahist --arquivo COTAHIST_A2024.ZIP   # ZIP já baixado
python -m datajob diario                         # o que o cron roda; com o banco vazio, carrega tudo
python -m datajob reprocessar --fonte cvm_dfp    # do bruto guardado, sem baixar
```

`reprocessar` aceita qualquer fonte: `b3_cotahist`, `b3_emissores`, `b3_proventos`, `cvm_cadastro`,
`cvm_fca`, `cvm_dfp`, `cvm_itr`, `cvm_fre`, `cvm_ipe`, `cvm_fii`, `tesouro_direto`. Não há comando
de carga histórica: o `diario` com o banco vazio busca cada fonte desde o primeiro ano dela.

## Execução

Tudo roda no `diario`, uma etapa depois da outra. A etapa que falha fica registrada na `rodada` e não
impede as seguintes. Cron no Railway, 23h de Brasília, depois de cada pregão.

| Etapa | Quando | O que busca |
|---|---|---|
| Cotações da B3 | Toda rodada | O que falta desde o último pregão — o arquivo de 08/10 saiu às 20:42 |
| Cadastro, FCA, emissores da B3 e ligação emissor–CNPJ | Toda rodada | FCA do ano corrente e do anterior; o hash pula o que não mudou |
| DFP e ITR | Toda rodada | Ano corrente e anterior |
| Séries do BCB | Toda rodada | Desde a última data gravada de cada série |
| Tesouro Direto | Toda rodada | O arquivo inteiro do Tesouro Transparente |
| Proventos e eventos da B3 | **Às sextas** (e na primeira carga) | Por emissor: companhias com histórico; fundos e BDRs negociados nos últimos dois anos, só os recentes |
| Informe de FII da CVM | Toda rodada | Ano corrente e anterior |
| IPE e FRE da CVM | Toda rodada | Ano corrente e anterior |
| Composição do capital | Só com a tabela vazia | Do bruto de DFP e ITR já guardado |
| Recálculo das visões | Fim de toda rodada | `serie_papel`, `serie_fundo`, `ativo_hoje` e `fundamento_app`; depois a inferência de eventos, e as visões de novo se algum foi inferido |

O calendário de pregão já existe em `backend/app/core/pregao.py`; o data-job leva uma cópia até haver
pacote compartilhado. Datas e horários seguem o fuso brasileiro, como em `backend/app/core/brt.py`.

---

## Como cada dado é tratado

### A base, e como foi aceita na carga inicial

COTAHIST de 2005 em diante, cadastro e FCA, DFP e ITR de 2010 em diante, BCB SGS.

**Conferido na carga inicial (2026-10-09):**

- A série da PETR4 de 2005 a hoje bate, em 5 datas sorteadas, com o fechamento publicado pela B3
- Uma empresa que saiu da bolsa tem cotação até a saída
- Uma troca de ticker (`VVAR3` → `VIIA3` → `BHIA3`) aparece como **um** ativo
- Lucro líquido e patrimônio da PETR4 em 2024 batem com a DFP publicada
- Rodar o `diario` duas vezes seguidas não muda nenhuma linha
- O volume de `demonstracao_linha` está medido, e cabe no plano do banco
- `ruff` e `pytest` no CI, como os do backend

### Visões de fundamento

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

### Série contínua de um papel — `mercado.cotacao_papel`

A troca de ticker cria ISIN novo: VVAR3, VIIA3 e BHIA3 são três ISINs da mesma empresa. A visão costura
as cotações por **CNPJ e classe da ação** (ON, PN, PNA, PNB…, UNT), e só com código BDI de ação —
recibo e direito de subscrição (ITSA9, BBDC10) têm espécie ON ou PN e ficam de fora. Em produção: 841
papéis de 543 empresas; a Casas Bahia sai contínua de 2012 a hoje.

**Restam algumas centenas de dias com duas cotações para o mesmo papel**, de tickers especiais
negociados como lote padrão (AZUL97–99, BEES11, JBDU11/12, BPAC13). Nesses dias, a pesquisa fica com
a de maior volume.

O preço é o **bruto**. Desdobramento, grupamento e provento entram na série ajustada
(`mercado.serie_papel`).

### Ligação do ativo à empresa

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

### Eventos e proventos

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
- **O fator do evento:** desdobramento e bonificação dão o percentual de ações a mais (100 = 1 para 2);
  grupamento dá o multiplicador (0,1 = 10 para 1)
- **Evento é conferido pelo preço** antes de ajustar: a razão entre o fechamento até a data-com e a
  abertura seguinte, com o preço por ação (dividido pelo fator de cotação), tem de bater com o
  multiplicador em 12%. Eventos do mesmo dia se combinam — o Bradesco fez ×50 e ×0,02 em 2009.
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

A composição do capital vem dos arquivos de DFP e ITR já guardados; o número de ações tem unidade
inconsistente entre empresas (a Gafisa declara em milhares), o que não afeta a razão, mas afeta qualquer
uso absoluto.

**Fundos e BDRs** (espécie `CI` ou `DR*`, qualquer que seja o BDI: até out/2022 o BDR era BDI 02) entram pela
**`mercado.serie_fundo`**, com a mesma regra, por código do emissor no ISIN e classe da cota. A B3 dá
os eventos de cota completos, mas o histórico de proventos só de companhia: de fundo e BDR, só os
recentes — cerca de 12 meses antes da primeira coleta, em out/2026. Esses se **acumulam** a cada coleta (`provento.origem = 'b3_recente'`) e nunca são
apagados; o histórico de companhia (`b3_historico`) substitui tudo o que veio da B3 para o emissor.
Entram os fundos e BDRs negociados nos últimos dois anos.

**O rendimento de FII anterior aos recentes da B3 é estimado** pelo informe mensal da CVM (2016 em diante): o
yield do mês vezes o valor patrimonial da cota, com data-com no último dia do mês de referência
(`origem = 'cvm_estimado'`). Conferido em 2024: HGLG11 e KNRI11 batem no centavo; MXRF11 erra até 10%
num mês. No mês em que a B3 deu o pago, o estimado sai da série; `provento_estimado` marca o dia que
usou estimativa.

**Limites declarados:**

- **Rendimento antigo de ETF, Fiagro e BDR não existe na base**, nem o de FII antes de 2016. O que é
  anterior aos recentes trazidos pela primeira coleta (out/2026) só entra se vier de outra fonte
- **Amortização de cota de FII não entra pela CVM**, só pela B3
- **Data de pagamento só nos proventos recentes.** O histórico da B3 não a traz; os recentes trazem
  (`provento.data_pagamento`), e ela preenche também a linha do histórico de mesmo valor e data-com. Os
  recentes cobrem cerca de 12 meses antes da primeira coleta (out/2026): antes de out/2025, o provento
  fica sem data de pagamento
- **Provento bruto.** O JCP tem imposto retido na fonte, e o retorno total não o desconta
- **Cisão e redução de capital não ajustam** (Itaú/XP em 2021): o preço cai sem que a série saiba por quê
- **Emissor que a B3 não encontra fica sem proventos** — a ALL, incorporada pela Rumo em 2015

### O que o app lê

Em 2026-10-12, com a ADR-022 aceita, `backend/app/collectors/universal.py` passou a montar o
`AssetSnapshot` de `mercado.ativo_hoje` e `mercado.fundamento_app` (por `collectors/mercado.py`), e a
BRAPI saiu do código. Histórico de preço e proventos também vêm da base. Desde 2026-10-14, a
leitura passa pela `fiance-dados`. Os índices (P/L, P/VP, ROE,
yield) seguem regra do backend; a visão entrega só números brutos.

**Decidido:** ativo que a base não tem — não negociou nos últimos 30 dias, é Fiagro, ou nunca entrou —
**o app não mostra**: o coletor não devolve snapshot, e não há fonte de reserva. A cotação é a do
último fechamento, com a idade carimbada; o Ibovespa é medido pelo BOVA11, porque a base não tem o
índice.

---

## Fora do data-job

- As pesquisas (motor de *backtest*, protocolos, prova lacrada): [pesquisas](pesquisas/README.md)
- O painel do autor (`fiance-trend/frontend`), que lê esta base: [07-OPERACAO](07-OPERACAO.md)
- Cotação ao longo do pregão: nenhuma fonte gratuita oficial entrega
