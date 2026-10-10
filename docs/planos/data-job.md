# Plano — data-job

**Estado:** `[PLANEJADO]` · **Decisão:** [ADR-022](../decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)
(`PROPOSTO`) · **Escrito em:** 2026-10-09

O data-job coleta dados de mercado de fontes oficiais, guarda o arquivo como veio e grava a versão
interpretada no schema `mercado` do Postgres. Ele é a base de dois consumidores:

- **`backend/`** — o aplicativo, que hoje busca na BRAPI sob demanda
- **a pesquisa de carteira** — uso próprio do autor, em horizonte de meses, que precisa de histórico
  longo, empresas que saíram da bolsa e fundamento como se sabia na data

Nada aqui existe ainda. O que existe está em [08-ESTADO](../08-ESTADO.md).

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
  pyproject.toml          # ruff, pytest — mesmas versões do backend
  requirements.txt
  alembic.ini
  migrations/             # version_table dentro do schema mercado
  datajob/
    __main__.py           # CLI
    config.py             # DATABASE_URL, armazenamento, sem default para ambiente
    armazenamento.py      # bruto: diretório local ou bucket S3 do Railway
    coleta.py             # abre e fecha o registro de execução
    banco.py              # sessão, COPY, upsert
    fontes/
      b3_cotahist.py      # baixar + interpretar
      cvm_cadastro.py
      cvm_fca.py
      cvm_dfp_itr.py
      bcb_sgs.py
    plausibilidade.py
  tests/
    fixtures/             # trechos pequenos de arquivos reais
```

O `backend/app/collectors/plausibility.py` é a referência para as faixas; o data-job não importa o
backend, para não arrastar a configuração dele.

---

## Schema `mercado` — fase 1

As colunas finais são as das migrações. O que importa decidir agora é a chave e o que cada tabela
guarda.

| Tabela | Chave | Guarda |
|---|---|---|
| `empresa` | `cnpj` | Código CVM, razão social, setor, situação, datas de registro e cancelamento |
| `ativo` | `isin` | CNPJ (quando houver), espécie (ON, PN, UNT, CI), classe (ação, FII, ETF, BDR) |
| `ticker` | `(codigo, inicio)` | ISIN, fim de vigência. Vem do COTAHIST e do FCA |
| `cotacao` | `(isin, data)` | Abertura, máxima, mínima, fechamento, média, negócios, quantidade, volume, fator de cotação — tudo bruto, `NUMERIC` |
| `documento` | `(cnpj, tipo, data_referencia, versao)` | Tipo (DFP, ITR), data de entrega, id CVM |
| `demonstracao_linha` | `(documento, demonstracao, ordem_exercicio, conta)` | Descrição, valor já multiplicado pela escala, início e fim do exercício |
| `indicador_serie` | `(serie, data)` | CDI, Selic, IPCA |
| `coleta` | `id` | Fonte, arquivo, hash, início, fim, linhas lidas, gravadas, em quarentena, status, erro |
| `quarentena` | `id` | Coleta, chave da linha, motivo, conteúdo bruto |

**O que entra da CVM na fase 1:** balanço ativo e passivo (BPA, BPP), DRE e fluxo de caixa (DFC),
consolidados; o individual só quando a empresa não publica consolidado. Os arquivos consolidados de
2025 somam cerca de 240 mil linhas na DFP; com o ITR e 15 anos, a ordem é de dezenas de milhões. Para
caber, a fase 1 grava só empresas com valor mobiliário negociado em bolsa no FCA — e mede o volume
real antes de seguir.

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
| COTAHIST do dia | Dias de pregão, 21h BRT — o arquivo de 08/10 saiu às 20:42 | Cron no Railway |
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
