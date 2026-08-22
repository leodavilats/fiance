# Fase 2 — Auditoria de UX/UI

> Base factual: [00-DISCOVERY.md](00-DISCOVERY.md). Todo achado aqui tem evidência de código.
> Prioridade: **P0** impede uso · **P1** prejudica muito · **P2** melhoria importante ·
> **P3** refinamento.

## Leitura de uma linha

O fiance tem um backend de qualidade incomum — valuation roteado por tipo de ativo, score com
`data_completeness`, IR com compensação de prejuízo, RF marcada a mercado, proveniência de dado.
**A interface não está à altura disso.** O produto não sofre de falta de informação: sofre de
falta de *hierarquia*. Hoje as telas são depósitos de blocos em ordem de implementação, e a
feature mais estratégica do sistema (Estratégia + Quick Invest no web) está literalmente
inalcançável. O problema é estrutural, não cosmético.

## Tabela de achados

### Navegação e arquitetura da informação

| # | Área | Problema | Impacto | Prio | Solução |
|---|---|---|---|---|---|
| 1 | Navegação | `strategy.component` (1092 linhas) e `dip.component` (485) não têm rota nem uso. Estratégia recomendada, Ajustes necessários, Alocação projetada, Posições para revisar e **Quick Invest** são inacessíveis no web; Estratégia não existe em nenhuma plataforma | A feature que responde "o que eu faço agora" — o núcleo da proposta do produto — não pode ser usada. `GET /strategy` e `POST /quick-invest` rodam para ninguém | **P0** | Estratégia vira destino de primeira classe (`/estrategia`), Quick Invest vira `/estrategia/aporte`. `dip.component` é excluído (superseded por `dip-scanner` + `dip-analysis-modal`, e renderiza IA/notícias que não existem mais no backend) |
| 2 | Navegação | 4 itens de menu para ~20 features. `/market` acumula 3 tabs × até 5 sub-tabs = 8 destinos em 2 níveis, **nenhum com URL** (`activeTab`/`oppMode`/`toolMode` são `signal`) | Sem deep link, sem voltar, sem compartilhar, sem restaurar após F5. "Onde estava aquela comparação?" não tem resposta | **P0** | 5 destinos por intenção + sub-rotas reais na URL (ver [02-INFORMATION-ARCHITECTURE.md](02-INFORMATION-ARCHITECTURE.md)) |
| 3 | Arq. informação | Agrupamento por origem técnica, não por intenção: "Mercado → Ferramentas → Simulador de RF" e "Mercado → Rebalanceamento" são decisões de estratégia; "Meus Ativos" mistura análise (leitura diária) com proventos e IR (tarefas mensais) | O usuário precisa saber a topologia do backend para achar o que quer | **P0** | Reagrupar em Hoje / Carteira / Descobrir / Estratégia / Ativo |
| 4 | Navegação contextual | Não existe página de ativo. `PETR4` aparece em oportunidades, dip, carteira, comparador e estratégia — cada um com um subconjunto diferente de dados, nenhum navegável para "o ativo" | Não há lugar onde a análise de um ativo esteja completa. O usuário reabre o mesmo ticker em 4 telas | **P0** | `/ativo/:ticker` como camada acessível de qualquer lista, com ações contextuais (comparar, alerta, adicionar, ver queda) |
| 5 | Navegação | Busca global inexistente. `GET /universe/search` existe mas só como autocomplete de campo em 3 formulários | Para ver um ativo, o usuário precisa lembrar em qual tab existe um campo de busca | **P1** | Busca global (`⌘K` no desktop, campo fixo no mobile) com resultados categorizados: ativos, setores, telas |

### Hierarquia e densidade

| # | Área | Problema | Impacto | Prio | Solução |
|---|---|---|---|---|---|
| 6 | Dashboard | 10 blocos de peso visual igual em coluna única de 1180px, sem ordem de urgência. Patrimônio, meta, alertas, saúde, oportunidades, sinais de venda, benchmark, evolução e tabela de posições competem pelo mesmo nível | A pergunta "o que merece minha atenção agora?" exige rolar e comparar 10 blocos. É exatamente o "painel cheio de cards" que o produto não quer ser | **P0** | Home de decisão em 3 níveis: patrimônio + veredito de saúde (nível 1), feed "o que mudou" com ação (nível 2), tudo o mais atrás de link para a tela dona do assunto |
| 7 | Densidade | Nenhum controle de nível de detalhe. Todo usuário — primeiro dia ou cinco anos — recebe a mesma densidade | Iniciante se afoga; avançado precisa de 4 cliques para o que caberia numa tabela | **P1** | Preferência `detail_level` (Essencial / Completo / Avançado) governando densidade, nº de métricas e verbosidade. Requer campo novo em `PreferencesDb` (**mudança de contrato**) |
| 8 | Progressive disclosure | Existe em um único lugar (explicação da Saúde da carteira, expansível). O resto expõe tudo de uma vez: `/assets` mostra 8 colunas de RF + 8 de operações encerradas + 4 de proventos sem que nada esteja recolhido | Ruído permanente para dado consultado uma vez por mês | **P1** | Nível 1 sempre visível; nível 2+ em drawer/accordion/bottom sheet. Padrão único documentado no design system |
| 9 | Desktop | Container fixo `max-w-[1180px]`, `xl:`/`2xl:` nunca usados, nenhum layout master-detail. Em 1920px sobram ~700px de fundo decorativo | Telas de análise (oportunidades, dip, comparar) forçam ir-e-voltar onde caberia lista + detalhe lado a lado | **P1** | Shell responsivo até 1600px+, `xl:`/`2xl:` reais, split view lista/detalhe em Descobrir e Carteira → Posições |
| 10 | Tabelas | Tabelas com 8 colunas em `overflow-x` no mobile-web; nenhuma permite esconder/fixar coluna. A tabela de posições (`/assets`) já ordena, mas é a única | Avançado não consegue montar sua visão; mobile-web rola horizontalmente | **P2** | Componente de tabela único: ordenar, esconder coluna, fixar ticker, densidade, e degradação para lista no mobile |

### Cor, tipografia e sistema visual

| # | Área | Problema | Impacto | Prio | Solução |
|---|---|---|---|---|---|
| 11 | Cor | Nove famílias semânticas (`.v-*`, `.score-pill`, `.dip-*`, `.alert-*`, `.tag-*`, `.bar-*`, `.news-*`, `.cat-*`, `.active`) mapeiam todas para verde/amarelo/vermelho. Verde é simultaneamente cor de marca, de "positivo", de botão primário e de "boa oportunidade" | A cor perde poder de sinalizar: quando tudo é colorido, nada chama atenção. E é semanticamente errado no domínio — queda de preço em verde/vermelho trata matemática como julgamento (uma queda pode ser a oportunidade) | **P1** | Paleta com dois eixos separados: **direção** (variação numérica: alta/baixa, cor fria e discreta) e **estado** (julgamento do sistema: favorável/atenção/adverso/indeterminado). Marca deixa de ser verde-de-lucro |
| 12 | Cor | Cor é o único canal de informação. Score, veredito e diagnóstico de queda não têm forma, ícone ou texto redundante consistente | ~8% dos homens não distingue verde/vermelho e perde o significado inteiro | **P1** | Todo estado carrega cor + forma/ícone + rótulo textual. Regra de aceite no design system |
| 13 | Cor | Hexadecimais fixos duplicando tokens: `#4ade80`/`#fbbf24`/`#f87171` em `.dip-*` e `.dip-badge-*`; gradiente `#4ade80→#22d3ee` e texto `#0b0e14` na nav ativa | Light mode e temas futuros divergem por arquivo. `theme.dart` já precisa ser mantido em paralelo à mão | **P2** | Zero hex fora da camada de tokens; tokens gerados de uma fonte única para CSS e Dart |
| 14 | Tipografia | **Zero** `tabular-nums`/`font-variant-numeric` em todo o web. Inter proporcional em colunas de preço, percentual e patrimônio | Números desalinham verticalmente em toda tabela financeira do produto — o defeito tipográfico mais visível num app de investimento | **P1** | Token `--font-numeric` com `font-variant-numeric: tabular-nums` obrigatório em preço, %, R$, score, taxa e data |
| 15 | Tipografia | Nenhuma escala definida. Tamanhos escritos inline caso a caso: `text-[1.3rem]`, `text-[10px]`, `text-[11px]`, `text-2xl`, `text-lg`, `text-base` misturados sem regra; `font-size: 15px` no `body` | Hierarquia inconsistente entre telas; nenhum número é reconhecível em <1s por tamanho | **P1** | Escala tipográfica nomeada com papel semântico (`display-money`, `metric`, `metric-sm`, `label`, `body`, `caption`, `mono-ticker`) |
| 16 | Estética | Fundo com dois `radial-gradient` fixos + gradiente verde-ciano na nav ativa + `box-shadow` de 24px em painel | É exatamente a estética "dashboard genérico/gerado por IA" que o produto quer evitar; nada disso carrega informação | **P2** | Superfície sóbria por elevação de valor (não por sombra), gradiente eliminado, marca expressa por tipografia e ritmo |
| 17 | Consistência | Régua de score divergente: "Boa oportunidade" é verde no web e azul no mobile, apesar do comentário nos dois arquivos dizendo que devem andar juntos. `scoreBandFor`/`trendBasisLabel`/`consensusLabel` existem no Dart e não no TS | O mesmo ativo tem cor diferente em cada plataforma. A régua "única" já divergiu | **P1** | Bandas de score (limiar + cor + rótulo + ícone) num contrato único gerado para os três alvos; `score-ruler.ts` ganha paridade com o Dart |
| 18 | CSS morto | `.cat-renda`, `.cat-trade`, `.cat-caixa` (categorias removidas do domínio) e `.news-*` (feature sem backend) seguem no CSS global | Superfície de manutenção falsa; sugere features que não existem | **P3** | Remover na Fase 7 |

### Estados, feedback e confiança

| # | Área | Problema | Impacto | Prio | Solução |
|---|---|---|---|---|---|
| 19 | Estados | `SkeletonComponent` existe e nunca é usado; cada tela reimplementa skeleton inline. `GlobalLoaderComponent` cobre a navegação inteira após 150ms | Loading não reflete a estrutura do conteúdo; a tela "pisca" em vez de se preencher | **P1** | Skeleton por composição — o esqueleto tem a forma do bloco real. `global-loader` só para transição de rota fria |
| 20 | Estados | Erro cru no mobile em 6 pontos: `Text('Erro: $err')` em assets, config e market expõe exceção Dio | Quebra de confiança num produto financeiro; usuário não sabe se o dado está errado ou a rede caiu | **P1** | Estado de erro com causa em linguagem humana + ação de recuperação + preservação do dado antigo com marca de idade |
| 21 | Estados | "Dados parciais" não é estado projetado. O backend já distingue `data_completeness` e `market_data_stale`, e a UI trata como número comum na maior parte dos lugares | O produto tem a informação para ser honesto e desperdiça — o oposto do requisito de confiança | **P1** | Estado explícito de dado parcial/velho em todo componente numérico: valor + selo de idade/completude |
| 22 | Empty states | `EmptyStateComponent` é genérico (ícone + título + descrição) e a maioria dos vazios é `<p>Nenhum ... encontrado.</p>` sem CTA. O "Bem-vindo ao fiance" do dashboard são 3 instruções em texto mandando o usuário navegar sozinho | Primeiro acesso não tem caminho; carteira vazia não tem porta de entrada | **P1** | Cada vazio com causa + próximo passo executável no próprio bloco |
| 23 | Confiança | Proveniência existe no dashboard (idade da cotação, fonte do CDI) e não se propaga: preço justo, score e RF não dizem de onde vêm nem quando foram calculados fora dali | A metodologia é o diferencial do produto e fica invisível na hora da decisão | **P2** | Rodapé de proveniência padrão em todo componente de valuation/score: método, insumo, data, limitação |

### Acessibilidade

| # | Área | Problema | Impacto | Prio | Solução |
|---|---|---|---|---|---|
| 24 | A11y | 97 `<button>`, **1** `aria-label`, **2** `role`. Botões só-ícone (tema, perfil, tooltips) sem nome acessível — apenas `title` | Leitor de tela anuncia "botão" sem função. Produto inutilizável por teclado+leitor | **P1** | Nome acessível obrigatório em todo controle; `aria-*` como critério de aceite de componente |
| 25 | A11y | Tabs implementadas como `<button>` sem `role="tab"`/`aria-selected`/setas; `side-panel`/`panel-overlay` sem `role="dialog"`, sem focus trap, sem retorno de foco | Navegação por teclado se perde ao abrir painel; estado da tab não é anunciado | **P1** | Tabs e drawers do design system com semântica e gestão de foco embutidas |
| 26 | A11y | Nenhum estilo de foco definido além do `outline` de input; alvos de toque abaixo de 44px em vários lugares (`text-[10px]` na bottom nav, tooltips, botões de ícone 36px) | Toque impreciso no mobile; foco invisível no desktop | **P2** | Token de foco visível único; mínimo 44×44 de área de toque |
| 27 | A11y | `font-size: 15px` no `body` com `text-[10px]`/`text-[11px]` em rótulos e nav | Ilegível para baixa visão; abaixo do mínimo prático | **P2** | Base 16px; mínimo 12px para texto de apoio, 11px só em selo com redundância |

### Microcopy e UX de decisão

| # | Área | Problema | Impacto | Prio | Solução |
|---|---|---|---|---|---|
| 28 | Microcopy | Vocabulário de módulo, não de intenção: "Dashboard", "Visão Geral", "Análise Detalhada", "Ferramentas", "Simulador de RF", "RF x Bolsa", "Rebalanceamento", "Mercado". Tagline repetida em toda tela: "Sistema de gestão de ativos — descubra o que comprar, manter ou vender" | O menu descreve o sistema em vez de descrever o que o usuário quer fazer | **P2** | Reescrita completa por intenção: "Hoje", "Minha carteira", "Descobrir", "Estratégia", "Ver por que esse score é alto", "Entender esta queda" |
| 29 | Microcopy | Registro inconsistente: "Duas formas de olhar pro mesmo mercado:" (coloquial) ao lado de "Executar análise" e "Alocação necessária" (burocrático) | Produto soa montado por várias mãos — o oposto de "equipe sênior" | **P2** | Guia de tom único: claro, direto, sem jargão não explicado, sem coloquialismo |
| 30 | UX de decisão | Insights não têm estrutura comum. `whats-new` já traz linha + ação (o melhor padrão do produto hoje) e ele não se repete: alertas, oportunidades, dip e saúde cada um inventa o seu formato, e alguns não têm ação nenhuma | O usuário aprende a ler o produto cinco vezes | **P1** | Padrão único **o que aconteceu → por que importa → o que sustenta → o que fazer**, como componente (`Insight` / `DecisionSummary`), aplicado em todo insight do produto |
| 31 | Dados financeiros | Números soltos sem referência: "P/L 7,4", "DY 6,2%", "Score 87" aparecem sem contexto comparativo em quase todo lugar | "Isso é bom ou ruim?" fica sem resposta — e o backend frequentemente tem o insumo para responder | **P2** | Toda métrica de destaque com âncora (meta do usuário, média do setor via `/sectors-summary`, CDI, histórico) **quando o dado existir**; sem dado, dizer que não há |
| 32 | Onboarding | Não existe. Primeiro acesso cai no dashboard vazio com 3 instruções em texto. Perfil de risco, metas e yields desejados — que governam score e sugestões — ficam escondidos em Configurações | O usuário recebe score e sugestão calibrados por defaults que ele nunca viu | **P1** | Onboarding de 3 passos (experiência → objetivo → primeira posição), tudo mais adiável, com escrita nos endpoints que já existem (`/preferences`, `/goals`, `/portfolio/position`) |

### Mobile

| # | Área | Problema | Impacto | Prio | Solução |
|---|---|---|---|---|---|
| 33 | Mobile | Espelha a topologia do desktop (mesmas 4 abas, mesmas 3 tabs de Mercado) em vez da hierarquia de uso móvel. `assets_screen.dart` tem 1231 linhas e `dashboard_screen.dart` 1214 — as duas telas mais longas do produto são as duas mais roladas no celular | O caso de uso mais móvel (conferir patrimônio em 10s, decidir aporte) exige a mesma rolagem do desktop | **P1** | Redesenho próprio: Hoje enxuto, bottom nav de 5, bottom sheet como camada padrão de detalhe, listas em vez de tabelas |
| 34 | Mobile | Bons padrões já existem e não são usados de forma consistente: `_FiltersSheet` (bottom sheet de filtro em Oportunidades) e `SegmentedButton` (composição em Meus Ativos) são melhores que os equivalentes web, mas convivem com `DataTable` (`_CompareTable`) e formulários longos inline | Inconsistência interna da própria plataforma | **P2** | Elevar filtro-em-sheet e segmented control a padrão; `DataTable` sai do mobile |
| 35 | Mobile | RF × Bolsa ausente; Estratégia ausente (não existe em lugar nenhum); Renda fixa tem tela própria no mobile e é sub-seção de cadastro no web | Paridade declarada não corresponde ao código | **P2** | Redefinir explicitamente o que é paridade e o que é decisão de plataforma, em [02](02-INFORMATION-ARCHITECTURE.md) |

### Gráficos e motion

| # | Área | Problema | Impacto | Prio | Solução |
|---|---|---|---|---|---|
| 36 | Gráficos | Nenhum gráfico declara a pergunta que responde. Patrimônio e Benchmark ocupam dois blocos separados no dashboard respondendo perguntas quase idênticas ("como evoluí?" / "evoluí mais que o índice?") | Dois gráficos onde um comparativo resolve; espaço nobre gasto em redundância | **P2** | Cada gráfico com pergunta explícita no título; patrimônio e benchmark fundidos numa série com linha de referência |
| 37 | Gráficos | 11 tokens `--series-*` para gráficos que raramente passam de 4 séries; composição por setor pode gerar mais categorias que cores distinguíveis | Cores de série sem hierarquia — decorativas | **P3** | Paleta categórica de 6 + agrupamento "Outros"; séries de comparação em papéis fixos (carteira / benchmark / meta) |
| 38 | Motion | Só `spin`, `fadeIn`, `slideIn` e `animate-pulse`. Nenhuma transição em mudança de tab, filtro, período ou expansão de análise | Trocas de estado acontecem por corte seco; a interface parece travar, não parece rápida | **P3** | Tokens de motion (120/180/240ms) aplicados só a mudança de estado que precisa ser compreendida |

## Resumo por prioridade

| Prio | Qtd | Natureza |
|---|---|---|
| **P0** | 4 | Feature inacessível (1), navegação sem URL (2), agrupamento por técnica (3), ausência de página de ativo (4), home sem hierarquia (6) |
| **P1** | 17 | Densidade, disclosure, desktop, cor semântica, tipografia numérica, régua divergente, estados de loading/erro/parcial, empty states, a11y, padrão de decisão, onboarding, mobile |
| **P2** | 12 | Tabelas, tokens hardcoded, estética, proveniência, foco/toque, microcopy, contexto numérico, paridade, gráficos |
| **P3** | 3 | CSS morto, paleta de séries, motion |

## Classificação por tipo de mudança (requisito §44 do briefing)

**Só frontend (UX/UI):** achados 1–6, 8–10, 11–19, 22–31, 33–38. É a maioria — o backend já
devolve o que a nova interface precisa.

**Mudança de contrato de API:**
- #7 — `detail_level` (Essencial/Completo/Avançado) em `PreferencesDb` + `GET/PUT /preferences`.
- #32 — onboarding precisa de um marcador de conclusão (`onboarded_at` ou equivalente) para não
  reaparecer; usa endpoints existentes para o resto.
- #21 — nenhum campo novo: `data_completeness`, `freshness` e proveniência já existem; falta
  consumir.

**Feature nova (exige análise backend+frontend):**
- #5 — busca global sobre ativos + setores + telas. A parte de ativos já existe
  (`GET /universe/search`); setores e telas são índice de cliente.
- Nada mais. **O redesign não exige nenhum algoritmo novo** — exige tornar alcançável e legível
  o que já é calculado.

## O que NÃO vou mexer

- Regras de negócio (`analysis/`, `optimizer/`) — permanecem a única fonte de verdade.
- Limiares de score (75/60/40) — só a *apresentação* muda; a régua numérica fica.
- `POST /portfolio/position` / `DELETE` como caminho de escrita; `PUT /portfolio` segue restrito
  a importação.
- Multi-tenancy, auth, migrações.
