# Operação

Subir, observar, reverter — e o que falta para publicar nas lojas.
Última revisão: 2026-09-13

---

## Ambientes

| Ambiente | Onde | Banco |
|---|---|---|
| Desenvolvimento | Máquina local | SQLite em `.cache/fiance.db` |
| **Staging** | Railway, projeto `fiance`, ambiente `staging` | Postgres próprio, volume de 5 GB |
| Produção | Railway, ambiente `production` | Postgres gerenciado |

URL de produção: `https://fiance.up.railway.app`

⚠️ **Staging acompanha a mesma branch que produção (`main`)**, então ele não é um passo *antes* do
deploy: é uma segunda cópia do mesmo commit, e os dois sobem juntos. Para virar staging de verdade,
precisaria acompanhar outra branch.

---

## Deploy

**A migração é *release command*, não startup.**

```bash
python -m app.release
```

⚠️ **No Railway, quem executa isso é o campo Pre-Deploy Command do serviço**, já apontado para
`python -m app.release`. O Railway **não** roda a linha `release:` do Procfile — ela existe para
plataformas que seguem a convenção do Heroku. Trocar uma sem a outra faz a migração parar de rodar em
silêncio, e o sintoma aparece no deploy seguinte, com o startup falhando em `BancoAtrasado`.

O processo web:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers ${WEB_CONCURRENCY:-2}
```

Dois workers são seguros porque o cache mora no banco da aplicação e os jobs de background são
protegidos por lock no banco.

### Dois caminhos sobem código, e os dois esperam o CI

| Caminho | Gatilho | Espera o CI? |
|---|---|---|
| Auto-deploy do Railway | push em `main`, nos **dois** ambientes | Sim, desde 2026-09-19 |
| [deploy.yml](../.github/workflows/deploy.yml) | manual, com confirmação escrita para produção | Sim, e recusa commit com verificação falhando |

**A espera do CI é o botão `Wait for CI`** (Service → Settings → Source), e ele vive no
`DeploymentTrigger`: nenhuma rota da API pública, comando da CLI ou agente do Railway alcança esse
campo — o agente chega a relatar sucesso sem ter mudado nada. Confira sempre por
`source.checkSuites` na descrição do serviço, nunca pela confirmação de quem mexeu.

⚠️ Com a espera ligada, **commit sem verificação nenhuma não sobe**: o Railway fica aguardando um
check suite que nunca chega. Se um push precisar ir ao ar com o CI fora do ar, o caminho é promover
pelo `deploy.yml` ou disparar o deploy à mão no painel.

O caminho manual **nunca rodou**: ele exige `RAILWAY_TOKEN` nos segredos e `RAILWAY_SERVICE` e
`SITE_URL` nas variáveis de cada ambiente do GitHub. Sem isso ele para com mensagem, de propósito.

---

## Variáveis de ambiente

### Falham alto se ausentes ou erradas

| Variável | Comportamento |
|---|---|
| `APP_ENV` | **Sem default.** Vazio falha no startup; se algo escapar, falha **fechado** (não é development) |
| `JWT_SECRET` | Valor default (`change-me`) é recusado fora de desenvolvimento |
| `BILLING_WEBHOOK_SECRET` | Mesmo rigor do JWT |
| `CACHE_BACKEND` | Nome inválido falha alto — cair em silêncio para cache por nó é defeito que só aparece semanas depois |
| `REDIS_URL` | Definida sem o pacote instalado, falha alto |
| `SENTRY_DSN` | Definida sem o pacote instalado, falha alto |
| `ENTITLEMENTS_ENABLED=true` sem `ENTITLEMENTS_ENABLED_AT` | Falha alto |

### Operacionais

| Variável | Default | Para quê |
|---|---|---|
| `DATABASE_URL` | SQLite local | Postgres em produção |
| `GOOGLE_CLIENT_ID` | vazio | Login |
| `APPLE_CLIENT_ID` | vazio | Login com Apple: bundle id e Services ID aceitos como audience, separados por vírgula. Vazio, a rota recusa com 500 |
| `BRAPI_TOKEN` | vazio | Fonte de mercado |
| `BRAPI_HISTORY_RANGE` | `3mo` | Janela de histórico |
| `ALLOWED_ORIGINS` | localhost | CORS |
| `ADMIN_USER_IDS` | vazio | Rotas de operador |
| `RATE_LIMIT_ENABLED` | `true` | Teto de uso |
| `AFFIRMATION_LEVEL` | `2` | Nível de afirmação — ver [ADR-007](decisoes/ADR-007-nivel-de-afirmacao.md) |
| `ENTITLEMENTS_ENABLED` | `false` | Cerca de plano |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | vazio | Push |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.0` | Amostragem |
| `WEB_CONCURRENCY` | `2` | Workers |

**`ENTITLEMENTS_ENABLED_AT` é a âncora do relógio de trial.** `start_trial` é chamado na primeira
posição salva **sem consultar a flag**, então toda conta com carteira carrega um `trial_ends_at` no
passado. O relógio conta do **mais tarde** entre qualificar e a cerca subir. Sem essa variável, virar
a flag derrubaria a base inteira para Free num instante, sem volta pelo código.

---

## Observabilidade

**Sentry** (`SENTRY_DSN`), com `before_send` como **lista de permissão** nas duas plataformas.
Telemetria não leva carteira: ticker no caminho vira `{id}`, valor em reais e número citado em erro
são redigidos, corpo de request e `extra` não saem. Duas suítes travam isso — é a Política de
Privacidade escrita como código.

**Qualidade de fonte:** `GET /data-quality/source` mostra o estado dos disjuntores da BRAPI e do BCB
sem varrer o universo.

**Eventos de produto:** dicionário fechado em `core/events.py`. Nome fora dele, ou propriedade com
ticker ou valor, devolve 422.

---

## Quando uma fonte cai

O sistema degrada em ordem e **nunca inventa número**:

1. Cache válido
2. Cache vencido, com a idade carimbada e visível na tela
3. Ausência declarada — a tela diz que não conseguiu ler

O disjuntor abre depois de falhas repetidas e para de tentar. O rótulo de fonte (`bcb`,
`bcb_cache_vencido`, `estimativa`) viaja até a interface, inclusive em `BenchmarkResponse.cdi_source`.

**O que verificar quando o Descobrir esvaziar:**

1. `GET /data-quality/source` — disjuntor aberto?
2. Cota da BRAPI — o limite é 3.000 requisições/dia
3. Horário — fora de 10h–18h30 em dia com pregão na B3, a varredura do universo não vai à rede
   por desenho. Feriado nacional, Carnaval e 24 e 31/12 contam como fechados; na Quarta-feira de
   Cinzas a janela abre às 13h
4. Log `não há universo em cache` — a lista de tickers da BRAPI falhou e não havia universo vencido
   para servir; `servindo o universo vencido` é a degradação funcionando, não a causa

---

## Backup e recuperação

O Postgres do Railway é gerenciado, e o provedor tem o próprio backup. Além dele existe uma cópia
lógica própria, portátil entre Postgres e SQLite, cuja restauração é testada no CI
(`backend/app/backup.py`, `backend/tests/test_backup_e_restauracao.py`):

```bash
cd backend
python -m app.backup exportar copia.json            # todas as tabelas, menos cache e trava de job
python -m app.backup restaurar copia.json           # só em banco vazio e na mesma revisão
python -m app.backup reaplicar-exclusoes nova.json  # lápides de conta de uma cópia mais nova
```

- **Dinheiro volta exato:** `Decimal` passa por texto na cópia.
- **A restauração recusa** banco com dados e revisão de esquema diferente. Para restaurar, crie o
  banco, rode `python -m app.release` na mesma versão do código que gerou a cópia, e só então
  restaure.
- **Exclusão de conta vence a cópia.** Restaurar uma cópia anterior a uma exclusão traria de volta
  dados que a pessoa pediu para apagar. Depois de restaurar, exporte o banco danificado se ele ainda
  for legível e rode `reaplicar-exclusoes` com essa exportação.
- **A cópia é dado pessoal financeiro.** Guarde cifrada, fora do git e fora de artefato de CI, e por
  no máximo **30 dias** (`account_store.DELETION_SLA_DAYS`): é o prazo que a política de exclusão
  promete para backups. Cópia mais velha que isso descumpre a política.

**Falta decisão de operação:** agendar a exportação (um serviço de cron no Railway, por exemplo) e
escolher o destino cifrado. As duas coisas dependem da conta do Railway e de onde guardar, e não do
código. Até lá, a exportação roda à mão.

Para reverter um deploy, use o rollback do Railway. Migração aplicada **não** é revertida por
rollback de aplicação — migração que precise voltar exige `downgrade` escrito e testado antes.

---

## Publicação nas lojas — pré-requisitos

Nada disso existe hoje. Todos são bloqueadores de `[09-FUTURO](09-FUTURO.md)`, item 7.

| Pré-requisito | Estado | Observação |
|---|---|---|
| Conta Google Play | ❌ | Taxa única |
| Conta Apple Developer | ❌ | Anuidade |
| Mac para build e publicação iOS | ❌ | Não há alternativa oficial |
| **O app rodar em iOS ao menos uma vez** | ❌ | Nunca executado, nem em simulador |
| **Sign in with Apple** | ⚠️ | Backend pronto e testado (`POST /auth/apple`, verificação pelas chaves públicas da Apple). Falta o botão no app, que exige conta Apple Developer (Services ID), um Mac e o pacote `sign_in_with_apple` |
| Exclusão de conta dentro do app | ✅ | `/voce/conta` → **Excluir esta conta**, com a exportação oferecida ao lado |
| URL de privacidade pública | ✅ | `/privacidade`, sem login |
| URL de termos pública | ✅ | `/termos` |
| Ficha de segurança de dados | ❌ | A escrever, a partir da lista de permissão da telemetria |

**Sign in with Apple** é um segundo provedor de identidade, e a parte do servidor já existe: o token
é verificado pelas chaves públicas da Apple, a conta ganha id próprio, e o e-mail oculto (relay) nunca
liga contas. O que falta é o cliente, e ele depende de conta Apple Developer e de um Mac para ser
construído e testado.

---

## Rotina de operação

Não há rotina automatizada de monitoramento, alerta ou verificação de saúde além do que o Railway
oferece. Com um usuário isso é adequado; com usuários reais, não é.
