# Paridade web → aplicativo

> ## ⏳ DOCUMENTO TEMPORÁRIO
>
> **Critério de morte:** quando as funcionalidades marcadas `[SEM CLIENTE]` tiverem tela no
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

### ~~1 · Livro-razão~~ — ✅ **fechado em 2026-09-13**

`mobile/lib/features/patrimony/ledger_screen.dart`, na rota `/patrimonio/razao`, alcançável pela
seção "Livro-razão" do Patrimônio.

Lista, registra e apaga lançamento, com reprojeção da carteira. Cobre os oito tipos, inclusive os
eventos corporativos (item 8 desta lista, fechado junto). O formulário muda de campos conforme o
tipo, e cada tipo explica o que faz com a posição.

Ficou de fora, de propósito: **editar** lançamento. O backend não tem `PUT /transactions/{id}` — o
caminho é apagar e registrar de novo, que é o que reprojeta corretamente.

### 2 · Importação de extrato — `import-trades`

| | |
|---|---|
| Backend | `POST /transactions/import` — prévia e commit, gravação atômica |
| Falta | Colar ou anexar extrato, revisar a prévia, decidir sobre duplicidade |
| Nota | A regra "duplicidade é apresentada para decisão, nunca silenciada" exige tela |

### ~~3 · Proventos~~ — ✅ **fechado em 2026-09-13**

`mobile/lib/features/patrimony/dividends_screen.dart`, na rota `/patrimonio/proventos`.

Registra, lista e apaga provento recebido; mostra o total de 12 meses e a média mensal com
proveniência; e traz as sugestões do calendário na mesma tela, **uma a uma**. Cada sugestão exibe a
base do cálculo (quantidade × valor por ação), avisa quando a quantidade é a de hoje em vez da data
do crédito, e lista as ressalvas da fonte.

A regra foi respeitada: **nada vem marcado** e **não existe "aceitar todos"** — o botão diz quantos
você escolheu e fica desabilitado em zero.

### ~~4 · Sugestões de rebalanceamento~~ — ✅ **fechado em 2026-09-13**

`/sobra/desvio` já listava as posições a revisar, mas mostrava só a primeira razão e **omitia
`realocar_para`** — o alvo, que é a segunda metade da frase-alvo do produto.

Agora mostra as três razões, o alvo com régua de score, e o perfil de risco que ordenou a lista,
com o glossário explicando o que ele muda. O mesmo indicador de perfil entrou em `/descobrir`.

### 5 · Ativos seguidos — `followed-suggestions`

Zero arquivos no aplicativo. Backend em `api/followed.py`.

### 6 · Onboarding — `onboarding`

| | |
|---|---|
| Backend | `GET /onboarding` — passo derivado do que a pessoa já fez |
| Falta | A tela. O recorte mora na URL (`?passo=2`) e nada bloqueia |

### 7 · Reconciliação e reconstrução

`GET /transactions/reconciliation` e `POST /transactions/rebuild`. Sem tela e sem plano.

### ~~8 · Eventos corporativos~~ — ✅ **fechado em 2026-09-13**

`split`, `bonus` e `amortization` entram pelo formulário do razão.

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
| 2026-09-13 | 9 |
| 2026-09-13 | 7 — livro-razão e eventos corporativos fechados |
| 2026-09-13 | 6 — proventos fechados |
| 2026-09-13 | **5** — rebalanceamento fechado |

Atualize esta tabela ao fechar cada uma. **Quando chegar a zero, apague o arquivo.**
