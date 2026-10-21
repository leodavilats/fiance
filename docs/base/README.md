# Base de mercado — `data-job`

**Fonte de verdade** do que o `data-job/` coleta e do que entrega no schema `mercado`. Como cada dado
é tratado está em [tratamento](tratamento.md); o porquê, na
[ADR-022](../decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md); o estado, no
[03-ESTADO](../03-ESTADO.md#base-de-mercado).
Última revisão: 2026-10-21

O data-job coleta dados de mercado de fontes oficiais, guarda o arquivo como veio e grava a versão
interpretada no schema `mercado` do Postgres. É a infraestrutura comum da plataforma, e tem dois
leitores diretos:

- **`fiance-dados/`** — a API de dados ([dados/](../dados/README.md)), que serve terceiros e o
  próprio app. O backend do app não abre este banco: lê pela API
- **`fiance-trend/`** — o laboratório ([pesquisa/](../pesquisa/README.md)), que precisa de histórico
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

Os da [ADR-022](../decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md), aplicados:

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

**Variáveis.**

Obrigatórias, sem default: ausente, o job falha ao começar (`datajob/config.py`).

| Variável | Para quê |
|---|---|
| `DATABASE_URL` | O `postgres-mercado`, com permissão de escrita no schema `mercado` |
| `DATAJOB_BRUTO_DIR` | Onde guardar os arquivos brutos. Em produção, `/bruto` |

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
([ADR-024](../decisoes/ADR-024-api-de-dados.md)).

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
| `indicador` | `(serie, data)` | Séries do BCB SGS de 2005 em diante: CDI diário (12), Selic diária (11), meta da Selic (432), IPCA mensal (433), dólar PTAX de venda (1); Selic mensal anualizada (4189) desde 2000, para a Selic média de 10 anos — o app lê a mesma série direto no BCB |
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

## Fora do data-job

- A API que serve esta base: [dados/](../dados/README.md)
- O laboratório e o painel, que leem esta base direto: [pesquisa/](../pesquisa/README.md)
- Cotação ao longo do pregão: nenhuma fonte gratuita oficial entrega

