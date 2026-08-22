# Fase 4 — Jornadas do usuário

> Cada jornada é escrita contra a IA de [02-INFORMATION-ARCHITECTURE.md](02-INFORMATION-ARCHITECTURE.md)
> e usa **apenas** endpoints que já existem. Onde um passo depende de dado que o backend não
> tem, isso está marcado explicitamente — nada é inventado.
>
> Formato: caminho · o que cada passo mostra · estado quando dá errado.

## Os três perfis

| | Iniciante | Intermediário | Avançado |
|---|---|---|---|
| `detail_level` | Essencial | Completo | Avançado |
| Métricas por bloco | 2–3 | 4–6 | todas |
| Jargão | sempre com explicação inline | tooltip | sem explicação |
| Entrada preferida | Hoje → ação sugerida | Descobrir / Carteira | Posições / Comparar / tabela |
| Densidade | confortável | confortável | compacta |

Não são três produtos: é o mesmo produto com nível de revelação diferente. Um iniciante que
clica em "ver detalhes" três vezes chega exatamente à tela do avançado.

---

## J1 — Primeiro acesso

**Hoje:** cai no dashboard vazio com 3 instruções em texto ("Vá em Meus Ativos e adicione...").
Perfil de risco e metas — que calibram score e sugestões — nunca são apresentados.

**Novo caminho** (3 passos, tudo mais adiável):

```
Login Google
  │
  ├─ 1. "Como você se descreve?"        → grava risk_profile em PUT /preferences
  │     começando · já invisto · invisto há anos
  │     (define detail_level inicial e o perfil de risco do score)
  │
  ├─ 2. "O que você quer deste app?"    → grava goals em PUT /goals
  │     renda mensal · crescer patrimônio · sair da renda fixa
  │     (1 pergunta, opcional: valor da meta)
  │
  └─ 3. "Você já tem investimentos?"
        ├─ sim → campo de ticker com autocomplete (GET /universe/search)
        │        1 posição basta. POST /portfolio/position
        │        "Adicione o resto quando quiser" → /carteira/editar
        └─ não → vai direto para Descobrir com o perfil já aplicado
```

Chega em `/hoje` com conteúdo real, não com vazio.

**Estado sem carteira** (usuário que escolheu "não"): `/hoje` mostra patrimônio zerado sem
fingir dado, e o bloco central passa a ser "comece por aqui" apontando para
`/descobrir/oportunidades` filtrado pelo perfil declarado. Carteira, Estratégia e Atividade
mostram vazio com causa e porta de entrada — nunca "nenhum dado encontrado".

**Contrato novo necessário:** marcador de onboarding concluído (para não repetir) e
`detail_level`. Sem eles, o onboarding pode ir ao ar reaparecendo a cada login — inaceitável.

---

## J2 — Retorno diário (a jornada mais frequente, alvo: 10 segundos)

```
/hoje
  N1  R$ 187.430   +1,2% no mês        ← tabular-nums, o número mais legível da tela
      "Carteira saudável"  ou  "Sua carteira merece atenção"
      └ 2–3 motivos, em texto: "concentração em PETR4 (14%)" · "FIIs 7 p.p. abaixo da meta"

  N2  O QUE MUDOU                      ← GET /whats-new (até 5 linhas, cada uma com ação)
      ↓ PETR4 caiu 8,4% hoje                          [Entender esta queda]
      ↓ R$ 340 de proventos creditados em novembro     [Ver proventos]
      ↓ CDB do Banco X vence em 12 dias                [Ver posição]

  N3  PRÓXIMA AÇÃO
      "Seu maior gap é FIIs: 7 p.p. abaixo da meta"    [Ver estratégia]

      Atualizado às 16:42 · CDI do BCB                 ← proveniência, sempre visível
```

O que **sai** da home: tabela de posições, dois gráficos, grid de oportunidades, bloco de
alertas. Nada disso desaparece do produto — cada um passa a viver na tela que responde por ele,
alcançável em um clique a partir da linha que o menciona.

**Estados:** sem mudança → o bloco diz "nada mudou desde ontem" (não some — comportamento que o
`whats-new` já tem hoje e é correto). Dado velho → valor preservado com selo de idade, nunca
substituído por skeleton. Erro → última leitura + causa + [tentar de novo].

---

## J3 — Adicionar/atualizar a carteira

```
/carteira  →  [Editar carteira]  →  /carteira/editar
    ├─ ATIVOS NEGOCIADOS      ticker (autocomplete) · qtd · preço médio   → POST /portfolio/position
    └─ RENDA FIXA             tipo · valor · taxa · indexador · vencimento · liquidez
                                                                          → POST /fixed-income
```

Mantém o acerto da auditoria anterior: escrita explícita por linha, sem autosave sobre
`PUT /portfolio` destrutivo. O que muda é só o enquadramento — "editar minha carteira" em vez de
"cadastro", e o retorno automático para `/carteira` com o item novo já marcado a mercado.

**Iniciante:** o formulário de RF explica cada campo inline (o que é indexador, o que muda entre
liquidez diária e no vencimento). **Avançado:** entrada em linha, tab entre campos, sem
explicação.

---

## J4 — Entender a própria carteira

```
/carteira                          valor · rentabilidade · alocação vs meta · veredito de saúde
  ├─ /carteira/composicao          classes → setores → concentração ("PETR4 = 14% da carteira")
  ├─ /carteira/desempenho          UM gráfico: carteira × CDI × IBOV, período selecionável
  │                                (GET /benchmark — retorno ponderado no tempo, com aportes
  │                                 mostrados como marcação, não como rentabilidade)
  ├─ /carteira/proventos           recebido × estimado pelo app, mês / 12 meses / média
  ├─ /carteira/posicoes            tabela densa: ticker · preço · var · score · valuation · DY ·
  │                                posição · rentabilidade · decisão   (RF integrada como classe)
  └─ /carteira/encerradas          lucro realizado · IR pago · prejuízo disponível a compensar
```

A fusão dos dois gráficos do dashboard atual em um só (achado #36) é o ganho estrutural aqui: a
pergunta real nunca foi "como evoluí?" isolada, foi "evoluí mais do que se eu tivesse ficado no
CDI?".

---

## J5 — Analisar um ativo (a tela mais importante do produto)

Entrada de qualquer lugar: busca global, Descobrir, Carteira → Posições, feed de Hoje,
sugestão de Estratégia.

```
/ativo/PETR4                                    ← GET /asset/PETR4
┌────────────────────────────────────────────────────────────────────────────┐
│ PETR4  Petróleo Brasileiro   Ação BR                                       │
│ R$ 38,42   −8,4% hoje              Score 87 · Forte                        │
│ ─────────────────────────────────────────────────────────────────────────  │
│ N1  "Negociando 22% abaixo do preço justo estimado, com fundamentos        │
│      estáveis e tendência neutra."          ← 1 frase, derivada de reasons  │
│      Decisão do sistema:  ● Interessante                                   │
└────────────────────────────────────────────────────────────────────────────┘
  N2  gráfico de preço  ── preço médio da sua posição ── preço justo estimado
      períodos: 1M 6M 1A 5A
  N2  margem de segurança: 22%     ← barra, não só número

  N3  VALUATION       cada método separado, nunca somados num número só
        Bazin    R$ 49,30    +28%    dividendo médio de 5 anos ÷ 6%
        Graham   R$ 46,10    +20%    √(22,5 × LPA × VPA)
        DCF      R$ 51,00    +33%    crescimento projetado, % a.a.
        Consenso R$ 48,80            3 métodos · confiança 82%
  N3  FUNDAMENTOS     só os relevantes para o tipo de ativo
  N3  TÉCNICA         tendência · SMA 50/200 · RSI(14) · distância do topo 52s
  N3  PROVENTOS       DY · histórico · consistência (anos encontrados)

  N4  [ver como calculamos]  insumos do DCF · base da tendência · completude do dado

  AÇÕES  Comparar · Criar alerta · Adicionar à carteira · Entender a queda
```

Regras que essa tela impõe ao design system:
- Cada método de valuation exibe **preço estimado + preço atual + margem + metodologia**.
  Nunca um número de "preço justo" sem dizer de onde vem.
- FII não mostra Graham; ETF mostra só Bazin; BDR mostra Graham + DCF. O roteamento por tipo é
  do backend (`fair_price.py`) — a UI **não decide, só reflete** e explica a ausência
  ("Graham não se aplica a FII") em vez de deixar um campo vazio.
- Score com `data_completeness` baixo sai cinza e rotulado "dado insuficiente" — nunca colorido
  como nota baixa. A regra já existe no backend e no Dart; o web precisa alcançá-la (achado #17).

---

## J6 — Encontrar uma oportunidade

```
/descobrir/oportunidades
  Radar categorizado — não uma lista única:
    ▸ Melhores agora        ▸ Abaixo do preço justo     ▸ Renda (DY alto)
    ▸ Qualidade             ▸ Em queda relevante        ▸ Renda fixa

  Cada item responde PRIMEIRO "por que apareceu?":
  ┌──────────────────────────────────────────────────────────────┐
  │ BBAS3   Banco do Brasil                        Score 81      │
  │ "Preço 14% abaixo do justo estimado; DY de 8,2% com          │
  │  6 anos de histórico."                                       │
  │ R$ 24,10   MS 14%   DY 8,2%                     [Ver ativo]  │
  └──────────────────────────────────────────────────────────────┘

  filtros na URL (categoria, DY mín, MS mín, só destaques)
```

Linguagem: nunca "compre", nunca "vai subir". Sempre observação + confiança declarada
(`confidence`, `data_years`, `consensus_methods` já vêm do backend) + o rótulo de estimativa.

**Desktop:** split view — lista à esquerda, `/ativo/:ticker` à direita, para varrer 10 ativos sem
ir-e-voltar (briefing §18). **Mobile:** lista + bottom sheet.

---

## J7 — Investigar uma queda

O fluxo que o briefing §11 pede — **queda → diagnóstico → evidências → valuation → conclusão** —
numa tela, sem cinco navegações:

```
/descobrir/quedas                          ← GET /dip-scanner
  Três grupos, com o critério visível em cada cabeçalho:

  QUEDA SAUDÁVEL          preço caiu, fundamentos preservados
  QUEDA PARA INVESTIGAR   preço caiu e alguma métrica piorou
  QUEDA ESTRUTURAL        preço caiu junto de deterioração relevante

  [item] → drawer                          ← GET /asset/{symbol}/dip-analysis
     1. A QUEDA        −18% em 30 dias · −24% do topo de 52 semanas
     2. DIAGNÓSTICO    uma frase + a classe acima
     3. EVIDÊNCIAS     breakdown do score por dimensão (valor, fundamentos,
                       técnico, dividendos) — o que sustenta a leitura
     4. VALUATION      preço justo por método × preço atual
     5. CONCLUSÃO      ● Interessante / ● Neutro / ● Atenção / ● Evitar + motivo
                       [Ver ativo completo]  [Criar alerta de preço]
```

As três classes são de apresentação: agrupam o que `dip_analysis.py` já devolve. **Se o veredito
do backend não permitir separar "investigar" de "estrutural" com o dado atual, os grupos são
dois, não três** — a Fase 8 verifica isso no `DipAnalysis` real antes de desenhar o terceiro.
Inventar um grupo que o backend não sustenta seria inventar informação financeira.

Nota: o endpoint SSE de análise progressiva (`/dip-scanner/stream`) foi **removido em
2026-08-19**. A experiência "coletando · analisando · comparando · concluindo" do briefing §11
não tem backend hoje. Fica registrada como possibilidade futura; o que se implementa agora é o
skeleton em 5 etapas do drawer, refletindo a estrutura real do conteúdo que está carregando.

---

## J8 — Montar/ajustar a estratégia (a feature revivida)

```
/estrategia                                ← GET /strategy
  N1  "Onde você está × onde deveria estar"
      ┌────────────┬───────┬──────┬───────┐
      │ Categoria  │ Atual │ Meta │  Gap  │
      ├────────────┼───────┼──────┼───────┤
      │ Ações BR   │  42%  │ 35%  │  +7   │
      │ FIIs       │  18%  │ 25%  │  −7   │   ← maior gap, destacado
      │ Renda fixa │  40%  │ 40%  │   0   │
      └────────────┴───────┴──────┴───────┘

  N2  "Seu maior gap está em FIIs."
      "Para aproximar sua carteira da meta, o próximo aporte poderia priorizar FIIs."
                                              ↑ sugestão, claramente rotulada como tal
  N3  SUGESTÕES POR CATEGORIA     com a razão de cada uma
  N3  POSIÇÕES PARA REVISAR       veredito SELL/STRONG_SELL + por quê
  N3  ALOCAÇÃO PROJETADA          atual → projetada, se seguir o plano
  N3  O QUE VOCÊ SEGUIU           resultado × Ibovespa  ← /suggestions/followed

  [Tenho dinheiro para aportar]  →  /estrategia/aporte
  [Ajustar minhas metas]         →  /estrategia/metas
```

A separação que o briefing §12 exige fica explícita na própria hierarquia visual:
**informação** (a tabela) · **cálculo** (o gap) · **sugestão** (rotulada, com o motivo) ·
**ação do usuário** (o botão). Nunca uma sugestão sem que se veja de onde saiu.

## J9 — "Recebi dinheiro, onde aporto" (Quick Invest)

Quatro perguntas, uma tela, no máximo dois scrolls no celular:

```
/estrategia/aporte                         ← POST /quick-invest
  1. Quanto?                R$ [__________]
  2. Ordem mínima           R$ [__________]   (opcional)
  3. O que está abaixo da meta?  ← respondido pelo app, não perguntado
       FIIs (−7 p.p.) · Renda fixa (0)
  4. Opções que atendem                     ← lista com valor a alocar por ativo
       + a lógica: "priorizamos FIIs porque é seu maior gap; entre os FIIs,
         ordenamos por score ajustado ao seu perfil moderado"

  [Registrar o que eu executei]  → POST /suggestions/followed   (fecha o ciclo)
```

## J10 — Acompanhar renda fixa

```
/carteira/posicoes        RF como classe par das outras — taxa efetiva, valor hoje,
                          rendimento, no vencimento, liquidez, aviso de vencimento próximo
/estrategia/renda-fixa    a decisão, com duas perguntas na mesma tela:
                            "entre estes títulos, qual rende mais?"   ← /renda-fixa/comparar
                            "CDB ou FII?"                             ← /income-compare
```

Contexto obrigatório, nunca a taxa nua:

> "Rende aproximadamente **112% do CDI** líquido" · "Protege da inflação **+ 6,2% de juro real**"
> · "Resgate só no vencimento (**abril de 2028**)" · "Isento de IR"

E a honestidade que o `income_compare_service` já implementa: valorização potencial mostrada
**separada** — renda fixa não tem, e a tela diz isso.

## J11 — Acompanhar proventos

```
/carteira/proventos
  N1  Recebido no mês · últimos 12 meses · média mensal
  N2  linha do tempo por mês, com o tipo (dividendo/rendimento/amortização)
  N3  recebido × estimado pelo app        ← o confronto que torna o produto auditável
  N3  quebra por ativo
  [Lançar provento recebido]  → POST /dividends/received
```

## J12 — Configurar alertas

```
/voce/alertas
  [Novo alerta]  PETR4  ▾  quando ficar  abaixo de ▾  R$ [32,00]
  ATIVOS         lista com o disparo, se houve
  ENTREGA        push (requer o app instalado — dito com clareza no web)
                 alertas de preço: imediatos
                 resumo de oportunidades: off / diário / semanal / mensal
```

Atalho contextual: criar alerta a partir de `/ativo/:ticker` já vem com o ticker preenchido.

**Microcopy — a regra:** o disparo nunca aparece como código.
`DIP_THRESHOLD_TRIGGERED` → **"PETR4 caiu 8,4% hoje."**

---

## Cobertura das 8 perguntas do briefing §2

| Pergunta | Onde é respondida | Em quantos cliques |
|---|---|---|
| Quanto eu tenho? | `/hoje` N1 | 0 |
| Como minha carteira está? | `/hoje` N1 (veredito) | 0 |
| O que mudou? | `/hoje` N2 (feed) | 0 |
| Existe algum problema? | `/hoje` N1 (motivos) + Atividade "Agora" | 0–1 |
| Existe alguma oportunidade? | `/hoje` N3 + `/descobrir` | 0–1 |
| O que merece atenção agora? | `/hoje` N3 (próxima ação) | 0 |
| Por que o fiance recomenda isso? | ação do insight → tela dona, com o "por quê" | 1 |
| Qual a próxima ação possível? | ação primária de cada insight | 1 |

Sete das oito são respondidas **sem rolar** na home. É o teste que a Fase 5 (wireframes) tem de
passar.
