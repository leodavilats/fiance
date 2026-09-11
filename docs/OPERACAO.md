# Operação: subir, observar, reverter

O que precisa existir **fora do repositório** para o produto ficar no ar de forma responsável, e o
que fazer quando algo quebra. O código de cada peça já está pronto e desligado; o que falta aqui é
conta, chave e um teste executado de verdade.

> **Este arquivo é sobre a máquina, não sobre o produto.** O que cada tela faz está em
> [FEATURES.md](FEATURES.md); como o sistema é montado, em [ARCHITECTURE.md](ARCHITECTURE.md); o
> que está aberto, em [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

---

## Variáveis de ambiente

`APP_ENV` **não tem default**: vazio derruba o startup, e se algo escapar ele falha fechado (não
assume development). Esquecer essa variável desarmaria JWT, CORS e a rota de operador de uma vez.

| Variável | Obrigatória | O que acontece se faltar |
|---|---|---|
| `APP_ENV` | **sim** | startup falha alto |
| `DATABASE_URL` | sim em produção | cai para SQLite local — dado some no próximo deploy |
| `JWT_SECRET` | sim fora de development | startup falha alto |
| `ALLOWED_ORIGINS` | sim fora de development | startup falha alto |
| `BILLING_WEBHOOK_SECRET` | sim fora de development | startup falha alto |
| `ENTITLEMENTS_ENABLED_AT` | **sim, se `ENTITLEMENTS_ENABLED=true`** | startup falha alto — sem a data em que a cerca subiu, ligá-la derruba a base inteira para Free |
| `BRAPI_TOKEN` | recomendada | cota anônima acaba rápido; o disjuntor abre |
| `SENTRY_DSN` | não | telemetria desligada (o pacote nem inicializa) |
| `RELEASE` | não | stack trace não aponta para o commit |
| `CACHE_BACKEND` | não | escolhe sozinho: banco da aplicação em Postgres, arquivo local em SQLite |
| `WEB_CONCURRENCY` | não | dois workers, que é o default do Procfile |

Há **um serviço de aplicação só** desde 2026-09-11: o front web saiu, e com ele o serviço
`fiance-web` e as variáveis dele (`SITE_URL`, `ALLOWED_HOSTS`, `NODE_ENV`). O cliente agora é o
aplicativo, que chega por loja.

`ALLOWED_ORIGINS` continua obrigatória e continua sendo lida pelo CORS, embora **nenhum navegador
seja mais cliente da API**: aplicativo nativo não faz *preflight*, e as três páginas jurídicas são
servidas pelo mesmo processo. Ela permanece porque falhar fechado é a regra do startup — deixar a
variável cair no vazio seria abrir CORS por omissão no dia em que um navegador voltar.

`SENTRY_DSN` configurado **com o pacote faltando falha alto**, de propósito: um sistema que se acha
observado e não está é pior que um assumidamente cego.

**Ligar a cerca de plano é ligar duas variáveis, não uma.** O trial começa na primeira posição
salva e é iniciado **mesmo com a cerca desligada**, então toda conta que já tem carteira carrega um
`trial_ends_at` no passado, e `start_trial` não re-arma. `ENTITLEMENTS_ENABLED_AT` é a data em que a
cerca subiu, e o relógio do trial passa a contar do **mais tarde** entre qualificar e essa data:
quem já tinha carteira ganha os 14 dias a partir dali. Aceita ISO (`2026-10-01`, lido em UTC) ou
epoch. Sem ela, o startup falha alto — de propósito, porque o modo de errar aqui é silencioso e
atinge todo mundo de uma vez.

---

## Migração: é *release command*, não startup

`app/core/database.py` separa as duas coisas:

- **`migrate()`** aplica as migrações. É o que `python -m app.release` chama, e é o que o
  `release:` do Procfile executa — **uma vez por deploy**.
- **`conferir_revisao()`** é o que o startup do processo web faz: confere que a revisão do banco
  bate com a do código e **falha alto** se não bater.

Migrar no `lifespan` funcionava com `--workers 1` e mordia no primeiro dia com tráfego suficiente
para escalar: duas réplicas subindo juntas começam duas migrações concorrentes, e o Alembic não
coordena isso. Banco local em SQLite continua se criando sozinho — é de um processo só.

**No Railway, quem executa isso é o campo Pre-Deploy Command do serviço**, já apontado para
`python -m app.release`. O Railway **não** roda a linha `release:` de um Procfile — ela existe lá
para plataformas que seguem a convenção do Heroku. Mexer numa sem a outra faz a migração parar de
rodar em silêncio, e o sintoma aparece só no deploy seguinte, como `BancoAtrasado` no startup.

Conferir a qualquer momento:

```bash
railway api 'query { project(id: "<PROJECT_ID>") { services { edges { node { name
  serviceInstances { edges { node { preDeployCommand } } } } } } } }'
```

**Se o startup falhar com `BancoAtrasado`:** rode `python -m app.release` contra aquele banco antes
de subir o processo web. A mensagem do erro já diz isso.

---

## Deploy: homologação, promoção, rollback

O fluxo está em [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) e é **acionado à
mão**. Ele confere que o commit está verde, migra e sobe, e termina com um teste de fumaça em
`/api/health` e `/api/public/asset/PETR4` — que exercita processo, banco, cache e fonte externa de
uma vez.

### O estado do projeto no Railway

Projeto `fiance` (`70bc2a47-2a8e-417c-9231-fbdccf3579aa`), workspace pessoal, plano **Hobby**.

| | production | staging |
|---|---|---|
| Serviços | `fiance` + `Postgres` | `fiance` + `Postgres` |
| URL da API | `fiance.up.railway.app` | `fiance-staging.up.railway.app` |
| `ADMIN_USER_IDS` | definido | definido |
| Volume do banco | `postgres-volume` | `postgres-volume-WKva` (separado) |
| Workers da API | 1 (`WEB_CONCURRENCY`) | 1 |
| Pre-Deploy Command | `python -m app.release` | `python -m app.release` |
| App sleeping | não | **sim** |
| `APP_ENV` | `production` | `staging` |
| `JWT_SECRET` | próprio | **próprio, diferente** |

O `JWT_SECRET` diferente não é detalhe: o ambiente novo nasce copiando as variáveis do de origem,
e com o mesmo segredo um token emitido em homologação valeria em produção.

O banco de homologação é outro de verdade: volume próprio, e `DATABASE_URL` aponta para
`postgres.railway.internal`, que resolve dentro do próprio ambiente.

**Armadilha ao criar um ambiente com `skipInitialDeploys`:** o volume do Postgres **não** é
provisionado junto, e o serviço falha com *"This service requires a volume to be mounted at
/var/lib/postgresql/data"*. O backend falha antes disso, sem conseguir resolver
`postgres.railway.internal` — o banco nunca subiu, então o nome não existe na rede privada. A ordem
que funciona é: criar o volume (`volumeCreate` com `mountPath: /var/lib/postgresql/data`), subir o
Postgres, e só então subir o backend.

### O que falta configurar (uma vez)

1. **Marcar *Wait for CI* no serviço de produção.** Conferido contra o Railway em 2026-09-09 com
   `get-service-config`: o `fiance` (API) tem gatilho `main`, filtro `rootDirectory: /backend` e
   `checkSuites: false`.

   **Ele sobe produção direto do `main`, sem esperar o CI.** Um commit vermelho vai ao ar, e o
   `preDeployCommand` é `python -m app.release` — ou seja, uma migração ruim é aplicada antes de
   qualquer teste terminar. É conserto de um clique.

   A assimetria cliente/servidor **cresceu** com a distribuição por loja: o aplicativo não se
   atualiza no próximo carregamento, passa por fila de revisão e convive com versões antigas
   instaladas. Mudança de contrato de API pede campo **opcional** no Dart, e agora isso é a regra
   que segura a compatibilidade, não uma precaução.

   Enquanto o *Wait for CI* não existir, **quem faz push no `main` publica em produção sem rede** —
   e precisa saber disso antes, não depois.

   **Apagar o serviço `fiance-web`** é o outro item deste bloco: ele não tem mais origem no
   repositório, mas continua de pé servindo a última build. Está registrado no
   [KNOWN_ISSUES](KNOWN_ISSUES.md), item 31.

   Há **mudanças de configuração STAGED e não implantadas** no patch `27a43c52`, e eram **33**:
   **13** no `fiance`, **4** no serviço do front (que saiu) e **13 no `Postgres`** — inclusive
   `POSTGRES_PASSWORD`, `PGPASSWORD` e `DATABASE_URL`. O serviço de banco não estava nesta
   contagem antes, e é o que mais importa dela.

   **Elas não entram no deploy de código.** Uma revisão anterior deste documento afirmava que
   entravam, o que fazia todo push parecer capaz de trocar a senha do banco em produção. Conferido
   em 2026-09-09: o patch continua `STAGED` depois de **oito** deploys de git bem-sucedidos no
   mesmo dia (de `234182a` a `e6cf63a`), com o mesmo `patchId`. Patch de ambiente no Railway pede
   aprovação explícita — o botão *Deploy* do painel, ou `accept-deploy`; o deploy disparado por
   commit constrói e sobe o **código**, e passa ao lado dele.

   O que continua verdade é que o patch existe e ninguém sabe o que há dentro dele: os nomes
   staged são **idênticos** aos que já estão no ar nos três serviços, o que tem a cara de
   re-stage do conjunto inteiro, mas os **valores** não se conferem sem despejar segredo. Conferir
   com `get-service-config`, que lista nome e não valor — e **não** com `list-variables`, que
   devolve `JWT_SECRET`, `DATABASE_URL` e `POSTGRES_PASSWORD` em texto claro. Antes de apertar
   *Deploy* naquele patch, é preciso saber o que ele muda.

2. No GitHub, em *Settings → Environments*, criar `staging` e `production`. Em `production`,
   marcar *Required reviewers* — a confirmação escrita do fluxo é a segunda tranca, não a primeira.

   **Ainda não existem** (conferido em 2026-09-08): a API lista `fiance / production` e
   `fiance / staging`, que são os *deployment environments* criados pelo Railway, não os
   *environments do Actions* que o `deploy.yml` referencia. Enquanto isso, `workflow_dispatch`
   para com a mensagem de token ausente em vez de promover — o fluxo de promoção **não está
   utilizável**, e produção depende do auto-deploy do item 1 e do botão do Railway.
3. Em cada ambiente, definir:
   - segredo `RAILWAY_TOKEN` (token de projeto do Railway);
   - variável `RAILWAY_SERVICE` (`fiance`);
   - variável `SITE_URL` (a URL daquele ambiente, sem barra no fim) — é o que o teste de fumaça
     chama, e é a mesma URL de onde o aplicativo abre o texto jurídico.

### Domínio novo? São três cadastros, não um

Trocar o domínio da API exige mexer em três lugares, e esquecer qualquer um quebra em silêncio ou
no pior momento:

1. **`ALLOWED_ORIGINS`** na API — hoje nenhum navegador é cliente, mas a variável é obrigatória e
   o startup falha sem ela;
2. **`SITE_URL`** em `mobile/lib/core/legal_links.dart`, que vem por `--dart-define` e tem default
   embutido: um build antigo continua apontando para o domínio velho, e quem já instalou não
   recebe a correção até atualizar o aplicativo;
3. **Authorized origins** do cliente OAuth, no
   [Google Cloud Console](https://console.cloud.google.com/apis/credentials) — sem isso o login
   falha por origem não autorizada e nada mais funciona. O `serverClientId` do Google Sign-In é o
   **Client ID Web** mesmo num aplicativo: é ele que torna o `aud` do idToken validável no
   backend.

O terceiro é o que menos se lembra, e é o único que não está em arquivo nenhum deste repositório.

### Quanto isso custa

O Hobby é **US$ 5/mês incluindo US$ 5 de consumo**, e a cobrança é por **recurso**, não por
ambiente — não existe taxa por ambiente criado. O que um ambiente novo faz é consumir RAM e CPU.

Medido em 2026-09-06, em regime, com a API em um worker e o front ainda publicado:

| Serviço | RAM média | Custo/mês |
|---|---|---|
| `fiance` (API) | 0,334 GB | US$ 3,34 |
| `Postgres` | 0,174 GB | US$ 1,74 |
| ~~`fiance-web` (SSR)~~ | ~~0,099 GB~~ | ~~US$ 0,99~~ |
| CPU | 0,011 vCPU | US$ 0,23 |
| **Total medido** | | **US$ 6,30** |

As tarifas são US$ 10/GB/mês de RAM e US$ 20/vCPU/mês. Apagar o serviço do front tira ~US$ 1/mês e
leva o total para perto do crédito — mas a medição acima é de antes dele sair, e vale refazer
depois em vez de confiar na subtração.

Baixar a API para um worker **não** reduziu o consumo dela: ela saiu de 0,252 para 0,334 GB no
mesmo período, porque o SDK do Sentry entrou junto. O worker a menos economizou; o observador a
mais custou mais. Vale saber antes de puxar essa alavanca de novo esperando o resultado de antes.

Homologação **dormindo** custa quase só o Postgres, que não dorme: ~US$ 1/mês. É o que cabe na
folga, e é por isso que `sleepApplication` está ligado lá e `WEB_CONCURRENCY=1`. Sem dormir, seriam
~US$ 2,50/mês e o crédito estouraria.

Para conferir o consumo real a qualquer momento:

```bash
railway api 'query { metrics(projectId: "<PROJECT_ID>", startDate: "<ISO8601>",
  measurements: [MEMORY_USAGE_GB, CPU_USAGE], sampleRateSeconds: 3600,
  groupBy: [SERVICE_ID]) { measurement values { value } tags { serviceId } } }'
```

**`WEB_CONCURRENCY` é o botão de custo.** O Procfile subiu para 2 workers porque o cache saiu do
disco local — isso torna dois workers *possíveis*, não obrigatórios. Num orçamento de US$ 5, cada
worker a mais é ~US$ 2,50/mês de RAM.

### Promover

1. *Actions → Deploy → Run workflow*, ambiente `staging`.
2. Abrir a URL de homologação e conferir o que mudou.
3. Rodar de novo com ambiente `production`, digitando `produção` no campo de confirmação.

### Rollback

O Railway guarda os deploys anteriores: *Deployments → o último que funcionava → Redeploy*. Isso
reverte **o código**, não o banco.

**Sem gatilho de repositório, o Railway não segue o branch.** `serviceInstanceDeploy` sozinho
reconstrói o **mesmo commit** que já estava no ar — o que é o comportamento certo para rollback e
o errado para publicar. Para levar o topo do `main` a produção, é `latestCommit: true`:

```bash
railway api 'mutation { serviceInstanceDeploy(serviceId: "<SERVICE_ID>",
  environmentId: "<ENV_ID>", latestCommit: true) }'
```

**Migração não volta sozinha.** Antes de promover algo que apaga ou renomeia coluna, a regra é a de
sempre: duas etapas. Primeiro sobe o código que funciona com as duas formas do schema; só depois,
num deploy seguinte, sobe a migração que remove a forma antiga. Assim o rollback de código nunca
precisa de rollback de banco.

---

## Observabilidade: o que ligar

O código está pronto nas duas plataformas e é inerte sem DSN. O que falta é conta.

### 1. Sentry (erro)

| Plataforma | Onde | Como ligar |
|---|---|---|
| Backend | `app/core/telemetry.py` | variável `SENTRY_DSN` |
| Aplicativo | `lib/core/telemetry.dart` | DSN embutido; reporta em **release**, cala em debug |

Os DSN estão colados e **conferidos por entrega**, com evento visto na tela de cada projeto
(2026-09-06) — menos o do aplicativo, que nunca teve evento visto em painel (KNOWN_ISSUES #21). Vale saber que a ingestão do Sentry não é instantânea: um evento aceito com `200`
pode levar alguns minutos para aparecer em *Issues*, e a ausência imediata não é sinal de erro. O plano gratuito do Sentry
cobre o volume desta fase com folga.

DSN não é segredo — ele vai no binário do aplicativo de qualquer forma; é um endereço de
escrita, não uma credencial de leitura. Por isso o do aplicativo mora no código, e só o do backend
é variável de ambiente.

No mobile, o build de **release** reporta sempre e o de **debug** cala. Isso é de propósito: um
`--dart-define` que alguém esquece de passar produz um app que se acha observado e não está. Para
exercitar a telemetria num build de debug, passe o DSN explicitamente —
`--dart-define=SENTRY_DSN=…` — que aí ela liga.

### Ver um evento chegar

Em produção e homologação, `POST /api/telemetry/verify` estoura de propósito — exige sessão de
operador (`require_admin`). O erro aparece em *Issues* do projeto `fiance-backend`, filtrando pelo
ambiente. Exercitado em produção em 2026-09-06: devolve 500 e o log traz
`app.api.basic.ErroDeVerificacao`.

**`require_admin` depende de `ADMIN_USER_IDS`.** Sem ela, a rota devolve **403 mesmo com token
válido** em qualquer ambiente que não seja `development` — o token não é o suficiente. Os dois
ambientes têm a variável definida.

Sem sessão à mão, dá para exercitar o caminho inteiro localmente, o que também mostra o que a
limpeza deixa passar:

```bash
cd backend
SENTRY_DSN="<dsn do fiance-backend>" APP_ENV=verificacao-manual python -c "
import sentry_sdk
from app.core.telemetry import configurar_sentry
configurar_sentry()
try:
    raise RuntimeError('teste de telemetria: lucro de R\$ 38.400,00 e quantidade (300)')
except RuntimeError as e:
    print(sentry_sdk.capture_exception(e))
sentry_sdk.flush(timeout=15)
"
```

Na tela do Sentry, o valor e a quantidade devem aparecer como `[redigido]`.

**`capture_exception` devolver um id não prova que o evento chegou.** O SDK é *fire-and-forget*:
ele gera o id localmente, enfileira, e se o servidor recusar (DSN errado, projeto apagado, cota
estourada) a falha morre num log de debug. O teste decisivo é falar com o endpoint na mão e ler o
status:

```bash
python - <<'FIM'
import json, time, urllib.request, uuid
dsn = "<dsn>"
chave = dsn.split("//")[1].split("@")[0]
host = dsn.split("@")[1].split("/")[0]
projeto = dsn.rsplit("/", 1)[1]
eid = uuid.uuid4().hex
envelope = (
    json.dumps({"event_id": eid, "dsn": dsn}) + "
"
    + json.dumps({"type": "event", "content_type": "application/json"}) + "
"
    + json.dumps({"event_id": eid, "timestamp": time.time(), "platform": "python",
                  "level": "error", "environment": "teste-de-dsn",
                  "logentry": {"formatted": "teste de DSN"}})
).encode()
req = urllib.request.Request(
    f"https://{host}/api/{projeto}/envelope/", data=envelope,
    headers={"Content-Type": "application/x-sentry-envelope",
             "X-Sentry-Auth": f"Sentry sentry_version=7, sentry_key={chave}, sentry_client=teste/1.0"})
print(urllib.request.urlopen(req, timeout=30).status)
FIM
```

`200` com um `id` no corpo é entrega confirmada. `403 ProjectId` significa que a chave não pertence
ao projeto daquele DSN — recopie em *Settings → Projects → &lt;projeto&gt; → Client Keys (DSN)*.

**O `@app.exception_handler(Exception)` de `main.py` não atrapalha.** Ele registra e devolve um 500
limpo, o que poderia esconder a exceção do Sentry — mas a integração do Starlette embrulha os
handlers e reporta antes de delegar. Verificado: o `ErroDeVerificacao` chega ao `before_send` mesmo
com o handler no caminho.

**Não mexa no `before_send` sem ler o teste.** Ticker e valor são dado pessoal financeiro, e a
Política de Privacidade promete que nenhum terceiro os recebe. A limpeza é **lista de permissão**:
sai o que foi liberado, e não "tudo menos o que eu lembrei de proibir" — uma chave nova num payload
nasce redigida. Os dois testes que travam isso:

- `backend/tests/test_telemetria_nao_vaza_carteira.py`
- `mobile/test/telemetry_test.dart`

**O que a limpeza não cobre, e por quê:** o Sentry envia as linhas de código-fonte ao redor do erro
(`context_line`, `pre_context`, `post_context`). São o **código do repositório**, não dado de quem
usa — em produção elas mostram `f"Quantidade de venda ({req.quantity})…"`, o molde, e não o valor.
Ficam ligadas de propósito: sem elas a stack trace perde a maior parte do que a torna útil. A única
forma de vazarem algo é alguém escrever segredo ou dado real como literal no código, que é problema
maior que a telemetria.

Vale notar que **nada no produto chama `set_user`**, nas duas plataformas. O identificador de conta
só chegaria ao Sentry se alguém passasse a chamá-lo — e nesse caso a limpeza reduz o objeto a
`{id}`, sem nome nem e-mail.

### 2. Disponibilidade

Um monitor externo (BetterStack, Checkly ou UptimeRobot — todos com plano gratuito suficiente) em
**duas** verificações:

- `GET {SITE_URL}/api/health` — o processo está de pé;
- `GET {SITE_URL}/api/public/asset/PETR4` — e o caminho inteiro funciona: banco, cache e fonte
  externa. Só a primeira passa verde com a BRAPI fora do ar;
- `GET {SITE_URL}/privacidade` — a URL que a loja exige e que o aplicativo linka. Ela cai sem que
  ninguém perceba, porque nenhuma tela do produto depende dela.

### 3. Log que sobrevive ao restart

O log do Railway é efêmero e as métricas de `app/core/observability.py` vivem **na memória do
processo**: somem no restart, e com dois workers cada um tem as suas. Encaminhe para BetterStack
Logs, Axiom ou Grafana Loki.

### 4. Alerta em canal humano

Sem isto, os três itens acima são painel que ninguém abre. O mínimo, para um canal que apita:

- qualquer 5xx;
- disjuntor da BRAPI ou do BCB aberto (`GET /api/data-quality/source` mostra os dois);
- job periódico parado. Este é o que mais dói: um worker morto pode travar o snapshot diário por
  até 5,4h e **ninguém saberia** (KI#14).

---

## Backup: restaurado, ou é só esperança

Três documentos deste repositório usam "o Postgres já tem backup" como justificativa de decisão de
arquitetura. **Backup nunca restaurado não é backup.**

### O teste, uma vez por trimestre

1. Criar um banco vazio novo (pode ser um serviço temporário no Railway).
2. Restaurar o backup mais recente nele.
3. Apontar uma instância da API para esse banco e rodar `python -m app.release` — a migração tem
   que ser no-op, o que prova que o dump veio de um schema em dia.
4. Conferir três coisas: `GET /api/health` responde; uma conta conhecida tem as posições que
   deveria; `GET /api/portfolio/trades` devolve a mesma apuração de imposto de antes.
5. Destruir o banco temporário.
6. **Registrar a data aqui embaixo.** Um teste de restore que ninguém sabe quando rodou não conta.

| Data do restore | Quem | Tempo até responder | Observação |
|---|---|---|---|
| — | — | — | nunca executado |

### RPO e RTO propostos

Números para esta fase, a confirmar no primeiro teste — declarar é o que transforma "temos backup"
em compromisso conferível:

- **RPO (quanto de dado se aceita perder): 24 horas.** É o intervalo do backup automático do
  Postgres gerenciado. Um dado de carteira digitado à mão vale o retrabalho de um dia; se isso
  deixar de ser verdade, o número muda.
- **RTO (quanto tempo até voltar): 4 horas.** Restaurar, apontar e conferir, com uma pessoa só e
  sem automação.

---

## Quando algo quebra

| Sintoma | Onde olhar primeiro |
|---|---|
| 500 em rota específica | Sentry, agrupado pela rota — o caminho vem sem o ticker de propósito |
| Preço velho ou faltando | `GET /api/data-quality/source` — disjuntor aberto e idade do cache |
| Preços diferentes por acesso | `CACHE_BACKEND`: cache por nó com duas réplicas |
| Startup falha com `BancoAtrasado` | rode `python -m app.release` contra aquele banco |
| Startup falha com `InsecureConfigurationError` | a mensagem nomeia a variável que falta |
| Snapshot diário parado | lock de job — KI#14; o TTL é o próprio intervalo do job |
