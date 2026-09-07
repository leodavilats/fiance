# Arquitetura de informação

> **Duas IAs vivem neste arquivo.** A de baixo — cinco destinos por intenção — é a que **está
> construída** hoje e continua sendo a referência de qualquer tela existente. A de cima é a
> **decisão para a transformação** (caixa + investimento), tomada em 2026-09-06, e nada dela está
> implementado. Quando a Fase 3 do
> [ROADMAP](../produto/ROADMAP.md) terminar, a de baixo sai daqui.

---

# A IA nova: o mês entra, e o "Hoje" sai

## O problema que a estrutura atual não resolve

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
| `/estrategia/metas` | **mover** | `/sobra/metas` | A meta é a régua que produz o desvio que a sobra preenche — fica onde é usada, não onde é configurada |
| `/estrategia/projecao` | **mover** | `/sobra/projecao` | Projeção de renda passiva é a consequência do aporte |
| `/estrategia/renda-fixa` | **mover** | `/sobra/renda-fixa` | "Onde ponho renda" é a mesma decisão |
| `/estrategia` (o destino) | **excluir** | dissolvido | Sem aporte, meta e projeção, sobra o desvio — que é leitura de patrimônio |
| `/descobrir/*` | **manter** | — | Continua respondendo uma pergunta só |
| `/voce/*` | **manter** | — | — |
| `/ativo/:ticker` | **manter** | — | Camada, e canal de aquisição |
| — | **novo** | `/mes` | Linha do tempo: salário previsto/recebido, contas a vencer, gastos lançados, sobra projetada em faixa |
| — | **novo** | `/mes/lancar` | Escrita do caixa, separada da leitura — mesma disciplina de `/carteira/editar` |
| — | **novo** | `/mes/dividas` | Saldo, taxa, e a comparação com o que a carteira rende |

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
  [DESIGN-SYSTEM](DESIGN-SYSTEM.md#o-vocabulário-do-caixa--decidido-ainda-não-gerado). Não entrou
  em `product-rules.json` de propósito: vocabulário gerado sem consumidor é pior que não gerado, e
  a entrada acompanha a primeira tela que o usa. O tipo de dívida **não** carrega se ela é cara —
  isso é derivado da taxa, porque a regra manda classificar por custo, não por instrumento.
- **`provento` no caixa é decisão de domínio pendente**, e bloqueia `cashflow/`: provento
  creditado é entrada de caixa **e** lançamento do razão, e sem regra o mesmo dinheiro conta duas
  vezes — inflando a renda do mês e a sobra junto.
- **Mobile**: a barra inferior recebe os mesmos cinco. `Sobra` é o caso de uso mais móvel do
  produto — decidir o aporte é coisa de sofá, não de mesa.
- **URLs antigas** viram redirect, como na transição anterior.

---

# A IA construída hoje — cinco destinos por intenção

> Decorre dos achados 1–6 da auditoria de UX (documento removido em 2026-08-28; ver
> [CHANGELOG](../CHANGELOG.md)). É o que está **no ar**; a decisão acima a substitui quando a
> Fase 3 terminar.

## Princípio de agrupamento

O agrupamento atual segue a topologia do backend (Mercado = o que vem do scan; Meus Ativos = o
que está no `PortfolioPosition`). O novo agrupamento segue **a pergunta que o usuário tem na
cabeça ao abrir o app**:

| Pergunta | Destino |
|---|---|
| "O que mudou e o que merece minha atenção?" | **Hoje** |
| "Como está meu patrimônio?" | **Carteira** |
| "O que eu poderia comprar?" | **Descobrir** |
| "O que eu faço com o próximo aporte?" | **Estratégia** |
| "Este ativo específico — vale?" | **Ativo** (camada, não destino) |
| "Quero mudar como o app me trata" | **Você** |

Cinco destinos. O limite não é estético: acima de cinco, o usuário deixa de manter o mapa na
cabeça e volta a caçar features.

## Mapa de navegação

```
┌─ Busca global (⌘K desktop / campo no topo de Hoje no mobile) ────────────┐
│  ativos · setores · telas                                                │
└──────────────────────────────────────────────────────────────────────────┘

HOJE                    /hoje
  patrimônio + variação do período
  veredito de saúde da carteira (1 frase + 2–3 motivos)
  o que mudou  (feed com ação por linha)
  próxima ação (o maior gap / a melhor oportunidade)
  └ camada: Atividade (drawer)   /hoje/atividade
      Agora · Hoje · Informativo   ← alertas disparados + eventos

CARTEIRA                /carteira                    (resumo)
  /carteira/composicao      classes · setores · concentração
  /carteira/desempenho      carteira × CDI × IBOV, período selecionável
  /carteira/proventos       recebidos × estimado, linha do tempo
  /carteira/posicoes        tabela densa (ações/FIIs/BDRs/ETFs + RF)
  /carteira/encerradas      operações fechadas, IR, prejuízo a compensar
  /carteira/editar          cadastro (escrita) — posições e renda fixa

DESCOBRIR               /descobrir                   (radar)
  /descobrir/oportunidades  categorizado, não lista única
  /descobrir/quedas         dip scanner com diagnóstico em 3 classes
  /descobrir/comparar       comparador de até 4 ativos

ESTRATÉGIA              /estrategia                  (onde estou × onde deveria estar)
  /estrategia/aporte        Quick Invest — "recebi dinheiro, onde ponho"
  /estrategia/metas         metas de alocação, renda passiva, prazo
  /estrategia/renda-fixa    simulador de RF + RF × bolsa
  /estrategia/projecao      projeção de renda passiva / aportes

ATIVO                   /ativo/:ticker               (camada de research)
  resumo · gráfico · valuation · fundamentos · técnica · proventos · decisão
  ações: comparar · alertar · adicionar/editar posição · ver queda

VOCÊ                    /voce
  /voce/preferencias        nível de detalhe · perfil de risco · yields · benchmark padrão
  /voce/alertas            CRUD de alertas de preço + canais
  /voce/conta              conta, tema, sair, dados e limitações
```

### Por que Atividade é drawer e não destino

O volume real é baixo por decisão de produto: `whats-new` devolve **até 5 linhas**, alertas do
dashboard são **agrupados com teto de 4**, e o resumo de oportunidades é um push por cadência
configurada. Uma "central de notificações" como quinto destino seria uma sala vazia. Vira drawer
acionado pelo sino no header, com os três grupos do briefing (Agora / Hoje / Informativo), e as
linhas de maior peso continuam aparecendo em Hoje.

### Por que Renda Fixa não é destino próprio

RF aparece em três papéis diferentes e cada um pertence a um lugar distinto:
posição que compõe patrimônio → **Carteira**; cadastro → **Carteira → Editar**;
escolha entre títulos e comparação com bolsa → **Estratégia → Renda fixa**.
Um destino "Renda Fixa" forçaria os três a coabitar, e é o erro que o briefing §13 pede para
evitar (fazer RF parecer uma página de ação).

## Destino de cada superfície atual

`manter` = existe e continua · `mover` = mesmo conteúdo, outro lugar · `fundir` = junta com outro ·
`dividir` = quebra em dois · `reviver` = existe em código e volta a ser alcançável ·
`excluir` = sai do produto

| Superfície atual | Fate | Novo lar | Razão |
|---|---|---|---|
| `/dashboard` — "O que mudou" | **manter** (promover) | `/hoje` — bloco central | É o melhor padrão do produto: linha + ação. Vira o modelo de todo insight |
| `/dashboard` — resumo de patrimônio | **manter** | `/hoje` — nível 1 | Pergunta nº 1 |
| `/dashboard` — progresso da meta mensal | **fundir** | `/hoje` (linha) + `/estrategia/metas` (detalhe) | Uma frase basta na home; a planilha vive em Metas |
| `/dashboard` — alertas | **mover** | drawer Atividade + linha em `/hoje` quando é "Agora" | Alerta é evento, não bloco permanente |
| `/dashboard` — saúde da carteira | **manter** (reformular) | `/hoje` — nível 1 (veredito) → `/carteira` (as 4 dimensões) | Hoje mostra o julgamento; Carteira mostra a conta |
| `/dashboard` — oportunidades | **fundir** | `/hoje` (top 2) → `/descobrir/oportunidades` | Home mostra as melhores, não a parede |
| `/dashboard` — sinais de venda | **fundir** | `/hoje` (linha) → `/estrategia` (posições para revisar) | Vender é decisão de estratégia |
| `/dashboard` — benchmark (Carteira × IBOV) | **fundir** com evolução | `/carteira/desempenho`, resumo em `/hoje` | Dois gráficos respondendo quase a mesma pergunta (achado #36) |
| `/dashboard` — evolução do patrimônio | **fundir** com benchmark | idem | idem |
| `/dashboard` — tabela de posições | **mover** | `/carteira/posicoes` | Tabela densa não é conteúdo de home |
| `/dashboard` — "Bem-vindo ao fiance" | **excluir** | substituído por onboarding real | Três instruções em texto não são um caminho |
| `/assets` — resumo (4 stats) | **manter** | `/carteira` | — |
| `/assets` — composição (pizza ativo/setor) | **mover** | `/carteira/composicao` (+ concentração) | Ganha a dimensão que faltava: concentração |
| `/assets` — renda fixa marcada a mercado | **mover** | `/carteira/posicoes` (integrada) + `/carteira` (linha de classe) | RF deixa de ser bloco anexo e passa a ser classe de ativo par |
| `/assets` — tabela de posições | **mover** | `/carteira/posicoes` | Vira a tabela profissional única do produto |
| `/assets` — proventos recebidos | **mover** | `/carteira/proventos` | Tarefa mensal ganha lugar próprio, sai do caminho diário |
| `/assets` — operações encerradas + IR | **mover** | `/carteira/encerradas` | idem |
| `/assets/cadastro` | **manter** | `/carteira/editar` | Separação leitura/escrita foi acerto da auditoria anterior — preservada |
| `/market` (o hub) | **excluir** | dissolvido | O nó do problema: agrupava por origem do dado |
| `/market` → Oportunidades → Lista | **mover** | `/descobrir/oportunidades` | Ganha URL e categorias |
| `/market` → Oportunidades → Em queda | **mover** | `/descobrir/quedas` | Deixa de ser sub-modo de sub-tab |
| `/market` → Rebalanceamento | **fundir** | `/estrategia` (plano) | Rebalancear é executar estratégia |
| `/market` → Rebalanceamento → Sugestões seguidas | **mover** | `/estrategia` (bloco "resultado do que você seguiu") | Fecha o ciclo no lugar onde a sugestão nasceu |
| `/market` → Ferramentas → Analisar Ativo | **fundir** | `/ativo/:ticker` | "Analisar" era um destino sem sujeito; agora o sujeito é o ativo |
| `/market` → Ferramentas → Comparar Ativos | **mover** | `/descobrir/comparar` | — |
| `/market` → Ferramentas → Simulador de RF | **mover** | `/estrategia/renda-fixa` | — |
| `/market` → Ferramentas → RF × Bolsa | **fundir** | `/estrategia/renda-fixa` (mesma tela, duas perguntas) | São a mesma decisão: onde ponho renda |
| `/market` → Ferramentas → Simulador de Aportes | **mover** | `/estrategia/projecao` | — |
| `strategy.component` (inacessível) | **reviver** + **dividir** | `/estrategia` (gaps, ajustes, sugestões, projetada) + `/estrategia/aporte` (Quick Invest) + `/ativo/:ticker` (a análise detalhada que ele duplicava) | Achado #1 — P0. 1092 linhas em uma tela viram três com propósito |
| `dip.component` (inacessível) | **excluir** | — | Superseded por `dip-scanner` + `dip-analysis-modal`; renderiza IA e notícias sem backend |
| `/config` — metas de alocação e renda passiva | **mover** | `/estrategia/metas` | Meta não é configuração: é insumo de decisão, e precisa ficar ao lado do gap que ela gera |
| `/config` — metas por setor | **mover** | `/estrategia/metas` | idem |
| `/config` — perfil de risco, yields, preferidos, excluídos | **manter** | `/voce/preferencias` (+ `detail_level` novo) | Calibram o motor — ficam em preferências, mas ganham explicação do efeito |
| `/config` — alertas de preço | **mover** | `/voce/alertas` | — |
| `/config` — aviso de push | **manter** | `/voce/alertas` | — |
| `/config` — limpar cache | **mover** | `/voce/conta` (bloco "dados e limitações", junto de proveniência) | Sai do caminho principal; ganha companhia lógica |
| `skeleton` component | **reviver** | design system | Existe, funciona, nunca foi usado |
| `GET /data-quality` (sem UI) | **novo consumo** | `/voce/conta` → "qualidade dos dados" | Instrumentação de honestidade já pronta no backend |

**Saldo:** 6 rotas web → 5 destinos com 19 rotas reais e endereçáveis. Nenhuma feature perdida;
duas revividas (Estratégia, Quick Invest web); uma tela excluída (`dip.component`); um hub
dissolvido (`/market`).

## Mobile — hierarquia própria, não compressão

Bottom nav de 5, como o briefing §19 recomenda:

| Aba | Rota | O que é no celular |
|---|---|---|
| **Hoje** | `/hoje` | Patrimônio + veredito + feed. A tela de 10 segundos |
| **Carteira** | `/carteira` | Resumo + segmented control (Composição · Desempenho · Proventos · Posições). Sub-telas empilhadas, não tabs aninhadas |
| **Descobrir** | `/descobrir` | Lista com filtro em bottom sheet (padrão que o mobile já acertou em `_FiltersSheet`) |
| **Estratégia** | `/estrategia` | Gaps + "o maior gap é X" + botão Aporte. Quick Invest é o caso de uso mais móvel do produto |
| **Mais** | `/voce` | Preferências, alertas, conta |

Diferenças **deliberadas** em relação ao desktop (não lacunas):

| Superfície | Desktop | Mobile | Por quê |
|---|---|---|---|
| Detalhe de ativo | rota `/ativo/:ticker` em split view | bottom sheet expansível → tela cheia ao rolar | Comparar vários ativos é gesto de mesa; no celular é leitura sequencial |
| `/carteira/posicoes` | tabela densa com colunas configuráveis | lista inteligente agrupada por classe, ordenação em sheet | Tabela de 8 colunas não existe em 390px |
| `/carteira/encerradas` (IR) | tabela completa | resumo + lista; exportação por compartilhamento do sistema | Apuração de IR é tarefa de desktop |
| `/estrategia/projecao` | gráfico + tabela de cenários | 3 cenários em cards, gráfico simplificado | — |
| `/descobrir/comparar` | 4 ativos lado a lado | 2 ativos, troca por sheet | Largura |
| Busca global | `⌘K` overlay | campo fixo no topo de Hoje | Sem teclado físico |

Assimetrias que **deixam de existir**: Estratégia (hoje em lugar nenhum) passa a existir nas
duas; RF × Bolsa chega ao mobile; Quick Invest chega ao web.
Assimetria que **permanece declarada**: push exige o app instalado — o web continua sinalizando
isso em `/voce/alertas`.

## Progressive disclosure — os 4 níveis, por tela

O briefing §3 pede quatro níveis. Aplicados:

| Tela | N1 — essencial | N2 — contexto | N3 — detalhe | N4 — técnico |
|---|---|---|---|---|
| **Hoje** | patrimônio, variação, veredito de saúde | 2–3 motivos do veredito, feed do que mudou | link para a tela dona de cada assunto | — |
| **Carteira** | valor, rentabilidade, alocação vs meta | saúde nas 4 dimensões, maior concentração | composição/desempenho/proventos | posições, IR, prejuízo a compensar |
| **Ativo** | preço, variação, score, veredito em 1 frase | margem de segurança, gráfico com preço justo | valuation por método, fundamentos, técnica, proventos | insumos do DCF, SMA/RSI, anos de provento, completude |
| **Descobrir** | por que apareceu (1 frase) + score | queda %, MS, DY | diagnóstico completo em drawer | breakdown do score por dimensão |
| **Estratégia** | maior gap + próxima ação | tabela atual/meta/gap | sugestões por categoria com razão | alocação projetada, custo/IR de ajuste |
| **Renda fixa** | rende X% do CDI | proteção contra inflação, liquidez, risco | taxa líquida, IR por faixa, equivalência bruta | fórmula e insumos |

O nível 4 aparece por ação explícita ("ver como calculamos") e é o que o
`detail_level: Avançado` traz para cima por padrão.

## Regras de navegação contextual (briefing §33)

1. Toda lista de ativos leva a `/ativo/:ticker` **preservando a origem** (breadcrumb
   "Oportunidades → PETR4", voltar retorna à lista com filtros e scroll intactos).
2. `/ativo/:ticker` sempre oferece, sem sair da tela: comparar, criar alerta,
   adicionar/editar posição, ver a queda (se houver), ver por que o score é esse.
3. Todo insight (Hoje, Estratégia, Descobrir) tem exatamente uma ação primária que leva à tela
   onde a decisão se resolve — nunca ao menu.
4. Filtros e período vivem na URL (query params), não em `signal`. Recarregar não perde estado;
   o link é compartilhável.
5. Tabelas e listas guardam ordenação/colunas por usuário localmente; não viram preferência de
   servidor.

## Checkpoint antes da Fase 5

Esta IA implica, em ordem:

1. **Reescrever o shell e o roteamento** do web (6 → 19 rotas) e do mobile (4 → 5 branches).
2. **Criar `/ativo/:ticker`** — tela nova, montada com endpoints existentes (`/asset/{symbol}`,
   `/asset/{symbol}/dip-analysis`, `/compare`, `/alerts`, `/portfolio/position`).
3. **Reviver Estratégia** e dividi-la em três telas.
4. **Dissolver `/market`** e redistribuir 8 subcomponentes.
5. **Mover metas de Configurações para Estratégia** — a mudança de IA mais contraintuitiva
   desta proposta, e a que mais muda o produto: hoje a meta é um formulário; ali ela é a régua
   contra a qual o gap é medido.

Duas coisas exigem contrato novo e podem ser feitas em paralelo:
`detail_level` em `/preferences` (achado #7) e um marcador de onboarding concluído (#32).
