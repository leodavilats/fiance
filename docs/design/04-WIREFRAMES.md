# Fase 5 — Wireframes

> Estrutura antes de visual. Aqui não há cor, ícone nem tipografia — só hierarquia, ordem de
> leitura e estados. Cada bloco anota o **nível** de disclosure (N1–N4, ver
> [02](02-INFORMATION-ARCHITECTURE.md)) e o **endpoint** que o alimenta.
>
> Notação: `[Botão]` · `(link)` · `▸` acordeão fechado · `▾` aberto · `░` skeleton ·
> `│` hairline · `·····` limite de dobra em 900px de altura.

---

## Shell — desktop (≥1280px)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ fiance      Hoje  Carteira  Descobrir  Estratégia            [⌘K buscar]  ⚲  ◔  ⬤   │  56px
├────────┬─────────────────────────────────────────────────────────────────────────────┤
│        │                                                                             │
│  sub-  │   CONTEÚDO                                    ┌─ painel contextual ───┐      │
│  nav   │   largura máxima 1120px para leitura;         │  (drawer, sob demanda) │      │
│  da    │   full-bleed para tabela e split view         │  Atividade · detalhe   │      │
│  seção │                                               └────────────────────────┘      │
│ 200px  │                                                                             │
└────────┴─────────────────────────────────────────────────────────────────────────────┘
   ⚲ busca  ◔ Atividade (drawer)  ⬤ conta → /voce
```

Regras do shell:
- Nav primária **horizontal no topo** com 4 itens de trabalho; `/voce` fica no avatar. Sidebar
  vertical não se justifica com 5 destinos e rouba largura de tabela.
- Sub-nav da seção à esquerda, largura fixa 200px, **só quando a seção tem sub-rotas** (Carteira,
  Descobrir, Estratégia, Você). Hoje e Ativo ocupam a largura inteira.
- Container adaptativo: 1120px para leitura, **até 1600px** em `/carteira/posicoes`,
  `/descobrir/*` (split view) e `/descobrir/comparar`. O `max-w-[1180px]` global sai.
- Painel contextual é drawer da direita (600px), nunca modal centralizado — modal interrompe,
  drawer contextualiza.

## Shell — mobile

```
┌──────────────────────────┐        Bottom nav: 5 destinos, 56px + safe area
│ ⚲ Buscar ativo      ◔ ⬤ │        Sem tabs aninhadas em nenhuma tela.
├──────────────────────────┤        Detalhe = bottom sheet expansível.
│                          │        Filtro = bottom sheet (padrão já acertado
│   CONTEÚDO               │                 em _FiltersSheet).
│   rolagem única          │        Troca de sub-seção = segmented control,
│                          │                 nunca TabBar de 5 itens.
├──────────────────────────┤
│ Hoje Carteira Desc. Est. Mais │
└──────────────────────────┘
```

---

## 1. `/hoje` — a central de decisão

### Desktop

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│  PATRIMÔNIO                                        N1 · GET /dashboard               │
│  R$ 187.430,22                                                                       │
│  ↑ R$ 2.214  ·  +1,20%  ·  no mês ▾                    ← período trocável, na URL    │
│                                                                                      │
│  ───────────────────────────────────────────────────────────────────────────────      │
│                                                                                      │
│  Carteira saudável                                 N1 · veredito, 1 frase, serif     │
│  │ Concentração: PETR4 é 14% da carteira                                             │
│  │ FIIs estão 7 p.p. abaixo da sua meta                                              │
│                                                       (ver a carteira inteira →)     │
│                                                                                      │
│  ───────────────────────────────────────────────────────────────────────────────      │
│                                                                                      │
│  O QUE MUDOU                                       N2 · GET /whats-new (máx. 5)      │
│                                                                                      │
│   ▪  PETR4 caiu 8,4% hoje                                    [Entender esta queda]   │
│   ▪  R$ 340 de proventos creditados em novembro              [Ver proventos]          │
│   ▪  CDB Banco X vence em 12 dias                           [Ver posição]            │
│   ▪  Prejuízo de R$ 1.240 disponível para abater IR         [Ver operações]          │
│                                                                                      │
│  ···························· dobra em 900px ·······································  │
│                                                                                      │
│  PRÓXIMA AÇÃO                                      N3 · derivado de /strategy         │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │  FIIs estão abaixo da sua meta                                                 │  │
│  │  Sua exposição está 6,8 p.p. abaixo do objetivo — o maior gap atual.           │  │
│  │                                                        [Ver estratégia]         │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  OPORTUNIDADES EM DESTAQUE                         N3 · GET /opportunities, top 2    │
│   BBAS3  score 81   "14% abaixo do justo, DY 8,2% com 6 anos de histórico"     →     │
│   HGLG11 score 78   "P/VP 0,88 com vacância estável"                          →     │
│                                                       (ver todas as 34 →)            │
│                                                                                      │
│  ────────────────────────────────────────────────────────────────────────────────     │
│  Cotações de 16:42 · CDI e Selic do Banco Central · estimativas, não garantias        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**Saíram da home** (cada um para a tela dona): tabela de posições → `/carteira/posicoes`;
gráfico de patrimônio + benchmark → `/carteira/desempenho`; grid de oportunidades →
`/descobrir/oportunidades`; alertas → drawer Atividade; sinais de venda → `/estrategia`;
progresso da meta → uma linha no feed + `/estrategia/metas`.

**Ganho medido:** 10 blocos → 5. Sete das oito perguntas do briefing §2 respondidas acima da
dobra.

### Mobile

```
┌──────────────────────────┐
│ R$ 187.430,22            │  N1 — o número mais legível do app
│ ↑ 1,20% no mês           │
│ ─────────────────────────│
│ Carteira saudável        │  N1 — veredito em serif
│ · PETR4 = 14%            │
│ · FIIs −7 p.p.           │
│ ─────────────────────────│
│ O QUE MUDOU              │  N2 — feed é o corpo da tela no celular
│ PETR4 caiu 8,4%      →   │
│ R$ 340 de proventos  →   │
│ CDB vence em 12d     →   │
│ ─────────────────────────│
│ ┌──────────────────────┐ │
│ │ Maior gap: FIIs −7pp │ │  N3 — ação primária, alcance do polegar
│ │      [Ver estratégia]│ │
│ └──────────────────────┘ │
│ 16:42 · CDI do BCB       │
└──────────────────────────┘
```

### Estados de `/hoje`

| Estado | Comportamento |
|---|---|
| Carregando (1ª vez) | Skeleton **com a forma real**: um bloco de valor alto, uma frase larga, 4 linhas de feed. Não um retângulo genérico |
| Carregando (refresh) | Valores antigos permanecem, com barra de progresso fina no topo. Nunca esvaziar a tela que já tinha conteúdo |
| Sem carteira | Patrimônio não é exibido como R$ 0,00. Bloco único: "Sua carteira ainda está vazia — adicione uma posição para o fiance começar a analisar" + [Adicionar primeira posição] + (ou explorar o mercado) |
| Carteira pequena (1–3 ativos) | Veredito de saúde é substituído por "Carteira ainda pequena para avaliar concentração" — honesto, em vez de "concentração crítica: 100% em PETR4" |
| Nada mudou | Feed diz "Nada mudou desde ontem" — o bloco não desaparece |
| Dado velho (`market_data_stale`) | Valores mantidos + selo "cotações de ontem, 18:05" no topo do bloco, não só no rodapé |
| Erro | Última leitura conhecida + "Não conseguimos atualizar agora" + causa + [Tentar de novo]. Nunca tela branca |
| Offline (mobile) | Último snapshot + faixa "sem conexão · dados de 16:42" |

---

## 2. `/carteira`

### Resumo (desktop)

```
Carteira │ Composição │ Desempenho │ Proventos │ Posições │ Encerradas    [Editar carteira]
─────────┴────────────────────────────────────────────────────────────────────────────────
  R$ 187.430,22        Investido R$ 164.100      Resultado ↑ R$ 23.330 · +14,2%      N1
  ────────────────────────────────────────────────────────────────────────────────────
  ALOCAÇÃO × META                                            N1 · GET /goals + /portfolio
    Ações BR   ▮▮▮▮▮▮▮▮▮▮▮▮▯▯▯  42%   meta 35%   +7 p.p.
    FIIs       ▮▮▮▮▮▮▯▯▯▯▯▯▯▯▯  18%   meta 25%   −7 p.p.   ← maior gap
    Renda fixa ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮  40%   meta 40%     0
                                                        (ajustar metas →)
  ────────────────────────────────────────────────────────────────────────────────────
  SAÚDE                                                      N2 · as 4 dimensões
    Concentração 72 │ Setor 65 │ Diversificação 80 │ Risco 88
    ▸ O que cada dimensão considera                          N3 · acordeão
  ────────────────────────────────────────────────────────────────────────────────────
  Maior posição PETR4 14%  ·  12 ativos em 5 setores  ·  RF vencendo em 12 dias: 1
```

O gráfico **não** aparece no resumo: quem quer a curva vai em Desempenho. O resumo responde
"quanto, comparado a quê" com números e barras — mais rápido de ler que qualquer gráfico.

### Posições (desktop — a tabela profissional)

```
                                             [⚙ colunas] [densidade: compacta ▾] [↓ CSV]
┌───────┬────────┬────────┬───────┬───────────┬──────┬──────────┬──────────┬───────────┐
│TICKER↓│  PREÇO │   VAR  │ SCORE │ VALUATION │  DY  │  POSIÇÃO │  RESULT. │  DECISÃO  │
├───────┼────────┼────────┼───────┼───────────┼──────┼──────────┼──────────┼───────────┤
│PETR4  │  38,42 │ −8,40% │  87 ▮ │ −22% just │ 12,1%│ 26.894   │ ↑ 14,2%  │ Interess. │
│HGLG11 │ 158,10 │ +0,30% │  78 ▮ │  −9% just │  9,4%│ 18.972   │ ↑  3,1%  │ Neutro    │
│CDB BX │      — │      — │     — │        —  │  —   │ 25.000   │ ↑  8,9%  │ vence 12d │  ← RF na mesma tabela
└───────┴────────┴────────┴───────┴───────────┴──────┴──────────┴──────────┴───────────┘
  ticker fixo à esquerda no scroll horizontal · clique na linha → /ativo/:ticker
  seleção múltipla (até 4) → [Comparar]      RF sem cotação mostra "—", não zero
```

Renda fixa entra **na mesma tabela** como classe par (decisão de IA): colunas de mercado ficam
`—` e as de posição/resultado são preenchidas pela marcação a mercado do backend. Hoje RF é um
bloco anexo, o que contradiz "renda fixa é entidade de primeira classe".

### Posições (mobile — lista, não tabela)

```
┌──────────────────────────┐
│ [Todas ▾] [ordenar ⇅]    │  filtro e ordenação em bottom sheet
│ ─── AÇÕES BR  42% ────── │  agrupado por classe, com peso do grupo
│ PETR4          26.894    │
│ 38,42  −8,4%   87 ▮  ↑14%│  4 dados por linha, no máximo
│ HGLG11         18.972    │
│ ...                      │
│ ─── RENDA FIXA  40% ──── │
│ CDB Banco X    25.000    │
│ 112% CDI · vence em 12d  │  RF fala a língua dela, não a de ação
└──────────────────────────┘
  toque → bottom sheet do ativo (expansível até tela cheia)
```

### Outras sub-telas

- **Composição** — classes → setores → concentração, em três níveis do mesmo gráfico + a lista
  ao lado (gráfico sem lista é decorativo). Pergunta declarada no título: "Onde meu dinheiro
  está concentrado?"
- **Desempenho** — **um** gráfico: carteira × CDI × IBOV (`GET /benchmark`, TWR), período na
  URL, aportes marcados como ticks na linha do tempo (não como rentabilidade). Título:
  "Estou rendendo mais do que se tivesse ficado no CDI?"
- **Proventos** — N1 três números (mês / 12 meses / média); N2 linha do tempo por mês; N3
  recebido × estimado pelo app; N3 quebra por ativo; `[Lançar provento]` em drawer.
- **Encerradas** — N1 lucro realizado + IR pago + prejuízo a compensar; N2 tabela. O prejuízo a
  compensar ganha destaque: é dinheiro que o usuário recupera e hoje está enterrado.
- **Editar** — dois grupos (negociados, renda fixa), escrita por linha, sem autosave. Estrutura
  atual preservada; muda o enquadramento e o retorno para `/carteira`.

---

## 3. `/ativo/:ticker` — a página de research

### Desktop

```
(← Oportunidades)                                     ← breadcrumb preserva a origem
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ PETR4   Petróleo Brasileiro S.A.   Ação BR              [Comparar] [Alertar] [+Carteira]│
│                                                                                      │
│ R$ 38,42        −8,40% hoje                    SCORE  ▮▮▮▮▮▮▮▮▯▯  87  Forte          │
│                                                       └ ScoreRuler, tamanho página   │
│ ────────────────────────────────────────────────────────────────────────────────────│
│ "Negociando 22% abaixo do preço justo estimado, com fundamentos estáveis e            │  N1
│  tendência neutra."                                          ● Interessante          │  serif
│ ────────────────────────────────────────────────────────────────────────────────────│
│                                                                                      │
│  ┌── preço ─────────────────────────────────────┐   MARGEM DE SEGURANÇA        N2   │
│  │                                              │   ▮▮▮▮▮▮▮▮▯▯▯▯  22%              │
│  │        ╱╲     ── preço justo 48,80           │   └ mesma régua do score          │
│  │   ╲  ╱   ╲╱   ── seu preço médio 33,10       │                                   │
│  │    ╲╱         ●                              │   SUA POSIÇÃO                     │
│  │                                              │   700 un · R$ 26.894 · ↑14,2%     │
│  │  1M  6M  1A  5A                              │                                   │
│  └──────────────────────────────────────────────┘                                   │
│                                                                                      │
│  VALUATION                                              N3 · nunca somados          │
│  ┌────────┬───────────┬─────────┬────────────────────────────────────────────────┐  │
│  │ Bazin  │ R$ 49,30  │  +28%   │ dividendo médio de 5 anos ÷ yield desejado 6%  │  │
│  │ Graham │ R$ 46,10  │  +20%   │ √(22,5 × LPA × VPA)                            │  │
│  │ DCF    │ R$ 51,00  │  +33%   │ fluxo descontado, crescimento 4,2% a.a.        │  │
│  ├────────┼───────────┼─────────┼────────────────────────────────────────────────┤  │
│  │Consenso│ R$ 48,80  │  +27%   │ 3 métodos · confiança 82% · 6 anos de provento │  │
│  └────────┴───────────┴─────────┴────────────────────────────────────────────────┘  │
│                                                                                      │
│  ▸ FUNDAMENTOS       ROE 28% · margem 21% · D/E 0,74 · crescimento 6,1%       N3    │
│  ▸ TÉCNICA           tendência neutra · SMA50 39,80 / SMA200 41,20 · RSI 42   N3    │
│  ▸ PROVENTOS         DY 12,1% · 6 anos consecutivos · último R$ 1,12         N3    │
│  ▸ COMO CALCULAMOS   insumos, base da tendência, completude do dado          N4    │
│                                                                                      │
│  Cotação de 16:42 · fundamentos da BRAPI · estimativa, não garantia de retorno       │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Regras que esta tela impõe:
- Método não aplicável **diz por quê**: em FII, a linha Graham é substituída por
  "Graham não se aplica a fundo imobiliário" — nunca campo vazio. O roteamento por tipo vem de
  `fair_price.py`; a UI reflete.
- `data_completeness < 0.5` → score em cinza + "dado insuficiente", nunca colorido como nota
  baixa (regra que já existe no backend e no Dart e falta no web).
- Sem posição na carteira, o cartão "Sua posição" vira `[Adicionar à carteira]`.

### Split view em Descobrir (desktop ≥1440px)

```
┌── lista ──────────┬── /ativo/:ticker embutido ─────────────────────────┐
│ ▸ BBAS3   81      │  PETR4 …                                          │
│ ▸ HGLG11  78      │  (a mesma tela acima, sem breadcrumb)             │
│ ▸ PETR4   87  ◀   │                                                   │
│ ▸ …               │                                                   │
└───────────────────┴───────────────────────────────────────────────────┘
  ↑↓ navega a lista sem perder o painel — varrer 10 ativos sem ir-e-voltar
```

### Mobile

Bottom sheet em dois estágios: **peek** (ticker, preço, score, veredito de 1 frase, ações) →
**arrastar para cima** = tela cheia com o restante. O usuário decide em 2 segundos no peek e
aprofunda só se quiser.

---

## 4. `/descobrir/oportunidades` — radar

```
[Todas ▾] [DY mín] [MS mín] [☐ só destaques]                      filtros na URL
─────────────────────────────────────────────────────────────────────────────────
MELHORES AGORA · 4                                       GET /opportunities
┌──────────────────────────────────────────────────────────────────────────────┐
│ BBAS3  Banco do Brasil            Ação BR                    ▮▮▮▮▮▮▮▮▯▯ 81  │
│ "Preço 14% abaixo do justo estimado; DY de 8,2% com 6 anos de histórico."    │ ← por que
│ R$ 24,10   MS 14%   DY 8,2%   P/L 4,2                                    →  │   apareceu
└──────────────────────────────────────────────────────────────────────────────┘
ABAIXO DO PREÇO JUSTO · 11        ▸
RENDA (DY ALTO) · 7               ▸
QUALIDADE · 5                     ▸
EM QUEDA RELEVANTE · 6            ▸  (ver o scanner de quedas →)
RENDA FIXA · 3                    ▸  (comparar títulos →)
```

Categorias são agrupamentos de apresentação sobre o mesmo `GET /opportunities` — o critério de
cada uma aparece no cabeçalho ao expandir. Só a primeira categoria vem aberta: a tela abre com
4 itens, não com 36.

**Linguagem obrigatória:** observação + confiança, nunca promessa. "Preço 14% abaixo do justo
estimado" ✓ · "BBAS3 vai subir" ✗ · "Compre BBAS3" ✗.

---

## 5. `/descobrir/quedas` — dip com diagnóstico

```
QUEDA SAUDÁVEL · 4          preço caiu, fundamentos preservados
  PETR4  −18% em 30d   score 87   "queda acompanhou o setor; ROE e margem estáveis"  →
QUEDA PARA INVESTIGAR · 3   preço caiu e alguma métrica piorou
  XPTO3  −22% em 30d   score 54   "margem caiu de 18% para 11% no mesmo período"     →
QUEDA ESTRUTURAL · 2        preço caiu junto de deterioração relevante
  ABCD4  −41% em 90d   score 22   "endividamento e margem pioraram; sem provento há 2 anos" →
```

Drawer de diagnóstico — o fluxo do briefing §11 numa tela:

```
┌─ PETR4 · por que está aqui ─────────────────────────────────────┐
│ 1  A QUEDA          −18% em 30 dias · −24% do topo de 52 semanas│
│ 2  DIAGNÓSTICO      Queda saudável                              │
│                     "Fundamentos preservados no período."       │
│ 3  EVIDÊNCIAS       valor        ▮▮▮▮▮▮▮▮▮▯                     │
│                     fundamentos ▮▮▮▮▮▮▮▮▯▯                     │
│                     técnico     ▮▮▮▮▮▯▯▯▯▯                     │
│                     dividendos  ▮▮▮▮▮▮▮▮▮▮                     │
│ 4  VALUATION        justo 48,80 × atual 38,42 → margem 22%      │
│ 5  CONCLUSÃO        ● Interessante — motivo em 1 frase          │
│                     [Ver ativo]  [Criar alerta]                 │
└─────────────────────────────────────────────────────────────────┘
```

**Verificação obrigatória na Fase 8:** as três classes precisam ser deriváveis do `DipAnalysis`
real. Se o veredito atual não separar "investigar" de "estrutural", **são dois grupos**, não
três. Não se inventa classificação financeira para preencher um wireframe.

O skeleton deste drawer tem as 5 etapas numeradas visíveis enquanto carrega — a "análise viva"
do briefing §11 sem SSE (o endpoint `/dip-scanner/stream` foi removido em 2026-08-19).

---

## 6. `/estrategia`

```
Plano │ Aporte │ Metas │ Renda fixa │ Projeção
──────┴────────────────────────────────────────────────────────────────────────────
ONDE VOCÊ ESTÁ × ONDE DEVERIA ESTAR                    N1 · GET /strategy
┌────────────┬───────┬──────┬───────┐
│ Categoria  │ Atual │ Meta │  Gap  │
│ Ações BR   │  42%  │ 35%  │  +7   │
│ FIIs       │  18%  │ 25%  │  −7   │ ◀ maior gap
│ Renda fixa │  40%  │ 40%  │   0   │
└────────────┴───────┴──────┴───────┘                       (ajustar metas →)
─────────────────────────────────────────────────────────────────────────────────
Seu maior gap está em FIIs.                                N2 · cálculo
Para aproximar sua carteira da meta, o próximo aporte
poderia priorizar FIIs.                                    N2 · sugestão (rotulada)
                                        [Tenho dinheiro para aportar]  N2 · ação
─────────────────────────────────────────────────────────────────────────────────
▸ SUGESTÕES POR CATEGORIA · 6      cada uma com a razão            N3
▸ POSIÇÕES PARA REVISAR · 2        veredito de venda + por quê     N3
▸ ALOCAÇÃO PROJETADA               atual → projetada               N3
▸ O QUE VOCÊ SEGUIU · 4            resultado × Ibovespa            N3
```

As quatro camadas do briefing §12 são visualmente distintas por posição e peso:
**informação** (tabela) · **cálculo** (a frase do gap) · **sugestão** (texto rotulado como
sugestão) · **ação** (botão). Nunca uma sugestão sem o cálculo visível acima dela.

### `/estrategia/aporte` — Quick Invest

```
Quanto você quer aportar?      R$ [ 3.000,00 ]
Ordem mínima (opcional)        R$ [   500,00 ]
                                                     [Ver onde aportar]
─────────────────────────────────────────────────────────────────────────
ABAIXO DA META            FIIs −7 p.p. · Renda fixa 0        ← app responde,
                                                                não pergunta
SUGESTÃO                                          POST /quick-invest
  HGLG11   R$ 1.500   FII · score 78 · P/VP 0,88
  XPLG11   R$ 1.000   FII · score 74 · DY 9,1%
  sobra    R$   500   abaixo da ordem mínima
▸ POR QUE ESTA DISTRIBUIÇÃO
  "Priorizamos FIIs porque é seu maior gap. Entre os FIIs disponíveis,
   ordenamos por score ajustado ao seu perfil moderado."
                                        [Registrei o que executei]  → /suggestions/followed
```

Três campos, uma resposta, a lógica atrás de um acordeão. É a tela mais curta do produto por
projeto — no celular cabe sem rolar.

### `/estrategia/metas`

```
RENDA PASSIVA MENSAL     R$ [ 3.000 ]        hoje: R$ 1.140 (38%)  ▮▮▮▮▯▯▯▯▯▯
ALOCAÇÃO POR CATEGORIA   Ações 35% · FIIs 25% · BDRs 5% · ETFs 5% · RF 30%   soma 100% ✓
                         ← sliders com a alocação ATUAL marcada na trilha
POR SETOR (ações e BDRs) ▸
```

A alocação atual marcada na própria trilha do slider é o detalhe que transforma o formulário em
ferramenta de decisão: o usuário vê o gap enquanto move a meta.

### `/estrategia/renda-fixa`

```
[ Comparar títulos ]  [ Renda fixa × bolsa ]        ← duas perguntas, uma tela

COMPARAR TÍTULOS                                     POST /renda-fixa/comparar
  título A: CDB · 112% do CDI · 24m · líquida diária
  título B: Tesouro IPCA+ · IPCA + 6,2% · 60m · no vencimento
  ┌─────────────────────────────────────────────────────────────────────┐
  │ CDB 112% do CDI          líquida 13,4% a.a.   ▮▮▮▮▮▮▮▮▯▯          │
  │ "Rende ~112% do CDI. Resgate a qualquer momento. IR de 17,5%."     │
  │ Tesouro IPCA+ 6,2%       líquida 11,8% a.a.   ▮▮▮▮▮▮▮▯▯▯          │
  │ "Protege da inflação + 6,2% de juro real. Resgate em abr/2028."    │
  └─────────────────────────────────────────────────────────────────────┘
  CDI 14,40% · Selic 14,40% · IPCA 5,00% — Banco Central, hoje

RENDA FIXA × BOLSA                                   GET /income-compare
  renda recorrente líquida a.a., mesma unidade dos dois lados
  + valorização potencial mostrada SEPARADA — renda fixa não tem, e a tela diz isso
```

---

## 7. `/voce`

```
Preferências │ Alertas │ Conta
─────────────┴──────────────────────────────────────────────────────────
NÍVEL DE DETALHE     ( ) Essencial  (•) Completo  ( ) Avançado
                     "Completo: métricas de valuation e score detalhado."
                     ← muda densidade, nº de métricas e verbosidade em todo o app
PERFIL DE RISCO      conservador · (•) moderado · agressivo
                     "Pondera o score: moderado equilibra valuation e dividendos."
                     ← todo controle diz o EFEITO, não só o nome
YIELD DESEJADO       ações 6% · FIIs 10% · BDRs 4% · ETFs 4%
                     "Entra no cálculo do preço-teto de Bazin."
PREFERIDOS           categorias · setores        EXCLUÍDOS  tickers
BENCHMARK PADRÃO     (•) CDI  ( ) IBOV
```

Cada controle explica **o efeito no produto**, não só o rótulo — hoje o usuário muda perfil de
risco sem saber que está mudando o score de todos os ativos.

`/voce/conta` recebe também: proveniência e limitações dos dados, **qualidade dos dados**
(`GET /data-quality`, hoje sem nenhuma UI) e limpar cache.

---

## 8. Onboarding

```
1/3  Como você se descreve?              → risk_profile + detail_level
     ( ) Estou começando        → Essencial + conservador
     ( ) Já invisto             → Completo + moderado
     ( ) Invisto há anos        → Avançado + moderado
2/3  O que você quer daqui?              → PUT /goals
     ( ) Renda mensal  ( ) Crescer patrimônio  ( ) Sair da renda fixa
     valor da meta (opcional)  R$ [______]
3/3  Você já tem investimentos?
     ( ) Sim → [ticker ▾] [qtd] [preço médio]  → POST /portfolio/position
               "Uma posição basta. Adicione o resto quando quiser."
     ( ) Ainda não → vai para Descobrir com o perfil já aplicado
                                              [Pular] sempre visível
```

Três perguntas, `[Pular]` em todas, nada mais. Exige um marcador de conclusão no backend
(mudança de contrato) para não reaparecer a cada login.

---

## 9. Matriz de estados — o contrato de toda tela

| Estado | Regra geral | Antipadrão a evitar |
|---|---|---|
| Loading 1ª vez | Skeleton com a **forma do conteúdo real** | Retângulo genérico; spinner de tela cheia |
| Loading refresh | Conteúdo antigo + progresso fino no topo | Esvaziar tela que já tinha dado |
| Vazio | Causa + próximo passo executável no bloco | "Nenhum dado encontrado." |
| Erro | Último dado + causa humana + [Tentar de novo] | `Text('Erro: $err')`; tela branca |
| Dados parciais | Valor + selo de completude ("62% dos indicadores") | Número parcial indistinguível de completo |
| Dado velho | Valor + idade ("cotações de ontem, 18:05") | Substituir por skeleton; exibir como atual |
| Atualizando | Progresso fino, sem bloqueio de interação | Overlay que congela a tela |
| Offline (mobile) | Último snapshot + faixa persistente | Erro de rede cru |
| 1ª utilização | Onboarding de 3 passos | Dashboard vazio com instruções em texto |
| Sem carteira | Porta de entrada em Hoje, Carteira, Estratégia | "R$ 0,00" como se fosse patrimônio |
| Carteira pequena | Análise de concentração suprimida com explicação | "100% concentrado em 1 ativo — crítico" |
| Carteira grande | Densidade compacta, agrupamento, paginação de tabela | Renderizar 200 linhas sem virtualização |

## 10. Responsividade

| Faixa | Nome | Comportamento |
|---|---|---|
| < 420px | mobile pequeno | 1 coluna · 3 dados por linha de lista · valores abreviados (R$ 187,4 mil) |
| 420–767 | mobile grande | 1 coluna · 4 dados por linha · valor cheio |
| 768–1023 | tablet | 2 colunas em Hoje e Carteira · tabela com scroll horizontal e ticker fixo |
| 1024–1279 | desktop pequeno | nav horizontal + sub-nav · conteúdo 1120px · sem split view |
| 1280–1439 | desktop | idem + drawer contextual |
| ≥ 1440 | desktop grande | **split view** em Descobrir · tabela até 1600px · 4 colunas em Comparar |

`xl:` e `2xl:` passam a ser usados de fato — hoje são zero ocorrências.
