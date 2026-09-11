# fiance

Plataforma de inteligência de investimentos com análise fundamentalista, varredura de oportunidades e sugestões determinísticas de alocação, focada no mercado brasileiro (B3). É um **aplicativo para celular** (iOS/Android) sobre uma API própria, com login por conta Google e dados isolados por usuário.

## Documentação

Este README cobre **instalação, execução e operação**. O resto tem lugar próprio —
comece pelo [índice](docs/README.md), que diz qual arquivo responde o quê.

| Quero saber | Leia |
|---|---|
| Invariantes, armadilhas e checklists de contribuição | [CLAUDE.md](CLAUDE.md) |
| Como o sistema é montado por dentro | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| O que cada tela faz | [docs/FEATURES.md](docs/FEATURES.md) |
| O que está aberto agora | [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) |
| Por que uma decisão foi tomada | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| Por que a interface é assim | [docs/design/](docs/design/) |

## Visão Geral

O fiance integra dados de mercado em tempo real e métodos clássicos de valuation (Bazin, Graham, DCF) para entregar uma visão consolidada da sua carteira, identificar ativos com desconto e gerar estratégias de alocação personalizadas — focado 100% na B3 (ações, BDRs, FIIs e ETFs).

**Principais funcionalidades:**

- Login com Google (multi-usuário, dados isolados por conta)
- Dashboard com posições, P&L e metas de alocação
- Scanner de oportunidades com pontuação fundamentalista e técnica
- Scanner de quedas ("dip") com diagnóstico por ativo
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
| Aplicativo | Flutter (iOS/Android), Riverpod, go_router |
| Dados de mercado — B3/FIIs/BDRs/ETFs | [BRAPI](https://brapi.dev) |
| Dados de renda fixa — CDI/Selic/IPCA | [BCB SGS](https://www3.bcb.gov.br/sgspub/) |
| Hospedagem backend | Railway |
| Linting / Format | Ruff (Python), `flutter analyze` (Dart) |

## Pré-requisitos

- Python 3.11+
- Flutter 3.x + Android Studio / Xcode (para o aplicativo)
- Chave de API: [BRAPI](https://brapi.dev)
- OAuth Client IDs do Google (Web, Android e iOS) em [console.cloud.google.com](https://console.cloud.google.com/apis/credentials) — o **Web** é usado como `serverClientId`, mesmo não havendo site
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

### Aplicativo

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
| `ALLOWED_ORIGINS` | Não | Origens CORS permitidas. Nenhum navegador é cliente da API hoje, mas fora de `development` a variável é obrigatória: falhar fechado é a regra do startup |
| `ENTITLEMENTS_ENABLED` | Não | Liga a régua de plano (padrão: `false` — todo mundo tem tudo) |
| `AFFIRMATION_LEVEL` | Não | Modo de afirmação: `1` descritivo, `2` analítico (padrão), `3` prescritivo |
| `SUITABILITY_PERSONALIZATION_ALLOWED` | Não | Libera personalização por perfil **no nível 3**. Só com parecer jurídico (padrão: `false`) |
| `ADMIN_USER_IDS` | Não | IDs (o `sub` do Google) liberados em `/cache/clear` e `/metrics`, separados por vírgula. Vazio libera em `development` e **nega** em produção |
| `DEFAULT_UNIVERSE` | Não | Tickers monitorados, separados por vírgula |
| `BRAPI_HISTORY_RANGE` | Não | Janela de histórico da BRAPI. O padrão `3mo` (plano gratuito) **torna a SMA200 incalculável** — a tendência sai como `short` e é rotulada como tal. `2y` exige plano pago |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Não | Credencial do Firebase Admin para push. Sem ela, o envio apenas loga em vez de falhar |
| `REDIS_URL` | Não | Cache compartilhado via Redis. Ver [Cache](#cache) |
| `CACHE_BACKEND` | Não | `database`, `sqlite` ou `redis`. Sem ela, o banco decide. Ver [Cache](#cache) |
| `CACHE_DB_PATH` | Não | Caminho do cache em arquivo (padrão: `backend/.cache/http_cache.db`) |
| `RATE_LIMIT_ENABLED` | Não | Liga o teto de requisições (padrão: `true`) |
| `RATE_LIMIT_FACTOR` | Não | Multiplicador dos tetos, para afrouxar em dev |

No app mobile (`mobile/lib/core/auth_service.dart`), o login com Google usa um `serverClientId` (o Client ID **Web**) — é ele que faz o `idToken` ter uma audience validável pelo backend, independente da plataforma (Android/iOS).

## Execução

### Desenvolvimento

```bash
# Terminal 1 — Backend (http://localhost:8000)
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Aplicativo (emulador/dispositivo, apontando pro backend local)
cd mobile
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api   # emulador Android
flutter run --dart-define=API_BASE_URL=http://localhost:8000/api  # iOS simulator
```

O texto jurídico abre no navegador do aparelho, e vem do mesmo backend: para apontá-lo para o
local, passe `--dart-define=SITE_URL=http://10.0.2.2:8000`.

### Build de Produção

```bash
# Backend — Railway usa o Procfile (uvicorn) automaticamente.
# Root Directory do serviço no Railway deve ser "backend".

# Mobile — APK de teste (assina com a chave de debug se não houver keystore)
cd mobile
flutter build apk --release   # saída em build/app/outputs/flutter-apk/

# Mobile — App Bundle para a Play Store (exige android/key.properties; ver abaixo)
flutter build appbundle --release
```

Por padrão, o app mobile aponta para o backend em produção (`https://fiance.up.railway.app/api`), configurado em `mobile/lib/core/api_client.dart`.

### Assinatura do Android

O APK de release sai assinado com a **chave de debug** quando não há keystore: serve para
instalar no aparelho, e a Play Store recusa. O App Bundle não aceita isso e **falha** sem chave,
porque ele é o artefato de loja.

A chave é sua e não mora no repositório. Gere uma vez e guarde as duas coisas — o `.jks` e a
senha —, porque **keystore perdido é aplicativo que não pode mais ser atualizado**:

```bash
keytool -genkeypair -v -keystore ~/fiance-release.jks -keyalg RSA -keysize 2048         -validity 10000 -alias fiance
```

Depois declare em `mobile/android/key.properties` (já está no `.gitignore`):

```properties
storePassword=…
keyPassword=…
keyAlias=fiance
storeFile=/caminho/absoluto/para/fiance-release.jks
```

O arquivo é lido em `android/app/build.gradle.kts`. Declarado pela metade — campo faltando ou
`.jks` inexistente —, o build **falha dizendo qual**; é a situação em que assinar com a chave
errada em silêncio seria pior.

### Firebase no build

`android/app/google-services.json` é segredo de projeto e não está no repositório. Sem nenhum
arquivo o plugin do Firebase interrompe o build, então há um substituto que **não fala com projeto
nenhum** e serve só para compilar (é o que o CI usa):

```bash
cp android/app/google-services.ci.json android/app/google-services.json
```

Com ele, login pelo Google e push não funcionam — para rodar o app de verdade, use o arquivo do
projeto Firebase.

### Telemetria do mobile

O DSN vem embutido (`lib/core/telemetry.dart`) e o app só reporta em release. O ambiente é
`production` num build de release e `development` fora dele; para apontar um build de release
para outro projeto ou ambiente, passe no build:

```bash
flutter build apk --release   --dart-define=SENTRY_DSN=…   --dart-define=APP_ENV=staging
```

## Páginas públicas

Não há front web. O que o backend serve em HTML são **três páginas de documento**, fora de
`/api`: `/termos`, `/privacidade` e `/aviso-cvm` (`app/api/legal.py` +
`app/services/legal_pages.py`). Elas existem porque as lojas exigem uma URL de privacidade que
abra sem login, e é para elas que o aplicativo manda quem toca em "Termos" nas configurações.

São páginas sem JavaScript, sem asset externo e sem paleta — a cor vem do agente do usuário, e
uma segunda cópia dos tokens de design envelheceria calada. O Aviso CVM lê a postura de afirmação
em vigor **no servidor**, então `AFFIRMATION_LEVEL` continua sendo a única fonte da frase.

O backend também expõe a leitura **sem titular** em `/api/public/asset/{ticker}` — impessoal de
propósito, para que a mesma URL devolva o mesmo conteúdo a quem chega por um link compartilhado.
O teto de abuso dessa rota é por IP, não por usuário.

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
de canal**. Com a distribuição só por loja, o canal provável é a compra in-app (15–30% de
comissão) — a alternativa de vender fora do aplicativo saiu junto com o site, e a decisão está
aberta em [docs/produto/PRE_PRODUCAO.md](docs/produto/PRE_PRODUCAO.md) §B1. O que a arquitetura
garante é que trocar de canal não migra assinante.

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

## Cache

São três lugares onde o cache pode morar, e a escolha padrão é a do banco:
**se existe Postgres, o cache vai para ele.** O arquivo local só é o padrão
quando o banco também é local.

O motivo é o disco do contêiner: ele é efêmero. Cache em arquivo nasce frio a
cada deploy, e a cota da fonte paga a conta de reconstruir o que já se sabia. O
Postgres já está de pé, já tem backup e já é alcançável por todos os nós — o
cache pega carona sem serviço novo para operar.

Com **mais de um nó**, cache por nó deixa de ser desempenho e vira correção:
cada nó guarda a própria cópia, e a mesma pessoa recarregando a página vê preços
diferentes conforme o balanceador. "Subiu 2% ou caiu 1%?" passa a depender de
qual máquina atendeu, e isso mina a confiança no número muito além do que
algumas chamadas externas a mais custariam.

| Variável | Efeito |
| --- | --- |
| _(nenhuma)_ | Banco se `DATABASE_URL` for Postgres; arquivo local se for SQLite |
| `CACHE_BACKEND=database` | Tabela `cache_entries` no banco da aplicação |
| `CACHE_BACKEND=sqlite` | Arquivo local (`CACHE_DB_PATH`, opcional) |
| `REDIS_URL` | Cache compartilhado via Redis — a opção mais rápida |

Nome errado em `CACHE_BACKEND` **falha alto**, pelo mesmo motivo que `REDIS_URL`
sem o pacote falha: cair em silêncio para cache por nó é o tipo de defeito que
só aparece num gráfico de latência, semanas depois.

`CACHE_BACKEND=database` **sobre SQLite não é recomendado**: o SQLite serializa
escritores, então uma gravação de cache durante uma escrita de carteira aberta
falha com *database is locked* — ela é registrada e engolida, virando leitura
externa a mais, não erro para o usuário. É por isso que o padrão só escolhe o
banco quando ele é Postgres. Em dev, deixe no arquivo.

`GET /metrics` (rota de operador) diz onde o cache está morando e se ele é
compartilhado. Descobrir que os nós não compartilham cache olhando gráfico de
latência é caro; a resposta é uma palavra.

Se `REDIS_URL` estiver configurado e o pacote `redis` faltar, a aplicação
**falha alto** em vez de cair para cache por nó — o sintoma silencioso seria
preço divergente entre nós, que ninguém atribui a um pacote faltando.

O contrato do cache é escrito uma vez (`tests/test_cache_backends.py`) e rodado
contra os três backends. O do Redis precisa de um servidor: no CI ele sobe como
serviço; localmente, exporte `REDIS_TEST_URL` (sem isso os testes do Redis são
**pulados com o motivo escrito**, não silenciosamente ignorados). O do banco roda
sempre, porque roda contra o banco de teste.

### Economia de cota

A BRAPI cobra por requisição, e o plano gratuito dá 3.000 por dia. Duas decisões
mantêm o consumo bem abaixo disso:

**O universo é buscado em lote.** `prefetch_brapi_raw` pede até 20 tickers por
chamada e preenche `brapi_raw:*` de uma vez; como todo caminho de leitura passa
por essa chave, o resto do módulo trabalha sem tocar na rede. A varredura do
universo caiu de ~285 requisições para ~15.

**A ausência é lembrada.** Ticker que a fonte não conhece fica marcado por 30
minutos. Antes, um ticker morto no universo era repedido a cada rodada do scan —
96 vezes por dia, cada, para ouvir o mesmo "não". Falha de rede **não** vira
ausência: não saber se o ticker existe é diferente de saber que não existe, e
confundir os dois esconderia uma fonte fora do ar por meia hora.

`GET /metrics` conta `external.brapi.ok` e `external.brapi.error`. Dois pontos
separados por uma hora dão o consumo real.

## Documentação da API

Com o backend rodando, acesse a documentação interativa:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints principais

O caminho canônico é **`/api/v1`**; `/api` responde como alias em transição (ver
[Versão da API](#versão-da-api-e-paginação)). São 33 routers — a lista completa, com o arquivo de
cada rota, está em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check (público) |
| `POST` | `/auth/google` | Login: troca o `id_token` do Google por um JWT de sessão (público) |
| `GET` | `/public/asset/{ticker}` , `/public/affirmation` | Leitura **sem titular**, com teto por IP (público) |
| `GET` | `/dashboard` | Dados consolidados do dashboard |
| `GET/PUT` | `/portfolio` | Ler carteira · `PUT` é **importação destrutiva** |
| `POST/DELETE` | `/portfolio/position` , `/portfolio/position/{ticker}` | Escrita por item — o caminho normal |
| `POST` | `/portfolio/evaluate` | Calcular P&L e alocação |
| `GET/POST` | `/transactions` , `/transactions/import` | Lançamentos e importação (prévia + commit) |
| `GET` | `/transactions/reconciliation` | Compara posição corrente com a projeção do razão |
| `GET` | `/opportunities` | Oportunidades com score |
| `GET` | `/dip-scanner` | Ativos abaixo do preço justo |
| `GET` | `/asset/{ticker}` , `/asset/{ticker}/dip-analysis` , `/compare` | Análise de ativo |
| `GET` | `/sectors-summary` | Agrupamento por setor |
| `GET` | `/strategy` , `/rebalance-suggestions` | Estratégia de alocação e rebalanceamento |
| `POST` | `/quick-invest` | Distribuição de um aporte |
| `GET` | `/search` | Busca global: carteira, renda fixa e universo |
| `GET` | `/onboarding` | Passo derivado do que a pessoa já fez |
| `GET/POST/PUT/DELETE` | `/fixed-income` | Renda fixa, marcada a mercado |
| `GET` | `/dividends/received` , `/dividends/pending` | Proventos lançados e sugeridos pelo calendário |
| `GET/POST` | `/alerts` | Alertas de preço |
| `GET/PUT` | `/goals` , `/sector-goals` , `/preferences` | Metas e preferências |
| `GET` | `/benchmark` , `/income-compare` , `/projection/passive-income` | Comparações e projeção |
| `GET` | `/billing/plans` · `POST` `/billing/checkout` , `/billing/webhook` | Cobrança |
| `GET` | `/referral` · `POST` `/referral/rotate` | Indicação |
| `GET` | `/account/export` · `DELETE` `/account` | Exportação e exclusão — nunca atrás de plano |
| `GET` | `/data-quality` , `/data-quality/source` | Cobertura do dado e estado do disjuntor |
| `GET` | `/metrics` · `POST` `/cache/clear` | Rotas de operador (`ADMIN_USER_IDS`) |

Todas as rotas acima (exceto `/health`, `/auth/google` e `/public/*`) exigem `Authorization: Bearer <token>` e retornam dados isolados por usuário.

## Estrutura do Projeto

```
fiance/
├── backend/
│   ├── app/
│   │   ├── main.py              # App FastAPI, CORS, observabilidade, lifespan
│   │   ├── analysis/            # Cálculo puro, sem I/O: Bazin, Graham, DCF, score,
│   │   │                        #   falsificadores, cenários, renda fixa
│   │   ├── optimizer/           # Custo de venda e IR (com compensação de prejuízo)
│   │   ├── ledger/              # Livro-razão: lançamentos e projeção (não conhece banco)
│   │   ├── importing/           # Importação de operações: prévia + commit
│   │   ├── entitlement/         # Cerca de plano — o ÚNICO lugar com condicional de plano
│   │   ├── payments/            # Catálogo, checkout, webhook idempotente
│   │   ├── api/                 # 33 routers REST
│   │   ├── collectors/          # BRAPI e BCB SGS, com plausibilidade e disjuntor
│   │   ├── services/            # Orquestração de negócio
│   │   ├── models/              # Schemas Pydantic + ORM SQLAlchemy
│   │   ├── repositories/        # Fachada tipada sobre storage/
│   │   ├── storage/             # Persistência — onde o multi-tenant é aplicado
│   │   ├── notifications/       # Push via Firebase (degrada sem credencial)
│   │   ├── affirmation.py       # Modo de afirmação (CVM 19/20) como configuração
│   │   └── core/                # Config, banco, auth, sessões, cache, dinheiro,
│   │                            #   paginação, eventos, uso, jobs, fuso fiscal
│   ├── migrations/              # Alembic — coluna nova exige migração
│   ├── tests/                   # 1036 testes
│   └── requirements.txt
│
└── mobile/                      # Flutter — o único cliente
    ├── assets/brand/            # A marca: ícone do app e kit de referência (gerados)
    ├── tool/build_icons.py      # Gera os ícones a partir da cor de design_tokens.dart
    ├── test/                    # 125 testes, incluindo lint_ui_test e contraste_test
    └── lib/
        ├── core/                # API client, auth, providers, router,
        │                        #   design_tokens.dart — a ÚNICA paleta do produto
        └── features/            # mes, sobra, patrimonio, market, config,
                                 #   busca, assets, auth, shell, tools
```

## Métodos de Valuation

| Método | Fórmula | Aplicação |
|--------|---------|-----------|
| **Bazin** | `Preço justo = DPA médio / Yield desejado` | Ações com dividendos consistentes, FIIs |
| **Graham** | `Preço justo = √(22,5 × LPA × VPA)` | Ações de valor, BDRs |
| **DCF** | Fluxo de caixa descontado | Crescimento futuro |
| **P/VP justo** | `Preço justo = VPA × P/VP alvo` | FIIs, no consenso com Bazin |
| **Consenso** | Média dos métodos aplicáveis ao tipo | `consensus_methods` diz quantos entraram |

O roteamento é por tipo de ativo: **FII** → Bazin + P/VP (nunca Graham); **BDR** → Graham + DCF;
**ETF** → só Bazin (não tem LPA nem VPA de empresa); **ação BR** → Bazin + Graham + DCF.

## Scripts Disponíveis

```bash
# Backend
uvicorn app.main:app --reload            # servidor dev
python -m pytest -q                      # 1032 passam (11 pulam sem Redis)
python -m ruff check app tests migrations
python -m ruff format app tests migrations
alembic upgrade head                     # aplicar migrações

# Aplicativo — a partir de mobile/
flutter analyze
flutter test         # 125 testes, incluindo as 11 regras de interface e o contraste
flutter build apk --release   # analyze e test NUNCA tocam o Gradle; este comando toca

# Marca — a partir de mobile/
# Não há gerador de design. Cor, tipografia, espaço e as réguas do produto são escritos à mão,
# em lib/core/design_tokens.dart e lib/core/product_rules.dart.
python tool/build_icons.py            # regenerar os ícones a partir da cor da marca
python tool/build_icons.py --check    # falha se a marca divergir (roda no CI)
dart run flutter_launcher_icons       # ícones nativos (segundo passo, e é fácil esquecer)
```

> **Não rode `dart format`**: ele reescreve `design_tokens.dart` e quebra `if`s de uma linha que o
> repositório mantém.

## Licença

Distribuído sob licença proprietária. Consulte o arquivo [LICENSE](LICENSE) para detalhes.
