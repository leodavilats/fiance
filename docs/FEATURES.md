# fiance — Inventário de features por tela

> Gerado por varredura completa em 2026-08-10; **revisado em 2026-08-20** após a
> implementação da auditoria. Web (Angular) e Mobile (Flutter) têm paridade quase total de
> navegação (4 abas espelhadas) e consomem a mesma API.

## Dashboard
Tela inicial consolidada: resumo de carteira, alertas de preço, indicadores gerais e "Saúde da carteira" (score 0–100 com sub-métricas Concentração/Setor/Diversificação/Risco — clicável para exibir o que cada uma considera). (`web/.../dashboard/`, `mobile/.../dashboard/dashboard_screen.dart`)

**Ajustes 2026-08-19:** removida a seção "Alocação por categoria" do dashboard (redundante com a composição por ativo/setor em Meus Ativos); alertas de rebalanceamento passaram a exibir o rótulo traduzido da categoria (ex.: "Renda Fixa") em vez da chave crua (`renda_fixa`).

## Meus Ativos (`/assets`)
CRUD de posições da carteira (ações, FIIs, BDRs, ETFs) e formulário de Renda Fixa. No web, inclui preview client-side de rendimento RF (calculado no navegador antes de salvar). No mobile, o preview vem sempre do backend.

**Composição da carteira (2026-08-19):** gráfico de pizza com alternância entre "Por ativo" (categoria) e "Por setor" (ações/BDRs), web e mobile. A funcionalidade de rebalanceamento de carteira foi removida dessa tela (e da API de suporte a ela, `/rebalance`, no cliente mobile).

**Venda de ativos e histórico (2026-08-10):** cada posição pode ser vendida parcial ou totalmente (botão "Vender" no web e no mobile), gerando automaticamente lucro/prejuízo realizado e o imposto de renda devido (alíquotas por categoria, com isenção mensal acumulada só para ações BR — BDR/FII/ETF são tributados sem isenção). Toda venda vira um registro em "Operações Encerradas", com totais de lucro realizado e IR pago.

**Explicações de decisão:** cada posição mostra os motivos (`reasons`) por trás do veredito de compra/venda/manutenção — no web, expansível ao clicar na pill de Decisão; no mobile, num botão "Por quê?". Tooltips de glossário (DY, MS, P/VP, Bazin, Graham, Score) disponíveis no web (Meus Ativos e Mercado) e no mobile (Oportunidades).

**Autocomplete de ticker (2026-08-11):** o campo de ticker (Meus Ativos, web e mobile) sugere ticker+nome da empresa enquanto o usuário digita, via `GET /universe/search` (busca por prefixo/substring em toda a lista de ações/FIIs/BDRs/ETFs da B3 — não só o universo limitado usado no scanner de oportunidades). Tickers não suportados pelo sistema (ex.: ação US pura, cripto) não aparecem nas sugestões.

**Notificações push (Fase 3, 2026-08-11; cadência configurável, 2026-08-19):** alertas de preço disparados continuam imediatos via FCM (toggle em Configurações). O antigo toggle "novas oportunidades" foi substituído por uma cadência (`off`/diária/semanal/mensal, em Configurações) — o job periódico só envia o resumo agregado de oportunidades quando o intervalo escolhido já venceu, alinhado à filosofia de investimento (não day trade) da plataforma.

## Mercado (`/market`)
Maior área do app, reduzida a 2 abas (2026-08-19, removidas "Segmentos" e "Investir" de ambas as plataformas — o quick-invest e a visão por setor não tinham uso comprovado nessa tela):
- **Oportunidades** — varredura do universo de ativos com score/fair price, com sub-modo "Em queda" (scanner de dip). Score (2026-08-19) combina margem de segurança + qualidade (ROE/margem) + endividamento + crescimento + dividend yield + técnico, ponderados pelo perfil de risco configurado em Preferências; categorias/setores marcados como preferidos recebem um pequeno boost, e tickers em `excluded_tickers` somem da lista.
- **Ferramentas** — Analisar (ficha de um ativo), Simulador de Renda Fixa, Comparar Ativos, Simulador de Aportes.

A "Estratégia de Investimento" (`/strategy`, motor de decisão/alocação sugerida via IA) permanece como página própria fora de Mercado — não afetada por essa mudança.

**Correções 2026-08-19:** simulador de aportes no mobile aceitava só teclado numérico inteiro (sem separador decimal) nos campos de percentual/valor — corrigido para `numberWithOptions(decimal: true)` com normalização de vírgula/ponto. Espaçamento dos campos do Simulador de RF (web) alinhado ao do Simulador de Aportes. Sub-abas de Oportunidades/Ferramentas (mobile) passaram de rolagem horizontal para wrap.

## Configurações (`/config`)
Metas de dividend yield por categoria (ações/FII/BDR/ETF), preferências de perfil de risco e alertas de preço. (Nota: a API tinha um endpoint de watchlist — `GET/PUT /watchlist`, `DELETE /watchlist/{ticker}` — mas nunca existiu tela para ele em nenhuma plataforma; removido em 2026-08-19, ver KNOWN_ISSUES.md.)

**Correção 2026-08-19:** sliders de meta de alocação por categoria/setor tinham a trilha (parte não preenchida) invisível em light mode, tanto no web (CSS só definia `accent-color`, sem cor de track) quanto no mobile (Material3 derivava a cor de `colorScheme.surfaceVariant`, próxima da cor do painel). Corrigido com CSS de track explícito no web e `SliderThemeData` explícito no tema mobile.

## Autenticação
Login via Google (mesmo fluxo web e mobile, JWT emitido pelo backend).


---

## Novidades da implementação da auditoria (2026-08-20)

### "O que mudou" — primeiro bloco do Dashboard
`GET /whats-new` compara o estado atual com o anterior e devolve até 5 linhas: variação de
patrimônio (já descontando aportes), posições com sinal de venda, vencimento de renda fixa
próximo, categoria fora da meta, prejuízo disponível para compensar IR e destaque de
oportunidade. **Cada linha tem uma ação** que leva à tela onde a decisão acontece. Sem nada a
dizer, o bloco diz isso — em vez de sumir. Web e mobile.

### Renda fixa de verdade (`/fixed-income`)
Tabela própria no servidor com tipo, valor, taxa, tipo de taxa, % do CDI, data de aplicação,
vencimento, liquidez e isenção. **Marcada a mercado no backend**: rendimento acumulado, valor
hoje, projeção até o vencimento e aviso de vencimento próximo. Entra no patrimônio total, no
P&L, na alocação, na saúde da carteira, na projeção de renda passiva e no Quick Invest.
Cadastro no web (`/assets/cadastro`) e tela dedicada no mobile.

### Proventos recebidos
Antes todo número de renda era estimativa derivada de dividend yield. Agora dá para lançar o
que caiu na conta (`/dividends/received`), ver total do mês, dos últimos 12 meses, média
mensal, quebra por ativo — e **confrontar com a estimativa do próprio app**.

### Renda fixa × bolsa na mesma tela (Mercado → Ferramentas → RF x Bolsa)
"Com a Selic a 14,4%, vale mais o CDB ou o FII?" — ambos os lados na mesma unidade (renda
recorrente líquida a.a.), com valorização potencial mostrada **separada** (renda fixa não tem, e
a tela diz isso) e um veredito em texto.

### Resultado das sugestões seguidas (Mercado → Rebalanceamento)
Registre o que você executou a partir de uma sugestão e o app mostra o resultado contra o
Ibovespa, agregado por origem da sugestão. Torna o produto auditável por quem usa.

### Compensação de prejuízo de IR
Prejuízo realizado passa a abater ganho futuro da mesma categoria, como a legislação permite —
o app superestimava o IR devido de quem já havia realizado prejuízo. O saldo por categoria
aparece em Operações Encerradas, e cada venda mostra quanto foi compensado.

### Proveniência e frescor do dado
Ao lado de cada veredito: anos de proventos encontrados, quantos métodos entraram no consenso e
confiança. Score com dado incompleto sai **cinza** e rotulado "dado insuficiente" em vez de
colorido com a nota. O dashboard mostra a idade das cotações e se o CDI/Selic vem do BCB ou é
estimativa.

### Alertas com desfecho
Agrupados por tipo, com contagem e teto de 4 — e cada um com uma ação (ver análise, simular
venda, rebalancear, ajustar meta). Antes eram alertas sem limite e a única ação da tela era ir
para Mercado.

### Cadastro separado de análise (web)
`/assets` é leitura (o retorno diário); `/assets/cadastro` é escrita (tarefa rara), com
salvamento explícito por linha. O autosave por debounce sobre um PUT destrutivo saiu.

### Desktop mais aproveitado
Tabela de posições ordenável por qualquer coluna, seleção de até 4 ativos para comparar (leva
direto ao comparador) e exportação CSV da carteira.

### Quick Invest no mobile
"Recebi meu salário, onde aporto" existia só no web, apesar de ser um caso de uso mais de
celular. Disponível em Mercado → Ferramentas.

### Push honesto no web
A tela de Configurações agora informa que notificações requerem o app instalado, em vez de
oferecer cadência e alerta sem efeito para quem usa só o navegador. E o logout no app
desregistra o aparelho, que antes continuava recebendo o resumo da conta anterior.

### Qualidade de dado (`GET /data-quality`)
Taxa de preenchimento por campo no universo, com o impacto de cada ausência descrito — a
instrumentação que faltava para distinguir "o modelo está errado" de "o dado não chegou".
