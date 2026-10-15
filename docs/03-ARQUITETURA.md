# Arquitetura

Como o sistema é montado e por que as fronteiras estão onde estão.
Estrutura e endpoints são derivados do código; a **intenção** vive aqui e nas
[decisões](decisoes/).
Última revisão: 2026-10-12

---

## Visão geral

Um backend FastAPI com o seu Postgres (`postgres-app`), um cliente Flutter. Os dados de mercado vêm
de um segundo Postgres (`postgres-mercado`), escrito só pelo `data-job/` e lido pelo backend sem
escrever. Sem microsserviços, sem fila. O painel do autor (`trend-backend/` + `trend-frontend/`) lê
a mesma base e fica fora do produto ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)).

```
┌──────────────────────────────────────────┐
│  Flutter  (mobile/)  — o único cliente   │
└───────────────────┬──────────────────────┘
                    │  HTTPS  /api/v1
┌───────────────────▼──────────────────────┐
│  FastAPI  (backend/app)                  │
│                                          │
│  api/         rotas, autenticação, teto  │
│  services/    orquestra e liga ao banco  │
│  storage/     acesso a dados por usuário │
│                                          │
│  ── matemática pura, sem banco ──        │
│  ledger/      razão, projeção, apuração  │
│  cashflow/    mês, cascata, dívida       │
│  analysis/    preço justo, score         │
│                                          │
│  collectors/  base de mercado, BCB, disj.│
└───────────────────┬─────────────────┬────┘
                    │                 │ só leitura (mercado_leitura)
        ┌───────────▼───────────┐ ┌───▼──────────────────┐
        │  postgres-app         │ │  postgres-mercado    │
        │  dados + cache        │ │  schema mercado      │
        └───────────────────────┘ └───▲──────────────────┘
                                      │ escreve (cron diário)
                                  ┌───┴──────────────────┐
                                  │  data-job/           │
                                  └──────────────────────┘
```

---

## A fronteira que sustenta o sistema

**`ledger/`, `cashflow/` e `analysis/` não conhecem banco de dados.** Recebem dados, devolvem
resultados. Quem liga isso à persistência são os `*_service.py`.

Consequências práticas:

- a matemática é testável sem infraestrutura — é o que permite a maior parte dos testes do backend rodar sem banco;
- uma regra financeira errada é um bug localizável, não um efeito de consulta;
- o cálculo não sabe quem paga, e não pode passar a saber (ver a regra de monetização abaixo).

Decisão registrada em [ADR-001](decisoes/ADR-001-matematica-pura.md).

**A regra prática:** se um módulo dessas três pastas precisar importar `storage/` ou `models/db_*`,
a solução está errada. Passe o dado por parâmetro.

---

## Camadas

| Camada | Responsabilidade | Não faz |
|---|---|---|
| `api/` | Rota, autenticação, teto de uso, validação de entrada | Regra de negócio |
| `services/` | Orquestra, resolve dependências, liga cálculo ao banco | Matemática |
| `storage/` | Acesso a dados, sempre por `user_id` | Decisão |
| `ledger/`, `cashflow/`, `analysis/` | Matemática | Tocar em banco |
| `collectors/` | Dado externo, cache, disjuntor | Julgamento |
| `entitlement/` | Cerca de plano | Existir fora de si mesmo |

---

## Multi-tenant

Todo dado é de um usuário, e o isolamento é aplicado na camada `storage/`: `portfolio_store.py`
abre a sessão filtrada, e `cash_store`, `ledger_store`, `account_store` e `event_store` filtram pelo
titular em cada consulta.

**`_session_global()` não filtra por usuário.** Existe para job cross-tenant e **nunca** deve
aparecer em caminho de request. Tabelas sem dono estão em `account_store.GLOBAL_TABLES` —
`cache_entries` é uma delas.

**Tabela nova com `user_id` entra em `account_store.USER_SCOPED_MODELS`**, senão a exportação de
conta deixa de cobri-la e o teste falha.

**"Tem carteira" é uma pergunta só:** `portfolio_store.has_holdings()`, que olha posições **e** renda
fixa. Perguntar a `list_positions` ignora quem chegou por CDB.

---

## Sessão e segurança

| Item | Valor |
|---|---|
| Login | Google (`POST /auth/google`) e Apple (`POST /auth/apple`). Não existe senha. As duas rotas são públicas por natureza: é por elas que a sessão começa. A conta Apple tem id `apple:<sub>`, para não colidir com o `sub` do Google, e entra na conta existente só quando a Apple confirma um e-mail real (`email_verified` e não relay privado) |
| Token de acesso | 1 hora |
| Refresh | 30 dias, **rotacionado e queimado no uso** |
| Revogação | Por `jti` (um dispositivo) e `session_cuts` (todos) |

**Dois refreshes simultâneos derrubam a sessão.** A renovação é compartilhada no cliente: quem levar
401 espera a que está em voo em vez de abrir a segunda.

**`APP_ENV` não tem default.** Vazio falha alto no startup e, se algo escapar, falha **fechado** —
esquecer a variável desarmava JWT, CORS e rota de operador de uma vez.

`BILLING_WEBHOOK_SECRET` e o segredo do JWT são validados no startup com o mesmo rigor.

**O token de push é da instalação, não da conta, e vive enquanto a sessão vive.** O token do FCM
identifica o aplicativo num aparelho; quem entra por último nesse aparelho é quem recebe o aviso, e
`portfolio_store.register_device_token` reatribui o token a essa conta. Reatribuir é o certo: o
contrário deixaria a conta anterior recebendo alerta de preço — que diz o que a carteira segue — num
aparelho que já não é dela. O risco real é outro, e fecha em três pontos:

- **Sair apaga o token antes de encerrar a sessão.** `signOutProvider` (`mobile/lib/core/providers.dart`)
  chama o `DELETE /notifications/register-token` enquanto a sessão ainda autentica, e só depois
  revoga e limpa. Falha nesse passo não impede a saída: o token órfão é reatribuído no próximo login
  do aparelho.
- **Sair de todos os aparelhos apaga todos os tokens da conta** (`POST /auth/logout` com
  `all_devices`, via `portfolio_store.unregister_all_device_tokens`). Sessão cortada em todo lugar
  não deixa aparelho recebendo aviso.
- **Token tem forma.** Registro e remoção (`api/notifications.py`) aceitam só o alfabeto do FCM
  (letras, dígitos, `-`, `_`, `:`), de 32 a 512 caracteres; plataforma é `android` ou `ios`. O
  token real tem por volta de 150 caracteres, e o Google não fixa o tamanho — o piso recusa lixo,
  não um formato que pode mudar.

Fica de fora a sessão que expira sem logout: sem sessão, o aplicativo não tem como pedir a remoção,
e o token segue com a conta até o próximo login no aparelho ou até o FCM o declarar inválido
(`services/notification_job.py` apaga o que o FCM recusa).

---

## API

**Versão no caminho:** `/api/v1` é canônico. `/api` responde como alias em transição e carimba
`X-API-Deprecation`.

**Campo que some é pego por contrato.** `tests/contrato_das_rotas.json` registra os campos de cada
rota `/api/v1` — os de resposta, inclusive aninhados, e os de entrada, com `!` nos obrigatórios; o
FastAPI descarta em silêncio o que o `response_model` não declara, e campo de entrada que vira
obrigatório quebra o aplicativo que ainda não atualizou. Regravar é
`python -m tests.contrato_das_rotas`, e o diff entra no mesmo commit.

⚠️ **7 rotas ainda devolvem `dict` solto e não têm contrato.** `SEM_MODELO_HOJE` é a catraca que
impede esse número de crescer. Ver [10-PROBLEMAS](10-PROBLEMAS.md).

**Listas paginam por cursor keyset**, nunca offset. Onde há agregado, ele é **da conta inteira** —
senão o total encolhe conforme a rolagem. Em proventos e renda fixa a página sai do banco com
limite, e o agregado de uma consulta própria que lê só as colunas que soma, mais uma contagem; a
marcação completa da renda fixa (vencimento, equivalências) só roda para a linha exibida. Sugestões
seguidas ainda cortam só o payload.

**Rota cara casada por prefixo tem de casar por sufixo:** `/api/opportunities` casa,
`/api/v1/opportunities` não. O teto morreria em silêncio no dia da migração para o caminho canônico.

**Escrita seguida de 4xx:** os handlers de `DomainError` vivem no `ExceptionMiddleware` do Starlette,
interno ao middleware de observabilidade — a exceção nunca sobe. Quem decide commit ou rollback é o
**status da resposta**. O que precisa sobreviver ao 4xx que provocou (contador de teto, marca de
paywall) usa `independent_session()` / `outside_request_transaction()`.

---

## Dados externos

**Duas fontes, e só duas:** a base de mercado própria (`postgres-mercado`, ações, FIIs, BDRs,
ETFs) e BCB SGS (CDI, Selic, IPCA). A base é escrita só pelo `data-job/`, a partir da B3, da CVM,
do Tesouro e do BCB ([ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md)); o backend
lê **pela `dados-api`** ([ADR-024](decisoes/ADR-024-api-de-dados.md)), com uma chave do plano
`interno`, pela rede privada do Railway (`collectors/mercado.py`): `/v1/retratos` em lotes de 50
para o retrato e as demonstrações, `/v1/ativos` para a lista, `/cotacoes` para o histórico e
`/proventos` sem o rendimento estimado. Ticker que a API não tem (404) é ausência, não falha. **A cotação é a do último fechamento**, e o `as_of`
é o fechamento daquele pregão, às 18h de Brasília — o que a tela carimba como idade.

Os índices (P/L, P/VP, ROE, margem, dívida sobre patrimônio, yield) são calculados no backend a
partir dos números brutos (`collectors/universal.snapshot_do_pacote`): lucro de 12 meses pelo
acumulado do ano mais o anual anterior menos o mesmo ponto do ano anterior; valor de mercado pelo
preço de cada classe vezes a quantidade dela; quantidade em milhares corrigida quando o valor de
mercado fica abaixo de 2% do patrimônio; unit vale as ações que contém. O Ibovespa é medido pelo
BOVA11, porque a base não tem o índice.

### A regra que não se negocia

**O sistema não inventa dado.** Fonte fora do ar produz ausência declarada, nunca estimativa
silenciosa.

Em ordem de degradação:

1. Cache válido
2. Cache **vencido**, com a idade carimbada e visível na tela
3. Ausência explícita — `None`, e a tela diz que não conseguiu ler

Constantes de `collectors/rates.py` são o **último** recurso, e o rótulo de fonte (`bcb`,
`bcb_cache_vencido`, `estimativa`) viaja até a tela.

O universo da varredura segue a mesma ordem (`core/universe.py::get_universe`): com a base
fora do ar, serve o universo vencido e loga a idade; só sem nenhum devolve lista vazia, e loga isso.
A idade fica no log porque a lista não é exibida; o que a tela carimba é a idade da varredura. O
vencido não é regravado como válido, e dura 72 h depois do vencimento (`STALE_MARGIN_SECONDS`).

**Falha de rede não vira ausência.** Confundir "não sei" com "não existe" esconde fonte caída por
meia hora.

### Proteções

| Mecanismo | O que faz | Onde |
|---|---|---|
| Faixa de plausibilidade | Campo absurdo vira `None`; preço absurdo rejeita o snapshot inteiro | `collectors/plausibility.py` |
| Disjuntor | Aberto, nem tenta; quem chama cai no cache vencido | `collectors/circuit.py` |
| Leitura em lote | 50 tickers por consulta à base | `collectors/universal.prefetch` |
| Marcador de inexistente | 6h — tem de durar mais que o ciclo de varredura | idem |
| Somente leitura | Toda conexão à base de mercado faz `SET ROLE mercado_leitura` e `SET default_transaction_read_only = on` | `collectors/mercado.engine` |
| Portão de pregão | 10h–18h30 em dia com pregão na B3; fora disso a varredura do universo serve a última varredura em cache | `core/pregao.py` |

O dado chega em lote: o `data-job` carrega a base uma vez por dia útil, às 23h de Brasília (cron
`0 2 * * 2-6`, UTC). Reler a base fora do pregão não traz nada novo, e o portão evita a varredura
sem motivo. Ele **não** se aplica a: busca de um ativo pedido por uma pessoa às 22h, ou num feriado;
servir cache no fim de semana. A janela vai da abertura (`ABERTURA`, 10h) ao fechamento
(`FECHAMENTO`, 18h30).

**O calendário é calculado, sem rede e sem banco** (`core/pregao.py::dias_sem_pregao`):

- feriados nacionais fixos: 1/1, 21/4, 1/5, 7/9, 12/10, 2/11, 15/11, 25/12, e 20/11 a partir de
  2024 (Consciência Negra, nacional pela Lei 14.759/2023);
- móveis, pela Páscoa (`pascoa`): segunda e terça de Carnaval, Sexta-feira Santa, Corpus Christi;
- os dias sem pregão da própria B3: 24/12 e 31/12.

Feriado municipal ou estadual de São Paulo (25/1, 9/7) **não** fecha a janela: a B3 funciona neles.
Na Quarta-feira de Cinzas o pregão começa às 13h, e a janela abre às 13h (`abertura`). Feriado que
cai no fim de semana não se transfere. O instante com fuso é lido em horário de Brasília. Um
fechamento extraordinário que a B3 anuncie fora dessas regras não entra sozinho: é linha nova no
cálculo.

### Cache

Onde o cache mora é trocável (`core/cache_backends.py`): banco da aplicação quando `DATABASE_URL` é
Postgres, arquivo local quando o banco é local, Redis quando `REDIS_URL` existir. `CACHE_BACKEND`
força a escolha e **nome errado falha alto**.

Não é desempenho, é correção: com dois nós e cache por nó, a mesma pessoa vê preços diferentes
conforme o balanceador. O vencimento vai **dentro** do valor mesmo no Redis, porque `get_with_age`
precisa do dado vencido para o disjuntor degradar. Pelo mesmo motivo, `cache.get` devolve `None` para
o vencido **sem apagá-lo**: quem apaga é a manutenção (`core/jobs.py`, `cache.purge_expired`), e só o
que venceu há mais de 72 h (`cache_backends.py::STALE_MARGIN_SECONDS`, a mesma janela que o Redis
guarda e a tolerância da varredura). Com 6 h, a manutenção apagava o vencido antes de a degradação
precisar dele, e num fim de semana a varredura voltava à rede a cada ciclo.

**Redis fora do ar vira falta de cache, e rápido** (`RedisBackend`). A conexão tem 1 s para abrir e
cada leitura do socket 1 s para responder; timeout e erro de conexão são tentados mais uma vez, com
a conexão refeita, e conexão ociosa há mais de 30 s recebe um ping antes do uso. Ler, gravar e apagar
capturam o erro, logam e seguem: a leitura devolve `None` e quem chamou vai à fonte. No pior caso a
operação espera uns 2 s, e não o tempo do TCP. A limpeza pedida pelo operador (`delete_pattern`,
`clear_all`) falha alto, porque quem pediu precisa saber que o cache não foi limpo.

Sem servidor nenhum, `tests/test_cache_backends.py` cobre porta recusada e servidor que aceita a
conexão e não responde. Com o Redis do CI (`REDIS_TEST_URL`), cobre o pool derrubado e a conexão
que o servidor matou, as duas refeitas na operação seguinte. Failover (Sentinel, réplica promovida)
não é coberto.

---

## Monetização, isolada por arquitetura

**A cerca de plano mora só em `entitlement/`**, e entra desligada.

Dois testes de arquitetura travam isso:

- nenhuma condicional de plano fora do módulo;
- `analysis/`, `cashflow/`, `collectors/` e `ledger/` **não importam nada dele**.

Se o cálculo souber quem paga, a independência do algoritmo vira promessa. Ativo da própria carteira
nunca consome cota; a rota pública também não.

O titular de um evento de cobrança sai da sessão de checkout, **nunca do corpo** do webhook: a rota é
pública, e a assinatura protege a integridade da mensagem, não a autoridade sobre quem ela nomeia.

---

## Persistência e migração

SQLAlchemy, Alembic, Postgres em produção e SQLite local.

**Migração é *release command*, não startup.** `python -m app.release` aplica; o startup só chama
`conferir_revisao()` e **falha alto** se o banco estiver atrasado. Migrar no `lifespan` com duas
réplicas são duas migrações concorrentes, e o Alembic não coordena isso.

SQLite local continua se criando sozinho, porque é de um processo só.

⚠️ **Coluna nova exige migração Alembic**, senão `test_database_migration.py` falha.

**Colunas monetárias são `Money` (`ExactNumeric`)**: inteiro escalado por 10^8 no SQLite, `Numeric`
no Postgres. O `NUMERIC` do SQLite é `real` por baixo, e somar imposto em float erra o número que vai
para a declaração.

---

## Privacidade como código

O `before_send` de cada plataforma (`core/telemetry.py`, `core/telemetry.dart`) é **lista de
permissão**: ticker no caminho vira `{id}`, valor em reais e número citado em erro são redigidos,
corpo de request e `extra` não saem, do usuário sai só o identificador, variável local de frame é
descartada. **Uma chave nova num payload nasce redigida.**

Evento de produto tem dicionário fechado (`core/events.py`). Nome fora dele, ou propriedade com
ticker ou valor, devolve 422. O app envia pelo `ProductEvents` (`mobile/lib/core/product_events.dart`),
sem ticker nem valor, e engole a falha: telemetria nunca derruba tela.
`tests/test_eventos_do_app_estao_no_catalogo.py` varre o app e recusa nome fora do catálogo, que de
outro modo sumiria em silêncio.

Marcos de ativação são gravados pelo **servidor**, não pelo cliente.

Exportação, importação e exclusão de conta nunca ficam atrás de plano.

---

## Páginas públicas

Três páginas de HTML ficam **fora de `/api`**: `/termos`, `/privacidade`, `/aviso-cvm`. Robô de loja
não faz login, e a ficha de segurança de dados pede uma URL de privacidade que abra sozinha.

São páginas de documento: sem JavaScript, sem asset externo, sem paleta — a cor vem do agente do
usuário. A lista é fechada, e crescê-la é decisão registrada.

O Aviso CVM lê `affirmation.current()` no servidor; uma segunda cópia da frase desatualizaria
justamente onde a pessoa a lê.
