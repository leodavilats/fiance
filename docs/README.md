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
| Por que a interface é assim — identidade, design system, arquitetura de informação, wireframes | [design/](design/) |
| Para onde o produto vai — visão, modelo de negócio, regras de domínio, roadmap | [produto/](produto/) |
| Subir, observar e reverter — variáveis, deploy, Sentry, backup | [OPERACAO.md](OPERACAO.md) |

## As três naturezas de documento

A pasta tem três tipos de arquivo, e misturá-los é o que fez esta documentação apodrecer antes.

**O que o sistema É.** `ARCHITECTURE.md`, `FEATURES.md`, `KNOWN_ISSUES.md` e `design/`. Se algo
aqui não corresponde ao código, é **bug de documentação** — corrija o documento, não o leitor.

**Como o sistema chegou aqui.** `CHANGELOG.md`, e só ele. Nada lá é pendência, mesmo quando
descreve um problema: é o registro de decisões, incluindo as revertidas e o código apagado de
propósito.

**Para onde o produto vai.** `produto/`. Nada ali está construído, e por isso todo arquivo tem
prazo de validade: item fechado se apaga, direção que virou código vira entrada no `CHANGELOG` e
sai de lá.

Essa separação existe porque não existia. `KNOWN_ISSUES.md` já teve 227 linhas com a maioria dos
itens marcada como resolvida e um aviso no topo pedindo para ler a última seção primeiro, porque
ela invalidava as anteriores; seis itens contradiziam o código.

## Antes de mexer

- **Regra de negócio** (preço justo, score, renda fixa, IR, caixa) vive **só** no backend, em
  `analysis/`, `optimizer/`, `ledger/` e `cashflow/`. Web e mobile delegam.
- **A camada visual é escrita; a régua é gerada.** Cor, tipografia, espaço e motion vivem em
  [web/src/foundation.css](../web/src/foundation.css), com espelho à mão em
  `mobile/lib/core/design_tokens.dart`. O que continua gerado é o que precisa ser igual nas três
  plataformas por ser **número**, e não aparência: `design-tokens/product-rules.json` →
  `node design-tokens/build-rules.mjs`. O contraste é verificado no CI, não recomendado.
- **Navegação e telas** seguem a arquitetura de informação em
  [design/INFORMATION-ARCHITECTURE.md](design/INFORMATION-ARCHITECTURE.md). O que já está
  construído está no código; o que **não** está, em [produto/ROADMAP.md](produto/ROADMAP.md).
- **Suíte verde é pré-requisito de merge.** Os comandos exatos, com as contagens esperadas, estão
  em [CLAUDE.md](../CLAUDE.md). Tudo roda no CI a cada push.
- **Link quebrado é erro.** `node docs/checar-links.mjs` varre todo `.md` do repositório, arquivo
  e âncora. Documentação reorganizada sem conferir link é refatoração sem teste.
- **Invariantes e armadilhas** — o que não pode ser violado e o que quebra em silêncio — estão em
  [CLAUDE.md](../CLAUDE.md), não aqui.
