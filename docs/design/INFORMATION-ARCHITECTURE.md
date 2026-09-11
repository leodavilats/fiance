# Arquitetura de informação

> **Uma IA só.** A navegação é o ciclo do dinheiro — `Mês` → `Sobra` → `Patrimônio`, mais
> `Descobrir` e `Você`, com `/ativo/:ticker` como camada. A decisão é de 2026-09-06 e está
> construída; a estrutura anterior (`Hoje`, `Carteira`, `Estratégia`) saiu deste arquivo em
> 2026-09-11, com as URLs antigas vivas como redirect. O porquê está no
> [CHANGELOG](../CHANGELOG.md).

---

# Por que o mês entra, e o "Hoje" sai

## O problema que a estrutura anterior não resolvia

A IA construída agrupa por **pergunta que a pessoa tem na cabeça ao abrir o app**, e isso continua
certo. O que quebra é a aritmética: o caixa acrescenta três perguntas que não cabem em destino
nenhum dos existentes.

| Pergunta nova | Onde caberia hoje |
|---|---|
| "quanto sobra este mês?" | lugar nenhum |
| "o que vence esta semana?" | lugar nenhum |
| "minha dívida é cara?" | lugar nenhum |

Manter "um destino, uma pergunta" com oito perguntas dá oito destinos, e o limite de cinco não é
estético: acima dele a pessoa deixa de manter o mapa na cabeça e volta a caçar funcionalidade.

A pergunta de projeto, então, não é *"onde encaixo o mês"*. É **qual princípio de agrupamento
sobrevive ao produto dobrar de escopo**.

## O que foi considerado e recusado

As três opções levantadas em
[ARQUITETURA_INFORMACAO_NOVA](../produto/ROADMAP.md) partem todas de
que a resposta é um arranjo dos cinco destinos de hoje. Nenhuma questiona o princípio.

| Caminho | Por que não |
|---|---|
| **A — `Hoje` abre pelo mês** | Resolve por acomodação: o mês vira conteúdo de uma tela que existe para outra coisa, e sobram duas leituras concorrentes de "o que merece atenção" na mesma casa |
| **B — sexto destino `/dinheiro`** | Seis é o teto físico da barra inferior, e cria dois resumos rivais: `Hoje` ("o que mudou") e `Dinheiro` ("quanto sobrou") respondem quase a mesma coisa em telas vizinhas |
| **C — `Carteira` vira `Patrimônio` com abas** | Enterra a ponte dois níveis. A tese é que o mês é a porta de entrada; ali ele vira aba dentro de patrimônio |
| **Alternar entre dois mundos** (toggle no topo) | [VISAO_NOVA](../produto/VISAO.md) recusa: "não é dois apps num só instalador" |
| **Navegação por verbo** (Ver · Decidir · Ajustar) | Falha o critério de ser **objetiva**: ninguém abre um app de dinheiro pensando num verbo |

## A decisão: a navegação **é** o ciclo do dinheiro

A visão descreve um ciclo — renda → gasto → **sobra** → aporte → patrimônio, e o patrimônio
voltando a informar a próxima decisão. Se o ciclo é o produto, ele é o mapa. Cinco destinos, mesmo
orçamento de antes:

| Destino | Rota | A pergunta |
|---|---|---|
| **Mês** | `/mes` | "como estou agora, e o que exige atenção?" |
| **Sobra** | `/sobra` | "o que faço com o que sobrou?" |
| **Patrimônio** | `/patrimonio` | "como está o que eu já tenho?" |
| **Descobrir** | `/descobrir` | "o que eu poderia comprar?" |
| **Você** | `/voce` | "quero mudar como o app me trata" |

`/ativo/:ticker` continua **camada, não destino** — e continua sendo a rota pública de aquisição.

### Por que `Hoje` deixa de existir

`Hoje` responde "o que mudou e o que merece minha atenção". Isso é **um feed, não um lugar** — e o
produto já sabe disso: `Atividade` virou drawer pela mesma razão, com o argumento escrito de que
uma central de notificações como destino seria "uma sala vazia".

Com um mês no produto, `Hoje` e a linha do tempo do mês passam a disputar a mesma frase. Os quatro
conteúdos de `Hoje` se distribuem sem sobra:

| O que `Hoje` mostra | Vai para |
|---|---|
| feed do que mudou, urgência | **Mês** — porque "agora" é o mês |
| patrimônio e variação | **Patrimônio** |
| veredito de saúde | **Patrimônio** |
| próxima ação | **Sobra** — a próxima ação passou a ter tela própria |

Não é funcionalidade perdida: é uma tela que existia porque o produto não tinha um "agora" de
verdade. Agora tem.

### Por que `Sobra` é destino, e não bloco

É a decisão mais cara deste documento, e é o que sustenta a tese. A visão é explícita: *"se a sobra
não alimentar a decisão de investir, a ponte não existe e o produto é dois apps num só
instalador"*. Ponte que mora dentro de outra tela é decoração da tese, não a tese.

É também o único destino que existe para **uma decisão**, e não para um assunto. Visita-se uma vez
por mês — e é exatamente o ritual que o produto quer criar.

### Por que o nome é `Sobra`, e não `Aporte`

`Aporte` nomeia a resposta, e a resposta nem sempre é aportar: com dívida cara, a
[regra de domínio](../produto/REGRAS_DE_DOMINIO.md#dívida) manda quitar antes. Um destino
chamado `Aporte` embutiria no mapa uma conclusão que o próprio produto contradiz.

`Sobra` nomeia o **insumo** — o número que a pessoa já usa nessa frase, "quanto sobrou esse mês" —
e deixa a conclusão para o conteúdo. É a mesma disciplina de nomear o que é medido, e não o que se
deseja.

## Onde cada coisa vai

Mesmo vocabulário de fate da tabela mais abaixo.

| Superfície | Fate | Novo lar | Razão |
|---|---|---|---|
| `/hoje` (o destino) | **dividir** | `Mês` + `Patrimônio` + `Sobra` | Feed não é lugar |
| `/hoje/atividade` (drawer) | **manter** | drawer, acionado do `Mês` | O argumento da sala vazia continua valendo |
| `/carteira/*` | **mover** | `/patrimonio/*` | Muda o nome do destino; a sub-árvore fica inteira |
| `/estrategia/aporte` (Quick Invest) | **fundir** | `/sobra` | Era a ponte sem o lado do caixa; agora tem os dois |
| `/estrategia/metas` | **mover** | `/voce/objetivos` | **Declarar** um objetivo é armar a estratégia; **ler** a distância até ele é leitura de sobra e de patrimônio. A declaração tem uma casa, a leitura aparece nas duas |
| `/estrategia/projecao` | **mover** | `/patrimonio/projecao` | "Aportando assim, onde eu chego" é pergunta de patrimônio. Continua alcançável de `/sobra` como consequência do aporte escolhido |
| `/estrategia/renda-fixa` | **mover** | `/descobrir/renda-fixa` | Comparar títulos à venda é descoberta. Sem isso, metade das aplicações do produto não tinha porta de entrada |
| `/estrategia` (o destino) | **excluir** | dissolvido | Sem aporte, meta e projeção, sobra o desvio — que é leitura de patrimônio |
| `/descobrir/*` | **manter** | — | Continua respondendo uma pergunta só, agora cobrindo renda fixa também |
| `/voce/*` | **manter** | — | Ganha `Objetivos` como eixo: como invisto · para onde vou · como o produto age · meus dados |
| `/ativo/:ticker` | **manter** | — | Camada, e canal de aquisição |
| — | **novo** | `/mes` | Linha do tempo: salário previsto/recebido, contas a vencer, gastos lançados, sobra projetada em faixa |
| — | **novo** | `/mes/lancar` | Escrita do caixa, separada da leitura — mesma disciplina de `/carteira/editar` |
| — | **novo** | `/mes/dividas` | Saldo, taxa, e a comparação com o que a carteira rende |

### A forma de cada destino

Cinco destinos, e o que cada um abre. Nenhum subnav passa de quatro entradas: seis pares não são
hierarquia, são uma lista.

| Destino | Subnav | Por quê assim |
|---|---|---|
| `/mes` | — | Uma tela só, em ordem de importância: veredito, atenção, a vencer, o mês, o que mudou |
| `/sobra` | A ordem · Aporte · Alocação × meta | Os **três passos de uma decisão só**. Tinha seis, e duas não eram sobra |
| `/patrimonio` | Resumo · Composição · Desempenho · Projeção, + **Movimento** (Posições · Encerradas · Proventos) | Movimento agrupa três leituras do **mesmo** razão — o agrupamento diz uma verdade da arquitetura |
| `/descobrir` | Oportunidades · Quedas · Renda fixa · Comparar | Variável e fixa, agora as duas |
| `/voce` | Preferências · Objetivos · Alertas · Indicação · Conta e dados | Área de conta: lista plana é o padrão natural. O eixo que faltava era `Objetivos` |

Toda URL que saiu de casa continua resolvendo por redirect, num salto só — link salvo é contrato,
e `app.routes.server.spec.ts` cobra isso pelo nome.

**Saldo:** cinco destinos continuam cinco. Um sai (`Estratégia`), um entra (`Mês`), um é renomeado
(`Carteira` → `Patrimônio`), e a ponte deixa de ser sub-rota para ser destino.

## O risco que esta IA cria, declarado

Quem só investe e não quer lançar gasto nenhum abre o app e cai numa tela vazia. É o modo de falha
mais provável desta estrutura, e o mais fácil de não enxergar projetando para o caso feliz.

A mitigação não é uma preferência a mais: é **derivar o destino inicial**, do mesmo jeito que o
passo de onboarding já é derivado. Sem lançamento de caixa e com carteira, a porta é `Patrimônio`;
com caixa, é `Mês`. Um contador de "já usou o caixa?" criaria segunda verdade — a pergunta se
responde com o que existe no razão do caixa.

O que **não** vale fazer: pedir na entrada que a pessoa escolha um perfil. A visão decidiu que o
produto atende amplo e **deriva por dentro**, e uma tela de "você é investidor ou quer controlar
gastos?" é exatamente a presunção que ela recusa.

## O que fica pendente desta decisão

- **Wireframe da `Sobra` — feito** (2026-09-07), em [WIREFRAMES](WIREFRAMES.md#n1-sobra--a-ponte).
  É o portão da Fase 3, e ele traz um critério de aceite: se em algum estado a tela voltar a
  **pedir** o valor do aporte a quem tem caixa lançado, a ponte não está construída. Fica em
  aberto de propósito a **reserva de emergência** — não há decisão de produto sobre quantos meses,
  contra qual base, e antes ou depois da dívida cara.
- **Wireframe da linha do tempo do mês — feito** (2026-09-07), em
  [WIREFRAMES](WIREFRAMES.md#n2-mes--a-linha-do-tempo). Ele resolve o risco de `/mes` e `/sobra`
  virarem dois resumos rivais: a cifra grande de `/mes` é **fato** (livre agora) e a de `/sobra` é
  **projeção** (piso da sobra), e a diferença entre as duas é exatamente a estimativa de gasto
  variável — o que dá uma frase que liga as telas sem repetir nada.
- **Vocabulário do caixa — decidido** (2026-09-07), em
  [DESIGN-SYSTEM](DESIGN-SYSTEM.md#o-vocabulário-do-caixa--decidido-ainda-não-declarado). Não
  entrou em `vocabulary.ts` de propósito: vocabulário sem consumidor é pior que vocabulário nenhum,
  e a entrada acompanha a primeira tela que o usa. O tipo de dívida **não** carrega se ela é cara —
  isso é derivado da taxa, porque a regra manda classificar por custo, não por instrumento.
- **`provento` no caixa é decisão de domínio pendente**, e bloqueia `cashflow/`: provento
  creditado é entrada de caixa **e** lançamento do razão, e sem regra o mesmo dinheiro conta duas
  vezes — inflando a renda do mês e a sobra junto.
- **Mobile**: a barra inferior recebe os mesmos cinco. `Sobra` é o caso de uso mais móvel do
  produto — decidir o aporte é coisa de sofá, não de mesa.
- **URLs antigas** viram redirect, como na transição anterior.

---
# Princípios que sustentam os cinco

## O agrupamento é a pergunta, não a topologia do backend

O agrupamento antigo seguia o backend (Mercado = o que vem do scan; Meus Ativos = o que está no
`PortfolioPosition`). O atual segue **a pergunta que a pessoa tem na cabeça ao abrir o app**:

| Pergunta | Destino |
|---|---|
| "Como está meu mês, e o que vence?" | **Mês** |
| "O que faço com o que sobrou?" | **Sobra** |
| "Como está meu patrimônio?" | **Patrimônio** |
| "O que eu poderia comprar?" | **Descobrir** |
| "Este ativo específico — vale?" | **Ativo** (camada, não destino) |
| "Quero mudar como o app me trata" | **Você** |

Cinco destinos. O limite não é estético: acima de cinco, a pessoa deixa de manter o mapa na
cabeça e volta a caçar features.

### Por que Atividade é drawer e não destino

O volume real é baixo por decisão de produto: `whats-new` devolve **até 5 linhas**, alertas do
dashboard são **agrupados com teto de 4**, e o resumo de oportunidades é um push por cadência
configurada. Uma "central de notificações" como quinto destino seria uma sala vazia. Vira drawer
acionado do Mês, com os três grupos do briefing (Agora / Hoje / Informativo), e as
linhas de maior peso continuam aparecendo em Hoje.

### Por que Renda Fixa não é destino próprio

RF aparece em três papéis diferentes e cada um pertence a um lugar distinto:
posição que compõe patrimônio → **Patrimônio**; cadastro → **Patrimônio → Editar**;
escolha entre títulos e comparação com bolsa → **Descobrir → Renda fixa**.
Um destino "Renda Fixa" forçaria os três a coabitar, e o efeito seria fazer RF parecer uma página
de ação.

## Progressive disclosure — os 4 níveis, por tela

O briefing §3 pede quatro níveis. Aplicados:

| Tela | N1 — essencial | N2 — contexto | N3 — detalhe | N4 — técnico |
|---|---|---|---|---|
| **Mês** | livre agora, o que vence, veredito do mês | 2–3 motivos do veredito, feed do que mudou | link para a tela dona de cada assunto | — |
| **Sobra** | a sobra em faixa + o próximo passo da cascata | dívida cara, reserva, aporte | a ordem inteira, com o porquê de cada passo | taxa de virada, base da estimativa |
| **Patrimônio** | valor, rentabilidade, alocação vs meta | saúde nas 4 dimensões, maior concentração | composição/desempenho/proventos | posições, IR, prejuízo a compensar |
| **Ativo** | preço, variação, score, veredito em 1 frase | margem de segurança, gráfico com preço justo | valuation por método, fundamentos, técnica, proventos | insumos do DCF, SMA/RSI, anos de provento, completude |
| **Descobrir** | por que apareceu (1 frase) + score | queda %, MS, DY | diagnóstico completo em drawer | breakdown do score por dimensão |
| **Renda fixa** | rende X% do CDI | proteção contra inflação, liquidez, risco | taxa líquida, IR por faixa, equivalência bruta | fórmula e insumos |

O nível 4 aparece por ação explícita ("ver como calculamos") e é o que o
`detail_level: Avançado` traz para cima por padrão.

## Regras de navegação contextual (briefing §33)

1. Toda lista de ativos leva a `/ativo/:ticker` **preservando a origem** (breadcrumb
   "Oportunidades → PETR4", voltar retorna à lista com filtros e scroll intactos).
2. `/ativo/:ticker` sempre oferece, sem sair da tela: comparar, criar alerta,
   adicionar/editar posição, ver a queda (se houver), ver por que o score é esse.
3. Todo insight (Mês, Sobra, Descobrir) tem exatamente uma ação primária que leva à tela onde a
   decisão se resolve — nunca ao menu.
4. Filtro e recorte vivem na rota (parâmetro de consulta), não em estado local: voltar não perde
   o recorte, e o mesmo endereço leva ao mesmo lugar.
5. Ordenação e colunas de lista ficam no aparelho; não viram preferência de servidor.

