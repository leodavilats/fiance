# fiance

Plataforma de análise de investimentos para a B3, multi-tenant: carteira, fluxo de caixa, apuração
de imposto e análise de ativos num só lugar.

**Backend** FastAPI + Postgres (`backend/`) · **Cliente** Flutter (`mobile/`), o único

---

## Para quem chega agora

| Pergunta | Onde |
|---|---|
| Por que este sistema existe | [docs/01-PRODUTO.md](docs/01-PRODUTO.md) |
| **O que realmente funciona hoje** | [docs/08-ESTADO.md](docs/08-ESTADO.md) |
| Como ele é montado | [docs/03-ARQUITETURA.md](docs/03-ARQUITETURA.md) |
| Como trabalhar sem quebrar nada | [CLAUDE.md](CLAUDE.md) |
| Índice completo | [docs/README.md](docs/README.md) |

**Estado:** em desenvolvimento, um usuário (o autor), nada publicado em loja, sem receita.

---

## Pré-requisitos

- **Python 3.13** (o CI usa 3.13)
- **Flutter 3.x** + Android Studio, ou Xcode para iOS
- Token da [BRAPI](https://brapi.dev) — cotações e fundamentos
- OAuth Client IDs do Google (Web, Android, iOS) em
  [console.cloud.google.com](https://console.cloud.google.com/apis/credentials). O **Web** é usado
  como `serverClientId`, mesmo não havendo site — é ele que dá ao `idToken` uma audience validável
  pelo backend em qualquer plataforma
- Postgres, para produção. Local roda em SQLite sem configuração

---

## Instalação

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt

# Aplicativo
cd mobile
flutter pub get
```

## Configuração

```bash
cp backend/.env.example backend/.env
```

### Obrigatórias

| Variável | Para quê |
|---|---|
| `APP_ENV` | `development` ou `production`. **Não tem default**: vazio falha no startup, e se algo escapar, falha **fechado** |
| `GOOGLE_CLIENT_ID` | Client IDs aceitos como audience do login, separados por vírgula |
| `APPLE_CLIENT_ID` | Bundle id e Services ID aceitos como audience do login com Apple, separados por vírgula |
| `JWT_SECRET` | Assina o JWT de sessão. O valor de exemplo é recusado fora de desenvolvimento |
| `BRAPI_TOKEN` | Cotações e fundamentos |

### Principais opcionais

| Variável | Padrão | Para quê |
|---|---|---|
| `DATABASE_URL` | SQLite local | Postgres. O Railway injeta automaticamente |
| `ALLOWED_ORIGINS` | localhost | CORS. Nenhum navegador é cliente hoje, mas fora de `development` a variável é exigida |
| `BRAPI_HISTORY_RANGE` | `3mo` | ⚠️ `3mo` **torna a SMA200 incalculável**, e a tendência sai rotulada como curta. `1y` dá ~250 pregões e é o que produção usa |
| `AFFIRMATION_LEVEL` | `2` | `1` descritivo, `2` analítico, `3` prescritivo — ver [ADR-007](docs/decisoes/ADR-007-nivel-de-afirmacao.md) |
| `ENTITLEMENTS_ENABLED` | `false` | Cerca de plano. Ligar exige `ENTITLEMENTS_ENABLED_AT`, ou falha alto |
| `ADMIN_USER_IDS` | vazio | O `sub` do Google (ou `apple:<sub>` para conta Apple), separado por vírgula. Vazio libera em dev e **nega** em produção |
| `CACHE_BACKEND` | automático | `database`, `sqlite` ou `redis`. Nome errado **falha alto** |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | vazio | Push. Sem ela, o envio apenas loga |
| `RATE_LIMIT_FACTOR` | `1.0` | Afrouxar tetos em desenvolvimento |

Lista completa em `backend/app/core/config.py` — é a fonte de verdade.

---

## Rodar

```bash
# Terminal 1 — backend em http://localhost:8000
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — aplicativo
cd mobile
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1   # emulador Android
flutter run --dart-define=API_BASE_URL=http://localhost:8000/api/v1  # simulador iOS
```

O texto jurídico abre no navegador do aparelho e vem do mesmo backend. Para apontá-lo ao local:
`--dart-define=SITE_URL=http://10.0.2.2:8000`.

---

## Testar

**Esta é a lista do CI inteira.** Rode antes de commitar.

```bash
cd backend && python -m pytest -q
cd backend && python -m ruff check app tests migrations
cd backend && python -m ruff format --check app tests
cd mobile  && flutter analyze && flutter test
cd mobile  && flutter build apk --release
cd mobile  && python tool/build_icons.py --check
```

Três avisos que já custaram tempo, detalhados em
[docs/06-DESENVOLVIMENTO.md](docs/06-DESENVOLVIMENTO.md):

- **não rode `dart format`** — reescreve o `design_tokens.dart`
- **`analyze` e `test` nunca tocam o Gradle** — o build Android é outra metade
- se está no CI, está nesta lista

---

## Estrutura

```
backend/
  app/
    api/          rotas
    services/     orquestração
    storage/      acesso a dados, por usuário
    ledger/       razão, projeção, apuração — sem banco
    cashflow/     mês, cascata, dívida — sem banco
    analysis/     preço justo, score — sem banco
    collectors/   BRAPI, BCB, cache, disjuntor
    entitlement/  cerca de plano, isolada
    importing/    leitura de extrato, prévia + commit
    payments/     cobrança (só FakeProvider, será refeita para loja)
    notifications/ push
    backup.py     cópia lógica, restauração, reaplicar exclusões
  migrations/     Alembic
  tests/

mobile/
  lib/
    core/         tokens, roteador, modelos, rede
    features/     telas, por destino
  test/           inclui lint_ui_test e contraste_test

docs/             ver docs/README.md
```

A separação entre `ledger`/`cashflow`/`analysis` e o resto **é invariante**, não estilo:
[ADR-001](docs/decisoes/ADR-001-matematica-pura.md).

---

## Deploy

Railway, com Postgres gerenciado. A migração roda como **pre-deploy**
(`python -m app.release`), nunca no startup.

Procedimento e pré-requisitos de loja em [docs/07-OPERACAO.md](docs/07-OPERACAO.md).

### Chave de release do Android

O App Bundle de release exige um `key.properties` na pasta `android/` do app, **fora do git** (o
`.gitignore` do Android já recusa `key.properties` e `*.keystore`). Sem o arquivo, o APK cai na chave
de debug, que a Play Store recusa; o AAB nem é gerado.

```bash
keytool -genkey -v -keystore mobile/android/fiance-release.keystore -alias fiance   -keyalg RSA -keysize 2048 -validity 10000
```

```properties
# mobile/android/key.properties
storeFile=fiance-release.keystore
storePassword=...
keyAlias=fiance
keyPassword=...
```

`storeFile` é relativo a `mobile/android/`. **Perder a chave impede atualizar o app na loja** — guarde
o keystore e as senhas num cofre, fora da máquina de quem gerou.

---

## Licença

Ver [LICENSE](LICENSE).
