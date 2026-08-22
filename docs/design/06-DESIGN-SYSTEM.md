# Fase 7 — Design system

> Traduz [05-VISUAL-LANGUAGE.md](05-VISUAL-LANGUAGE.md) em tokens e componentes.
> Os tokens **não são documentação**: são código gerado, já no repositório.

## Tokens: uma fonte, três alvos

```
design-tokens/tokens.json          ← fonte única. Só este arquivo se edita à mão.
design-tokens/build.mjs            ← gerador (Node, sem dependências)
        │
        ├─→ web/src/tokens.css                      custom properties + classes de papel
        ├─→ web/src/app/core/design-tokens.ts       consts tipadas + régua do score
        └─→ mobile/lib/core/design_tokens.dart      Color/TextStyle/enums equivalentes
```

```bash
node design-tokens/build.mjs           # regenera os três alvos
node design-tokens/build.mjs --check   # falha se algo divergir  (roda no CI)
```

**Por que gerar em vez de documentar.** A régua de score já divergiu: "Boa oportunidade" é verde
no web e azul no mobile, apesar de os dois arquivos trazerem um comentário dizendo que devem
andar juntos (achado #17). Token mantido à mão em N lugares diverge em N−1 deles. O job
`design-tokens` no CI transforma divergência em build vermelho.

Os arquivos gerados estão em `web/.prettierignore` — são artefatos, e a sincronia deles é
verificada pelo `--check`, não pelo Prettier.

### O que os limiares NÃO são

`tokens.json → scoreRuler.thresholds` **espelha** `backend/app/analysis/score_ruler.py`. A régua
numérica continua sendo do backend; o design system só decide como ela é *lida*. Mudar um
limiar: Python primeiro, depois `tokens.json`, depois regenerar.

---

## Foundations

### Cor

Todo token nomeia uma **função**, nunca uma cor. `state-favorable`, não `green`.

| Grupo | Tokens |
|---|---|
| Chão | `ground-0` (página) · `ground-1` (superfície) · `ground-2` (elevada/campo) |
| Fio | `hairline` · `hairline-strong` |
| Tinta | `ink-1` · `ink-2` · `ink-3` · `ink-on-brand` |
| Marca / interativo | `brand` · `brand-quiet` |
| Estado | `state-favorable` · `state-attention` · `state-adverse` · `state-indeterminate` |
| Direção (aritmética) | `direction-up` · `direction-down` |
| Séries | `series-1..6` · `series-other` |

**Contraste verificado** — todo token de tinta e de estado atinge ≥ 4,5:1 sobre o `ground-0` do
próprio tema:

| Token | Escuro | Claro |
|---|---|---|
| `ink-2` | 8,3:1 | 6,5:1 |
| `ink-3` | 4,9:1 | 4,8:1 |
| `brand` | 6,4:1 | 6,2:1 |
| `state-favorable` | 7,1:1 | 4,6:1 |
| `state-attention` | 8,1:1 | 5,3:1 |
| `state-adverse` | 5,9:1 | 5,4:1 |
| `direction-up` / `down` | 5,1 / 5,0:1 | 4,6 / 5,4:1 |

Três regras de uso, verificáveis em revisão:

1. **Estado supera aritmética.** Um selo de estado é sempre mais cromático que qualquer número
   perto dele.
2. **Cor nunca é o único canal.** Estado = cor + forma/ícone + rótulo textual. Selo sem texto
   não passa.
3. **Zero hex fora dos tokens.** Nenhum `#4ade80` em componente — o CSS atual tem oito.

### Tipografia

`Inter` mede, `Source Serif 4` conclui. Papéis: `money-xl` · `money-lg` · `metric` ·
`metric-sm` · `verdict` · `verdict-sm` · `title` · `eyebrow` · `body` · `label` · `caption` ·
`ticker` (tabela completa em [05](05-VISUAL-LANGUAGE.md#tipografia)).

- No web, um papel = uma classe: `.fi-money-xl`, `.fi-verdict`, `.fi-eyebrow`…
- No mobile, um papel = um `TextStyle` em `FiType` + a família em `fiTypeFamily` (resolvida via
  `google_fonts`). `eyebrow` precisa de `.toUpperCase()` na aplicação — `TextStyle` não
  transforma caixa.
- Cifras tabulares (`tabular-nums slashed-zero` / `FontFeature.tabularFigures()` +
  `slashedZero()`) já vêm embutidas em todo papel numérico. Fora da escala existe `.fi-num`.
- **Um único `money-xl` por tela.** Dois números do mesmo tamanho significam que a tela não
  decidiu qual é a resposta.

### Espaço, forma, sombra

- Espaço: escala de 4px (`--fi-space-1..16`).
- Raio: `sm` 4 · `md` 8 · `lg` 12 · `pill`.
- Sombra: **duas** (`drawer`, `popover`), só para o que flutua. Estrutura usa chão + fio.
- Densidade: `comfortable` (linha 48px) / `compact` (36px), por `data-density` no web e
  `FiDensity` no mobile.

### Motion

`fast` 120ms · `base` 180ms · `slow` 240ms; entrada `cubic-bezier(0.2,0,0,1)`, saída
`cubic-bezier(0.4,0,1,1)`. `prefers-reduced-motion` colapsa tudo para 1ms via `tokens.css`.
**Números não animam contagem.**

### Foco, toque, z-index

Anel de foco único: 2px em `brand`, offset 2px (`.fi-focusable:focus-visible`). Hoje o produto
não define nenhum. Alvo mínimo de toque 44px (`--fi-min-touch-target`).
Camadas: nav 100 · drawer/sheet 200 · popover 300 · toast 400.

### Breakpoints

`mobile-sm` 0 · `mobile-lg` 420 · `tablet` 768 · `desktop-sm` 1024 · `desktop` 1280 ·
`desktop-lg` 1440. Comportamento por faixa em [04](04-WIREFRAMES.md#10-responsividade).
Largura de leitura 1120px, densa 1600px — o `max-w-[1180px]` global sai.

---

## Componentes base

Contrato mínimo de cada um: **estados** (default/hover/focus/active/disabled/loading) ·
**nome acessível obrigatório** · **zero hex** · **densidade respeitada**.

| Componente | Notas específicas do fiance |
|---|---|
| `Button` | primária (marca) · secundária (fio) · discreta (tinta) · destrutiva. Uma primária por bloco |
| `IconButton` | `aria-label`/`tooltip` **obrigatório** — hoje há 97 botões e 1 `aria-label` |
| `Input` / `Money` / `Percent` | variantes numéricas com cifras tabulares, alinhamento à direita e máscara pt-BR |
| `Select` / `Segmented` | segmented substitui tab quando há 2–4 opções mutuamente exclusivas |
| `Tabs` | `role="tablist"`/`aria-selected`, navegação por setas, **estado na URL** |
| `Card` | só para objeto acionável. Seção usa fio + espaço |
| `Drawer` | 600px à direita, `role="dialog"`, focus trap, Esc, retorno de foco |
| `BottomSheet` | mobile; dois estágios (peek / cheio) |
| `Modal` | reservado a confirmação destrutiva. Não é o padrão de detalhe |
| `Tooltip` | glossário; acessível por teclado, não só hover |
| `Toast` | ação concluída/falhou; nunca informação que precisa persistir |
| `Table` | ordenar · esconder coluna · fixar 1ª coluna · densidade · virtualização. Degrada para lista no mobile |
| `Chart` | eixos, tooltip, linha de referência, anotação; **pergunta declarada no título** |
| `Badge` | cor + ícone + texto, sempre os três |
| `Skeleton` | composto na forma do conteúdo real (o componente existe e nunca foi usado) |
| `EmptyState` | causa + próximo passo executável; CTA não é opcional |
| `ErrorState` | último dado + causa humana + repetir. Nunca exceção crua |
| `Nav` / `SubNav` / `BottomNav` | itens ≥44px; rótulo ≥12px |
| `SearchGlobal` | `⌘K` no desktop; resultados por categoria (ativos, setores, telas) |
| `Provenance` | rodapé padrão: fonte, momento, método, limitação |

---

## Componentes de domínio

O que hoje é remontado com `div`/`Row` em cada tela, e por isso é inconsistente.

### `ScoreRuler` — o elemento-assinatura

Uma régua com zonas nomeadas e um valor marcado, não um gauge.

```
      evitar        neutro       boa        forte
├───────────┼────────────┼───────────┼──────────────┤
0          40           60          75            100
                                        ▼
                                       87  Forte
```

- Zonas por peso de tinta; cor só na zona onde o valor caiu.
- Tamanhos: `inline` 16 · `list` 24 · `card` 40 · `page` 64 (`fiScoreRulerSizes`).
- Bandas, rótulos e estados vêm de `fiScoreBands` / `fiScoreBandFor()` — gerados.
- `data_completeness < 0,5` → régua tracejada, cinza, número suprimido, rótulo
  **"Dado insuficiente"**.

**Rótulos novos:** `Forte` · `Boa` · `Neutra` · `Fraca`, substituindo "Excelente entrada" /
"Boa oportunidade" / "Neutro" / "Evitar agora". Os limiares não mudam; a linguagem deixa de dar
ordem e passa a descrever a leitura (briefing §10 e §43). Muda nas três plataformas de uma vez,
porque sai de `tokens.json`.

### A régua reaproveitada

Mesma mecânica — valor numa escala com zonas nomeadas — em quatro leituras:

| Componente | Escala | Zonas |
|---|---|---|
| `ScoreRuler` | 0–100 | 40 / 60 / 75 |
| `MarginOfSafety` | −x% … +x% | zona negativa (acima do justo) / neutra / positiva |
| `AllocationGap` | −meta … +meta | dentro da meta / desvio / desvio relevante |
| `GoalProgress` | 0–100% da meta | atrás / no ritmo / atingida |

Um instrumento, quatro leituras. É o que faz o produto parecer projetado, e não montado.

### Os demais

| Componente | Responde | Notas |
|---|---|---|
| `PortfolioValue` | "quanto eu tenho?" | `money-xl`, variação + período; **um por tela** |
| `PortfolioHealth` | "está tudo bem?" | veredito em serifa + 2–3 motivos; suprime concentração em carteira pequena |
| `AssetScore` | "quanto vale a leitura?" | `ScoreRuler` + breakdown por dimensão |
| `FairPrice` | "quanto deveria custar?" | **um bloco por método** — preço, atual, margem, metodologia. Nunca métodos somados num número |
| `DecisionSummary` | "e daí?" | Interessante / Neutro / Atenção / Evitar + motivo. Vocabulário de `fiDecision` |
| `Insight` | o padrão universal | **o que aconteceu → por que importa → o que sustenta → o que fazer**. Uma ação primária. Usado em Hoje, Estratégia, Descobrir, Atividade |
| `OpportunityCard` | "por que apareceu?" | a razão vem **antes** dos números |
| `DipDiagnosis` | "por que caiu?" | classe + critério + evidências + valuation + conclusão (`fiDipDiagnosis`) |
| `FixedIncomeRate` | "rende quanto, comparado a quê?" | nunca taxa nua: "~112% do CDI", "IPCA + 6,2% real", liquidez, IR |
| `DividendTimeline` | "quanto entrou?" | recebido × estimado pelo app |
| `BenchmarkComparison` | "ganhei do CDI?" | carteira = tinta primária, benchmark = marca, meta = marca tracejada |
| `MarketStatus` / `Provenance` | "posso confiar?" | idade da cotação, fonte das taxas, "estimativa, não garantia" |
| `AlertItem` | — | linguagem humana: `DIP_THRESHOLD_TRIGGERED` → "PETR4 caiu 8,4% hoje" |
| `AssetPriceChart` | "está longe do justo?" | preço + preço médio + preço justo + períodos |
| `MetricWithContext` | "isso é bom ou ruim?" | valor + âncora (meta, CDI, setor, histórico) **quando o dado existir**; sem dado, diz que não há |

`MetricWithContext` é o componente que resolve o achado #31 estruturalmente: se não há âncora
disponível, ele **não inventa** uma — mostra o valor e omite a comparação.

---

## Regras que valem para todo componente

1. **Nada de dado inventado.** Sem dado → estado, não número. Método não aplicável → diz por quê
   ("Graham não se aplica a fundo imobiliário"), não deixa vazio.
2. **Nome acessível obrigatório.** Nenhum controle sem nome; tabs e drawers com semântica e
   gestão de foco.
3. **Densidade respeitada.** Todo componente com linhas/listas honra `comfortable`/`compact`.
4. **Progressive disclosure declarada.** Cada bloco marca o nível (N1–N4) do que exibe; N3+ nasce
   fechado.
5. **Uma ação primária por bloco.** Insight sem ação é ruído.
6. **Zero hex, zero tamanho inline.** Só tokens.
7. **Estado antes de número.** Um bloco que julga põe o julgamento acima dos dados que o
   sustentam.

## O que ainda não existe e é preciso para a Fase 8

| Item | Tipo | Onde |
|---|---|---|
| `detail_level` (Essencial/Completo/Avançado) | **contrato** | `PreferencesDb` + `GET/PUT /preferences` + migração Alembic |
| marcador de onboarding concluído | **contrato** | idem |
| Source Serif 4 | asset | `<link>` no `web/src/index.html`; `google_fonts` no mobile |
| `tokens.css` no build do Angular | fiação | importar em `styles.css`, apontar `tailwind.config.js` para `--fi-*` |
| `FiTheme` a partir de `design_tokens.dart` | fiação | reescrever `mobile/lib/core/theme.dart` sobre os tokens gerados |
| verificar as 3 classes de `dipDiagnosis` | verificação | `DipAnalysis` real precisa sustentar a separação; se não, ficam 2 |

Nenhum algoritmo novo. O redesign consome o que o backend já calcula.
