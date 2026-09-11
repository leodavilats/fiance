# Design system

> Traduz [VISUAL-LANGUAGE.md](VISUAL-LANGUAGE.md) em tokens e componentes.

## Onde cada peça mora

Tudo é escrito à mão. Não existe gerador de design.

```
mobile/lib/core/design_tokens.dart  ← cor (nos dois temas), tipo, espaço, raio, motion, densidade
mobile/lib/core/theme.dart          ← o ThemeData montado sobre eles
mobile/lib/core/product_rules.dart  ← bandas das réguas, veredito, diagnóstico
mobile/lib/core/vocabulary.dart     ← rótulo, ícone e série de cada categoria
```

```bash
cd mobile && flutter test   # contraste e regras de produto rodam aqui  (é o comando do CI)
```

**Por que nada disso é gerado.** O gerador existiu e resolvia o problema errado. Ele mantinha o
**valor** igual entre plataformas — e o valor nunca era o que divergia. O que divergia era o
**conceito**: houve meses sem `/mes` e sem `/sobra` no aplicativo, com a régua de cor
perfeitamente sincronizada. Em troca, o schema fechava o vocabulário visual: doze papéis de tipo,
quatro raios, duas sombras, e nada para estado de interação — não havia como declarar contorno de
controle, preenchimento pressionado ou poço de barra.

Com um cliente só, o custo daquela escolha desapareceu: existe **uma** paleta, e ela é esta.

**O que impede a régua de divergir** é a régua de baixo. `backend/app/analysis/score_ruler.py` é a
fonte; `product_rules.dart` a espelha. Ela já divergiu uma vez — "Boa oportunidade" saiu verde numa
plataforma e azul na outra — e a disciplina continua: **Python primeiro**, depois o Dart, no mesmo
commit.

### O que continua verificado

Contraste, em `mobile/test/contraste_test.dart`, nos **dois temas** e contra o **mínimo da WCAG** —
4,5:1 para texto e 3:1 para forma e limite de controle (1.4.3 e 1.4.11). Pisos acima da norma eram
escolha de design, e escolha de design não tem máquina: a paleta é livre, o ilegível não é.

| O que | Piso | Por quê |
|---|---|---|
| `ink-1` / `ink-2` / `ink-3` sobre o chão | 4,5 | legenda é texto pequeno, e a regra para texto pequeno é a mesma |
| `brand` e cada `state-*` sobre o chão | 4,5 | marca e estado escrevem texto |
| tinta do estado sobre a **superfície** do próprio estado | 5,5 | o rótulo do selo é a própria cor do estado |
| `series-*` (12) sobre o chão | 4,5 | a série nomeia o próprio chip |
| `control-border` sobre chão e superfície | 3 | é o contorno que faz um controle ser um controle |
| `brand` sobre `track` | 3 | preenchido contra vazio: é o par que faz barra e deslizador mostrarem onde estão |
| `ink-on-brand` sobre `brand` | 4,5 | o rótulo do botão primário |
| `ink-1` sobre `control-fill` | 4,5 | o rótulo do botão secundário |
| `ink-disabled` sobre `control-fill` | 3 | controle inerte continua tendo de ser lido |

`hairline` fica de fora: é separador decorativo. O que mudou antes disso é que **separador e
contorno de controle deixaram de ser o mesmo token** — enquanto eram, a borda de um botão
secundário desenhava a 1,24:1, um quarto do mínimo, e nenhuma revisão visual pegou isso.

### O que os limiares NÃO são

`fiScoreBands` **espelha** `backend/app/analysis/score_ruler.py`. A régua numérica continua sendo
do backend; o design system só decide como ela é *lida*. Mudar um limiar: Python primeiro, depois
`product_rules.dart`.

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
`ticker` (tabela completa em [identidade visual](VISUAL-LANGUAGE.md#tipografia)).

- Um papel = um `TextStyle` em `FiType` + a família em `fiTypeFamily` (resolvida via
  `google_fonts`). `eyebrow` precisa de `.toUpperCase()` na aplicação — `TextStyle` não
  transforma caixa.
- Cifras tabulares (`FontFeature.tabularFigures()` + `slashedZero()`) já vêm embutidas em todo
  papel numérico.
- **Um único `money-xl` por tela.** Dois números do mesmo tamanho significam que a tela não
  decidiu qual é a resposta.

### Espaço, forma, sombra

- Espaço: escala de 4px (`--fi-space-1..16`).
- Raio: `sm` 4 · `md` 8 · `lg` 12 · `pill`.
- Sombra: **duas** (`drawer`, `popover`), só para o que flutua. Estrutura usa chão + fio.
- Densidade: `comfortable` (linha 48px) / `compact` (36px), por `FiDensity`.

### Motion

`fast` 120ms · `base` 180ms · `slow` 240ms; entrada `cubic-bezier(0.2,0,0,1)`, saída
`cubic-bezier(0.4,0,1,1)`. Movimento reduzido no sistema colapsa tudo para 1ms.
**Números não animam contagem.**

### Foco, toque, z-index

Anel de foco único: 2px em `brand`, offset 2px (`.fi-focusable:focus-visible`). Hoje o produto
não define nenhum. Alvo mínimo de toque 44px (`--fi-min-touch-target`).
Camadas: nav 100 · drawer/sheet 200 · popover 300 · toast 400.

### Breakpoints

`mobile-sm` 0 · `mobile-lg` 420 · `tablet` 768. Comportamento por faixa em
[wireframes](WIREFRAMES.md#9-larguras). Acima de tablet não há faixa: o produto é distribuído
pelas lojas.

---

---

## O vocabulário do caixa — decidido, ainda não declarado

Entregável da Fase 2 do [ROADMAP](../produto/ROADMAP.md). **Não está em `vocabulary.ts`**, e é
decisão, não esquecimento: o CLAUDE.md registra que vocabulário sem consumidor é pior que
vocabulário nenhum, porque *parece* resolvido. `fiTiposDeRendaFixa` e `fiLiquidez` já custaram isso
— existiam e quatro telas reescreviam o mapa à mão.

A entrada em `vocabulary.ts` acompanha o commit que constrói a primeira tela que a consome, na
Fase 3.

### Categoria de despesa

Dez categorias, fechadas. O critério não é taxonômico — é **quantas a pessoa consegue escolher
sem parar para pensar** ao lançar um gasto no celular. Acima de uma dúzia, lançar vira
classificação e a pessoa desiste.

| Categoria | Cobre | Por que separada |
|---|---|---|
| `moradia` | aluguel, condomínio, financiamento, IPTU | é o maior gasto fixo, e o mais estável |
| `contas_da_casa` | energia, água, gás, internet, telefone | fixas mas variáveis no valor — é onde `A vencer` mais aparece |
| `mercado` | supermercado, feira, açougue | o maior gasto **variável** da maioria; é a linha que colapsa na linha do tempo |
| `transporte` | combustível, aplicativo, passagem, manutenção | varia com rotina, não com preço |
| `saude` | plano, farmácia, consulta, exame | irregular e não postergável |
| `educacao` | mensalidade, curso, material | fixa e de prazo longo |
| `lazer` | restaurante, assinatura, viagem, bar | a categoria que a pessoa **quer** ver isolada |
| `cuidados_pessoais` | vestuário, higiene, academia, salão | idem |
| `divida` | pagamento de dívida, juros | **não é consumo**: sai do caixa mas não é gasto de vida, e misturar as duas coisas corrompe a leitura de quanto a rotina custa |
| `outros` | o resto | existe para a pessoa não travar; se ela crescer demais, é sinal de que falta categoria, e isso se **mede** |

Cada uma tem rótulo, ícone Lucide e identidade de série, no mesmo formato de
`vocabulary.categories` — e, como as séries, a cor de despesa entra na régua de contraste como
forma **e** como texto de chip.

### Categoria de entrada

| Categoria | Nota |
|---|---|
| `salario` | tem dia previsto; é o que ancora o calendário |
| `decimo_terceiro` | evento de sobra maior, só para CLT |
| `ferias` | idem |
| `renda_variavel` | PJ, autônomo, comissão — sem data previsível |
| `reembolso` | entra e não é renda; não deve inflar a média de renda |
| `outros` | — |

**`provento` não está nesta lista, e isso é uma decisão pendente, não um esquecimento.** Provento
creditado é entrada de caixa **e** lançamento do razão, e o razão já é a fonte da carteira. Se as
duas coisas coexistirem sem regra, o mesmo dinheiro conta duas vezes — infla a renda do mês e a
sobra junto. As saídas possíveis são três: provento não entra no caixa e vive só no razão; entra
no caixa e é excluído da média de renda; ou o caixa lê o razão e a entrada é derivada, não
lançada. **É pergunta de domínio, e precisa de decisão antes de `cashflow/` existir** — a terceira
opção é a única que não cria segunda verdade, e é também a que acopla os dois módulos.

### Tipo de dívida — e o que ele deliberadamente **não** carrega

| Tipo | Cobre |
|---|---|
| `rotativo_cartao` | saldo não pago da fatura |
| `cheque_especial` | limite usado na conta |
| `credito_pessoal` | empréstimo sem garantia, consignado |
| `financiamento_imovel` | — |
| `financiamento_veiculo` | — |
| `parcelamento` | compra parcelada, parcelamento de fatura |
| `outros` | — |

**O tipo não diz se a dívida é cara.** A
[regra](../produto/REGRAS_DE_DOMINIO.md#dívida) é explícita: *"classificar a dívida por
custo, não por tipo"*. Cara e administrável são **derivados da taxa** contra o que a carteira da
pessoa rende — e por isso não existe campo `caro: true` no vocabulário. Se existisse, o código
classificaria por instrumento, que é exatamente o que a regra proíbe: consignado a 1,2% ao mês e
consignado a 3,5% ao mês não são a mesma decisão.

Consequência: **sem taxa informada não há classe**, e a tela diz isso. O produto não estima taxa
de rotativo, porque varia por banco e por dia, e errar aqui é pior que não mostrar nada.

## Componentes base

Contrato mínimo de cada um: **estados** (default/hover/focus/active/disabled/loading) ·
**nome acessível obrigatório** · **zero hex** · **densidade respeitada**.

| Componente | Notas específicas do fiance |
|---|---|
| `Button` | `FiButton`: primária (marca) · secundária (fio) · discreta (tinta) · destrutiva. **Uma primária por contexto**, e a hierarquia é declarada em `FiActions` |
| `IconButton` | `tooltip`/rótulo semântico **obrigatório**, e `test/lint_ui_test.dart` reprova quem não tem |
| `Input` / `Money` / `Percent` | variantes numéricas com cifras tabulares, alinhamento à direita e máscara pt-BR |
| `Select` / `Segmented` | segmented substitui tab quando há 2–4 opções mutuamente exclusivas |
| `Tabs` | `role="tablist"`/`aria-selected`, navegação por setas, **estado na URL** |
| `Card` | `FiObject`, e **só** para objeto acionável — uma posição, um título, uma oportunidade, um alerta com ação própria. Seção é `FiSection` (fio + espaço); linha de dado é `FiDataRow` dentro de `FiRows`. `Card`, `ListTile` e `CircleAvatar` do Material estão em catraca zero |
| `Measure` | `FiMeasure` — a régua: valor, trilho, marca da referência, leitura. É o elemento-assinatura, e vale para score, saúde, desvio, progresso, margem e distância até um benchmark. `ScoreRuler` é a variante de score, com as bandas do sistema |
| `Headline` | `FiHeadline` — a abertura de tela: sobrancelha, cifra, leitura. Existe para que seis telas não inventem seis grafias da mesma coisa |
| `Tag` | `FiTag` — selo de estado (veredito, severidade) ou de identidade (categoria, série). Estado ganha superfície; identidade, só contorno |
| `Segments` | `FiSegments` — recorte de seção com peso de legenda. **Recorte não é ação**: ele muda o que se lê, e por isso não usa forma de botão |
| `Drawer` | 600px à direita, `role="dialog"`, focus trap, Esc, retorno de foco |
| `BottomSheet` | mobile; dois estágios (peek / cheio) |
| `Modal` | reservado a confirmação destrutiva. Não é o padrão de detalhe |
| `Tooltip` | glossário; acessível por teclado, não só hover |
| `Toast` | ação concluída/falhou; nunca informação que precisa persistir |
| `Table` | ordenar · esconder coluna · fixar 1ª coluna · densidade · virtualização. Degrada para lista no mobile |
| `Chart` | eixos, tooltip, linha de referência, anotação; **pergunta declarada no título** |
| `Badge` | cor + ícone + texto, sempre os três |
| `Skeleton` | composto na forma do conteúdo real (`FiSkeleton`) — a altura de cada forma é a do papel de tipografia que vai ocupar o lugar |
| `EmptyState` | `FiEmptyState`: causa + próximo passo executável. Nunca compartilha tela com `FiErrorState` — "não conseguimos ler" e "você não tem nada" são estados diferentes |
| `AsyncState` | os quatro estados num contrato só (esperando · falhou · vazio · conteúdo), para que uma tela não possa tratar três e esquecer o quarto: `AsyncValue.when` com `FiSkeleton`/`FiErrorState` |
| `ErrorState` | último dado + causa humana + repetir. Nunca exceção crua, nunca código de status: a frase sai de `fiErrorMessage`, uma só para o produto inteiro |
| `Nav` / `SubNav` / `BottomNav` | itens ≥44px; rótulo ≥12px |
| `SearchGlobal` | porta em todo destino de raiz (`FiSearchAction`); resultados por categoria (ativos, setores, telas) |
| `Provenance` | rodapé padrão: fonte, método, limitação — **momento não**, que é linha visível |
| `DataAge` | quando a fonte foi lida, ao lado do número que ela qualifica. Em lista, o carimbo é o **mais antigo** |

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
  **"Sem dado"**.

**Rótulos novos:** `Forte` · `Boa` · `Neutra` · `Fraca`, substituindo "Excelente entrada" /
"Boa oportunidade" / "Neutro" / "Evitar agora". Os limiares não mudam; a linguagem deixa de dar
ordem e passa a descrever a leitura (briefing §10 e §43). Muda nas três plataformas no mesmo
commit, com o Python primeiro.

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
| verificar as 3 classes de `dipDiagnosis` | verificação | `DipAnalysis` real precisa sustentar a separação; se não, ficam 2 |

Nenhum algoritmo novo. O redesign consome o que o backend já calcula.
