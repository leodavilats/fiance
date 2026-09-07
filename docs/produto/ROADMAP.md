# Roadmap da transformação

> O checklist mestre. Cada fase só começa depois de a anterior fechar os itens marcados
> **portão** — não são sugestão de ordem, são dependência real. Sem data-alvo, por decisão
> registrada em [VISAO.md](VISAO.md#horizonte--meses-sem-pressa): o ritmo é ditado por
> cada fase provar ou refutar a aposta antes da próxima.
>
> Ao fechar um item, marque e, quando a fase inteira fechar, mova o que ela decidiu para
> [docs/CHANGELOG.md](../CHANGELOG.md) e para o invariante correspondente no
> [CLAUDE.md](../../CLAUDE.md). Este arquivo é o plano; não é o registro do que já aconteceu.

---

## Fase 0 — Fundamentos (feita nesta rodada)

- [x] Diagnóstico da proposta original — [DIRECAO.md](DIRECAO.md)
- [x] Decisões de escopo travadas — [VISAO.md](VISAO.md)
- [x] Fronteira grátis/pago definida — [MODELO_NEGOCIO.md](MODELO_NEGOCIO.md)
- [x] Regras de dívida, renda e onboarding rascunhadas — [REGRAS_DE_DOMINIO.md](REGRAS_DE_DOMINIO.md)
- [x] Opções de arquitetura de informação levantadas — [../design/INFORMATION-ARCHITECTURE.md](../design/INFORMATION-ARCHITECTURE.md)
- [ ] Confirmar que a base de produção não tem dado real de usuário (checar antes de assumir que
      B4 do [PRE_PRODUCAO.md](PRE_PRODUCAO.md) não se aplica)

**Portão para a Fase 1:** nenhum — pode começar imediatamente.

---

## Fase 1 — Validação (antes de qualquer código de tela)

O objetivo desta fase é uma pergunta só: **a ponte (sobra do mês → aporte) faz alguém voltar no mês
seguinte?** Tudo aqui é barato e rápido de propósito — é a fase que existe para não gastar meses
construindo em cima de uma aposta errada.

- [ ] 10 a 15 conversas com gente real do público amplo descrito em VISAO_NOVA — a pergunta certa é
      "o que você usa hoje para controlar dinheiro, e o que te fez parar de usar", não "você
      usaria isto"
- [x] **Landing publicada em `/`** (2026-09-06), com captura de e-mail em `interest_signups`. O
      centro dela é um mês de exemplo que fecha na conta, não uma headline — foi a saída que o
      [AI-TELLS](../design/AI-TELLS.md) apontava para não virar template gerado
- [x] **Educação: curada, por ora.** Decidido em 2026-09-05, por delegação. Educação própria é
      obrigação editorial permanente, e o produto ainda não sabe se a ponte retém gente — assumir
      uma redação contínua antes disso é gastar o recurso mais escasso na aposta não validada. A
      curadoria dá para reverter: virar produção própria depois é fácil, desligar uma linha
      editorial que já existe não é. **Revisar quando a Fase 3 medir retenção.**
- [ ] Atribuir quem assume o parecer jurídico da fronteira CVM, incluindo a leitura sobre dívida —
      só **atribuir** aqui; o parecer em si é portão da Fase 5, não desta. Continua **sem dono**,
      e é a pendência mais antiga do plano. O que já está pronto para entregar a ele:
      a decisão escrita de que o nível publicável é o 2, a minuta dos três textos legais em
      `/termos`, `/privacidade` e `/aviso-cvm`, e o `AFFIRMATION_LEVEL` como mecanismo já
      implementado (ver [PRE_PRODUCAO A3](PRE_PRODUCAO.md))
- [ ] Ligar a leitura de funil/retenção sobre os 27 eventos que `core/events.py` já produz (PostHog
      ou tela de operador — decisão já discutida no PRE_PRODUCAO, seção de integrações)

**Portão para a Fase 2:** as conversas e a landing indicam interesse real na ponte — não em
"orçamento" isolado, que é mercado disputado e de baixa disposição a pagar (ver
[DIRECAO.md §4.1](DIRECAO.md#41-o-mercado-de-orçamento-é-mais-disputado-e-paga-menos-que-o-de-investimento)).
Se o sinal vier fraco, **voltar à Fase 0** e revisar a tese antes de gastar em design ou construção.

---

## Fase 2 — Design (arquitetura de informação e telas)

- [x] **IA nova decidida** (2026-09-06), em
      [docs/design/INFORMATION-ARCHITECTURE.md](../design/INFORMATION-ARCHITECTURE.md): a
      navegação passa a ser o ciclo do dinheiro — `Mês` → `Sobra` → `Patrimônio`, mais `Descobrir`
      e `Você`. `Hoje` sai (feed não é lugar) e a ponte vira destino, chamada `Sobra` e não
      `Aporte`. Continuam cinco destinos
- [x] **A ponte desenhada** (2026-09-07), em
      [docs/design/WIREFRAMES.md](../design/WIREFRAMES.md#n1-sobra--a-ponte). Traz critério de
      aceite: se em algum estado ela voltar a **pedir** o valor do aporte a quem tem caixa
      lançado, a ponte não está construída. **Portão da Fase 3 fechado**
- [x] **Sistema de design refeito** (2026-09-07), registrado em
      [docs/CHANGELOG.md](../CHANGELOG.md). A direção de 2026-09-05 mudou em 2026-09-07:
      não era *manter* o mecanismo de geração, era **tirar a camada visual dele** — o schema
      fechava o vocabulário e não tinha chave para estado de interação. Cor, tipo, espaço, raio,
      motion e densidade passaram a ser escritos em `web/src/foundation.css`, com espelho à mão
      em `design_tokens.dart`; réguas e vocabulário continuam gerados de `product-rules.json`,
      porque são número e não aparência. A afordância era o diagnóstico certo e virou número:
      contorno de controle a **1,20:1** (WCAG pede 3) e preenchimento contra poço a **2,28:1**.
      Três travas novas, cada uma conferida contra o defeito que a motivou
- [x] **Vocabulário do caixa decidido** (2026-09-07), em
      [docs/design/DESIGN-SYSTEM.md](../design/DESIGN-SYSTEM.md). Dez categorias de despesa,
      seis de entrada, sete tipos de dívida. **Não** foi para `product-rules.json`: a armadilha do
      CLAUDE.md diz que gerado sem consumidor é pior, então a entrada acompanha a primeira tela da
      Fase 3 que o usa
- [x] **Wireframe da linha do tempo feito** (2026-09-07), com o feed de urgência dentro dele —
      `Exige atenção` é o que era o feed do `Hoje`, e a dívida entra ali. A ordem dos blocos é por
      **custo de não ver**, não por assunto

**Portão para a Fase 3:** design aprovado para a tela da ponte, pelo menos — o resto pode iterar
durante a construção, mas a peça central não pode começar a ser codificada sem forma definida.
**Fechado em 2026-09-07.**

**Duas decisões de domínio ficaram pendentes, e as duas bloqueiam `cashflow/`:**

1. **`provento` no caixa.** Provento creditado é entrada de caixa **e** lançamento do razão. Sem
   regra, o mesmo dinheiro conta duas vezes e infla a renda do mês e a sobra junto. Três saídas
   possíveis, e só uma não cria segunda verdade (o caixa **lê** o razão, e a entrada é derivada).
2. **Reserva de emergência.** Não é passo da cascata da `Sobra` porque não há decisão: quantos
   meses, contra qual base, e antes ou depois da dívida cara.

---

## Fase 3 — Construção do MVP grátis (manual)

Tudo nesta fase é **manual** — nenhuma conexão bancária ainda. É onde a hipótese da Fase 1 vira
produto de verdade e se testa com uso real, não com conversa.

- [ ] `cashflow/` como módulo irmão de `ledger/` (ver
      [DIRECAO.md §7](DIRECAO.md#7-o-que-precisa-ser-construído)): lançamento de
      renda, gasto fixo, gasto eventual, dívida
- [ ] Porta única de escrita (`cashflow_service`), pelo mesmo padrão de `ledger_service`
- [ ] Recorrência: salário no dia X, contas fixas, com previsto × realizado
- [ ] Sobra projetada do mês, em faixa quando a renda é variável (mesma disciplina de
      `analysis/scenarios.py`)
- [ ] Orientação de dívida (regra do REGRAS_NOVO_DOMINIO), com dado só manual nesta fase
- [ ] Perfil de onboarding (as ≤5 perguntas do REGRAS_NOVO_DOMINIO)
- [ ] A tela da ponte, ligando `cashflow/` a `optimizer/`/`quick_invest` de verdade
- [ ] Extrato B3 (XLSX) no parser de importação — libera a carteira sem digitação manual, fica no
      Free (ver MODELO_NEGOCIO), e não depende de nenhuma decisão desta fase para ser feito
- [ ] Nova IA implementada nas telas (opção decidida na Fase 2), conferindo cada tela nova contra
      [docs/design/AI-TELLS.md](../design/AI-TELLS.md) antes de considerar pronta
- [ ] Toda tabela nova entra em `account_store.USER_SCOPED_MODELS` — exportação e exclusão
      continuam cobrindo tudo, sem exceção nova
- [ ] Medir: quem completa o onboarding volta na semana seguinte? No mês seguinte?

**Portão para a Fase 4:** retenção real medida e minimamente saudável. Sem isso, contratar o Open
Finance é pagar o piso fixo da Pluggy (ver MODELO_NEGOCIO) sem ter para quem vender a automação.

---

## Fase 4 — Automação (Open Finance)

- [ ] Cotação atualizada com Pluggy (ou concorrente: Belvo, Klavi, Quanto) para o volume real de
      usuários da Fase 3
- [ ] Decisão de preço da assinatura Premium, agora com dado de retenção e custo reais —
      pendência que MODELO_NEGOCIO deixou deliberadamente em aberto até aqui
- [ ] Integração: Pluggy Connect (widget) nas duas plataformas
- [ ] Produto **Accounts + Transactions** → alimenta `cashflow/` automaticamente
- [ ] Produto **Investments** + **Investment Transactions** → alimenta `ledger_service.import_entries`
      automaticamente, no padrão de prévia + commit que a importação já usa
- [ ] Produto de **crédito/empréstimo** → alimenta a orientação de dívida automaticamente
- [ ] Categorização (enrichment) da Pluggy mapeada para o vocabulário de categoria de despesa
      gerado na Fase 2 — precisa de normalizador, a taxonomia deles não é a nossa
- [ ] `Feature.OPEN_FINANCE_SYNC` (ou nome equivalente) em `entitlement/plans.py`, seguindo o padrão
      já existente — nenhuma condicional de plano fora de `entitlement/`
- [ ] LGPD: revisão específica de consentimento de Open Finance — prazo, escopo, revogação — além
      do texto geral que a trilha A do PRE_PRODUCAO já cobre

**Portão para a Fase 5:** automação funcionando em produção, com reconciliação testada (duplicidade
apresentada para decisão, nunca silenciada — mesmo padrão que a importação de extrato já segue).

---

## Fase 5 — Cobrança

Esta fase **é** a trilha B do [PRE_PRODUCAO.md](PRE_PRODUCAO.md), sem duplicar aqui. O que muda com
a direção nova:

- [ ] Parecer jurídico da fronteira CVM (A3 do PRE_PRODUCAO), incluindo a leitura específica sobre
      dívida deste documento
- [ ] Régua de `entitlement/plans.py` refeita com o `Feature` de automação, e a régua de preço da
      Fase 4 aplicada
- [ ] Resto da trilha B (IAP, provedor de pagamento, tela de plano, trial, e-mail, nota fiscal) —
      sem alteração pela direção nova, seguir o checklist de lá

**Portão para produção paga:** todo o checklist da trilha B do PRE_PRODUCAO fechado.

---

## O que corre em paralelo, sem portão

Independente de fase — pode e deve acontecer a qualquer momento a partir de agora:

- [ ] Trilha A do PRE_PRODUCAO (subir de graça) — continua sendo o único bloqueio real para ter
      qualquer versão publicamente testável. **A parte de código foi feita em 2026-09-05** (suíte,
      IR, migração, texto legal, Sentry); o que resta é conta, painel de terceiro e um advogado
- [ ] CVM Dados Abertos e Tesouro Direto (integrações do PRE_PRODUCAO/DIRECAO_PRODUTO) — resolvem
      buracos do motor de análise (KI#3, KI#21) que continuam existindo e não dependem de nenhuma
      decisão deste documento

---

## Onde cada decisão já tomada vive

Para não reabrir debate por não lembrar que já foi decidido:

| Assunto | Decidido em |
|---|---|
| Nome, marca, público, horizonte, o que preservar do código | [VISAO.md](VISAO.md) |
| Fronteira grátis/pago | [MODELO_NEGOCIO.md](MODELO_NEGOCIO.md) |
| Dívida, renda líquida, perfil de onboarding | [REGRAS_DE_DOMINIO.md](REGRAS_DE_DOMINIO.md) |
| Opções de navegação e telas | [../design/INFORMATION-ARCHITECTURE.md](../design/INFORMATION-ARCHITECTURE.md) |
| Por que a direção é extensão e não pivô, o que a proposta original acertava e subestimava | [DIRECAO.md](DIRECAO.md) |
| O que falta para subir, cobrar e publicar, hoje, sem relação com esta direção | [PRE_PRODUCAO.md](PRE_PRODUCAO.md) |
