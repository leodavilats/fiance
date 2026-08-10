# fianceAI — Inventário de features por tela

> Gerado por varredura completa em 2026-08-10. Web (Angular) e Mobile (Flutter) têm paridade quase total de navegação (4 abas espelhadas) e consomem a mesma API.

## Dashboard
Tela inicial consolidada: resumo de carteira, alocação por categoria, alertas de preço, indicadores gerais. (`web/.../dashboard/`, `mobile/.../dashboard/dashboard_screen.dart`)

## Meus Ativos (`/assets`)
CRUD de posições da carteira (ações, FIIs, BDRs, cripto) e formulário de Renda Fixa. No web, inclui preview client-side de rendimento RF (calculado no navegador antes de salvar). No mobile, o preview vem sempre do backend.

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
