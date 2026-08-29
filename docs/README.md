# Documentação do fiance

Cada arquivo responde **uma** pergunta. Se você não sabe onde procurar, comece pela tabela.

| Quero saber… | Leia |
|---|---|
| Como rodar o projeto, variáveis de ambiente | [../README.md](../README.md) |
| O que não pode ser violado — invariantes, armadilhas, checklists | [../CLAUDE.md](../CLAUDE.md) |
| Como o sistema é montado por dentro — camadas, algoritmos, endpoints | [ARCHITECTURE.md](ARCHITECTURE.md) |
| O que cada tela faz | [FEATURES.md](FEATURES.md) |
| O que está quebrado, faltando ou pendente **agora** | [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |
| Por que uma decisão foi tomada, e quando | [CHANGELOG.md](CHANGELOG.md) |
| Por que a interface é assim — auditoria, arquitetura de informação, design system | [design/](design/) |

## A divisão que importa

**Estado atual** vive em `ARCHITECTURE.md`, `FEATURES.md` e `KNOWN_ISSUES.md`. Se algo nesses três
não corresponde ao código, é bug de documentação — corrija.

**Histórico** vive em `CHANGELOG.md`. Nada lá deve ser lido como pendência, mesmo quando descreve
um problema: é o registro de como o produto chegou aqui, incluindo decisões revertidas e código
apagado de propósito.

Essa separação existe porque não existia: `KNOWN_ISSUES.md` tinha 227 linhas em que a maioria dos
itens estava marcada como resolvida, com um aviso no topo pedindo para ler a última seção primeiro
porque ela invalidava as anteriores. Seis itens contradiziam o código.

## Antes de mexer

- **Regra de negócio** (fair price, score, renda fixa, IR) vive **só** no backend, em `analysis/` e
  `optimizer/`. Web e mobile delegam.
- **Token de design** é gerado, não escrito: edite `design-tokens/tokens.json` e rode
  `node design-tokens/build.mjs`. O CI falha se web e mobile divergirem.
- **Navegação e telas** seguem a arquitetura de informação em
  [design/02-INFORMATION-ARCHITECTURE.md](design/02-INFORMATION-ARCHITECTURE.md). O que já está
  construído está no código; o que **não** está, em [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
- **Suíte verde é pré-requisito de merge.** Os comandos exatos, com as contagens esperadas,
  estão em [CLAUDE.md](../CLAUDE.md#como-trabalhar-aqui). Em resumo: `pytest` (724) ·
  `flutter analyze && flutter test` (49) · `npm test && npm run build && npm run lint:ui` (90) ·
  `node design-tokens/build.mjs --check`. Tudo roda no CI a cada push.
- **Invariantes e armadilhas** — o que não pode ser violado e o que quebra em silêncio — estão em
  [CLAUDE.md](../CLAUDE.md), não aqui.
