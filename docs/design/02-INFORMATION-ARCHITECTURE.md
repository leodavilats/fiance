# Fase 3 — Arquitetura de informação

> Decorre de [01-UX-AUDIT.md](01-UX-AUDIT.md) achados 1–6. Esta é a decisão estrutural: **nada
> de visual é implementado antes de ela estar aceita**, porque ela define quais componentes
> existem.

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
