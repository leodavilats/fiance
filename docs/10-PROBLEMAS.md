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

### 1 · O caminho do Redis nunca rodou contra um servidor real fora do CI

Coberto: o contrato e a tradução do adaptador. Não coberto: rede instável, reconexão, failover.

### 4 · Universo hardcoded como fallback

`core/config.py::default_universe` mantém ~400 tickers, apesar de existir universo dinâmico via
BRAPI. Fallback defensivo intencional, mas extenso.

### 33 · A janela de pregão não conhece feriado da B3

`core/pregao.py` bloqueia a varredura em dia de feriado como se fosse pregão normal.

---

## C · Produto incompleto

### 15 · Sugestões seguidas dependem de lançamento manual

### 20 · A apuração de IR não cobre day trade nem IOF de renda fixa

### 27 · A cobrança é backend sem cliente

Existe a cerca, a régua de plano, o preço travado e o webhook — e nenhuma tela. Agravado pela decisão
de refazer tudo para RevenueCat ([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)): o que existe
hoje **não** será aproveitado.

### 16 · `detail_level` (Essencial / Completo / Avançado) não existe no backend

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

### 7 · Duas famílias de controle ainda são Material puro, com estilo só no tema

`Switch` e `Slider`. A ficha saiu em 2026-09-15 — `FiChoiceChip` —, e `ExpansionTile` foi substituído
onde o produto usava caixa expansível.

### 9 · Falta a regra do alvo de toque de 44dp no Dart

### 11 · Falta o componente de evidência

Falta `Evidence`, o nível 2 da explicabilidade. O par que revelava detalhe foi construído em
2026-09-15: `FiDisclosure` e `FiGroupDisclosure`.

### 12 · A régua de afirmação anula `allocated_cash` e deixa a subtração de pé

### 17 · A régua não cobre o score em linha densa, e ali ele sai só como selo

### 26 · A aparência nos dois temas nunca foi conferida num aparelho

O contraste é verificado por máquina; a aparência não.

### 25 · A acessibilidade foi coberta por verificação, não por auditoria — e a verificação encolheu

---

## F · Teste, automação e operação

### 13 · Não existe mais teste de ponta a ponta

O que havia rodava no navegador e saiu com o front web.

### 14 · As regras de interface que só rodavam no front não foram portadas

Três não têm equivalente no Dart: **gráfico sem tabela equivalente**, **destino de navegação
inexistente** *(esta foi portada — regra 13 do lint)* e **controle montado à mão**.

### 6 · Rótulo e régua são escritos dos dois lados — os números já são comparados, os textos não

Desde 2026-09-13, `tests/test_regua_nas_duas_plataformas.py` confronta os **cinco limiares
numéricos** da régua de score entre `analysis/score_ruler.py` e `mobile/lib/core/product_rules.dart`,
com o Python como fonte.

**O que ainda não é comparado:** os rótulos das bandas ("Excelente entrada", "Boa oportunidade"…),
o vocabulário de veredito e os rótulos de categoria. Continuam escritos duas vezes, e nada impede que
o Dart chame de "Boa oportunidade" o que o Python chama de outra coisa.

### 18 · O contrato das rotas guarda campo que sai, não campo que entra

### 45 rotas sem contrato de resposta

`SEM_MODELO_HOJE = 45` em `tests/test_contrato_das_rotas.py`. Metade das rotas devolve `dict` solto,
sem `response_model` — o FastAPI não pode conferir, e o contrato não as cobre. A catraca impede
crescer; não faz o número cair.

### 24 · A paginação das listas com agregado limita o payload, não a consulta

### 23 · Token de push é reatribuído a quem o registrar

### Não existe rotina de backup própria nem restauração testada

O backup é o do provedor. Nunca foi exercitado.

### 21 · O mobile nunca teve um release de verdade

Não existe chave de assinatura, e nenhum evento de telemetria foi visto em produção.

---

## G · Código morto a remover

| Item | Ação |
|---|---|
| `api/demo.py` — sem cliente desde 2026-09-11 | Decidir |

`optimizer/`, `OptimizationStrategy` e a duplicata de `MIN_DATA_COMPLETENESS` foram removidos em
2026-09-13 ([ADR-010](decisoes/ADR-010-remover-otimizador.md) e item A1).

---

## H · Pré-requisitos de loja não atendidos

### Sign in with Apple não existe

A App Store exige quando há login social de terceiros. O sistema só tem Google. É um segundo provedor
de identidade, não uma configuração.

### Não há contas de desenvolvedor, nem Mac

Ver [07-OPERACAO](07-OPERACAO.md).

---

## Armadilhas conhecidas

Não são bugs, mas mordem. Lista completa em [06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) e no
`CLAUDE.md`.
