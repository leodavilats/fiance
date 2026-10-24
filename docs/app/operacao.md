# O aplicativo — operação

Variáveis, sinais e o que falta para publicar, só do `backend/` e do `mobile/`. Serviços, deploy e
backup da plataforma: [07-OPERACAO](../07-OPERACAO.md).
Última revisão: 2026-10-21

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
| `DADOS_API_URL` | vazio | A `fiance-dados`. No Railway, pela rede privada: `http://${{fiance-dados.RAILWAY_PRIVATE_DOMAIN}}:8080` |
| `DADOS_API_CHAVE` | vazio | Chave de uma conta do plano `interno`, criada no `/console` da `fiance-dados`. Definida no painel, nunca no repositório |
| `ALLOWED_ORIGINS` | localhost | CORS |
| `ADMIN_USER_IDS` | vazio | Rotas de operador. Conta Apple entra como `apple:<sub>` |
| `RATE_LIMIT_ENABLED` | `true` | Teto de uso |
| `RATE_LIMIT_FACTOR` | `1.0` | Multiplica todos os tetos |
| `TRUSTED_PROXY_COUNT` | `0` | Quantos proxies à frente têm o `X-Forwarded-For` confiável. Zero usa o IP da conexão |
| `SUITABILITY_PERSONALIZATION_ALLOWED` | `false` | Permite leitura personalizada no nível prescritivo de afirmação |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `RELEASE` | vazio | Versão enviada ao Sentry |
| `AFFIRMATION_LEVEL` | `2` | Nível de afirmação — ver [ADR-007](../decisoes/ADR-007-nivel-de-afirmacao.md) |
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

**Qualidade de fonte:** `GET /data-quality/source` mostra o estado dos disjuntores da base de mercado e do BCB
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
2. A coleta — o painel do laboratório alerta quando a rodada do data-job falha ou a cotação fica velha
3. A carga da noite — a varredura guarda o resultado até a próxima carga da base (23h do próximo
   dia de pregão). Se o `data-job` não rodou, o backend revalida a cada 30 min e serve o mesmo
   fechamento
4. A API de dados — `/saude` da `fiance-dados`, e a chave do `DADOS_API_CHAVE` ativa no `/console`
5. Log `não há universo em cache` — a lista de tickers da base de mercado falhou e não havia universo vencido
   para servir; `servindo o universo vencido` é a degradação funcionando, não a causa

---

## Publicação nas lojas

Nada disso existe hoje. Todos são bloqueadores do item 7 de [05-FUTURO](../05-FUTURO.md).

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
