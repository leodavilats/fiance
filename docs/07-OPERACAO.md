# Operação

Subir, observar e reverter os serviços da plataforma. O que é de uma parte só — variáveis, contas,
publicação nas lojas — está na pasta dela.
Última revisão: 2026-10-21

---

## Ambientes

| Ambiente | Onde | Banco |
|---|---|---|
| Desenvolvimento | Máquina local | SQLite em `.cache/fiance.db` |
| Produção | Railway, projeto `fiance`, ambiente `production` | Dois Postgres: `postgres-app` (aplicativo) e `postgres-mercado` (dados de mercado) |

Em desenvolvimento, **sem `DADOS_API_URL` e `DADOS_API_CHAVE` não há ativo**: o cliente da API
falha com `SemBaseDeMercado` (`collectors/mercado.py`). Aponte para uma `fiance-dados` local ou a de
produção, com uma chave criada no `/console`.

Não há staging. O ambiente existiu até 2026-10-09 e foi removido: acompanhava a mesma branch que
produção (`main`), então era uma segunda cópia do mesmo commit, e não um passo antes do deploy.

URL de produção: `https://fiance.up.railway.app`

### Serviços

No ambiente `production`:

| Serviço | O quê | Volume |
|---|---|---|
| `backend` | API do app, de `/backend`; reconstrói só com mudança em `/backend/**` | — |
| `postgres-app` | Banco do aplicativo | 500 MB |
| `data-job` | Coleta de mercado, de `/data-job` ([base/](base/README.md)). Cron `0 2 * * 2-6` (UTC, 23h de Brasília), roda `python -m datajob diario` e termina. Migrações Alembic próprias (`data-job/migrations`), aplicadas pelo Pre-Deploy Command (`python -m alembic upgrade head`). Cada rodada fica em `mercado.rodada` | `data-job-bruto`, 5 GB, em `/bruto` |
| `postgres-mercado` | Schema `mercado`, só do data-job | 5 GB |
| `fiance-dados` | A API de dados para terceiros e para o próprio app, de `/fiance-dados` ([dados/](dados/README.md)). Entra como o papel `dados_api` ([dados/](dados/README.md#papel-no-banco)) e só lê `mercado` como `mercado_leitura`; contas, chaves, planos e uso no schema `acesso`, com migrações próprias (`fiance-dados/migrations`) pelo Pre-Deploy Command (`python -m alembic upgrade head`). Em `https://fiance-dados.up.railway.app`. Start: `uvicorn dadosapi.app:criar --factory --host 0.0.0.0 --port $PORT`; saúde em `/saude`; documentação pública em `/docs`, portal em `/` e console em `/console` | — |
| `fiance-trend` | Painel de uso próprio: API do `fiance-trend/backend` e front do `fiance-trend/frontend`, em `https://fiance-trend.up.railway.app`, com senha. Imagem de `fiance-trend/Dockerfile`, com a raiz do repositório como contexto; reconstrói com mudança em `/fiance-trend/**` e `/docs/**`, porque o painel serve documentos daqui. Lê o `postgres-mercado` como `mercado_leitura` | — |

O `fiance-trend` pede `TREND_USUARIO` e `TREND_SENHA` e falha ao subir sem elas. A senha é definida no painel do
Railway, e não passa pelo repositório.

**Para rodar o data-job fora da agenda:** tirar o cron do serviço, fazer uma implantação **nova**
(`railway up --service data-job`) e depois devolver o cron com outra implantação nova. O *redeploy*
do Railway reaproveita a configuração anterior, cron incluído, e o container fica esperando o
horário sem rodar.

Build, start e Pre-Deploy Command de `data-job` e `fiance-dados` vivem só no painel do Railway, sem
arquivo no repositório: o que está nesta tabela é a única cópia escrita.

As referências de `DATABASE_URL` apontam para o **id** do serviço de banco, e não para o nome:
renomear um serviço não quebra quem o referencia.

**O `postgres-mercado` tem `max_wal_size = 256MB`**, por `ALTER SYSTEM` em 2026-10-21: vive no
`postgresql.auto.conf` do volume, e não no repositório. Com o padrão de 1 GB, o WAL ocupava quase 1 GB
do volume de 5 GB sem servir a nada — não há réplica nem arquivamento. O custo é a carga noturna
fazer mais checkpoints. Banco recriado do zero volta ao padrão. Medido nesse dia: 2,5 GB de dados,
quase tudo em `demonstracao_linha`, `cotacao` e nas duas séries ajustadas.

**O Postgres não tem consulta pelo painel, e `railway ssh` não passa em toda rede.** Para chegar ao
banco, abra um proxy TCP no serviço, conecte com as variáveis `PG*` que `railway run --service
postgres-mercado` injeta, e remova o proxy logo depois — enquanto ele existe, o banco aceita conexão
da internet.

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
| Auto-deploy do Railway | push em `main`, no ambiente `production` | Sim, desde 2026-09-19 |
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

Cada parte documenta as suas; a fonte de verdade é o código que as lê.

| Serviço | Onde estão | Código |
|---|---|---|
| `backend` | [app/operacao](app/operacao.md#variáveis-de-ambiente) | `backend/app/core/config.py` |
| `data-job` | [base/](base/README.md#produção) | `data-job/datajob/config.py` |
| `fiance-dados` | [dados/](dados/README.md#variáveis) | `fiance-dados/dadosapi/config.py` |
| `fiance-trend` | [pesquisa/](pesquisa/README.md#variáveis) | `fiance-trend/backend/api/config.py` |

Segredo (`JWT_SECRET`, `DADOS_API_CHAVE`, `DADOS_API_ADMIN_TOKEN`, `TREND_SENHA`) é definido no
painel do Railway, nunca no repositório — e conferido pelo nome antes do deploy.

---

## Backup e recuperação

**Nenhum banco tem backup automático** — conferido em 2026-10-12. O agendamento de backup do Railway
e o PITR são do plano Pro, e a conta não é Pro. **Risco aceito pelo autor em 2026-10-12**, enquanto o
uso é pessoal: perder o volume do `postgres-app` perde carteiras e contas. O `postgres-mercado` se
reconstrói do bruto guardado no volume `/bruto` do data-job (`python -m datajob reprocessar`), menos
o que as fontes já não publicam. Rever antes de abrir qualquer produto ao público.

Existe uma cópia lógica própria do `postgres-app`, portátil entre Postgres e SQLite, cuja
restauração é testada no CI
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

A exportação roda à mão, e não há agendamento nem destino cifrado definido: é o mesmo risco aceito
no topo desta seção, a rever antes de abrir o produto ao público.

Para reverter um deploy, use o rollback do Railway. Migração aplicada **não** é revertida por
rollback de aplicação — migração que precise voltar exige `downgrade` escrito e testado antes.

---

## Rotina de operação

Não há rotina automatizada de monitoramento, alerta ou verificação de saúde além do que o Railway
oferece, com uma exceção: o painel `fiance-trend` alerta falha de etapa na última rodada do data-job
(`mercado.rodada`), rodada parada há mais de 80 h ou começada e não terminada, e cotação com mais de
2 dias úteis sem pregão novo (`fiance-trend/backend/api/alertas.py`). Com um usuário isso é adequado; com
usuários reais, não é.
