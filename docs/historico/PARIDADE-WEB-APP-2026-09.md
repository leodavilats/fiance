# Paridade web → aplicativo

> ## Registro, não pendência
>
> **Fechado em 2026-09-26:** as nove lacunas abertas pela saída da web têm tela no aplicativo, e a
> demonstração, que era vitrine da web, saiu do backend. O critério de morte deste documento era
> esse; ele saiu de `temporario/` e ficou aqui como registro, porque a
> [ADR-003](../decisoes/ADR-003-cliente-unico.md) aponta para ele. O estado atual está em
> [08-ESTADO](../08-ESTADO.md).

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

### ~~2 · Importação de extrato~~ — ✅ **fechado em 2026-09-26**

`mobile/lib/features/patrimony/import_screen.dart`, em `/patrimonio/razao/importar`, alcançável pelo
Livro-razão e pelos primeiros passos. Cola a lista ou o CSV, mostra a prévia com o erro na linha, e
a repetida fica de fora até a pessoa ligar a chave. Anexar arquivo ficou de fora: exigiria um plugin
novo, e colar o conteúdo do CSV cobre o caso.

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

### ~~5 · Sugestões seguidas~~ — ✅ **fechado em 2026-09-26**

`mobile/lib/features/patrimony/followed_screen.dart`, em `/patrimonio/seguidas`. A sugestão seguida
passou a sair do lançamento de compra do razão (`entry_id`), e a folha de compra do Descobrir a
registra, com chave para desligar.

### ~~6 · Onboarding~~ — ✅ **fechado em 2026-09-26**

`mobile/lib/features/config/onboarding_screen.dart`, em `/voce/comecar`, alcançável pela primeira
linha do Você. O passo vem do servidor, a URL pode apontar outro (`?passo=2`), e nada bloqueia.

### ~~7 · Reconciliação e reconstrução~~ — ✅ **fechado em 2026-09-26**

`mobile/lib/features/patrimony/reconciliation_screen.dart`, em `/patrimonio/razao/conferir`. Mostra
as diferenças; posição sem lançamento pode ir para o razão (`POST /transactions/backfill`) antes de
refazer, e refazer diz quais posições saem.

### ~~8 · Eventos corporativos~~ — ✅ **fechado em 2026-09-13**

`split`, `bonus` e `amortization` entram pelo formulário do razão.

### ~~9 · Exclusão de conta na interface~~ — ✅ **fechado em 2026-09-19**

`mobile/lib/features/config/delete_account_screen.dart`, em `/voce/conta/excluir`, alcançável pela
seção "Conta" do Você.

A tela lê `GET /account/deletion-policy` e mostra **o que o backend diz que apaga** — traduzido, não
reescrito —, o prazo em que backups e réplicas ainda guardam o dado, e a exportação ao lado, antes da
confirmação. O botão só se arma com a frase exata, e isso é travado por
`mobile/test/exclusao_de_conta_test.dart`.

A exportação (`GET /account/export`) sai pela folha de compartilhamento do sistema, em JSON — é o
outro lado do mesmo invariante, e por isso veio junto.

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
| `dip-diagnosis` | A queda virou recorte, sem diagnóstico por notícia ([ADR-018](../decisoes/ADR-018-a-queda-e-recorte-e-nao-veredito.md)) |
| `global-search` | Não há busca global no aplicativo: a busca mora no Descobrir |

---

## O que já tem paridade

`month`, `month-entry`, `month-debts`, `month-template`, `surplus`, `deviation`, `allocation-gap`,
`goals`, `goal-progress`, `positions`, `portfolio-editor`, `portfolio-summary`, `composition`,
`closed-trades`, `performance`, `patrimony-chart`, `asset`, `fair-price`, `margin-of-safety`,
`opportunities-list`, `dip-scanner`, `compare-assets`, `fixed-income`,
`fixed-income-rate`, `income-compare`, `benchmark-chart`, `quick-invest`,
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
| 2026-09-13 | 5 — rebalanceamento fechado |
| 2026-09-19 | 4 — exclusão de conta fechada |
| 2026-09-26 | **0** — importação, sugestões seguidas, onboarding e conferência fechadas |

Chegou a zero em 2026-09-26.
