# Paridade web → aplicativo

> ## ⏳ DOCUMENTO TEMPORÁRIO
>
> **Critério de morte:** quando as nove funcionalidades marcadas `[SEM CLIENTE]` tiverem tela no
> aplicativo, **apague este arquivo** e remova a linha do índice em [README](../README.md).
>
> Ele existe para fechar uma janela aberta em 2026-09-11 e não deve sobreviver a ela. Se você estiver
> lendo isto em 2027, provavelmente já é lixo — confira contra [08-ESTADO](../08-ESTADO.md).

Criado em 2026-09-13 · Referência: commit `3a922a6`

---

## O que aconteceu

Em **2026-09-11**, o front Angular saiu inteiro do repositório
([ADR-003](../decisoes/ADR-003-cliente-unico.md)). O aplicativo Flutter passou a ser o único cliente
— **sem ter paridade** com o que saiu.

O backend continua servindo todas as rotas. Nove funcionalidades ficaram sem nenhuma forma de acesso.

**Isto não é trabalho novo: é trabalho de recuperação.** O código da interface antiga está no
histórico do git, e o backend está pronto e testado. Ver o componente Angular correspondente em
`git show 3a922a6^:web/src/app/components/<nome>/<nome>.component.ts`.

---

## As nove lacunas

Em ordem de gravidade.

### 1 · Livro-razão — `ledger-entries`

**A mais grave.** O razão é a fonte da carteira e do imposto
([ADR-002](../decisoes/ADR-002-razao-fonte-unica.md)), e não há nenhuma tela.

| | |
|---|---|
| Backend | `POST /transactions`, `GET /transactions`, `DELETE /transactions/{id}` |
| Falta | Listar, lançar, editar e apagar lançamento |
| Depende | Nada. É o primeiro item do roadmap |

### 2 · Importação de extrato — `import-trades`

| | |
|---|---|
| Backend | `POST /transactions/import` — prévia e commit, gravação atômica |
| Falta | Colar ou anexar extrato, revisar a prévia, decidir sobre duplicidade |
| Nota | A regra "duplicidade é apresentada para decisão, nunca silenciada" exige tela |

### 3 · Proventos — `dividends` + `pending-dividends`

| | |
|---|---|
| Backend | `GET /dividends`, `GET /dividends/pending` |
| Falta | Ver a origem de cada provento; aceitar os pendentes um a um |
| Nota | Nada vem pré-selecionado, e não existe "aceitar todos" — toda ressalva do calendário erra para mais |

### 4 · Sugestões de rebalanceamento — `rebalance-suggestions`

| | |
|---|---|
| Backend | `analysis/strategy.py:378` — compras por lacuna e reduções por veredito, com razões |
| Falta | A tela |
| Nota | **É a frase-alvo do produto** e a hipótese de receita. Ver [09-FUTURO](../09-FUTURO.md), item 3 |

### 5 · Ativos seguidos — `followed-suggestions`

Zero arquivos no aplicativo. Backend em `api/followed.py`.

### 6 · Onboarding — `onboarding`

| | |
|---|---|
| Backend | `GET /onboarding` — passo derivado do que a pessoa já fez |
| Falta | A tela. O recorte mora na URL (`?passo=2`) e nada bloqueia |

### 7 · Reconciliação e reconstrução

`GET /transactions/reconciliation` e `POST /transactions/rebuild`. Sem tela e sem plano.

### 8 · Eventos corporativos

`split`, `bonus`, `amortization` são lançamentos do razão. Sem tela, **desdobramento vira imposto
errado**.

### 9 · Exclusão de conta na interface

`api/account.py` existe. As lojas exigem o caminho **dentro do aplicativo** — é bloqueador de
publicação, não só paridade.

---

## O que saiu e não precisa voltar

| Componente | Por quê |
|---|---|
| `landing` | Decisão de produto: não há landing page |
| `terms`, `privacy`, `cvm` | Migraram para o backend e **passaram a funcionar** |
| `gate` | Será refeito para RevenueCat ([ADR-008](../decisoes/ADR-008-monetizacao-por-loja.md)) |
| `provenance`, `score-ruler`, `range`, `skeleton`, `section`, `ruler-track` | Já existem no Flutter como `FiProvenance`, `ScoreRuler`, `FiRange`, `FiSkeleton`, `FiSection` |
| `portfolio-shell`, `surplus-shell`, `you-shell`, `section-nav` | A navegação do Flutter é outra |
| `global-loader`, `snackbar`, `profile-modal` | Equivalente nativo |

---

## O que já tem paridade

`month`, `month-entry`, `month-debts`, `month-template`, `surplus`, `deviation`, `allocation-gap`,
`goals`, `goal-progress`, `positions`, `portfolio-editor`, `portfolio-summary`, `composition`,
`closed-trades`, `performance`, `patrimony-chart`, `asset`, `fair-price`, `margin-of-safety`,
`opportunities-list`, `dip-scanner`, `dip-diagnosis`, `compare-assets`, `fixed-income`,
`fixed-income-rate`, `income-compare`, `benchmark-chart`, `quick-invest`, `global-search`,
`price-alerts`, `preferences`, `account`, `referral`, `activity-feed`, `changes-feed`,
`contribution-simulator`, `data-age`, `empty-state`, `async-state`, `help-tooltip`, `insight`,
`metric-with-context`, `logo`, `wordmark`, `page-header`, `login`.

---

## Progresso

| Data | Lacunas abertas |
|---|---|
| 2026-09-13 | **9** |

Atualize esta tabela ao fechar cada uma. **Quando chegar a zero, apague o arquivo.**
