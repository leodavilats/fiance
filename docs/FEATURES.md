# fiance — Inventário de features por tela

> Gerado por varredura completa em 2026-08-10. Web (Angular) e Mobile (Flutter) têm paridade quase total de navegação (4 abas espelhadas) e consomem a mesma API.

## Dashboard
Tela inicial consolidada: resumo de carteira, alertas de preço, indicadores gerais e "Saúde da carteira" (score 0–100 com sub-métricas Concentração/Setor/Diversificação/Risco — clicável para exibir o que cada uma considera). (`web/.../dashboard/`, `mobile/.../dashboard/dashboard_screen.dart`)

**Ajustes 2026-08-19:** removida a seção "Alocação por categoria" do dashboard (redundante com a composição por ativo/setor em Meus Ativos); alertas de rebalanceamento passaram a exibir o rótulo traduzido da categoria (ex.: "Renda Fixa") em vez da chave crua (`renda_fixa`).

## Meus Ativos (`/assets`)
CRUD de posições da carteira (ações, FIIs, BDRs, cripto) e formulário de Renda Fixa. No web, inclui preview client-side de rendimento RF (calculado no navegador antes de salvar). No mobile, o preview vem sempre do backend.

**Composição da carteira (2026-08-19):** gráfico de pizza com alternância entre "Por ativo" (categoria) e "Por setor" (ações/BDRs), web e mobile. A funcionalidade de rebalanceamento de carteira foi removida dessa tela (e da API de suporte a ela, `/rebalance`, no cliente mobile).

**Venda de ativos e histórico (2026-08-10):** cada posição pode ser vendida parcial ou totalmente (botão "Vender" no web e no mobile), gerando automaticamente lucro/prejuízo realizado e o imposto de renda devido (alíquotas por categoria, com isenção mensal acumulada para ações BR e cripto). Toda venda vira um registro em "Operações Encerradas", com totais de lucro realizado e IR pago.

**Explicações de decisão:** cada posição mostra os motivos (`reasons`) por trás do veredito de compra/venda/manutenção — no web, expansível ao clicar na pill de Decisão; no mobile, num botão "Por quê?". Tooltips de glossário (DY, MS, P/VP, Bazin, Graham, Score) disponíveis no web (Meus Ativos e Mercado) e no mobile (Oportunidades).

**Autocomplete de ticker (2026-08-11):** o campo de ticker (Meus Ativos, web e mobile) sugere ticker+nome da empresa enquanto o usuário digita, via `GET /universe/search` (busca por prefixo/substring em toda a lista de ações/FIIs/BDRs da B3 + ações US/cripto curadas — não só o universo limitado usado no scanner de oportunidades).

**Notificações push (Fase 3, 2026-08-11):** alertas de preço disparados e novas oportunidades (STRONG_BUY ou score alto + DY alto) notificam o usuário via FCM, com toggles em Configurações para ligar/desligar cada tipo.

## Mercado (`/market`)
Maior área do app, reduzida a 2 abas (2026-08-19, removidas "Segmentos" e "Investir" de ambas as plataformas — o quick-invest e a visão por setor não tinham uso comprovado nessa tela):
- **Oportunidades** — varredura do universo de ativos com score/fair price, com sub-modo "Em queda" (scanner de dip).
- **Ferramentas** — Analisar (ficha de um ativo), Simulador de Renda Fixa, Comparar Ativos, Simulador de Aportes.

A "Estratégia de Investimento" (`/strategy`, motor de decisão/alocação sugerida via IA) permanece como página própria fora de Mercado — não afetada por essa mudança.

**Correções 2026-08-19:** simulador de aportes no mobile aceitava só teclado numérico inteiro (sem separador decimal) nos campos de percentual/valor — corrigido para `numberWithOptions(decimal: true)` com normalização de vírgula/ponto. Espaçamento dos campos do Simulador de RF (web) alinhado ao do Simulador de Aportes. Sub-abas de Oportunidades/Ferramentas (mobile) passaram de rolagem horizontal para wrap.

## Configurações (`/config`)
Metas de dividend yield por categoria (ações/FII/internacional), preferências de perfil de risco e alertas de preço. (Nota: a API tinha um endpoint de watchlist — `GET/PUT /watchlist`, `DELETE /watchlist/{ticker}` — mas nunca existiu tela para ele em nenhuma plataforma; removido em 2026-08-19, ver KNOWN_ISSUES.md.)

**Correção 2026-08-19:** sliders de meta de alocação por categoria/setor tinham a trilha (parte não preenchida) invisível em light mode, tanto no web (CSS só definia `accent-color`, sem cor de track) quanto no mobile (Material3 derivava a cor de `colorScheme.surfaceVariant`, próxima da cor do painel). Corrigido com CSS de track explícito no web e `SliderThemeData` explícito no tema mobile.

## Autenticação
Login via Google (mesmo fluxo web e mobile, JWT emitido pelo backend).
