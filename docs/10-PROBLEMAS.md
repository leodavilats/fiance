# Problemas conhecidos

**Fonte de verdade** do que está aberto. Só pendências: nada de histórico, nada de item resolvido.
Última verificação contra o código: **2026-09-23**
Itens 1 a 33 herdados da verificação de 2026-09-11; itens A a E da auditoria do motor de cálculo de
2026-09-13. A0, 28, 30 e 31 saíram em 2026-09-19 — ver
[ADR-011](decisoes/ADR-011-preco-justo-e-faixa.md) e
[ADR-012](decisoes/ADR-012-o-alvo-e-de-quem-declara.md). A2, A3, A4 e A6 saíram em 2026-09-23, e
A7 a A9 entraram — ver [ADR-014](decisoes/ADR-014-um-modelo-por-classe.md). A10 e A11 entraram e
saíram em 2026-09-25 — ver [ADR-018](decisoes/ADR-018-a-queda-e-recorte-e-nao-veredito.md).

> **Ao fechar um item, apague-o daqui.** Item resolvido que fica é pior que item ausente, porque
> manda alguém refazer o que já existe. Este arquivo tem histórico de apodrecer: numa revisão de
> agosto, oito de 24 itens já estavam feitos.

---

## A · Motor de cálculo

Os itens da auditoria de **2026-09-13** foram fechados até 2026-09-25. A de **2026-09-20**, que inventariou os
40 problemas do caminho do preço ao veredito, foi fechada no mesmo dia
([ADR-013](decisoes/ADR-013-o-tecnico-nao-decide.md)) e virou registro em
[historico/AUDITORIA-DO-VEREDITO-2026-09-20](historico/AUDITORIA-DO-VEREDITO-2026-09-20.md). A de
**2026-09-25**, sobre a especificação do preço justo, teve os 19 itens fechados no mesmo dia
([ADR-015](decisoes/ADR-015-a-faixa-cobre-os-dois-cenarios.md) a
[ADR-017](decisoes/ADR-017-o-score-nao-le-o-tecnico.md)) e virou registro em
[historico/AUDITORIA-DO-PRECO-JUSTO-2026-09-25](historico/AUDITORIA-DO-PRECO-JUSTO-2026-09-25.md).

Nenhum item aberto. A calibração empírica dos parâmetros e o preço justo de BDR não são defeitos:
exigem fonte fora de BRAPI e BCB SGS, e estão em [09-FUTURO](09-FUTURO.md), *Considerado*.

## B · Dado e fonte

Nenhum item aberto. Redis com timeout e reconexão, universo com cache vencido e calendário da B3
foram fechados em 2026-09-25 — ver [03-ARQUITETURA](03-ARQUITETURA.md).

---

## C · Produto incompleto

### 15 · Sugestões seguidas dependem de lançamento manual

### 27 · A cobrança é backend sem cliente

Existe a cerca, a régua de plano, o preço travado e o webhook — e nenhuma tela. Agravado pela decisão
de refazer tudo para RevenueCat ([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)): o que existe
hoje **não** será aproveitado.

---

## D · Paridade perdida — o mais urgente

Nove funcionalidades ficaram sem cliente com a remoção do front web em 2026-09-11. **Quatro seguem
abertas:** importação de extrato, ativos seguidos, onboarding, e reconciliação com reconstrução.
Inventário completo e com critério de morte em
[PARIDADE-WEB-APP](temporario/PARIDADE-WEB-APP.md).

A mais grave é a **importação de extrato**: o razão ganhou tela em 2026-09-13, e alimentá-lo
continua sendo um lançamento de cada vez.

---

## E · Interface

### 12 · A régua de afirmação anula `allocated_cash` e deixa a subtração de pé

### 17 · A régua não cobre o score em linha densa, e ali ele sai só como selo

### 26 · A aparência nos dois temas nunca foi conferida num aparelho

O contraste é verificado por máquina; a aparência não.

### 25 · A acessibilidade foi coberta por verificação, não por auditoria — e a verificação encolheu

---

## F · Teste, automação e operação

### 13 · Não existe mais teste de ponta a ponta

O que havia rodava no navegador e saiu com o front web.

### 31 rotas sem contrato de resposta

`SEM_MODELO_HOJE = 31` em `tests/test_contrato_das_rotas.py` (eram 45). Conta, alertas, eventos,
qualidade de dado, regras de plano, universo e operação de cache ganharam modelo em 2026-09-26.
Seguem sem: transações, proventos pendentes, estratégia, aporte rápido, cobrança, logout, as exclusões
de posição, `/account/export` (é download de arquivo) e as leituras de operador (`/metrics`,
`/analytics/funnel`), cujo formato é aberto.

### 24 · A paginação das listas com agregado limita o payload, não a consulta

### 23 · Token de push é reatribuído a quem o registrar

### O backup próprio ainda não é agendado

A cópia lógica e a restauração existem e são testadas (`backend/app/backup.py`, ver
[07-OPERACAO](07-OPERACAO.md)). Falta agendar a exportação e escolher o destino cifrado, com
retenção de no máximo 30 dias. **Depende de decisão de operação na conta do Railway**, não de código.

### 21 · O mobile nunca teve um release de verdade

O app passou a enviar eventos de produto (`mobile/lib/core/product_events.dart`), conferidos contra o
catálogo fechado do servidor, e o README explica como gerar a chave de release. **Falta o que depende
de conta:** gerar e guardar a chave, publicar nas lojas (seção H) e ver o primeiro evento chegar de
um aparelho real.

---

## G · Código morto a remover

| Item | Ação |
|---|---|
| `api/demo.py` — sem cliente desde 2026-09-11 | Decidir |

`optimizer/`, `OptimizationStrategy` e a duplicata de `MIN_DATA_COMPLETENESS` foram removidos em
2026-09-13 ([ADR-010](decisoes/ADR-010-remover-otimizador.md) e item A1).

---

## H · Pré-requisitos de loja não atendidos

### Sign in with Apple não tem botão no app

O servidor está pronto (`POST /auth/apple`, ver [07-OPERACAO](07-OPERACAO.md)). O botão no app
depende de conta Apple Developer (Services ID), de um Mac e do pacote `sign_in_with_apple`, e só pode
ser construído e testado com eles.

### Não há contas de desenvolvedor, nem Mac

Ver [07-OPERACAO](07-OPERACAO.md).

---

## Armadilhas conhecidas

Não são bugs, mas mordem. Lista completa em [06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) e no
`CLAUDE.md`.
