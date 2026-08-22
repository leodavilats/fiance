# fiance — features por tela

> Inventário do que cada tela faz, organizado pela navegação **atual**. Revisado em 2026-08-22.
>
> Até esta revisão, este arquivo descrevia quatro telas — Dashboard, Meus Ativos (`/assets`),
> Mercado (`/market`) e Configurações (`/config`) — e nenhuma dessas rotas existe mais no web.
> Também carregava um changelog de 65 linhas no fim, que foi para [CHANGELOG.md](CHANGELOG.md).
>
> Estrutura, wireframes e o racional de cada decisão em [design/](design/).

## Navegação

Cinco destinos, agrupados por intenção do usuário — não pela topologia do backend.

| Destino | Pergunta que responde | Web | Mobile |
|---|---|---|---|
| **Hoje** | o que mudou e o que merece minha atenção? | `/hoje` | ✅ |
| **Carteira** | como está meu patrimônio? | `/carteira` | ✅ |
| **Descobrir** | o que eu poderia comprar? | `/descobrir` | ✅ |
| **Estratégia** | o que eu faço com o próximo aporte? | `/estrategia` | ✅ |
| **Você** | quero mudar como o app me trata | `/voce` | ✅ |
| **Ativo** | este ativo específico vale? | `/ativo/:ticker` | ✅ |

`/ativo/:ticker` é **camada, não destino**: não aparece na navegação e é alcançável de qualquer
lista. URLs antigas (`/dashboard`, `/assets`, `/market`, `/config`, `/strategy`) seguem como
redirect nas duas plataformas.

---

## Hoje

A central de decisão, em três níveis.

- **N1 — patrimônio:** valor atual, variação em R$ e %, e uma linha de apoio com investido, número
  de posições, DY médio e renda mensal estimada.
- **N1 — veredito de saúde:** uma frase ("Carteira saudável") mais 2–3 motivos em texto, ao lado da
  régua. Carteira com menos de 4 ativos **não** recebe leitura de risco — a régua sai indeterminada
  e o texto explica por quê.
- **N2 — o que mudou:** feed único ordenado por urgência, alimentado por `GET /whats-new` e pelos
  alertas de `GET /dashboard`, com uma ação por linha. Sem novidade, o bloco diz isso em vez de
  desaparecer.
- **N3 — próxima ação:** o maior desvio de alocação, com o cálculo visível antes da sugestão.
  Derivado de `allocations`, sem chamada extra.
- **N3 — em destaque:** as 3 melhores oportunidades, com o motivo antes dos números.
- **Rodapé:** idade da cotação, origem do CDI/Selic (BCB ou estimativa) e o aviso de estimativa.

Estados projetados: carga inicial (skeleton com a forma do conteúdo), atualização (dado antigo
preservado), carteira vazia, carteira pequena, nada mudou, dado velho, erro.

## Carteira

Sete sub-rotas, cada uma respondendo uma pergunta.

| Rota | Conteúdo |
|---|---|
| `/carteira` | valor, resultado, **alocação × meta** (trilha com o atual preenchido e a meta marcada) e as 4 dimensões de saúde |
| `/carteira/composicao` | pizza por classe ou por setor, sempre com a lista ao lado |
| `/carteira/desempenho` | evolução do patrimônio e carteira × CDI × Ibovespa (TWR), cada gráfico com a pergunta no título |
| `/carteira/proventos` | recebido no mês / 12 meses / média, quebra por ativo, e o confronto com a estimativa do app |
| `/carteira/posicoes` | tabela ordenável, seleção de até 4 para comparar, exportação CSV, renda fixa como classe par, venda parcial ou total |
| `/carteira/encerradas` | lucro realizado, IR pago e prejuízo disponível para compensar |
| `/carteira/editar` | escrita: CRUD de posições e de renda fixa, salvamento explícito por linha |

Renda fixa entra **na mesma tabela** das outras posições, falando a língua dela (taxa efetiva,
% do CDI, vencimento, liquidez) em vez de receber colunas de ação vazias. Marcada a mercado no
backend; aviso de vencimento em até 30 dias.

As sete rotas compartilham `CarteiraStore` — trocar de sub-aba não refaz
`POST /portfolio/evaluate`, que é a chamada mais caras do produto.

## Descobrir

- **Oportunidades** (`/descobrir/oportunidades`) — varredura do universo com score e preço justo.
  Cada item responde **por que apareceu** antes de mostrar números. Filtros na URL. Clicar leva ao
  ativo; "Entender queda" abre o diagnóstico.
- **Quedas** (`/descobrir/quedas`) — scanner de dip com drawer de diagnóstico: a queda, a leitura,
  as evidências (breakdown do score), o valuation e a conclusão.
- **Comparar** (`/descobrir/comparar`) — até 4 ativos lado a lado. Aceita `?tickers=` para chegar
  preenchido da carteira ou da página do ativo.

## Estratégia

- **Plano** (`/estrategia`) — "onde você está × onde deveria estar". Quatro camadas visualmente
  distintas: informação (tabela de gaps), cálculo (a frase do maior desvio), sugestão (rotulada) e
  ação (o botão). Inclui sugestões por categoria, posições para revisar, alocação projetada e o
  resultado do que você seguiu.
- **Aporte** (`/estrategia/aporte`) — Quick Invest: quanto, ordem mínima, e o app responde o que
  está abaixo da meta. Persiste o caixa em `/preferences`, que o plano lê.
- **Metas** (`/estrategia/metas`) — renda passiva mensal, alocação por categoria e por setor. Fica
  aqui, e não em Configurações, porque meta é insumo de decisão: ao lado do gap que ela gera.
- **Renda fixa** (`/estrategia/renda-fixa`) — duas perguntas na mesma tela: comparar títulos entre
  si, e renda fixa × bolsa na mesma unidade (renda recorrente líquida a.a.), com a valorização
  potencial mostrada **separada** — renda fixa não tem, e a tela diz isso.
- **Projeção** (`/estrategia/projecao`) — simulador de aportes e renda passiva.

## Ativo

`/ativo/:ticker` — página de research. O ticker vive na rota: recarregar mantém, o link é
compartilhável.

- **Cabeçalho:** ticker, nome, tipo, preço, distância do topo de 52 semanas, e as ações
  contextuais (comparar, criar alerta com o ticker preenchido, adicionar à carteira).
- **N1:** a leitura em uma frase, o veredito no vocabulário único (Interessante / Neutro / Atenção
  / Evitar / Sem leitura), a régua de confiança e os `reasons` do backend.
- **N2:** preço atual × consenso × margem de segurança, com a proveniência (quantos métodos, quantos
  anos de provento, qual confiança).
- **N3 — valuation:** **um bloco por método** (Bazin, Graham, DCF, e P/VP justo em FII), cada um com
  preço estimado, distância do atual e o insumo que usou. Método que não se aplica **diz por quê**
  ("Graham não se aplica a fundo imobiliário") em vez de deixar campo vazio. O roteamento por tipo
  é do backend; a UI reflete e explica.
- **N3:** fundamentos (só os que existem), tendência (com a base sobre a qual foi medida),
  proventos.
- **N4:** "Como calculamos" — meta de yield usada, LPA, VPA, P/VP, base da tendência.

## Você

- **Preferências** (`/voce/preferencias`) — yields desejados por classe (entram no preço-teto de
  Bazin), perfil de risco (pondera o score), categorias e setores preferidos, tickers excluídos.
  Cada controle diz o **efeito**, não só o nome.
- **Alertas** (`/voce/alertas`) — CRUD de alertas de preço; aceita `?ticker=` para chegar
  preenchido da página do ativo. Alertas de preço são imediatos; o resumo de oportunidades tem
  cadência configurável. Push exige o app instalado, e a tela diz isso.
- **Conta e dados** (`/voce/conta`) — origem de cada dado (BRAPI, BCB SGS), como o preço justo e o
  score são calculados, o aviso de que tudo é estimativa, e a limpeza de cache.

## Autenticação

Login via Google nas duas plataformas, JWT emitido pelo backend (TTL 30 dias). O `authGuard` do
web valida o `exp`, não só a presença do token.

## Notificações

Alertas de preço disparados são imediatos via FCM. O resumo de oportunidades (`STRONG_BUY`, ou
score ≥ 75 com DY ≥ 6%, excluindo o que já está na carteira e os tickers excluídos) sai por
cadência configurável — off, diária, semanal ou mensal. O mesmo push lista posições com veredito de
venda. Requer o app instalado.
