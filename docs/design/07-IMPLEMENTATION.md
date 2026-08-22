# Fase 8 e 9 — log de implementação

> O que foi de fato construído, em ordem cronológica, e o que cada etapa revelou.
>
> Separado do [README](README.md) de propósito: o índice responde "o que ler"; este arquivo
> responde "o que já está no ar e o que ainda não". As fases de projeto (1–7) estão nos
> documentos numerados; aqui é só execução.
>
> **Estado resumido:** o web tem a nova arquitetura de informação completa (5 destinos, 36
> rotas) e três telas redesenhadas de fato (`/hoje`, `/ativo/:ticker`, `/carteira`). O mobile tem
> tokens, shell de 5 destinos, Estratégia e a régua; o conteúdo de Hoje e Carteira ainda é o
> antigo.

---

## Etapa 1 — fiação do design system (web + mobile)

A paleta, a tipografia e a forma já saem dos tokens nas duas plataformas, **sem nenhuma tela
redesenhada ainda**. O que mudou de fato:

| | Antes | Agora |
|---|---|---|
| Paleta | 2 blocos de hex em `styles.css` + cópia à mão em `theme.dart` | tudo `var(--fi-*)` / `FiColors`, de `tokens.json` |
| Marca | verde, fazendo 4 papéis (marca, lucro, botão, "boa oportunidade") | azul-ardósia, só marca/interativo |
| Chão | `#0b0e14` azul-preto + 2 `radial-gradient` | grafite sólido (escuro) / papel morno (claro) |
| Selo de marca | gradiente verde→ciano com sombra colorida | chapa sólida na cor de marca |
| Nav ativa | gradiente + sombra colorida | marca sólida, sem sombra |
| Serifa | inexistente | Source Serif 4 carregada nas duas plataformas |
| Base tipográfica | 15px, rótulos a 10–11px | 16px, bottom nav a 12px |
| Raio | 14px único | 4 / 8 / 12 |
| Hex fora de token (web) | 8 em `.dip-*`/`.dip-badge-*` + 2 de `ink-on-brand` | 0 |
| CSS morto | `.cat-renda/trade/caixa/etfs`, `.news-*` | removido |
| Vars inexistentes | `--cat-renda_fixa`, `--color-success/danger/info`, `--tx` em `assets.component.scss` (renderizavam sem cor, em silêncio) | corrigidas |
| Séries de gráfico | 11 hex ad-hoc por tema | 11 tokens sistemáticos + `series-other` |

Três coisas ficaram deliberadamente **como estão**, para não introduzir regressão invisível:

- **`screens.sm` continua 640px.** Remapear para 420px moveria o layout de todas as telas
  atuais (46 usos de `sm:`). As faixas novas entraram como `xs` (420) e `2xl` (1440, zero usos
  hoje); `md`/`lg`/`xl` já batiam com tablet/desktop-sm/desktop.
- **`gainColor`/`lossColor`/`warnColor` (mobile) seguem no eixo de estado.** Eles fazem dois
  papéis nas telas — aritmética (P&L, linha de gráfico) e julgamento (selo de veredito, banda de
  saúde, severidade de alerta), que é o achado #11 em código. Rebaixá-los para o eixo de direção
  agora enfraqueceria os selos. `fiStateColor` e `fiDirectionColor` já existem; a separação é
  feita por chamada, junto do redesenho de cada tela.
- **Os ~130 `bg-accent`/`text-accent`/`border-accent` dos templates** continuam via alias. Os
  templates são reescritos na Fase 8; trocar classe em código que será substituído é trabalho
  jogado fora.

Ainda **não** feito nas Fases 8/9: o shell novo, as 19 rotas, `/ativo/:ticker`, reviver
Estratégia e Quick Invest, dissolver `/market`, os componentes de domínio (`ScoreRuler` à frente
de todos) e a densidade por `detail_level`.

---

## Etapa 2 — roteamento do web


A nova arquitetura de informação está no ar no web. **19 rotas endereçáveis** no lugar de 6, e
nenhuma tab guardando estado em `signal`.

| | Antes | Agora |
|---|---|---|
| Destinos | Dashboard · Meus Ativos · Mercado · Configurações | Hoje · Carteira · Descobrir · Estratégia (+ Você no avatar) |
| Estratégia | 1092 linhas de template **sem rota** | `/estrategia` (plano) |
| Quick Invest web | dentro da tela inalcançável | `/estrategia/aporte` |
| Sub-destinos de `/market` | 8, em tabs sem URL | rotas próprias em `/descobrir/*` e `/estrategia/*` |
| Página de ativo | não existia | `/ativo/:ticker`, ticker na rota |
| Metas de alocação | Configurações | `/estrategia/metas`, ao lado do gap |
| Alertas / cache | no meio de Configurações | `/voce/alertas` · `/voce/conta` |
| `dip.component` (485 linhas mortas) | exportado, sem rota | **removido** |
| `/market` (hub) | 3 tabs × 5 sub-tabs | **dissolvido** |

Divisões feitas: `strategy.component` (1092 → plano + aporte, descartando as abas "Analisar
Ativo" e "Simulador de RF" que duplicavam componentes já alcançáveis) e `config.component`
(525 → Metas + Preferências + Alertas + Conta, cada um com PUT parcial em `/preferences`).

Navegação contextual ligada: item de oportunidade, item de queda, linha de posição e feed de Hoje
levam a `/ativo/:ticker`; a página do ativo oferece Comparar, Criar alerta (com o ticker
preenchido) e Adicionar à carteira. Rotas antigas (`/dashboard`, `/assets`, `/market`, `/config`,
`/strategy`) viraram redirects — link salvo é contrato.

Efeitos colaterais que precisaram de conserto no caminho:

- **`rebalance-suggestions` e `followed-suggestions` ficaram órfãos** ao dissolver `/market` —
  exatamente o bug que a auditoria encontrou. Foram para `/estrategia`, como a IA define.
- O estado do drawer de diagnóstico de queda subiu de `market.component` para
  `DipAnalysisService`: um layout com `router-outlet` não recebe `output` de filho roteado.
- `/estrategia` lê o caixa de `/preferences` e `/estrategia/aporte` o grava — antes o plano lia o
  valor do formulário do Quick Invest, amarrando as duas telas. `saveCashAvailable()`, que existia
  no service sem nenhum consumidor, ganhou um.
- `getCategoryBarColor()` tinha cinco `rgba()` literais e um `rgba(var(--accent) / 0.5)` —
  sintaxe inválida, porque `--accent` nunca foi um triplete RGB. Passou a usar os tokens de série.

---

## Etapa 3 — `/hoje` como central de decisão


**`/hoje` é a central de decisão.** 10 blocos de peso igual → 5 seções em 3 níveis:

| | Antes | Agora |
|---|---|---|
| N1 | 4 cards (patrimônio, investido, DY, renda) | um `money-xl`, variação, e os números de apoio **numa linha** |
| N1 | score de saúde + 4 sub-scores numéricos + acordeão | veredito em serifa + 2–3 motivos em texto + a régua |
| N2 | "O que mudou" e "Alertas" em blocos separados, formatos diferentes | um feed, ordenado por urgência, um `Insight` por linha |
| N3 | — | "Próxima ação": o maior gap de alocação, com o cálculo visível |
| N3 | grid de oportunidades | as 3 melhores, com o porquê antes dos números |
| — | 2 gráficos, tabela de posições, bloco de sinais de venda | movidos para a tela dona; sinais de venda viraram uma linha do feed |

O maior gap sai de `allocations`, que `GET /dashboard` já devolve — sem chamada extra a
`/strategy`.

**Componentes de domínio no ar:**

- **`ScoreRuler`** — o elemento-assinatura. Zonas nomeadas com peso de tinta, cor só na zona onde
  o valor caiu, marca fina no valor, 4 tamanhos. Com `data_completeness` baixo fica cinza, o
  número sai e o rótulo é "Dado insuficiente". Aceita um conjunto de bandas: o mesmo instrumento
  serve score de ativo e saúde da carteira (`fiHealthBands`, mesmos limiares, rótulos próprios).
- **`Insight`** — o padrão único: o que aconteceu → por que importa → o que sustenta → o que
  fazer. Estado carrega cor **e** ícone **e** texto.
- **`/carteira/desempenho`** — os dois gráficos que disputavam o espaço nobre do dashboard,
  fundidos numa tela, cada um com a pergunta declarada no título (achado #36).

**`score-ruler.ts` agora delega aos tokens gerados.** A divergência do achado #17 (verde no web,
azul no mobile) deixou de ser possível: os limiares, rótulos e estados saem de `tokens.json`, e
`ui-helper` delega em vez de manter um `if` paralelo.

Mais três defeitos silenciosos encontrados nesta etapa:

- **`.card` (6 templates), `.btn-primary` (3), `.btn-secondary` (3) e `.pagination-btn` (1) não
  estavam definidos em nenhum CSS do projeto.** Um `.card` era só uma `div` sem fundo nem borda,
  e os botões primários herdavam a aparência default do navegador. Definidos com tokens.
- `SkeletonComponent` e `EmptyStateComponent` foram **removidos**: zero consumidores desde sempre,
  e as duas implementações contradiziam o próprio contrato do design system (skeleton genérico em
  vez da forma do conteúdo; empty state sem CTA obrigatório). A especificação dos dois segue em
  [06](06-DESIGN-SYSTEM.md); serão construídos quando uma tela precisar.
- `dataCompletenessLabel` existia duplicado em `ui-helper` e na régua, com a mesma frase.

---

## Etapa 4 — `/ativo/:ticker`, a página de research

A tela onde a metodologia do produto deixa de ser invisível. Cada método de valuation aparece
**separado**, com preço estimado, distância do preço atual e o insumo que usou — nunca um "preço
justo" único sem dizer de onde veio.

E quando um método não se aplica, a tela **diz por quê** em vez de deixar um campo vazio:
"Graham não se aplica a fundo imobiliário", "Valor patrimonial por ação não disponível na fonte",
"Lucro por ação não positivo". O roteamento por tipo é do backend (`analysis/fair_price.py`); a UI
reflete e explica, não decide.

Estrutura: cabeçalho com ações contextuais (comparar · alertar · adicionar) → leitura em uma frase
em serifa + veredito + régua de confiança + os `reasons` do backend → preço atual × consenso ×
margem de segurança → tabela de valuation → fundamentos (só os que existem) → tendência →
proventos → "Como calculamos" (N4, fechado).

### Três campos que a API calculava e descartava

`FairPriceBlock(**fair.__dict__)` e `TechnicalBlock(**tech.__dict__)` — Pydantic ignora chave extra
em silêncio, então:

| Campo | Situação | Correção |
|---|---|---|
| `consensus_methods` | calculado em `compute_fair_price`, **não declarado** no modelo de resposta | campo adicionado (**mudança de contrato**, aditiva) |
| `trend_basis` | calculado em `compute_technical`, **não declarado** — a tendência chegava sem dizer se veio de SMA 50/200 ou 20/50 | idem |
| `dcf` | declarado no backend, **ausente do modelo TypeScript** — nenhum template do web conseguia mostrar o terceiro método | tipo corrigido (só frontend) |

Dois testes de regressão travam isso (`test_fair_price.py`): a suíte foi de 206 para 208.

`fundamentals` deixou de ser `Record<string, number | null>` e passou a declarar as chaves reais
que `asset_service` monta — o acesso dinâmico em `compare-assets` virou `keyof AssetFundamentals`,
então chave inexistente quebra o build em vez de virar `undefined` em runtime.

O componente antigo `market/analyze-asset` foi **removido**: `/ativo/:ticker` o substitui por
inteiro.

---

## Etapa 5 — `/carteira` dividida: a IA do web está completa

A pilha de seis blocos de `/assets` (834 linhas de HTML, 651 de TS) virou sete rotas, cada uma
respondendo uma pergunta:

| Rota | Pergunta |
|---|---|
| `/carteira` | quanto tenho, comparado à minha meta, e a carteira está saudável? |
| `/carteira/composicao` | onde meu dinheiro está concentrado? |
| `/carteira/desempenho` | estou rendendo mais que o CDI? |
| `/carteira/proventos` | quanto de renda entrou, comparado ao estimado? |
| `/carteira/posicoes` | tudo o que eu tenho, em tabela |
| `/carteira/encerradas` | lucro realizado, IR pago e prejuízo a compensar |
| `/carteira/editar` | escrita |

O resumo ganhou duas coisas que `/assets` não tinha: **alocação × meta** (a composição mostrava a
pizza, mas não o desvio — sem a meta ao lado, uma pizza não responde "está certo?") e as **quatro
dimensões de saúde** com a régua, que é onde a conta vive agora que `/hoje` ficou só com o
julgamento. Categoria sem meta definida não entra na lista: o desvio de uma meta que não existe
seria um número inventado.

**`CarteiraStore`** (`core/services/carteira-store.service.ts`) sustenta as sete rotas. Sem ele,
cada troca de sub-aba refaria `GET /portfolio`, `POST /portfolio/evaluate`, `GET /fixed-income`,
`GET /dividends/received`, `GET /goals` e `GET /sector-goals` — e `evaluate` é a chamada mais cara
do produto, porque cota e avalia cada posição. `ensureLoaded()` é idempotente; `reload()` é
explícito.

Também corrigi ali a agregação de setores: era top-8 + "Outros", agora é top-6, alinhado à regra de
no máximo 6 séries por gráfico.

**36 rotas** no `app.routes.ts` (19 de conteúdo + redirects + layouts).

O que **falta** na Fase 8: gráfico de preço na página do ativo (com preço médio e preço justo como
linhas de referência); busca global; drawer de Atividade; `MarginOfSafety`, `AllocationGap`,
`GoalProgress` e `DipDiagnosis` como componentes reutilizáveis; colunas configuráveis e densidade
compacta na tabela de posições; densidade por `detail_level` (precisa do campo no backend).

---

## Etapa 6 — mobile: a mesma arquitetura, hierarquia própria

O mobile deixou de espelhar a topologia antiga do web e passou a espelhar a **nova**: cinco
destinos por intenção, 19 rotas, e **Estratégia existindo pela primeira vez em qualquer
plataforma**.

| | Antes | Agora |
|---|---|---|
| Bottom nav | Dashboard · Meus Ativos · Mercado · Config | Hoje · Carteira · Descobrir · Estratégia · Você |
| Estratégia | não existia | `/estrategia` com gaps, cálculo, sugestão e ação |
| Ferramentas | 5 views privadas num `FerramentasTab` de 892 linhas, modo em `setState` | 5 rotas, cada uma com título, voltar e a pergunta que responde |
| Quedas | sub-modo de filtro, sem rota | `/descobrir/quedas` |
| Página de ativo | bottom sheet sem rota | `/ativo/:ticker`, ticker na rota, análise já carregada |
| Erro | 13 pontos com `Text('Erro: $err')` | `FiErrorState` + `fiErrorMessage`, causa humana e ação |
| Régua | não existia | `ScoreRuler` em Dart, espelhando o web |

`market_screen.dart` e `rebalance_tab.dart` foram removidos — o hub de Mercado foi dissolvido no
mobile como já tinha sido no web. Rotas antigas (`/dashboard`, `/assets`, `/market`, `/config`)
viraram redirect, então push antigo e link salvo continuam funcionando.

### Mais um campo que o cliente descartava

`RebalanceSuggestions.fromJson` **ignorava `allocation_gaps`** — o backend enviava desde sempre e o
mobile não tinha como montar "onde você está × onde deveria estar", que é justamente o núcleo de
Estratégia. Terceira ocorrência do mesmo padrão nesta auditoria (as outras duas foram
`consensus_methods` e `trend_basis`, do lado do servidor). Modelo `AllocationGap` adicionado, com
`biggestGap` que ordena por módulo — o maior desvio pode ser para cima.

`fiErrorMessage` distingue rede caída, sessão expirada, 404, instabilidade do serviço e erro de
domínio (usando o `detail` que o backend manda). Quatro testes travam isso, incluindo um que
verifica que a exceção crua nunca vaza. A suíte mobile foi de 7 para 13 testes.

### Assimetrias que restam, declaradas

- **Metas** no mobile ainda vivem dentro de Configurações; `/estrategia/metas` leva para lá em vez
  de oferecer um destino vazio. No web já se mudaram.
- **RF × Bolsa** (`/income-compare`) continua sem cliente Dart.
- **Conteúdo de Hoje e Carteira** no mobile ainda é o antigo: `dashboard_screen.dart` (1214 linhas)
  e `assets_screen.dart` (1231) não foram reestruturados nos três níveis, e `/carteira` não foi
  fatiada. A régua e o `FiErrorState` já estão disponíveis para isso.

---

## Correção pontual — ícones: 16 nomes que só quebravam em runtime

`LucideAngularModule.pick({...})` registra ícone por ícone. Um nome ausente **não quebra o
build** — quebra a tela quando ela renderiza, com `The "x" icon has not been provided by any
available icon providers`. Foi assim que `sunrise` chegou à navegação principal.

A varredura achou 16: dez que eu introduzi e **seis pré-existentes** em telas menos visitadas
(`arrow-left`, `eye-off`, `pencil`, `save` no editor de carteira; `lock` em RF × Bolsa;
`alert-triangle`, que é o nome legado de `triangle-alert`). Todos registrados; o legado foi
corrigido para o nome atual.

**Não há verificação automática disso.** Um checker estático foi escrito e removido a pedido:
nomes dinâmicos (mapas em `ui-helper`, `icon:` de objetos de navegação) não são resolvíveis com
confiança fora do runtime, e a versão precisa o bastante para não virar ruído ainda deixava
brechas. Ao adicionar um `<lucide-icon>`, registre o import PascalCase em
`LucideAngularModule.pick({...})` de `web/src/main.ts` e **abra a tela** — o build passa mesmo
com o nome errado.
