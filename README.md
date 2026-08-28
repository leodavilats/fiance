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
| `ENTITLEMENTS_ENABLED` | Não | Liga a régua de plano (padrão: `false` — todo mundo tem tudo) |
| `AFFIRMATION_LEVEL` | Não | Modo de afirmação: `1` descritivo, `2` analítico (padrão), `3` prescritivo |
| `SUITABILITY_PERSONALIZATION_ALLOWED` | Não | Libera personalização por perfil **no nível 3**. Só com parecer jurídico (padrão: `false`) |
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
# Web — o build gera navegador **e** servidor de renderização
cd web
npm run build                        # dist/fiance/browser + dist/fiance/server
node dist/fiance/server/server.mjs   # sobe o servidor (porta 4000 por padrão)

# Backend — Railway usa o Procfile (uvicorn) automaticamente.
# Root Directory do serviço no Railway deve ser "backend".

# Mobile — APK de teste
cd mobile
flutter build apk --release   # saída em build/app/outputs/flutter-apk/

# Mobile — App Bundle para a Play Store (requer keystore de release configurado)
flutter build appbundle --release
```

Por padrão, o app mobile aponta para o backend em produção (`https://fiance.up.railway.app/api`), configurado em `mobile/lib/core/api_client.dart`.

## Renderização no servidor

A rota `/ativo/:ticker` é renderizada no servidor; todo o resto continua no
cliente. Não é refinamento técnico: é o canal de aquisição do produto — página
renderizada no cliente é invisível para busca, e o modelo de receita não
comporta mídia paga para compensar. A fronteira está declarada em
`web/src/app/app.routes.server.ts` e tem teste.

O servidor também serve `/sitemap.xml` (montado a partir de
`GET /api/public/universe`, com cache de 6h) e `/robots.txt`.

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `PORT` | Não | Porta do servidor de renderização (padrão: `4000`) |
| `ALLOWED_HOSTS` | **Em produção** | Hosts aceitos no cabeçalho `Host`, separados por vírgula. O Angular recusa host desconhecido para não virar proxy de SSRF; sem configurar, só `localhost` e `127.0.0.1` respondem. |
| `SITE_URL` | Sim | Base pública, usada nas URLs absolutas do sitemap (padrão: `https://fiance.app`) |

O backend expõe a leitura **sem titular** em `/api/public/asset/{ticker}` e
`/api/public/universe` — impessoal de propósito, para que a mesma URL devolva o
mesmo conteúdo ao robô e a quem chega pelo link. O teto de abuso dessas rotas é
por IP, não por usuário.

## Versão da API e paginação

O caminho canônico é `/api/v1`. `/api` continua respondendo — os apps instalados
apontam para lá e derrubá-los num deploy seria trocar um problema por outro —
mas é transição: toda resposta carrega `X-API-Version`, e as que chegam pelo
caminho sem versão carregam também `X-API-Deprecation`. O alias sai quando a
telemetria mostrar que não há mais cliente antigo chamando.

A versão muda quando uma resposta deixa de ser retrocompatível: campo removido
ou renomeado, semântica alterada. Campo **adicionado** não muda a versão —
cliente que não o conhece o ignora.

As listas que crescem com o uso aceitam `limit` e `cursor`:

| Rota | Corte |
| --- | --- |
| `/portfolio/trades` | no banco |
| `/transactions` | no banco |
| `/dividends/received` | no payload |
| `/fixed-income` | no payload |
| `/suggestions/followed` | no payload |

A distinção importa. Onde há agregado sobre a lista — total por mês, marcação a
mercado, comparação contra o Ibovespa — a **consulta** continua completa e só o
payload é limitado: cortar no banco faria o total falar apenas da página, e um
total que encolhe conforme a rolagem é pior que uma lista longa. Onde não há
agregado, o corte é no banco de verdade.

A resposta ganha `next_cursor`, `has_more` e `total_count`. O cursor é keyset —
a última chave lida, `(ordenação, id)` — e não offset: com offset, inserir um
registro entre duas páginas empurra tudo para baixo e o item da borda aparece
duas vezes.

## Cobrança

O direito de Premium mora no backend, ligado ao `user_id`; o gateway é **detalhe
de canal**. É isso que permite vender na web (Pix 1,19%, cartão 3,99% + R$ 0,39)
e liberar no app sem migrar assinante quando a compra in-app entrar — 14 pontos
de diferença de taxa sobre R$ 179,90, que em mil assinantes anuais são ~R$ 25
mil por ano.

Quatro peças: catálogo (`GET /billing/plans`), checkout
(`POST /billing/checkout`, que **não** concede nada), webhook
(`POST /billing/webhook`, idempotente por id de evento) e reconciliação
(`GET /billing/reconciliation`, rota de operador).

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `BILLING_WEBHOOK_SECRET` | **Em produção** | Segredo HMAC de verificação do webhook |

**A integração com a Stripe ainda não existe.** O provedor em uso é o de
desenvolvimento (`FakeProvider`), que assina com o mesmo HMAC — de propósito,
para que o caminho de verificação seja exercitado. O contrato à volta está
testado: sessão criada sem conceder, webhook idempotente, assinatura verificada
em tempo constante, corpo adulterado recusado, reconciliação nos dois sentidos.

Para ligar a Stripe de verdade:

1. Implementar `StripeProvider` com o mesmo protocolo de `payments/provider.py`
   (`create_checkout`, `verify`, `parse`, `active_subscriptions`).
2. Trocar o retorno de `payments.billing.provider()`.
3. Configurar `BILLING_WEBHOOK_SECRET` com o *signing secret* do endpoint.
4. Testar de ponta a ponta com chave de teste — **isto não é verificável na
   suíte**, porque depende de infraestrutura externa.

## Indicação

Mídia paga está fora de alcance por aritmética: R$ 500 a R$ 1.500 por
instalação qualificada em finanças no Brasil, contra um teto de CAC de R$ 72. O
canal que sobra é alguém contando para alguém, e o programa existe para tornar
isso um pouco mais provável — não para comprar cadastro.

A regra que importa é **quando** o crédito sai, não quanto ele vale. Conta é
grátis de fabricar aos milhares; carteira, não. Por isso o crédito só aparece
quando a pessoa indicada salva a primeira posição — o mesmo marco que dispara o
trial.

| Rota | O que faz |
| --- | --- |
| `GET /referral` | Código, contagens e crédito. Nunca a lista de quem foi indicado. |
| `POST /referral/rotate` | Queima o código atual. Indicações já atribuídas seguem valendo. |
| `POST /auth/google` | Aceita `referral_code`. É o **único** ponto de atribuição. |

São 30 dias por indicação qualificada, para os dois lados, com teto de 365 dias
acumulados por pessoa. Crédito sem teto é passivo sem teto, e quem traz duzentas
pessoas precisa de uma conversa de parceria, não de dezesseis anos de Premium.

Não existe rota para aplicar um código depois. Ela seria a porta de entrada para
reivindicar usuários que já estavam no produto — crédito por uma aquisição que
não aconteceu. Pelo mesmo motivo a atribuição é recusada quando a conta já tem
carteira, quando já foi atribuída antes, e quando o código é da própria pessoa.
Uma recusa **não** derruba o login: quem digitou um código errado ainda assim
quer entrar.

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
npm run build       # build de produção (navegador + servidor)
npm test            # testes (Vitest)
npm run lint:ui     # ícone não registrado e classe CSS inexistente
npm run format      # formatar código com Prettier
npm run format:check # verificar formatação

# Mobile
flutter analyze         # lint
flutter test             # testes
flutter build apk         # build de release (Android)
```

## Licença

Distribuído sob licença proprietária. Consulte o arquivo [LICENSE](LICENSE) para detalhes.
