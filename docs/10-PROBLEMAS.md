# Problemas conhecidos

**Fonte de verdade** do que está aberto. Só pendências: nada de histórico, nada de item resolvido.
Última verificação contra o código: **2026-10-12**
Itens 1 a 33 herdados da verificação de 2026-09-11; itens A a E da auditoria do motor de cálculo de
2026-09-13. A0, 28, 30 e 31 saíram em 2026-09-19 — ver
[ADR-011](decisoes/ADR-011-preco-justo-e-faixa.md) e
[ADR-012](decisoes/ADR-012-o-alvo-e-de-quem-declara.md). A2, A3, A4 e A6 saíram em 2026-09-23, e
A7 a A9 entraram — ver [ADR-014](decisoes/ADR-014-um-modelo-por-classe.md). A10 e A11 entraram e
saíram em 2026-09-25 — ver [ADR-018](decisoes/ADR-018-a-queda-e-recorte-e-nao-veredito.md). O 20
(day trade e IOF) saiu em 2026-09-25 — ver [ADR-020](decisoes/ADR-020-day-trade-apartado.md) —, e
os itens 1, 4 e 33 antes disso. O 12, o 23 e o 24 saíram em 2026-09-26 — ver
[ADR-007](decisoes/ADR-007-nivel-de-afirmacao.md) e [03-ARQUITETURA](03-ARQUITETURA.md) —, e no
mesmo dia o 15, o 17 e a seção D inteira: a paridade com a web fechou. A12 entrou em 2026-10-12 —
ver [pesquisas/calibracao](pesquisas/calibracao.md). No mesmo dia a fase passou a ser pessoal
([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)): o que só bloqueia a publicação está marcado,
e não sai daqui.

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

### A12 · O veredito de preço justo não ordenou o retorno no passado

Medido em 2026-10-12 ([pesquisas/calibracao](pesquisas/calibracao.md)): de 2011 a 2017, com só o que se
sabia em cada data, ação **abaixo do preço justo** não rendeu mais nos 12 meses seguintes que ação
**acima** (4,0% contra 3,0% ao ano em média, t de −0,09), e com o juro da época o modelo punha 9 em
cada 10 ações acima da faixa.

**Aberto:** os textos foram revistos ([pesquisas/calibracao](pesquisas/calibracao.md)); falta decidir em ADR se a taxa de desconto (Selic média de 10 anos + 5 pontos)
continua sendo a do modelo, já que em juro alto ela deixa quase tudo acima da faixa.

O preço justo de BDR segue em [09-FUTURO](09-FUTURO.md), *Considerado*.

## B · Dado e fonte

Redis com timeout e reconexão, universo com cache vencido e calendário da B3 foram fechados em
2026-09-25 — ver [03-ARQUITETURA](03-ARQUITETURA.md).

### Proventos antigos de BDR, ETF e FII não estão na base

A B3 só dá o histórico de proventos de companhia; de fundo e BDR, os últimos meses. **Faltam os
proventos de BDR e ETF antes de out/2026**, e os de FII antes de 2016 — de 2016 a out/2026 o
rendimento de FII é estimado pelo informe mensal da CVM. Só entra se vier de outra fonte. Detalhe em
[11-DADOS-DE-MERCADO](11-DADOS-DE-MERCADO.md).

### Proventos e eventos dependem de endpoints da B3 sem contrato

São as únicas fontes não documentadas
([ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)). Se mudarem, cotação, empresas e
demonstrações continuam, mas a série ajustada para de receber eventos novos. O disjuntor protege
contra queda, não contra descontinuação.

---

## C · Produto incompleto

### 27 · A cobrança é backend sem cliente

**Bloqueia só a fase pública** ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)).

Existe a cerca, a régua de plano, o preço travado e o webhook — e nenhuma tela. Agravado pela decisão
de refazer tudo para RevenueCat ([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)): o que existe
hoje **não** será aproveitado.

---

## E · Interface

### 26 · A aparência nos dois temas nunca foi conferida num aparelho

O contraste é verificado por máquina; a aparência não. **Depende de aparelho**, ou emulador com a
pessoa olhando: golden test não substitui, porque a renderização de fonte muda entre o Windows de
quem gera e o Linux do CI.

### 25 · A acessibilidade nunca teve auditoria com leitor de tela

A verificação voltou a crescer em 2026-09-26: alvo de toque de 44dp e ação de toque na semântica dos
componentes (`alvo_de_toque_test.dart`), as diretrizes de alvo rotulado e de tamanho nos cinco
destinos (`jornada_do_app_test.dart`), gráfico com tabela equivalente e controles com rótulo
(regras 15 e 17). Ela achou chip e gavetas que o leitor de tela não conseguia apertar. **Falta a
auditoria:** percorrer o app com TalkBack e VoiceOver, o que exige aparelho — e, para iOS, um Mac.

---

## F · Teste, automação e operação

### 7 rotas sem contrato de resposta

`SEM_MODELO_HOJE = 7` em `tests/test_contrato_das_rotas.py` (eram 45). Conta, alertas, eventos,
qualidade de dado, regras de plano, universo e operação de cache ganharam modelo em 2026-09-26, e
depois deles transações, proventos pendentes, estratégia e sugestões de rebalanceamento, aporte
rápido, atividade, direitos de plano, logout e as exclusões. Seguem sem: as quatro de cobrança, que
serão refeitas ([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)), `/account/export` (é download de arquivo) e as leituras de operador
(`/metrics`, `/analytics/funnel`), cujo formato é aberto. A lista exata sai de
`rotas_declaradas()` menos o contrato gravado.

### Nenhum banco tem backup automático

Vale para os dois: `postgres-app` e `postgres-mercado`. **Risco aceito pelo autor em 2026-10-12**,
enquanto o uso é pessoal ([07-OPERACAO](07-OPERACAO.md#backup-e-recuperação)). A cópia lógica do
`postgres-app` e a restauração existem e são testadas (`backend/app/backup.py`), mas não são agendadas;
o `postgres-mercado` se reconstrói do bruto do data-job, menos o que as fontes já não publicam.
**Reabre antes de abrir ao público:** agendar a exportação, com destino cifrado e retenção de no
máximo 30 dias.

### 21 · O mobile nunca teve um release de verdade

**Bloqueia só a fase pública** ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)).

O app passou a enviar eventos de produto (`mobile/lib/core/product_events.dart`), conferidos contra o
catálogo fechado do servidor, e o README explica como gerar a chave de release. **Falta o que depende
de conta:** gerar e guardar a chave, publicar nas lojas (seção H) e ver o primeiro evento chegar de
um aparelho real.

---

## G · Código morto a remover

Nenhum item aberto. `optimizer/`, `OptimizationStrategy` e a duplicata de
`MIN_DATA_COMPLETENESS` foram removidos em 2026-09-13
([ADR-010](decisoes/ADR-010-remover-otimizador.md) e item A1), e a demonstração (`api/demo.py`), que
era vitrine da web, em 2026-09-26.

---

## H · Pré-requisitos de loja não atendidos

**Bloqueia só a fase pública** ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)).

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
