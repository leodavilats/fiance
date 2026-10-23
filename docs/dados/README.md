# API de dados — `fiance-dados`

**Fonte de verdade** para o que a API de dados oferece, a quem, por quanto e como se opera. O porquê
está na [ADR-024](../decisoes/ADR-024-api-de-dados.md) e na
[ADR-025](../decisoes/ADR-025-cobranca-da-api-de-dados.md); as rotas e os campos, no OpenAPI do
próprio serviço (`/docs`).
Última revisão: 2026-10-23

---

## O produto

A base de mercado que o app lê ([base/](../base/README.md)), oferecida como serviço, com contas,
chaves e planos.

| | |
|---|---|
| O que entrega | Cotação desde 2005 com as empresas que saíram da bolsa, série ajustada com os eventos conferidos pelo preço, proventos, demonstrações como se sabia em cada data, informe mensal de FII, séries do BCB e Tesouro Direto |
| Para quem | Quem testa estratégia ou analisa empresa com dado da B3 e da CVM: investidor quantitativo, analista, desenvolvedor |
| Primeiro cliente | O próprio app, com uma chave do plano `interno` (`backend/app/collectors/mercado.py`) |
| Acesso hoje | Por convite, sem cobrança |

**A hipótese:** quem testa estratégia paga por não ter de montar a base — principalmente pelo que é
difícil de achar organizado: o histórico com quem saiu da bolsa, o ajuste por evento e o balanço sem
o futuro vazando no passado.

**O risco:** um serviço público mantido por uma pessoa. Disponibilidade e correção do dado viram
compromisso, e a base depende de endpoints da B3 sem contrato
([04-PROBLEMAS](../04-PROBLEMAS.md#base-de-mercado)).

## Modelo de negócio

Assinatura mensal ou anual (o anual custa dez meses), **sem plano gratuito**, em dois planos
públicos. Os preços são hipótese.

| Plano | Por minuto | Por dia | Histórico | Chaves | Recursos além do básico | Por mês | Na página |
|---|---|---|---|---|---|---|---|
| `interno` | 600 | 1.000.000 | inteiro | 10 | todos | — | não |
| `convidado` | 60 | 20.000 | inteiro | 3 | todos | — | não |
| `essencial` | 30 | 5.000 | 730 dias | 2 | nenhum | R$ 49 | sim |
| `pro` | 60 | 30.000 | inteiro | 5 | série ajustada, demonstração por data (`sabido_em`), informe de FII | R$ 149 | sim |

**O básico** é tudo o que não é recurso: ativos, retratos, cotação, proventos, eventos, empresas,
demonstrações sem `sabido_em`, indicadores e Tesouro — no Essencial, cortado em 730 dias.

Os planos são dados, não código: tabela `acesso.plano`, semeada pelas migrações
(`fiance-dados/migrations/`). Os recursos são `serie`, `ponto_no_tempo` e `informes`
(`dadosapi/acesso.py`), e um teste confere que cada um tem rota que o exige.

**A base não é entregue em arquivo** ([ADR-030](../decisoes/ADR-030-sem-exportacao-dois-planos.md)):
o acesso é pela API, consulta a consulta. Volume acima do Pro é contrato, por um plano não listado
criado quando houver o cliente.

**Condição para cobrar de terceiros:** a resposta da B3 sobre a licença do dado, a leitura da ODbL
da CVM, CNPJ e termos de uso. Até lá a cobrança fica desligada.

---

## O que o serviço expõe

| Onde | O quê |
|---|---|
| `/v1/...` | A API, por chave. Ativos, retratos em lote (até 50), cotações, série ajustada, proventos, eventos, informes, empresas e demonstrações, indicadores do BCB, Tesouro; e `/v1/conta` para a própria conta e as chaves |
| `/v1`, `/v1/planos`, `/v1/vitrine` | Sem chave: o índice, os planos públicos e o exemplo do portal |
| `/` | Portal público, em telas por âncora (`#inicio`, `#exemplo`, `#dados`, `#uso`, `#planos`, `#conta`): o que o serviço oferece, a documentação e "minha conta" para quem tem chave, com a assinatura quando a cobrança abre |
| `/docs` | OpenAPI público. As rotas `/admin` ficam fora dele |
| `/console` | O controle do autor, em telas (`#visao`, `#contas`, `#uso`, `#nova`): contas, uso por dia e por conta, emitir e revogar chave, desativar. Pede o token de administração na tela e o guarda só na aba |
| `/admin/...` | Administração, por `X-Admin-Token` |
| `/cobranca/asaas` | Webhook do Asaas |
| `/saude` | Saúde |

Paginação por cursor: `{"dados": ..., "proximo": ...}`, 500 itens por padrão, até 5.000.

## Regras

**Só lê `mercado`, só escreve `acesso`.** A conexão de leitura assume `mercado_leitura` e transação
só de leitura a cada conexão aberta (`dadosapi/banco.py`).

**A chave aparece uma vez**, na criação; a base guarda só o hash. Vale em `Authorization: Bearer` ou
em `X-API-Key`. Toda resposta autenticada traz `X-Limite-Dia` e `X-Restante-Dia`.

**Respostas de recusa:**

| Status | Quando |
|---|---|
| 401 | Chave ausente, desconhecida ou revogada; conta desativada |
| 402 | Plano pago sem `pago_ate` em dia, mais três dias de tolerância |
| 403 | Rota de um recurso que o plano não tem |
| 429 | Limite por minuto (com `Retry-After`) ou por dia |

**Os limites valem para a conta, não para a chave.** O uso é contado por chave e somado na conta,
inclusive o das chaves revogadas: trocar de chave não renova o dia. Uma conta emite no máximo 10
chaves novas em 24 horas pelo `/v1/conta/chaves`.

**O limite por minuto fica na memória do processo:** com mais de uma réplica, cada uma conta a sua.
O por dia fica no banco, no dia de Brasília, e **a requisição recusada pelo limite diário também
conta**.

**Sem o recurso `ponto_no_tempo`, o `/v1/retratos` traz só a última versão** de cada demonstração:
todas as versões com a data de entrega são o balanço como se sabia na data.

**Dez tentativas erradas do mesmo IP bloqueiam `/admin` por 15 minutos.** O IP é o que o proxy
acrescentou à direita do `X-Forwarded-For` (`PROXIES_CONFIAVEIS`); o da esquerda, o cliente escreve.

A `observacao` da conta é da administração: o `/v1/conta` não a devolve.

---

## Contas

Conta nasce por convite, pela administração — no `/console` ou pela rota —, e já sai com a primeira
chave. Quem tem conta gerencia as próprias chaves em `/v1/conta`.

```bash
# criar conta (devolve a primeira chave) — planos: interno, convidado, essencial, pro, quant
curl -X POST https://<dominio>/admin/contas -H "X-Admin-Token: $TOKEN" \
  -H "Content-Type: application/json" -d '{"email": "a@b.com", "nome": "Fulano", "plano": "convidado"}'
curl https://<dominio>/admin/contas -H "X-Admin-Token: $TOKEN"                  # contas e uso de hoje
curl -X PATCH https://<dominio>/admin/contas/1 -H "X-Admin-Token: $TOKEN" \
  -H "Content-Type: application/json" -d '{"ativa": false}'                    # desativar
curl -X PATCH https://<dominio>/admin/contas/1 -H "X-Admin-Token: $TOKEN" \
  -H "Content-Type: application/json" -d '{"pago_ate": "2026-12-31"}'         # pagamento por fora
curl -X DELETE https://<dominio>/admin/contas/1/chaves/fd_abcd1234 -H "X-Admin-Token: $TOKEN"  # revogar
curl "https://<dominio>/admin/uso?dias=90&conta_id=1" -H "X-Admin-Token: $TOKEN"       # uso de uma conta
```

O `PATCH` aceita `plano`, `ativa`, `pago_ate`, `nome` e `observacao`; campo ausente fica como está,
e `null` enviado de propósito limpa `pago_ate` e `observacao`. A lista traz a `situacao` — `ativa`,
`a_vencer` (a 7 dias do vencimento), `em_tolerancia`, `sem_pagamento` (a que responde 402),
`desativada` —, calculada pela mesma regra que autentica.

## Cobrança

Pelo Asaas (`dadosapi/cobranca.py`), **implementada e desligada** (`COBRANCA_ATIVA`). Desligada,
`POST /v1/conta/assinatura` e o webhook respondem 503.

Ligada: a página assina Essencial ou Pro, o serviço cria cliente e
assinatura no Asaas e devolve o link de pagamento. O Asaas avisa em `POST /cobranca/asaas`, com o
token no cabeçalho `asaas-access-token`; cada evento entra uma vez, o pagamento é **reconsultado**
antes de liberar, e o titular sai da assinatura gravada aqui, nunca do corpo do webhook. O pagamento
confirmado leva `pago_ate` ao fim do ciclo. Evento gravado sem `resultado` caiu antes de aplicar, e
a reentrega do Asaas o aplica de novo. Uma conta abre no máximo três assinaturas por dia.

## Variáveis

| Variável | Para quê |
|---|---|
| `DATABASE_URL` | `${{postgres-mercado.DATABASE_URL}}`. Lê `mercado` como `mercado_leitura` e escreve só no schema `acesso` |
| `DADOS_API_ADMIN_TOKEN` | Token das rotas `/admin`, 32 caracteres ou mais. **Falha ao subir sem ele.** Definido no painel do Railway, nunca no repositório |
| `CONTATO_EMAIL` | Opcional. Com ele, o portal mostra "Pedir um convite" |
| `PROXIES_CONFIAVEIS` | `1` por padrão: o proxy do Railway. Quantos endereços, da direita do `X-Forwarded-For`, foram escritos por proxy; `0` usa o IP da conexão |
| `COBRANCA_ATIVA` | `false` por padrão. `true` abre a assinatura pela página e o webhook |
| `ASAAS_API_KEY` | Obrigatória com a cobrança ativa |
| `ASAAS_WEBHOOK_TOKEN` | 32 caracteres ou mais. Obrigatória com a cobrança ativa |
| `ASAAS_URL` | `https://api.asaas.com/v3`; o sandbox é `https://api-sandbox.asaas.com/v3` |

Serviço, migrações e deploy em [07-OPERACAO](../07-OPERACAO.md#serviços).
