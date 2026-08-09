# fianceAI

Plataforma de inteligência de investimentos com análise fundamentalista, varredura de oportunidades e recomendações orientadas por IA, focada no mercado brasileiro (B3).

## Visão Geral

O fianceAI integra dados de mercado em tempo real, métodos clássicos de valuation (Bazin, Graham, DCF) e o modelo Gemini da Google para entregar uma visão consolidada da sua carteira, identificar ativos com desconto e gerar estratégias de alocação personalizadas.

**Principais funcionalidades:**

- Dashboard com posições, P&L e metas de alocação
- Scanner de oportunidades com pontuação fundamentalista e técnica
- Scanner de quedas ("dip") com streaming em tempo real (SSE)
- Visão por segmento de mercado: score médio, DY médio e top ativos por setor
- Histórico e análise de dividendos (DY, projeções)
- Alertas de preço configuráveis por ativo
- Insights e estratégias gerados por IA (Google Gemini)
- Suporte a ações B3, FIIs, ETFs, criptomoedas e renda fixa

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Web | Angular 18, TypeScript 5.5, Tailwind CSS |
| Mobile | Flutter (iOS/Android) |
| Dados de mercado | yfinance |
| IA | Google Gemini API |
| Linting / Format | Ruff (Python), Prettier (TypeScript) |

## Pré-requisitos

- Python 3.11+
- Node.js 18+ e npm
- Chave de API: [Google Gemini](https://aistudio.google.com/app/apikey) (plano gratuito: 15 req/min)

## Instalação

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### Web

```bash
cd web
npm install
```

## Configuração de Ambiente

Copie o arquivo de exemplo e preencha as variáveis:

```bash
cp backend/.env.example backend/.env
```

| Variável | Obrigatória | Descrição |
|----------|:-----------:|-----------|
| `GEMINI_API_KEY` | Sim | Chave da API Google Gemini |
| `APP_ENV` | Não | `development` ou `production` (padrão: `development`) |
| `LOG_LEVEL` | Não | Nível de log: `DEBUG`, `INFO`, `WARNING` (padrão: `INFO`) |
| `ALLOWED_ORIGINS` | Não | Origens CORS permitidas (padrão: `http://localhost:4200`) |
| `DEFAULT_UNIVERSE` | Não | Tickers monitorados, separados por vírgula |

## Execução

### Desenvolvimento

```bash
# Terminal 1 — Backend (http://localhost:8000)
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Web (http://localhost:4200)
cd web
npm start
```

### Build de Produção

```bash
# Web
cd web
npm run build   # saída em dist/

# Backend — recomenda-se usar Gunicorn com worker Uvicorn
pip install gunicorn
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Documentação da API

Com o backend rodando, acesse a documentação interativa:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/dashboard` | Dados consolidados do dashboard |
| `GET/POST` | `/api/portfolio` | Gerenciar posições |
| `POST` | `/api/portfolio/evaluate` | Calcular P&L e alocação |
| `GET` | `/api/opportunities` | Oportunidades de investimento com score |
| `GET` | `/api/dip-scanner` | Ativos abaixo do preço justo |
| `GET` | `/api/dip-scanner/stream` | Varredura de quedas em tempo real (SSE) |
| `GET` | `/api/sectors-summary` | Agrupamento por setor: score médio, DY médio, top ativos |
| `GET` | `/api/strategy` | Estratégia de alocação gerada por IA |
| `GET/POST` | `/api/alerts` | Alertas de preço |
| `GET` | `/api/dividends` | Histórico de dividendos |
| `GET` | `/api/recommendations` | Top recomendações de compra |

## Estrutura do Projeto

```
fianceAI/
├── backend/
│   ├── app/
│   │   ├── main.py              # Ponto de entrada FastAPI
│   │   ├── analysis/            # Algoritmos: Bazin, Graham, DCF, scoring
│   │   ├── api/                 # Rotas REST
│   │   ├── collectors/          # Coleta de dados (yfinance, RSS)
│   │   ├── services/            # Regras de negócio
│   │   ├── models/              # Schemas Pydantic
│   │   ├── repositories/        # Persistência (JSON local)
│   │   ├── llm/                 # Integração Google Gemini
│   │   ├── core/                # Configuração e cache
│   │   └── optimizer/           # Otimização de carteira
│   ├── requirements.txt
│   └── .env.example
│
├── web/
│   └── src/
│       └── app/
│           ├── components/      # Dashboard, Assets, Market, Strategy, Dip, Sectors…
│           └── core/            # Serviços HTTP, interceptors, tema
│
└── mobile/                      # App Flutter (iOS/Android)
```

## Métodos de Valuation

| Método | Fórmula | Aplicação |
|--------|---------|-----------|
| **Bazin** | `Preço justo = DPA médio / Yield desejado` | Ações com dividendos consistentes |
| **Graham** | `Preço justo = √(22,5 × LPA × VPA)` | Ações de valor |
| **DCF** | Fluxo de caixa descontado | Crescimento futuro |
| **Consenso** | Média dos métodos disponíveis (1–3) | Visão geral; `consensus_methods` indica quantos métodos foram usados |

## Scripts Disponíveis

```bash
# Backend
uvicorn app.main:app --reload    # servidor dev
ruff format .
ruff check --fix .

# Web
npm start           # servidor dev
npm run build       # build de produção
npm run format      # formatar código com Prettier
npm run format:check # verificar formatação
```

## Licença

Distribuído sob licença proprietária. Consulte o arquivo [LICENSE](LICENSE) para detalhes.
