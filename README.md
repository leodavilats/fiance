# fiance

Plataforma de inteligência de investimentos com análise fundamentalista, varredura de oportunidades e recomendações orientadas por IA, focada no mercado brasileiro (B3). Disponível como app web e mobile (iOS/Android), com login por conta Google e dados isolados por usuário.

## Visão Geral

O fiance integra dados de mercado em tempo real e métodos clássicos de valuation (Bazin, Graham, DCF) para entregar uma visão consolidada da sua carteira, identificar ativos com desconto e gerar estratégias de alocação personalizadas — focado 100% na B3 (ações, BDRs, FIIs e ETFs).

**Principais funcionalidades:**

- Login com Google (multi-usuário, dados isolados por conta)
- Dashboard com posições, P&L e metas de alocação
- Scanner de oportunidades com pontuação fundamentalista e técnica
- Scanner de quedas ("dip") com streaming em tempo real (SSE)
- Visão por segmento de mercado: score médio, DY médio e top ativos por setor
- Histórico e análise de dividendos (DY, projeções)
- Alertas de preço configuráveis por ativo
- Estratégias de alocação com sugestões determinísticas por gap de categoria
- Suporte a ações B3, BDRs, FIIs, ETFs e renda fixa

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy |
| Banco de dados | PostgreSQL (produção, via Railway) / SQLite (fallback local) |
| Autenticação | Login com Google (OAuth) + JWT de sessão próprio |
| Web | Angular 18, TypeScript 5.5, Tailwind CSS |
| Mobile | Flutter (iOS/Android), Riverpod, go_router |
| Dados de mercado — B3/FIIs/BDRs/ETFs | [BRAPI](https://brapi.dev) |
| Dados de renda fixa — CDI/Selic/IPCA | [BCB SGS](https://www3.bcb.gov.br/sgspub/) |
| Hospedagem backend | Railway |
| Linting / Format | Ruff (Python), Prettier (TypeScript) |

## Pré-requisitos

- Python 3.11+
- Node.js 18+ e npm (para o app web)
- Flutter 3.x + Android Studio / Xcode (para o app mobile)
- Chave de API: [BRAPI](https://brapi.dev)
- OAuth Client IDs do Google (Web, Android e iOS) em [console.cloud.google.com](https://console.cloud.google.com/apis/credentials)
- Projeto no [Railway](https://railway.app) com addon PostgreSQL (para produção)

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

### Mobile

```bash
cd mobile
flutter pub get
```

## Configuração de Ambiente

Copie o arquivo de exemplo e preencha as variáveis:

```bash
cp backend/.env.example backend/.env
```

| Variável | Obrigatória | Descrição |
|----------|:-----------:|-----------|
| `GOOGLE_CLIENT_ID` | Sim | Client IDs OAuth aceitos como audience do login (Web, Android, iOS — separados por vírgula) |
| `JWT_SECRET` | Sim | Segredo usado para assinar o JWT de sessão emitido após o login |
| `BRAPI_TOKEN` | Sim | Token da BRAPI (cotações/fundamentos B3, FIIs, BDRs, ETFs) |
| `DATABASE_URL` | Não | String de conexão Postgres. Em produção, o Railway injeta automaticamente; sem ela, cai no SQLite local |
| `APP_ENV` | Não | `development` ou `production` (padrão: `development`) |
| `LOG_LEVEL` | Não | Nível de log: `DEBUG`, `INFO`, `WARNING` (padrão: `INFO`) |
| `ALLOWED_ORIGINS` | Não | Origens CORS permitidas (padrão: `http://localhost:4200`) |
| `ADMIN_USER_IDS` | Não | IDs (o `sub` do Google) liberados em `/cache/clear` e `/metrics`, separados por vírgula. Vazio libera em `development` e **nega** em produção |
| `DEFAULT_UNIVERSE` | Não | Tickers monitorados, separados por vírgula |

No app mobile (`mobile/lib/core/auth_service.dart`), o login com Google usa um `serverClientId` (o Client ID **Web**) — é ele que faz o `idToken` ter uma audience validável pelo backend, independente da plataforma (Android/iOS).

## Execução

### Desenvolvimento

```bash
# Terminal 1 — Backend (http://localhost:8000)
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Web (http://localhost:4200)
cd web
npm start

# Terminal 3 — Mobile (emulador/dispositivo, apontando pro backend local)
cd mobile
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api   # emulador Android
flutter run --dart-define=API_BASE_URL=http://localhost:8000/api  # iOS simulator
```

### Build de Produção

```bash
# Web
cd web
npm run build   # saída em dist/

# Backend — Railway usa o Procfile (uvicorn) automaticamente.
# Root Directory do serviço no Railway deve ser "backend".

# Mobile — APK de teste
cd mobile
flutter build apk --release   # saída em build/app/outputs/flutter-apk/

# Mobile — App Bundle para a Play Store (requer keystore de release configurado)
flutter build appbundle --release
```

Por padrão, o app mobile aponta para o backend em produção (`https://fiance.up.railway.app/api`), configurado em `mobile/lib/core/api_client.dart`.

## Documentação da API

Com o backend rodando, acesse a documentação interativa:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/health` | Health check (público) |
| `POST` | `/api/auth/google` | Login: troca o `id_token` do Google por um JWT de sessão (público) |
| `GET` | `/api/dashboard` | Dados consolidados do dashboard |
| `GET/PUT` | `/api/portfolio` | Gerenciar posições |
| `POST` | `/api/portfolio/evaluate` | Calcular P&L e alocação |
| `GET` | `/api/opportunities` | Oportunidades de investimento com score |
| `GET` | `/api/dip-scanner` | Ativos abaixo do preço justo |
| `GET` | `/api/dip-scanner/stream` | Varredura de quedas em tempo real (SSE) |
| `GET` | `/api/sectors-summary` | Agrupamento por setor: score médio, DY médio, top ativos |
| `GET` | `/api/strategy` | Estratégia de alocação gerada por IA |
| `GET/POST` | `/api/alerts` | Alertas de preço |
| `GET/PUT` | `/api/watchlist` | Lista de acompanhamento |
| `GET/PUT` | `/api/goals` , `/api/sector-goals` | Metas de alocação por categoria/setor |
| `GET/PUT` | `/api/preferences` | Caixa disponível, yields desejados, meta de renda passiva |
| `GET` | `/api/dividends` | Histórico de dividendos |
| `GET` | `/api/recommendations` | Top recomendações de compra |

Todas as rotas acima (exceto `/health` e `/auth/google`) exigem `Authorization: Bearer <token>` e retornam dados isolados por usuário.

## Estrutura do Projeto

```
fiance/
├── backend/
│   ├── app/
│   │   ├── main.py              # Ponto de entrada FastAPI
│   │   ├── analysis/            # Algoritmos: Bazin, Graham, DCF, scoring
│   │   ├── api/                 # Rotas REST (auth, dashboard, portfolio, ...)
│   │   ├── collectors/          # Coleta de dados (BRAPI, RSS)
│   │   ├── services/            # Regras de negócio
│   │   ├── models/              # Schemas Pydantic + modelos ORM (SQLAlchemy)
│   │   ├── repositories/        # Camada de persistência
│   │   ├── storage/             # Acesso ao banco (portfolio, goals, preferences...)
│   │   ├── core/                # Config, banco de dados, autenticação, cache
│   │   └── optimizer/           # Otimização de carteira
│   ├── Procfile                 # Comando de start usado pelo Railway
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
    └── lib/
        ├── core/                # API client, auth (Google), providers, modelos
        └── features/            # Login, Dashboard, Meus Ativos, Mercado, Config
```

## Métodos de Valuation

| Método | Fórmula | Aplicação |
|--------|---------|-----------|
| **Bazin** | `Preço justo = DPA médio / Yield desejado` | Ações com dividendos consistentes, FIIs |
| **Graham** | `Preço justo = √(22,5 × LPA × VPA)` | Ações de valor, BDRs |
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

# Mobile
flutter analyze         # lint
flutter test             # testes
flutter build apk         # build de release (Android)
```

## Licença

Distribuído sob licença proprietária. Consulte o arquivo [LICENSE](LICENSE) para detalhes.
