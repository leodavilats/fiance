# API de dados — `fiance-dados`

**Fonte de verdade** para o que a API de dados oferece, a quem, por quanto e como se opera. O porquê
está na [ADR-024](../decisoes/ADR-024-api-de-dados.md), na
[ADR-025](../decisoes/ADR-025-cobranca-da-api-de-dados.md) e na
[ADR-034](../decisoes/ADR-034-cobranca-ligada-e-conferida.md); as rotas e os campos, no OpenAPI do
próprio serviço (`/docs`).
Última revisão: 2026-10-24

---

## O produto

A base de mercado que o app lê ([base/](../base/README.md)), oferecida como serviço, com contas,
chaves e planos.

| | |
|---|---|
| O que entrega | Cotação desde 2005 com as empresas que saíram da bolsa, série ajustada com os eventos conferidos pelo preço, proventos, demonstrações como se sabia em cada data, informe mensal de FII, séries do BCB e Tesouro Direto |
| Para quem | Quem testa estratégia ou analisa empresa com dado da B3 e da CVM: investidor quantitativo, analista, desenvolvedor |
| Primeiro cliente | O próprio app, com uma chave do plano `interno` (`backend/app/collectors/mercado.py`) |
| Acesso hoje | Por convite, sem cobrança. A cobrança está ligada, e só o autor paga por ela ([ADR-034](../decisoes/ADR-034-cobranca-ligada-e-conferida.md)) |

**A hipótese:** quem testa estratégia paga por não ter de montar a base — principalmente pelo que é
difícil de achar organizado: o histórico com quem saiu da bolsa, o ajuste por evento e o balanço sem
o futuro vazando no passado.

**O risco:** um serviço público mantido por uma pessoa. Disponibilidade e correção do dado viram
compromisso, e a base depende de endpoints da B3 sem contrato
([04-PROBLEMAS](../04-PROBLEMAS.md#base-de-mercado)).

## Modelo de negócio

Assinatura mensal ou anual (o anual custa dez meses), **sem plano gratuito**, em dois planos
públicos. O anual se paga à vista, com renovação automática, ou em até 12x no cartão, sem juros e
sem renovação automática ([ADR-035](../decisoes/ADR-035-anual-parcelado-no-cartao.md)). Os preços
são hipótese.

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
da CVM, CNPJ e termos de uso. Até lá a cobrança fica ligada só para o autor: a assinatura está no
portal, e ninguém é levado até ela.

---

## O que o serviço expõe

| Onde | O quê |
|---|---|
| `/v1/...` | A API, por chave. Ativos, retratos em lote (até 50), cotações, série ajustada, proventos, eventos, informes, empresas e demonstrações, indicadores do BCB, Tesouro; e `/v1/conta` para a própria conta e as chaves |
| `/v1`, `/v1/planos`, `/v1/vitrine` | Sem chave: o índice, os planos públicos e o exemplo do portal |
| `/` | Portal público, em telas por âncora (`#inicio`, `#exemplo`, `#dados`, `#uso`, `#planos`, `#assinar`, `#conta`): o que o serviço oferece, a documentação, a assinatura de quem chega e "minha conta" para quem tem chave, com a situação do pagamento |
| `/docs` | OpenAPI público. As rotas `/admin` ficam fora dele |
| `/console` | O controle do autor, em telas (`#visao`, `#contas`, `#uso`, `#nova`, `#fumaca`): contas, uso por dia e por conta, emitir e revogar chave, desativar e remover, a [fumaça](#fumaça-em-produção) e as pendências da [cobrança](#cobrança). Pede o token de administração na tela e o guarda só na aba |
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
| 402 | Plano pago sem `pago_ate` em dia, mais três dias de tolerância. Não vale para `/v1/conta`, que aceita a chave sem pagamento e não conta na cota ([ADR-033](../decisoes/ADR-033-conta-sem-pagamento-entra-em-minha-conta.md)) |
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
chave. Com a cobrança aberta, nasce também na assinatura, pelo portal
([ADR-031](../decisoes/ADR-031-assinatura-cria-a-conta.md)). Quem tem conta gerencia as próprias
chaves em `/v1/conta`, pague ou não: o `/v1/conta` traz a situação, a assinatura atual e o link da
cobrança em aberto ([ADR-033](../decisoes/ADR-033-conta-sem-pagamento-entra-em-minha-conta.md)).

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
curl -X DELETE https://<dominio>/admin/contas/1 -H "X-Admin-Token: $TOKEN"   # remover de vez (só desativada)
curl "https://<dominio>/admin/uso?dias=90&conta_id=1" -H "X-Admin-Token: $TOKEN"       # uso de uma conta
```

O `PATCH` aceita `plano`, `ativa`, `pago_ate`, `nome` e `observacao`; campo ausente fica como está,
e `null` enviado de propósito limpa `pago_ate` e `observacao`. A lista traz a `situacao` — `ativa`,
`a_vencer` (a 7 dias do vencimento), `em_tolerancia`, `aguardando_pagamento` (assinou e nunca pagou),
`sem_pagamento` (venceu), `desativada` —, calculada pela mesma regra que autentica: as duas sem
pagamento respondem 402 nas rotas de dados.

**Remover apaga de vez** a conta, as chaves, o uso, as assinaturas e os pagamentos, e libera o
e-mail. Só vale para conta já desativada (409 se ativa). Assinatura viva é cancelada no Asaas antes;
se o Asaas não cancelar, nada é apagado. Com a cobrança desligada, conta com assinatura viva não sai.

## Cobrança

Pelo Asaas (`dadosapi/cobranca.py`), atrás de `COBRANCA_ATIVA`. **Está ligada em produção, e só o
autor paga** ([ADR-034](../decisoes/ADR-034-cobranca-ligada-e-conferida.md)). Desligada,
`POST /v1/assinatura`, `POST /v1/conta/assinatura`, o webhook e a conferência respondem 503.

Ligada: a página assina Essencial ou Pro, o serviço cria cliente e
assinatura no Asaas e devolve o link de pagamento. **Quem não tem conta assina pelo
`POST /v1/assinatura`**, sem chave, e a resposta traz a chave, uma vez só, e o link. A chave
responde 402 até o pagamento ser confirmado. E-mail de conta existente recebe 409 e assina em
"Minha conta"; cadastro que nunca pagou é retomado por quem assina de novo, e as chaves antigas
caem, salvo se houver assinatura de até sete dias aguardando pagamento. Cinco cadastros por hora por
endereço.

**O que se pede de quem paga:**

| Campo | | Onde fica |
|---|---|---|
| `nome` | obrigatório | na conta e no cliente do Asaas |
| `email` | obrigatório; o portal pede duas vezes | na conta e no cliente do Asaas |
| `cpf_cnpj` | obrigatório; validado aqui pelo dígito, com ou sem máscara, inclusive o CNPJ com letras | só no Asaas |
| `cep` | obrigatório, oito dígitos | só no Asaas |
| `numero` | obrigatório, até 10 caracteres (`S/N` vale) | só no Asaas |
| `telefone` | opcional; celular com DDD, para o lembrete do Asaas | só no Asaas |
| `parcelas` | opcional, de 2 a 12, só com `ciclo` anual: o anual parcelado no cartão | na assinatura |

Documento, CEP, telefone ou parcelas inválidos respondem 422 antes de qualquer gravação e de
qualquer chamada ao Asaas. Cliente e assinatura levam `externalReference` com o id da conta.

**O anual parcelado** ([ADR-035](../decisoes/ADR-035-anual-parcelado-no-cartao.md)) não é assinatura
no Asaas: é uma cobrança parcelada no cartão (`POST /payments` com `installmentCount` e
`totalValue`), e `acesso.assinatura` guarda o id do parcelamento em `asaas_assinatura`, com
`parcelas` e `inicio`. A primeira parcela confirmada libera o ano contado do `inicio`, e a
assinatura passa a `quitada`: não há recorrência a cancelar, e trocar de plano não mexe nela.
Estorno ou chargeback de qualquer parcela desfaz o ano inteiro. Não renova sozinho: perto do
vencimento, a pessoa gera a cobrança do próximo ano em Minha conta. `GET /v1/planos` traz
`parcelas_no_anual`, o máximo que o portal oferece.

Quem já tem chave assina, renova ou troca de plano pelo `POST /v1/conta/assinatura`, mesmo sem
pagamento em dia; os dados de quem paga só são pedidos se a conta nunca assinou, porque a renovação
usa o cliente do Asaas que já existe. No `/v1/conta`, a assinatura traz `pagar_em`, o link da
cobrança vencida mais antiga ou, sem vencida, da pendente, consultado no Asaas na hora, ou
`pagar_em_indisponivel` quando ele não responde. Uma conta abre no máximo três assinaturas por dia.

**Assinar de novo cria a assinatura nova antes de cancelar a viva anterior**, que fica
`substituida`; o que já foi pago vale até o `pago_ate`. Se o Asaas recusar a nova, a antiga segue
intacta. Se a antiga não for cancelada na hora, fica com `cancelamento_pendente`, e a conferência
tenta de novo.

**O webhook** é `POST /cobranca/asaas`, com o token no cabeçalho `asaas-access-token`. Cada evento
entra uma vez. Evento gravado sem `resultado` caiu antes de aplicar, e a reentrega do Asaas o aplica
de novo. O corpo só aponta o pagamento: o estado e o titular saem da **consulta ao Asaas** e da
assinatura gravada aqui. Para cada estado do pagamento:

| Estado no Asaas | Efeito |
|---|---|
| `CONFIRMED`, `RECEIVED`, `RECEIVED_IN_CASH` | Grava o pagamento em `acesso.pagamento` e leva o `pago_ate` ao fim do ciclo. Põe a conta no plano da assinatura só se é ele que estende o `pago_ate`: pagamento antigo não desfaz ajuste à mão |
| Os mesmos, numa assinatura `substituida` | Pede o estorno ao Asaas, do parcelamento inteiro se for parcelado. Se ele recusar, ou negar depois, o evento fica com "estornar à mão" |
| Estornado, em chargeback ou removido | Marca o pagamento como estornado. Se era ele que segurava o `pago_ate`, o recua ao último pagamento que segue de pé ou, sem outro, à véspera do vencimento dele |
| Qualquer outro | Ignorado |

Os eventos que levam à consulta são os de confirmação, recebimento, estorno, chargeback, remoção e
restauração; o resto é ignorado sem chamar o Asaas.

**A conferência** (`cobranca.conferir`) roda sozinha um minuto depois de o serviço subir e depois a
cada seis horas, e na hora pelo console (`POST /admin/cobranca/conferir`). Ela cancela as
substituídas pendentes, aplica os pagamentos confirmados das assinaturas vivas que ainda não estão em
`acesso.pagamento` e reconsulta os pagamentos que seguram acesso hoje, para achar estorno. É o que
cobre a fila de webhooks que o Asaas interrompe depois de 15 falhas seguidas. `GET /admin/cobranca`
traz a última conferência e as pendências: evento sem resultado há mais de uma hora e estorno à mão
dos últimos 30 dias. O console as mostra em "Pede atenção".

## Variáveis

| Variável | Para quê |
|---|---|
| `DATABASE_URL` | `postgresql://dados_api:<senha>@${{postgres-mercado.PGHOST}}:${{postgres-mercado.PGPORT}}/${{postgres-mercado.PGDATABASE}}`, com o papel próprio ([abaixo](#papel-no-banco)). Lê `mercado` como `mercado_leitura` e escreve só no schema `acesso`. O valor termina no `}}`: quebra de linha colada no fim derruba o Pre-Deploy |
| `DADOS_API_ADMIN_TOKEN` | Token das rotas `/admin`, 32 caracteres ou mais. **Falha ao subir sem ele.** Definido no painel do Railway, nunca no repositório |
| `CONTATO_WHATSAPP` | Opcional. Com ele, o "Pedir um convite" do portal abre o WhatsApp (`wa.me`) com a mensagem pronta. Só os dígitos contam, com o 55 do país |
| `CONTATO_EMAIL` | Opcional. Sem WhatsApp, o "Pedir um convite" abre o e-mail |
| `PROXIES_CONFIAVEIS` | `1` por padrão: o proxy do Railway. Quantos endereços, da direita do `X-Forwarded-For`, foram escritos por proxy; `0` usa o IP da conexão |
| `COBRANCA_ATIVA` | `false` por padrão. `true` abre a assinatura pela página, o webhook e a conferência. Em produção, `true` |
| `ASAAS_API_KEY` | Obrigatória com a cobrança ativa |
| `ASAAS_WEBHOOK_TOKEN` | 32 caracteres ou mais. Obrigatória com a cobrança ativa |
| `ASAAS_URL` | `https://api.asaas.com/v3`; o sandbox é `https://api-sandbox.asaas.com/v3` |

Serviço, migrações e deploy em [07-OPERACAO](../07-OPERACAO.md#serviços).

## Fumaça em produção

`dadosapi/fumaca.py` faz só GET e confere cada rota contra o plano da chave, lido do `/v1/conta`:
200 ou 403 conforme o recurso, o corte do histórico, o `X-Limite-Dia`, a última cotação com até
cinco dias, os planos públicos e o 401 sem chave.

**Pelo console** (`#fumaca`, que chama `POST /admin/fumaca`): o serviço roda a conferência contra o
próprio processo, por `127.0.0.1`, com uma chave temporária para cada plano da tabela, e a revoga no
fim. Cada plano tem uma conta `<plano>@fumaca.invalid`, criada na primeira rodada, paga até 2099 e
sem chave fora da rodada; ela e o tráfego dela ficam fora de `/admin/contas` e `/admin/uso`. Duas
rodadas ao mesmo tempo: a segunda recebe 409. Cada conferência de rota traz a resposta: o código, `Content-Type`,
`X-Limite-Dia`, `X-Restante-Dia`, `Retry-After` e o corpo, cortado em 4.000 caracteres.

**Por fora**, contra a URL pública (o domínio e o TLS entram junto), com chaves suas:

```bash
cd fiance-dados && FIANCE_DADOS_CHAVE=fd_...,fd_... python -m dadosapi.fumaca [url]
```

Sem chave, só as rotas públicas. Sai com 1 se algo falhar.

## Papel no banco

A API entra no `postgres-mercado` como `dados_api`, desde 2026-10-23: membro de `mercado_leitura`,
dono só do schema `acesso`, sem poder criar schema nem escrever em `mercado`. O SQL é
`fiance-dados/papel.sql`, e `tests/test_papel.py` roda a API e as migrações com ele. Os passos
abaixo recriam o papel ou trocam a senha; cada execução do `ALTER ROLE` invalida a anterior.

1. Chegar ao banco como o dono do cluster ([07-OPERACAO](../07-OPERACAO.md#serviços)), e rodar
   `fiance-dados/papel.sql` seguido de `ALTER ROLE dados_api PASSWORD '<senha>'`, com uma senha
   gerada (`python -c "import secrets; print(secrets.token_urlsafe(32))"`).
2. No serviço `fiance-dados`, trocar a `DATABASE_URL` por
   `postgresql://dados_api:<senha>@${{postgres-mercado.PGHOST}}:${{postgres-mercado.PGPORT}}/${{postgres-mercado.PGDATABASE}}`.
   O Pre-Deploy Command migra com a mesma URL.
3. Rodar a [fumaça](#fumaça-em-produção) pelo `/console`.

Para voltar, a `DATABASE_URL` volta a `${{postgres-mercado.DATABASE_URL}}`; o papel pode ficar.
Tabela nova em `acesso`, criada pela migração com o próprio `dados_api`, já nasce dele.
