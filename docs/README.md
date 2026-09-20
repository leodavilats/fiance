# Documentação do fiance

Cada documento responde **uma** pergunta e é a fonte de verdade dela. Se dois responderem a mesma
coisa, um está errado e ninguém sabe qual.

---

## Qual arquivo responde o quê

| A pergunta | O arquivo |
|---|---|
| **Isto existe? Em que estado?** | [08-ESTADO](08-ESTADO.md) ⭐ |
| Por que o sistema existe, para quem, e como ganha dinheiro | [01-PRODUTO](01-PRODUTO.md) |
| O que significa esse termo? Qual é a regra? | [02-DOMINIO](02-DOMINIO.md) |
| Como o sistema é montado, e por que assim | [03-ARQUITETURA](03-ARQUITETURA.md) |
| Como esse número é calculado, e no que não confiar | [04-CALCULOS](04-CALCULOS.md) |
| Por que a interface é assim, e o que uma tela nova precisa respeitar | [05-INTERFACE](05-INTERFACE.md) |
| Como rodar, testar e não quebrar nada | [06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) |
| Como subir, observar e reverter | [07-OPERACAO](07-OPERACAO.md) |
| O que vem depois | [09-FUTURO](09-FUTURO.md) |
| O que está quebrado ou aberto | [10-PROBLEMAS](10-PROBLEMAS.md) |
| Por que essa decisão foi tomada | [decisoes/](decisoes/) |
| O que a web tinha e o aplicativo ainda não tem | [temporario/PARIDADE-WEB-APP](temporario/PARIDADE-WEB-APP.md) ⏳ |
| O que está errado no caminho do preço ao veredito | [temporario/AUDITORIA-DO-VEREDITO](temporario/AUDITORIA-DO-VEREDITO.md) ⏳ |
| O que aconteceu antes | [historico/CHANGELOG](historico/CHANGELOG.md) |

---

## Por onde começar

**Chegou agora:** [README](../README.md) do repositório → [01-PRODUTO](01-PRODUTO.md) →
[08-ESTADO](08-ESTADO.md) → [03-ARQUITETURA](03-ARQUITETURA.md).

**Vai escrever código:** [CLAUDE.md](../CLAUDE.md) →
[06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) → o documento da área que você vai tocar.

**Vai mexer numa tela:** [05-INTERFACE](05-INTERFACE.md), antes de abrir o editor.

**Vai mexer num cálculo:** [04-CALCULOS](04-CALCULOS.md) e [02-DOMINIO](02-DOMINIO.md).

---

## Estados

Todo item funcional carrega um marcador, e eles não se misturam:

`[ATUAL]` funciona e é usado · `[IMPLEMENTADO]` existe no código, sem uso real ·
`[SEM CLIENTE]` backend vivo, aplicativo não alcança · `[PLANEJADO]` decidido, não construído ·
`[EM DISCUSSÃO]` sem decisão · `[ABANDONADO]` existiu, saiu

Definições em [08-ESTADO](08-ESTADO.md).

---

## Regras desta documentação

**Toda afirmação tem âncora verificável** — nome de arquivo, teste que falha, comando que roda. Sem
âncora, a frase não entra. É o que impede a documentação de descrever um sistema que não existe, como
já aconteceu com `optimizer/`.

**O que é derivável do código não é copiado.** Endpoints, campos de resposta e esquema de banco têm
fonte no código; a documentação aponta para ela.

**Histórico fica fora do caminho.** Nada em `historico/` é pendência, mesmo quando descreve um
problema. O que está aberto está em [10-PROBLEMAS](10-PROBLEMAS.md), e só lá.

**Futuro nunca se mistura com presente.** O que não existe está em [09-FUTURO](09-FUTURO.md), em
seções rígidas por estágio.

---

## Fontes de verdade

| Assunto | Fonte |
|---|---|
| Endpoints e schemas | Código — OpenAPI do FastAPI |
| Campos de resposta | `backend/tests/contrato_das_rotas.json` |
| Esquema do banco | Migrações Alembic |
| Vocabulário fechado (classes, categorias) | `backend/app/models/enums.py` |
| Fórmulas | Código; [04-CALCULOS](04-CALCULOS.md) é o espelho auditado |
| Limiares de score | `backend/app/analysis/score_ruler.py` — Python primeiro |
| Cor, tipo, espaço | `mobile/lib/core/design_tokens.dart` |
| Regras de tela | `mobile/test/lint_ui_test.dart` |
| Comandos | `.github/workflows/ci.yml` |
| Variáveis de ambiente | `backend/app/core/config.py` |
| **O que existe** | [08-ESTADO](08-ESTADO.md) |
| **Regras de negócio e glossário** | [02-DOMINIO](02-DOMINIO.md) |
| **Visão e negócio** | [01-PRODUTO](01-PRODUTO.md) |
| **Decisões** | [decisoes/](decisoes/) |
| **Roadmap** | [09-FUTURO](09-FUTURO.md) |
| **Problemas** | [10-PROBLEMAS](10-PROBLEMAS.md) |
| **Invariantes de trabalho** | [CLAUDE.md](../CLAUDE.md) |

**Quando documentação e código divergirem, o código vence** em tudo que é derivável, e a divergência
é bug de documentação. Nos seis assuntos em negrito, a documentação vence — não há código que
responda intenção.

---

## Manutenção

Escrita em 2026-09-13, a partir de entrevista com o autor e leitura direcionada do repositório.

**Ao mudar o código, o documento correspondente muda no mesmo commit.** A tabela de fontes de verdade
diz qual é.

**Ao fechar um item de [10-PROBLEMAS](10-PROBLEMAS.md), apague-o.** Item resolvido que fica manda
alguém refazer o que existe.

Duas máquinas cobram esta documentação, e ambas rodam no CI:

- `docs/checar-links.mjs` — links quebrados entre documentos
- `backend/tests/test_ancoras_da_documentacao.py` — **arquivo citado que não existe**, e citação de
  linha que passou do fim do arquivo. Blocos de código ficam de fora: ali o caminho é comando, não
  referência de repositório
