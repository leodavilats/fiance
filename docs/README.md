# Documentação do fiance

Cada arquivo responde **uma** pergunta. Se você não sabe onde procurar, comece pela tabela.

| Quero saber… | Leia |
|---|---|
| Como rodar o projeto, variáveis de ambiente | [../README.md](../README.md) |
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
  construído está em [design/07-IMPLEMENTATION.md](design/07-IMPLEMENTATION.md).
- **Suíte verde é pré-requisito de merge.** `cd backend && python -m pytest -q` ·
  `flutter analyze && flutter test` · `npm run format:check && npx ng build` ·
  `node design-tokens/build.mjs --check`. Tudo roda no CI a cada push.
