# Plano — data-job

**Estado:** fase 1 `[IMPLEMENTADO]` — COTAHIST, cadastro, FCA, emissores, DFP, ITR, BCB SGS, papel de leitura e visões de fundamento. Fase 2 `[PLANEJADO]` · **Decisão:** [ADR-022](../decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)
(`PROPOSTO`) · **Escrito em:** 2026-10-09

O data-job coleta dados de mercado de fontes oficiais, guarda o arquivo como veio e grava a versão
interpretada no schema `mercado` do Postgres. Ele é a base de dois consumidores:

- **`backend/`** — o aplicativo, que hoje busca na BRAPI sob demanda
- **a pesquisa de carteira** — uso próprio do autor, em horizonte de meses, que precisa de histórico
  longo, empresas que saíram da bolsa e fundamento como se sabia na data

O que já existe está marcado em [08-ESTADO](../08-ESTADO.md); o resto deste plano ainda não.

---

## Fontes conferidas

Baixadas e abertas em 2026-10-09.

| Fonte | Endereço | Formato | O que se viu |
|---|---|---|---|
| **B3 COTAHIST** | `https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_{A2025 \| M092026 \| D08102026}.ZIP` | Texto de largura fixa, 245 posições, Latin-1 | O diário de 08/10/2026 tem 17.546 linhas — inclui opções, termo e fracionário — e saiu com carimbo 20:42. Cada linha traz o ISIN (`BRPETRACNPR6`), o código BDI e o tipo de mercado |
| **CVM DFP** | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/ | ZIP anual de CSVs `;`, Latin-1 | O de 2025 tem 12,8 MB e 19 arquivos (284 MB descompactado). O índice traz `VERSAO` e `DT_RECEB`; as demonstrações trazem `CD_CONTA`, `VL_CONTA`, `ESCALA_MOEDA` (`MIL`) e `ORDEM_EXERC` (`ÚLTIMO`, `PENÚLTIMO`) |
| **CVM ITR** | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/ | O mesmo da DFP, por trimestre | — |
| **CVM FCA** | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/ | ZIP anual | `valor_mobiliario` liga CNPJ a `Codigo_Negociacao`, com início e fim de negociação |
| **CVM informe mensal de FII** | https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/ | ZIP anual, 2016 → 2026 | — |
| **BCB SGS** | já usado em `backend/app/collectors/rates.py` | JSON | — |

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
      b3_cotahist.py      # feito: interpretar, validar, gravar
      cvm_*.py, bcb_sgs.py  # a fazer
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

O papel `mercado_leitura` (sem login) lê todo o schema, inclusive tabelas futuras, e não escreve. Quem
consome ganha um usuário próprio dentro dele, criado à mão quando existir:

```sql
CREATE ROLE <nome> LOGIN PASSWORD '<senha>' IN ROLE mercado_leitura;
```

A senha vai para uma variável do serviço consumidor no Railway, e não para o repositório.

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

## Schema `mercado` — fase 1

As colunas finais são as das migrações. O que importa decidir agora é a chave e o que cada tabela
guarda.

| Tabela | Chave | Guarda |
|---|---|---|
| `empresa` | `cnpj` | Cadastro da CVM: código CVM, razão social, setor, situação, registro e cancelamento — inclui as canceladas |
| `valor_mobiliario` | `(cnpj, data_referencia, versao, tipo, classe, codigo)` | FCA de 2010 em diante: o que cada empresa declara negociar, com o ticker quando preenchido |
| `emissor_b3` | `codigo` | Lista de emissores listados na B3, com CNPJ e código CVM |
| `emissor` | `codigo` | Derivada: o código de emissor do ISIN (`BRPETRACNPR6` → `PETR`) ligado a um CNPJ, e o método |
| `ativo` | `isin` | Nome resumido, espécie, código BDI, primeiro e último pregão. A fazer: classe (ação, FII, ETF, BDR) |
| `ticker` | `(codigo, isin)` | Primeiro e último pregão. Um código reaproveitado por outro ISIN é outra linha |
| `cotacao` | `(isin, data)` | Abertura, máxima, mínima, fechamento, média, negócios, quantidade, volume, fator de cotação — tudo bruto, `NUMERIC` |
| `documento` | `id`; único em `(cnpj, tipo, data_referencia, versao)` | Tipo (DFP, ITR), data de entrega, id CVM — todas as versões do índice |
| `demonstracao_linha` | `(documento_id, demonstracao, inicio_exercicio, fim_exercicio, conta)` | Descrição, valor em reais (a escala já aplicada), consolidado ou individual, conta fixa. No balanço, início = fim |
| `indicador` | `(serie, data)` | Séries do BCB SGS de 2005 em diante: CDI diário (12), Selic diária (11), meta da Selic (432), IPCA mensal (433) |
| `coleta` | `id` | Fonte, arquivo, hash, início, fim, linhas lidas, gravadas, em quarentena, status, erro |
| `quarentena` | `id` | Coleta, chave da linha, motivo, conteúdo bruto |

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
python -m datajob cvm --doc dfp --ano 2025
python -m datajob cvm --doc fca --ano 2026
python -m datajob bcb
python -m datajob diario                         # o que o cron roda
python -m datajob backfill --desde 2005          # carga histórica, local, uma vez
python -m datajob reprocessar --fonte cotahist   # do bruto guardado, sem baixar
```

## Execução

| O quê | Quando | Onde |
|---|---|---|
| Carga histórica | Uma vez | Local, gravando no banco de produção pela URL |
| COTAHIST do dia | 23h de Brasília, terça a sábado em UTC — o arquivo de 08/10 saiu às 20:42 | Cron no Railway, `diario` |
| CVM (DFP, ITR, FCA, cadastro) | Diário; o hash pula o que não mudou | Cron no Railway |
| BCB SGS | Diário | Cron no Railway |

O calendário de pregão já existe em `backend/app/core/pregao.py`; o data-job leva uma cópia até haver
pacote compartilhado. Datas e horários seguem o fuso brasileiro, como em `backend/app/core/brt.py`.

---

## Fases

### Fase 1 — a base

COTAHIST de 2005 em diante, cadastro e FCA, DFP e ITR de 2010 em diante, BCB SGS.

**Pronto quando:**

- A série da PETR4 de 2005 a hoje bate, em 5 datas sorteadas, com o fechamento publicado pela B3
- Uma empresa que saiu da bolsa tem cotação até a saída
- Uma troca de ticker (`VVAR3` → `VIIA3` → `BHIA3`) aparece como **um** ativo
- Lucro líquido e patrimônio da PETR4 em 2024 batem com a DFP publicada
- Rodar o `diario` duas vezes seguidas não muda nenhuma linha
- O volume de `demonstracao_linha` está medido, e cabe no plano do banco
- `ruff` e `pytest` no CI, como os do backend

### Visões de fundamento — feitas em 2026-10-10

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
O lucro de 12 meses é conta da pesquisa: acumulado do ano + último anual − acumulado do mesmo ponto
do ano anterior.

### Ligação do ativo à empresa — feita em 2026-10-10

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

### Fase 2 — eventos e proventos

Fator de ajuste por desdobramento, grupamento e bonificação; dividendos e JCP com data-com e
pagamento; rendimento de FII pelo informe mensal da CVM.

**A decisão aberta é a fonte de ações.** Dois candidatos, a comparar com 20 empresas antes de
escolher:

- Os endpoints JSON do site da B3 por empresa — gratuitos, não documentados, podem mudar sem aviso
- O plano gratuito da BRAPI, só para esta peça

**Pronto quando** o retorno total de 5 ações num ano bate com uma fonte de referência dentro de uma
tolerância declarada.

### Fase 3 — o backend lê de `mercado`

`backend/app/collectors/universal.py` passa a montar o `AssetSnapshot` do banco, e a BRAPI sai do
caminho de leitura. Exige a ADR-022 `ACEITO` e muda os documentos que ela lista. Ativo que alguém
procura e o data-job não tem continua precisando de resposta — a decisão sobre isso é desta fase.

---

## Fora deste plano

- A pesquisa de carteira em si (motor de *backtest*, protocolo de prova lacrada): plano próprio,
  depois da fase 1
- `trend-frontend`: só quando houver estratégia para acompanhar
- Cotação ao longo do pregão: nenhuma fonte gratuita oficial entrega

## Perguntas abertas

- O bucket do Railway atende o volume do bruto, ou o diretório local basta enquanto só o autor usa?
- A pesquisa e o aplicativo no mesmo Postgres pesam um no outro? A fase 1 mede antes de separar.
