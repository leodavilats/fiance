# fianceAI

Sistema de gestão e análise de ativos financeiros — descubra o que comprar, manter ou vender.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ · FastAPI · yfinance · Alpha Vantage · feedparser |
| Frontend | Angular 18 · Signals · Reactive Forms · Lucide Icons |
| Dados | Yahoo Finance (gratuito) · Alpha Vantage (gratuito) · Google News RSS |
| LLM (opcional) | Google Gemini AI |

---

## Funcionalidades

| Aba | Descrição |
|---|---|
| **Dashboard** | Visão geral: patrimônio, PnL, alertas, oportunidades de compra/venda, alocação vs. metas, evolução histórica |
| **Meus Ativos** | Cadastre posições (ticker, quantidade, preço médio). Auto-salvo com debounce. Avaliação em tempo real com P&L e veredicto |
| **Oportunidades** | Universo curado + watchlist ranqueado por score. Filtros por tipo, setor, DY mínimo e margem de segurança |
| **Dividendos** | Ranking de maiores pagadores de dividendos (DY 12m) com preço justo Bazin |
| **Analisar** | Análise detalhada de qualquer ativo (B3, EUA, FII, cripto): preço justo, técnicos, decisão fundamentada |
| **Na Baixa?** | Analisa se um ativo em queda é **oportunidade ou armadilha** — score 0–100 cruzando fundamentos, técnico, dividendos e notícias |
| **Configurações** | Caixa disponível, yield desejado (Bazin), metas de alocação por categoria, watchlist |

### Score "Vale na Baixa?" (0–100)

| Dimensão | Peso |
|---|---|
| Preço vs. Preço Justo (Bazin/Graham) | 30 pts |
| Qualidade fundamentalista (ROE, margem, dívida) | 25 pts |
| Indicadores técnicos (RSI, SMA200, queda do topo 52s) | 25 pts |
| Dividendos (DY e histórico 5 anos) | 10 pts |
| Sentimento de notícias (Google News RSS) | 10 pts |

**Veredicto:** `OPORTUNIDADE` (≥68) · `NEUTRO` (42–67) · `ARMADILHA` (<42)

---

## Estrutura

```
fianceAI/
├── backend/
│   ├── app/
│   │   ├── analysis/        # fair_price, scoring, decision, dip_analysis
│   │   ├── api/             # routes FastAPI
│   │   ├── collectors/      # yfinance (universal), Alpha Vantage, Google News RSS
│   │   ├── core/            # config (.env), cache, universe
│   │   ├── llm/             # gemini_client
│   │   ├── models/          # schemas Pydantic
│   │   ├── optimizer/       # alocação e otimização de carteira
│   │   └── storage/         # persistência local (portfolio_store)
│   └── requirements.txt
└── frontend/
    └── src/app/
        ├── app.component.ts  # componente único com todas as abas
        ├── models.ts          # interfaces TypeScript
        ├── recommend.service.ts
        └── theme.service.ts
```

---

## Configuração

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Crie um arquivo `.env` (opcional):

```env
ALPHA_VANTAGE_KEY=your_key    # gratuito em alphavantage.co — dados fundamentais precisos
GEMINI_API_KEY=your_key        # gratuito em ai.google.dev — análises com LLM
DEFAULT_UNIVERSE=PETR4,VALE3,ITUB4,BBDC4,BBAS3,WEGE3,ITSA4
```

Inicie o servidor:

```bash
uvicorn app.main:app --reload
# API disponível em http://127.0.0.1:8000
# Docs interativas em http://127.0.0.1:8000/docs
```

**Formatação de código:**

```bash
# Formatar código Python
ruff format .

# Verificar e corrigir linting
ruff check --fix .
```

### 2. Frontend

```bash
cd frontend
npm install
ng serve
# App disponível em http://localhost:4200
```

**Formatação de código:**

```bash
# Formatar código TypeScript/HTML/CSS
npm run format

# Verificar formatação sem alterar
npm run format:check
```

---

## Principais endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/recommend` | Recomendação de carteira otimizada |
| `GET` | `/api/asset/{symbol}` | Análise detalhada (fair price + técnico + decisão) |
| `GET` | `/api/asset/{symbol}/dip-analysis` | Score "vale na baixa" + notícias |
| `POST` | `/api/portfolio/evaluate` | Avalia posições com P&L e veredicto |
| `GET` | `/api/opportunities` | Ranking de oportunidades do universo |
| `GET` | `/api/dividends/ranking` | Top pagadoras de dividendos |
| `GET` | `/api/dashboard` | Visão consolidada completa |

---

## Mercados suportados

- **B3** — Ações (ex.: `PETR4`) e FIIs (ex.: `HGLG11`)
- **EUA** — Ações americanas (ex.: `AAPL`, `NVDA`)
- **Cripto** — BTC, ETH, SOL, entre outros

---

> **Aviso:** Conteúdo educativo. Não constitui recomendação formal de investimento. Consulte um profissional habilitado.
