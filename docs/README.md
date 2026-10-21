# Documentação do fiance

Cada documento responde **uma** pergunta e é a fonte de verdade dela. Se dois responderem a mesma
coisa, um está errado e ninguém sabe qual.

**O fiance são quatro partes, com peso igual aqui:** dois produtos — o **app** e a **API de dados** —,
a **base de mercado** que os alimenta, e o **laboratório** que mede antes de afirmar. O que vale para
todas fica na raiz, numerado; o que é de uma parte só, na pasta dela.

---

## Na raiz: o que vale para todas as partes

| A pergunta | O arquivo |
|---|---|
| O que é o fiance, de que partes é feito, e o que cada uma promete | [01-VISAO](01-VISAO.md) |
| Como as partes se ligam, quem escreve e quem lê cada dado | [02-ARQUITETURA](02-ARQUITETURA.md) |
| **Isto existe? Em que estado?** | [03-ESTADO](03-ESTADO.md) ⭐ |
| O que está quebrado ou aberto | [04-PROBLEMAS](04-PROBLEMAS.md) |
| O que vem depois | [05-FUTURO](05-FUTURO.md) |
| Como rodar, testar e não quebrar nada | [06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) |
| Como subir, observar e reverter | [07-OPERACAO](07-OPERACAO.md) |
| Por que essa decisão foi tomada | [decisoes/](decisoes/README.md) |
| O que aconteceu antes | [historico/CHANGELOG](historico/CHANGELOG.md) |

## Por parte

| Parte | Código | Pasta | Contrato de trabalho |
|---|---|---|---|
| **App** — produto, domínio, cálculos, interface | `backend/`, `mobile/` | [app/](app/README.md) | [backend/CLAUDE.md](../backend/CLAUDE.md), [mobile/CLAUDE.md](../mobile/CLAUDE.md) |
| **API de dados** — planos, rotas, contas, cobrança | `fiance-dados/` | [dados/](dados/README.md) | [fiance-dados/CLAUDE.md](../fiance-dados/CLAUDE.md) |
| **Base de mercado** — fontes, schema, tratamento de cada dado | `data-job/` | [base/](base/README.md) | [data-job/CLAUDE.md](../data-job/CLAUDE.md) |
| **Laboratório** — o painel, o protocolo e cada estudo | `fiance-trend/` | [pesquisa/](pesquisa/README.md) | [fiance-trend/CLAUDE.md](../fiance-trend/CLAUDE.md) |

---

## Por onde começar

**Chegou agora:** [README](../README.md) do repositório → [01-VISAO](01-VISAO.md) →
[03-ESTADO](03-ESTADO.md) → [02-ARQUITETURA](02-ARQUITETURA.md) → o README da parte que interessa.

**Vai escrever código:** [CLAUDE.md](../CLAUDE.md) → o `CLAUDE.md` da parte que você vai tocar →
[06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) → a pasta da parte.

**Vai mexer numa tela do app:** [app/interface](app/interface.md), antes de abrir o editor.

**Vai mexer num cálculo do app:** [app/calculos](app/calculos/README.md) e [app/dominio](app/dominio.md).

**Vai propor um estudo:** [pesquisa/](pesquisa/README.md#o-protocolo) — o protocolo vem antes do código.

---

## Estados

Todo item funcional carrega um marcador, e eles não se misturam:

`[ATUAL]` funciona e é usado · `[IMPLEMENTADO]` existe no código, sem uso real ·
`[SEM CLIENTE]` rota viva que o cliente não chama · `[PLANEJADO]` decidido, não construído ·
`[EM DISCUSSÃO]` sem decisão · `[ABANDONADO]` existiu, saiu · `[DESCONHECIDO]` nunca foi executado,
e não há como afirmar o estado

Definições em [03-ESTADO](03-ESTADO.md).

---

## Regras desta documentação

**Toda afirmação tem âncora verificável** — nome de arquivo, teste que falha, comando que roda. Sem
âncora, a frase não entra. É o que impede a documentação de descrever um sistema que não existe, como
já aconteceu com `optimizer/`.

**O que é derivável do código não é copiado.** Endpoints, campos de resposta e esquema de banco têm
fonte no código; a documentação aponta para ela.

**Histórico fica fora do caminho.** Nada em `historico/` é pendência, mesmo quando descreve um
problema. O que está aberto está em [04-PROBLEMAS](04-PROBLEMAS.md), e só lá.

**Futuro nunca se mistura com presente.** O que não existe está em [05-FUTURO](05-FUTURO.md), em
seções rígidas por estágio.

---

## Regras desta documentação

**Toda afirmação tem âncora verificável** — nome de arquivo, teste que falha, comando que roda. Sem
âncora, a frase não entra. É o que impede a documentação de descrever um sistema que não existe, como
já aconteceu com `optimizer/`.

**O que é derivável do código não é copiado.** Endpoints, campos de resposta e esquema de banco têm
fonte no código; a documentação aponta para ela.

**Estado, problema e futuro ficam na raiz, uma seção por parte.** Um documento de pasta não diz se
algo existe nem o que falta: aponta para o 03, o 04 e o 05.

**Histórico fica fora do caminho.** Nada em `historico/` é pendência, mesmo quando descreve um
problema. O que está aberto está em [04-PROBLEMAS](04-PROBLEMAS.md), e só lá.

**Futuro nunca se mistura com presente.** O que não existe está em [05-FUTURO](05-FUTURO.md), em
seções rígidas por estágio. O que foi entregue sai de lá.

---

## Fontes de verdade

| Assunto | Fonte |
|---|---|
| Endpoints e schemas | Código — OpenAPI do FastAPI |
| Campos de resposta e de entrada | `backend/tests/contrato_das_rotas.json` |
| Esquema do banco do app | Migrações Alembic em `backend/migrations/` |
| Esquema da base de mercado (schema `mercado`) | `data-job/datajob/esquema.py` e `data-job/migrations/` — só o data-job escreve nela |
| Coleta: fontes, rotina, tratamento | `data-job/datajob/`; intenção em [base/](base/README.md) |
| Pesquisas, ranking e calibração | `fiance-trend/backend/pesquisa/` e os registros `fiance-trend/backend/registro*.jsonl`; protocolo e resultado em [pesquisa/](pesquisa/README.md) |
| API de dados: contas, chaves, planos, rotas `/v1` | `fiance-dados/dadosapi/` e `fiance-dados/migrations/` (schema `acesso`); por quê em [ADR-024](decisoes/ADR-024-api-de-dados.md) |
| Painel do autor | `fiance-trend/backend/api/` e `fiance-trend/frontend/src/` — fora dos produtos ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)) |
| Vocabulário fechado (classes, categorias) | `backend/app/models/enums.py` |
| Fórmulas | Código; [app/calculos](app/calculos/README.md) é o espelho auditado |
| Limiares de score | `backend/app/analysis/score_ruler.py` — Python primeiro |
| Cor, tipo, espaço | `mobile/lib/core/design_tokens.dart` |
| Regras de tela | `mobile/test/lint_ui_test.dart` |
| Comandos | `.github/workflows/ci.yml` |
| Variáveis de ambiente | O `config.py` de cada parte — tabela em [07-OPERACAO](07-OPERACAO.md#variáveis-de-ambiente) |
| **O que existe** | [03-ESTADO](03-ESTADO.md) |
| **Visão e negócio** | [01-VISAO](01-VISAO.md); de cada produto, [app/produto](app/produto.md) e [dados/](dados/README.md) |
| **Regras de negócio e glossário do app** | [app/dominio](app/dominio.md) |
| **Protocolo de pesquisa** | [pesquisa/estudos/](pesquisa/estudos/) |
| **Decisões** | [decisoes/](decisoes/) |
| **Roadmap** | [05-FUTURO](05-FUTURO.md) |
| **Problemas** | [04-PROBLEMAS](04-PROBLEMAS.md) |
| **Invariantes de trabalho** | [CLAUDE.md](../CLAUDE.md) |

**Quando documentação e código divergirem, o código vence** em tudo que é derivável, e a divergência
é bug de documentação. Nos assuntos em negrito, a documentação vence — não há código que
responda intenção.

---

## Manutenção

Escrita em 2026-09-13, a partir de entrevista com o autor e leitura direcionada do repositório;
reorganizada por parte em 2026-10-21 ([ADR-029](decisoes/ADR-029-documentacao-por-parte.md)).

**Ao mudar o código, o documento correspondente muda no mesmo commit.** A tabela de fontes de verdade
diz qual é.

**Ao fechar um item de [04-PROBLEMAS](04-PROBLEMAS.md), apague-o.** Item resolvido que fica manda
alguém refazer o que existe.

Duas máquinas cobram esta documentação, e ambas rodam no CI:

- `docs/checar-links.mjs` — links quebrados entre documentos (job *Documentação* do CI)
- `backend/tests/test_ancoras_da_documentacao.py` — **arquivo citado que não existe**, e citação de
  linha que passou do fim do arquivo. Blocos de código ficam de fora: ali o caminho é comando, não
  referência de repositório. **Só confere caminho completo** (começando em `backend/`, `mobile/` ou
  `docs/`): um nome curto, como `analysis/fair_price.py`, não é verificado, e caminho em `data-job/`,
  `fiance-trend/backend/` ou `fiance-trend/frontend/` também não — confira à mão. As ADRs antigas citam
  arquivos que já saíram, e isso é esperado — ADR não se reescreve
