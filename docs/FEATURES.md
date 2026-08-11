# fianceAI — Inventário de features por tela

> Gerado por varredura completa em 2026-08-10. Web (Angular) e Mobile (Flutter) têm paridade quase total de navegação (4 abas espelhadas) e consomem a mesma API.

## Dashboard
Tela inicial consolidada: resumo de carteira, alocação por categoria, alertas de preço, indicadores gerais. (`web/.../dashboard/`, `mobile/.../dashboard/dashboard_screen.dart`)

## Meus Ativos (`/assets`)
CRUD de posições da carteira (ações, FIIs, BDRs, cripto) e formulário de Renda Fixa. No web, inclui preview client-side de rendimento RF (calculado no navegador antes de salvar). No mobile, o preview vem sempre do backend.

**Venda de ativos e histórico (2026-08-10):** cada posição pode ser vendida parcial ou totalmente (botão "Vender" no web e no mobile), gerando automaticamente lucro/prejuízo realizado e o imposto de renda devido (alíquotas por categoria, com isenção mensal acumulada para ações BR e cripto). Toda venda vira um registro em "Operações Encerradas", com totais de lucro realizado e IR pago.

**Explicações de decisão:** cada posição mostra os motivos (`reasons`) por trás do veredito de compra/venda/manutenção — no web, expansível ao clicar na pill de Decisão; no mobile, num botão "Por quê?". Tooltips de glossário (DY, MS, P/VP, Bazin, Graham, Score) disponíveis no web (Meus Ativos e Mercado) e no mobile (Oportunidades).

**Autocomplete de ticker (2026-08-11):** o campo de ticker (Meus Ativos, web e mobile) sugere ticker+nome da empresa enquanto o usuário digita, via `GET /universe/search` (busca por prefixo/substring em toda a lista de ações/FIIs/BDRs da B3 + ações US/cripto curadas — não só o universo limitado usado no scanner de oportunidades).

**Notificações push (Fase 3, 2026-08-11):** alertas de preço disparados e novas oportunidades (STRONG_BUY ou score alto + DY alto) notificam o usuário via FCM, com toggles em Configurações para ligar/desligar cada tipo.

## Mercado (`/market`)
Maior área do app, dividida em sub-abas (reduzidas de 4 para 3 no web, unificando Segmentos em "Explorar"):
- **Oportunidades** — varredura do universo de ativos com score/fair price.
- **Segmentos/Explorar** — visão por setor.
- **Investir** — fluxo de aporte guiado (quick-invest).
- **Ferramentas** — Analisar (ficha de um ativo) + Simulador de Renda Fixa.
- **Quedas (dip)** — scanner de ativos em queda com potencial.
- **Estratégia** — motor de decisão/alocação sugerida.

## Configurações (`/config`)
Metas de dividend yield por categoria (ações/FII/internacional), preferências de perfil de risco, gestão de watchlist e alertas de preço.

## Autenticação
Login via Google (mesmo fluxo web e mobile, JWT emitido pelo backend).
