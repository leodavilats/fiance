# fiance

Plataforma de investimento na B3, em quatro partes com peso igual
([ADR-029](docs/decisoes/ADR-029-documentacao-por-parte.md)): dois produtos — o **app** (`backend/`,
FastAPI + Postgres, multi-tenant, e `mobile/`, Flutter, o único cliente dele) e a **API de dados**
(`fiance-dados/`, a base como serviço, com contas e chaves) —, a **base de mercado** que os alimenta
(`data-job/`) e o **laboratório** do autor (`fiance-trend/backend/` + `fiance-trend/frontend/`,
[ADR-023](docs/decisoes/ADR-023-fase-pessoal-primeiro.md)).

Este arquivo é o **contrato de trabalho** do repositório inteiro: o que vale para mais de uma parte.
O que vale só para uma parte mora no `CLAUDE.md` dela:

| Parte | Contrato | Documentação |
|---|---|---|
| App: API, domínio, razão, caixa, sessão, cobrança | [backend/CLAUDE.md](backend/CLAUDE.md) | [docs/app/](docs/app/README.md) |
| App: Flutter, tela, design system | [mobile/CLAUDE.md](mobile/CLAUDE.md) | [docs/app/](docs/app/README.md) |
| API de dados | [fiance-dados/CLAUDE.md](fiance-dados/CLAUDE.md) | [docs/dados/](docs/dados/README.md) |
| Base de mercado | [data-job/CLAUDE.md](data-job/CLAUDE.md) | [docs/base/](docs/base/README.md) |
| Laboratório e painel do autor | [fiance-trend/CLAUDE.md](fiance-trend/CLAUDE.md) | [docs/pesquisa/](docs/pesquisa/README.md) |

Nenhum deles descreve o sistema — isso é [docs/](docs/), e [docs/README.md](docs/README.md) diz
qual arquivo responde o quê.

| Quero saber | Leia |
|---|---|
| **Isto existe? Em que estado?** | [docs/03-ESTADO.md](docs/03-ESTADO.md) |
| O que é o fiance, de que partes é feito | [docs/01-VISAO.md](docs/01-VISAO.md) |
| Como as partes se ligam, quem lê e escreve cada dado | [docs/02-ARQUITETURA.md](docs/02-ARQUITETURA.md) |
| Rodar, instalar, variáveis | [README.md](README.md) · [docs/07-OPERACAO.md](docs/07-OPERACAO.md) |
| Como trabalhar sem quebrar | [docs/06-DESENVOLVIMENTO.md](docs/06-DESENVOLVIMENTO.md) |
| Por que uma decisão foi tomada | [docs/decisoes/](docs/decisoes/) |
| O que está aberto **agora** | [docs/04-PROBLEMAS.md](docs/04-PROBLEMAS.md) |
| O que vem depois | [docs/05-FUTURO.md](docs/05-FUTURO.md) |
| App: público, regras de negócio, fórmulas, telas | [docs/app/](docs/app/README.md) |
| API de dados: planos, rotas, contas | [docs/dados/](docs/dados/README.md) |
| O que a base de mercado tem, e como trata cada dado | [docs/base/](docs/base/README.md) |
| O que já foi medido, e com que protocolo | [docs/pesquisa/](docs/pesquisa/README.md) |

**Histórico não é pendência.** Nada em [docs/historico/](docs/historico/) é trabalho a fazer, mesmo
quando descreve um problema. O que está aberto está no 04-PROBLEMAS, e só lá.

---

## Pronto = suíte verde

**Esta é a lista do CI, não um subconjunto dela.** Mexeu em uma parte, a parte dela é obrigatória;
as armadilhas de cada suíte estão no `CLAUDE.md` da parte.

```bash
cd backend && python -m pytest -q
cd backend && python -m ruff check app tests migrations
cd backend && python -m ruff format --check app tests
cd data-job && python -m pytest -q                 # gravação exige DATAJOB_TEST_DATABASE_URL
cd data-job && python -m ruff check datajob tests migrations
cd data-job && python -m ruff format --check datajob tests migrations
cd fiance-dados && python -m pytest -q                # exige DADOS_API_TEST_DATABASE_URL e ../data-job/requirements.txt
cd fiance-dados && python -m ruff check dadosapi tests migrations
cd fiance-dados && python -m ruff format --check dadosapi tests migrations
cd fiance-trend/backend && python -m pytest -q            # exige ../../backend/requirements.txt instalado
cd fiance-trend/backend && python -m ruff check pesquisa api tests
cd fiance-trend/backend && python -m ruff format --check pesquisa api tests
cd fiance-trend/frontend && npm ci && npm run build && npm test
cd mobile  && flutter analyze && flutter test
cd mobile  && flutter build apk --release
cd mobile  && python tool/build_icons.py --check
node docs/checar-links.mjs
```

- **Mexeu em `docs/` ou num `CLAUDE.md`, rode a suíte do backend:** ela confere que todo caminho
  citado existe.

---

## Invariantes que cruzam as partes

O **porquê** está nas [decisões](docs/decisoes/).

- **Regra de negócio vive só no backend** (`analysis/`, `ledger/`, `cashflow/`). O aplicativo delega.
- **Régua de score em um lugar por plataforma:** `analysis/score_ruler.py` e
  `mobile/lib/core/score_ruler.dart`. Mudar um limiar exige os dois, **Python primeiro**.
- **Fonte de mercado é a base própria** (`postgres-mercado`, escrita só pelo `data-job/`), e juro
  é BCB SGS. O backend lê **pela `fiance-dados`**, com uma chave do plano `interno`, nunca o banco
  direto. Nenhuma API de mercado paga.
- **O sistema não inventa dado.** Fonte fora do ar degrada em ordem: cache válido → cache vencido com
  idade visível → ausência declarada. **Falha de rede não vira ausência.**
- **Rendimento estimado pela CVM (`cvm_estimado`) não chega ao app**: é dado de pesquisa.
- **Unidades:** `roe`, `profit_margin`, `revenue_growth`, `debt_to_equity` chegam em **percentual**.
  Yield desejado e margem de segurança são **fração**.

---

## Armadilhas que cruzam as partes

Cada item já quebrou a tela ou o dado **com o CI verde**.

- **Construtor que ignora chave não declarada.** `Modelo(**resultado.__dict__)` e o `fromJson`
  descartam campo não declarado em silêncio. Três campos calculados nunca chegaram ao cliente assim.
- **Campo obrigatório novo no Dart quebra quem não atualizou.** O cliente chega por loja. Campo novo
  nasce opcional.
- **Vocabulário sem consumidor** é pior que vocabulário nenhum. E série nova precisa entrar nos mapas
  dos **três** blocos de categoria.

---

## Ao adicionar…

| O quê | Faça também |
|---|---|
| Campo calculado numa resposta | Modelo Pydantic **e** `fromJson` do Dart |
| Campo novo que o app já lê | Deixá-lo opcional no Dart |
| Limiar de score | As duas plataformas, Python primeiro |

O resto da tabela está no `CLAUDE.md` de cada parte.

---

## Comentário: quase nunca

**O porquê vive nas [decisões](docs/decisoes/); o que não pode ser violado vive nos `CLAUDE.md`.** O
fonte não é lugar de nenhum dos dois.

**Não entra:** narrativa histórica, justificativa que já está numa ADR, comentário que repete a
linha, docstring que reescreve a assinatura, explicação de teste em docstring — a razão de um teste
existir vai na **mensagem do assert**.

**Fica:** infra (CI, migração, build, script de operação), armadilha local em uma linha, e escape
declarado que uma regra de lint exige.

Se a explicação é boa demais para caber em uma linha, ela não é comentário: é uma ADR.
