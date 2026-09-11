# fiance — o que falta para subir

> Auditoria de **2026-09-04**, revista em **2026-09-11**, quando o front web saiu do produto e a
> distribuição passou a ser só por loja — o que muda a trilha B mais que qualquer outra coisa
> escrita aqui.
>
> **Escopo:** só o que impede colocar a aplicação no ar. Ferramenta ou integração que mudaria o
> patamar do produto saiu deste arquivo e está em [DIRECAO.md](DIRECAO.md).
> Pendência que não bloqueia go-live continua em [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) — item
> que já está lá vira `KI#n` aqui, e entra só pelo que significa para subir.
>
> **Prazo de validade:** documento de pendência apodrece — este repositório já teve oito de 24
> itens falsos numa única revisão. Ao fechar um item, **apague-o daqui**.

---

## Sumário executivo

O produto **não está pronto para produção comercial, e está perto de estar pronto para produção
gratuita.** A distinção é o que organiza este documento: são três trilhas independentes, e só a
primeira é obrigatória.

| Trilha | O que destrava | Bloqueios |
|---|---|---|
| **A — subir** | API no ar, de graça, com usuário real | 5 |
| **C — lojas** | publicar Android e iOS, que agora é **a única porta de entrada** | 5 |
| **B — cobrar** | ligar a cobrança, depois de C | 6 |

**A ordem mudou em 2026-09-11.** Enquanto havia site, dava para ter usuário antes de ter loja; hoje
não há produto alcançável sem passar por Play e App Store, e a trilha C deixou de ser a última.

O que existe é sólido e incomum para o estágio: 91 rotas de API, ~18,5k linhas de Python, ~12k de
Dart, nove migrações Alembic, CI de quatro jobs cobrindo backend, aplicativo, build Android e
marca, multi-tenancy aplicada na camada de store, sessão com refresh rotacionado e revogação,
exportação e exclusão de conta, e um livro-razão que é fonte única da carteira. Nada disso é o
problema.

O que impedia subir era, em boa parte, código — e essa parte foi feita em 2026-09-05: a suíte
ficou honesta e verde, o IR passou a ser apurado por mês, a migração saiu do startup, o texto
jurídico passou a existir e o Sentry foi integrado nas duas plataformas (ver
[CHANGELOG](../CHANGELOG.md)). **O que sobrou da trilha A não é código:** é criar conta de
Sentry e de monitor, montar a homologação no Railway, desligar o auto-deploy do `main`, executar um
restore de backup e conseguir um advogado para revisar a minuta dos termos.

Para cobrar, o problema é que **três camadas existem só no backend**:

| Camada | Backend | Interface | Consequência |
|---|---|---|---|
| Cobrança | régua de plano, webhook idempotente, preço travado, 402 com corpo de gate | **nada** | não há como receber dinheiro |
| Provedor de pagamento | `FakeProvider`, HMAC caseiro | — | não há como processar dinheiro |
| E-mail | **nada** | — | não há como avisar ninguém de nada |

**Estimativa:** poucos dias para o que resta da trilha A, quase tudo em painel de terceiro. A
trilha C passa a vir antes da B, e o prazo dela não é de engenharia: é fila de revisão de loja. Mais
2 a 3 semanas para a B, e a maior parte não é código de domínio — é integração, tela de cobrança e
texto jurídico.

> **Antes de começar a trilha B, leia [DIRECAO.md](DIRECAO.md).** Há uma mudança de
> direção em avaliação que altera o que é vendido, para quem, e por quanto. Tela de plano, régua de
> `plans.py` e escolha de provedor dependem dessa resposta; a trilha A não depende de nada.

---

## Trilha A — o que impede subir

> Cinco dos oito bloqueios originais foram fechados em 2026-09-05 e saíram deste arquivo — o
> **porquê** de cada um está no [CHANGELOG](../CHANGELOG.md). O que fica aqui é o que ainda
> depende de conta, chave ou de uma pessoa executar. O passo a passo de cada um está em
> [docs/OPERACAO.md](../OPERACAO.md); este arquivo só diz que falta.

### A2. O texto jurídico é minuta, e precisa de advogado

As três páginas existem, são públicas e servidas pelo backend, e o aplicativo linka para elas do
login e de Você → Conta: `/termos`, `/privacidade`, `/aviso-cvm`. Elas descrevem com honestidade o
que o produto faz hoje, e estão marcadas como **minuta pendente de revisão jurídica**.

O que falta é a revisão em si. Dois pontos que o advogado precisa fechar antes de o aviso de minuta
sair:

- o **endereço do encarregado** de dados, que a Política promete publicar e ainda não tem (é o
  item 30 do [KNOWN_ISSUES](../KNOWN_ISSUES.md), e as lojas exigem um canal);
- o **prazo de retenção do log técnico**, hoje descrito como "o necessário" — que é honesto e vago.

Quando o parecer chegar, apagar a constante `_MINUTA` de
[`services/legal_pages.py`](../../backend/app/services/legal_pages.py) tira o aviso das três
páginas de uma vez.

### A3. O parecer da fronteira CVM continua sem dono

A **decisão de engenharia** está registrada: o nível publicável é o 2 (analítico), o nível 3 fica
desligado, e o Aviso CVM lê a postura vigente de `GET /api/public/affirmation` em vez de repetir a
frase. Isso basta para subir de graça.

O que falta é jurídico e é de pessoa: **quem assume o parecer**. Ele é obrigatório antes de cobrar
(trilha B) e mais ainda se o nível 3 for ligado algum dia, porque "talvez valha vender X para
comprar Y" é exatamente ele. A leitura sobre orientação de dívida
([REGRAS_NOVO_DOMINIO](REGRAS_DE_DOMINIO.md#dívida)) entra no mesmo pedido.

### A5. Falta a conta de observabilidade, não o código

Sentry está integrado nas duas plataformas, com `before_send` que redige ticker e valor, e é
inerte sem DSN. `SENTRY_DSN` configurado sem o pacote falha alto.

O que falta, tudo em plano gratuito e detalhado em [OPERACAO.md](../OPERACAO.md):

- [x] projetos no Sentry criados e os DSN conferidos por entrega (2026-09-06) — menos o do
      aplicativo, que nunca teve evento visto em painel;
- [ ] monitor externo em `/api/health` **e** em `/api/public/asset/PETR4` — só o primeiro passa
      verde com a BRAPI fora do ar;
- [ ] agregação de log fora do Railway, que é efêmero;
- [ ] alerta em canal humano para 5xx, disjuntor aberto e job periódico parado. Sem este, os três
      acima são painel que ninguém abre — e um worker morto trava o snapshot diário por até 5,4h
      sem ninguém saber (KI#14).

### A7. Falta configurar a homologação, não o fluxo

`.github/workflows/deploy.yml` existe, é acionado à mão, confere que o commit está verde, migra
pelo *release command*, sobe e faz teste de fumaça.

- [x] ambiente de homologação no Railway, com banco próprio, `JWT_SECRET` distinto do de produção,
      um worker e `sleepApplication` ligado (2026-09-06). Ainda **não recebeu o primeiro deploy**
- [x] Pre-Deploy Command apontado para `python -m app.release` nos dois ambientes — o Railway não
      executa a linha `release:` de um Procfile, e sem isso a migração simplesmente não rodava
- [ ] ambientes `staging` e `production` no GitHub, com *required reviewers* em produção
- [ ] segredo `RAILWAY_TOKEN` e variáveis `RAILWAY_SERVICE` e `SITE_URL` em cada um
- [x] **auto-deploy do `main` para produção desligado** (2026-09-06). Ficou só `main` → staging,
      que é o arranjo desejado; a fonte do serviço de produção continua ligada, então deploy manual
      e redeploy de rollback seguem funcionando
- [x] primeiro deploy de homologação, e `ALLOWED_ORIGINS` corrigido (2026-09-06)
- [ ] apagar o serviço `fiance-web`, que perdeu a origem em 2026-09-11 e continua servindo a
      última build (KNOWN_ISSUES #31)

### A8. O restore de backup continua sem nunca ter sido testado

O roteiro está escrito em [OPERACAO.md](../OPERACAO.md#backup-restaurado-ou-é-só-esperança),
com RPO de 24h e RTO de 4h **propostos**, a confirmar no primeiro teste. Backup nunca restaurado
não é backup, é esperança — e três documentos deste repositório o usam como justificativa de
decisão de arquitetura.

- [ ] executar o restore uma vez, registrar a data na tabela de OPERACAO.md e confirmar os números.

---

## Trilha B — o que impede cobrar

> Não comece por aqui sem ler [DIRECAO.md](DIRECAO.md). B1, B2 e B3 são caros e são
> exatamente o que muda se a direção do produto mudar.

### B1. A pergunta que precede tudo: IAP das lojas

Google Play e App Store exigem compra in-app para conteúdo digital consumido dentro do app, com
comissão de 15–30%. Checkout aberto em navegador de dentro do app é motivo de rejeição nas duas.

**Sem site, a opção de 0% de comissão deixou de existir.** Ela dependia de vender a assinatura numa
página própria, com o aplicativo apenas lendo o estado — e essa página saiu do produto em
2026-09-11. O que sobra:

| Caminho | Como funciona | Custo | Risco |
|---|---|---|---|
| **IAP via RevenueCat** | unifica Play + App Store | comissão da loja; free até US$2,5k/mês | dependência a mais, mas resolve em dias |
| **IAP nativo** | Play Billing + StoreKit | 15% (1º US$1M) a 30% | dois provedores, dois webhooks, reconciliação com a assinatura do servidor |
| **Voltar a ter uma página de venda** | publicar de novo uma superfície de checkout fora do app | 0% na venda | é reabrir o front que acabou de sair; o app continua proibido de mencionar preço |

A arquitetura atual — assinatura no servidor, entitlement resolvido no backend, cliente burro —
suporta os três. **Decidir isto é o primeiro item da trilha**, porque B2 e B3 dependem da resposta,
e a decisão agora custa comissão em vez de custar tela.

### B2. Não existe provedor de pagamento real

`app/payments/billing.py:77` instancia `FakeProvider` e não há caminho para outro. A interface
`PaymentProvider` está bem desenhada (`create_checkout` / `verify` / `parse` /
`active_subscriptions`) e `subscription_service` já assume `provider: str = "stripe"` como default —
o encaixe foi previsto, o adaptador nunca foi escrito.

Falta: adaptador real, seleção por variável de ambiente, e o segredo de webhook do provedor
substituindo o HMAC caseiro. Validar em staging (A7) antes de qualquer venda.

### B3. Não existe interface de cobrança, e o CTA está quebrado

`billing` não aparece em `mobile/lib`. Não há tela de plano, exibição de preço, checkout, gestão
de assinatura, cancelamento, recibo nem histórico de pagamento — e o 402 do backend já devolve o
corpo que montaria o bloqueio.

O gate do front tinha um CTA que apontava para uma rota inexistente e mandava a pessoa para a home
sem erro nenhum; ele saiu com o front. **A lição fica:** todo destino de conversão precisa existir
antes do botão, e no Dart isso não tem máquina que cobre.

Cancelamento em interface não é conveniência: é exigência do CDC e das duas lojas.

### B4. O relógio do trial já está correndo com a cerca desligada

KI#19, segunda metade — o item com maior potencial de estrago. `start_trial()` é chamado na primeira
posição salva e `ENTITLEMENTS_ENABLED=false` hoje, então **todo usuário atual tem um trial de 14
dias já vencido gravado no banco**. Virar a flag derruba a base inteira para Free no mesmo instante,
sem aviso.

O trial precisa ser **reiniciado na ativação da cerca, antes de virar a flag**. É migração de dados
com janela, não deploy — e precisa de um e-mail avisando (B5).

### B5. Não existe e-mail transacional — nenhum

Sem SMTP, Resend, SendGrid, SES, nada. O único canal de saída é push FCM, que **exige o app
instalado** — decisão declarada e correta para alerta de preço, insuficiente para o que cobrança
exige:

- recibo de pagamento (CDC e fiscal);
- aviso de fim de trial — sem ele a conversão despenca e a reclamação sobe;
- falha de cobrança e retentativa (*dunning*) — sem isso, cartão vencido vira churn silencioso;
- confirmação de cancelamento;
- aviso de mudança de Termos e de Política de Privacidade (LGPD);
- entrega da exportação de dados.

Sem e-mail, cobrar é irresponsável. **Resend** pela DX, **AWS SES** pelo custo em escala,
**Postmark** pela entrega; qualquer um serve, e a decisão é secundária ao fato de não haver nenhum.

### B6. Nota fiscal de serviço

Sem emissão resolvida, é processo manual desde a primeira venda. Decisão de operação, não de código,
mas precisa estar tomada antes de a primeira cobrança cair.

---

## Trilha C — o que impede publicar nas lojas

| Item | Estado | Onde |
|---|---|---|
| Android assina release com chave de **debug** | `// TODO: Add your own signing config` | [build.gradle.kts:38-41](../../mobile/android/app/build.gradle.kts#L38-L41) |
| iOS sem `GoogleService-Info.plist` | push não funciona no iOS | `mobile/ios/Runner/` |
| Sem *Sign in with Apple* | único login é `/auth/google` | [auth.py](../../backend/app/api/auth.py) |
| ~~Sem política de privacidade pública~~ | **feito** — `/privacidade`, servida pelo backend e sem login; falta a revisão jurídica (A2) e o canal de atendimento | [legal_pages.py](../../backend/app/services/legal_pages.py) |
| `applicationId` genérico `com.fiance.fiance` | funciona; confira o domínio antes de registrar | — |

A ausência de *Sign in with Apple* é bloqueio duro: a diretriz 4.8 exige oferecer login que não
colete dados sempre que se oferece login social de terceiros. Google é exatamente esse caso.

A ficha de segurança de dados (Play Data Safety / App Privacy) não é bloqueio de engenharia: o
dicionário fechado de eventos de `core/events.py` e a lista de tabelas de `account_store` dão a
resposta pronta.

---

## Checklist de go-live

### Trilha A — antes de subir

- [x] Suíte verde de verdade: rede bloqueada no transporte e ETF de renda fixa classificado certo
- [x] Termos de Uso, Política de Privacidade e Aviso CVM públicos, servidos pelo backend — como
      minuta (A2 segue aberto pela revisão jurídica e pelo canal de atendimento)
- [x] Nível de afirmação publicável decidido por escrito, e registrado no CHANGELOG
- [x] IR consertado: apuração por mês e categoria, projetada do razão
- [x] Migração movida do startup para *release command*, e comentário do Procfile corrigido
- [x] Sentry integrado nas duas plataformas, com limpeza que não deixa carteira sair
- [ ] Evento do aplicativo visto no painel do Sentry, num aparelho real (A5)
- [ ] Monitor de uptime em `/api/health` **e** na rota pública (A5)
- [ ] Alerta em canal humano para 5xx, disjuntor aberto e job periódico parado (A5)
- [ ] Log persistente fora do Railway (A5)
- [ ] Ambiente de staging com banco próprio, e auto-deploy do `main` desligado (A7)
- [ ] Restore de backup testado, com data registrada, e RPO/RTO confirmados (A8)
- [ ] Minuta dos termos revisada por advogado, e o aviso de minuta removido (A2)
- [x] `APP_ENV=production`, `JWT_SECRET`, `ALLOWED_ORIGINS` e `BILLING_WEBHOOK_SECRET` conferidos
      no ambiente (2026-09-06)
- [ ] `ALLOWED_ORIGINS` revisada: as origens de navegador que ela liberava saíram com o front, e
      `http://localhost:4200` em produção deixa uma página local falar com a API de produção
- [x] `FINNHUB_API_KEY` e `GEMINI_API_KEY` apagadas dos dois ambientes (2026-09-06) — as fontes
      foram descontinuadas e o código não lia nenhuma das chaves
- [ ] Dependabot e scanner de segredo ligados — nada avisa de CVE em dependência, e nada impede o
      próximo commit vazar chave

### Trilha B — antes de ligar a cobrança

- [ ] Direção de produto decidida ([DIRECAO.md](DIRECAO.md)) — o que é vendido e por
      quanto precede a tela que vende
- [ ] Decisão de IAP tomada (B1)
- [ ] Provedor de pagamento real integrado e webhook validado em staging (B2)
- [ ] Tela de plano em `/voce/plano` — a rota não existe no aplicativo (B3)
- [ ] Checkout, gestão de assinatura, cancelamento e recibo em interface (B3)
- [ ] **Trial reiniciado para a base existente**, antes de virar `ENTITLEMENTS_ENABLED` (B4)
- [ ] E-mail transacional para recibo, fim de trial, falha de cobrança e cancelamento (B5)
- [ ] Fluxo completo — assinar, cobrar, falhar, retentar, cancelar, degradar — coberto de ponta a
      ponta. Não há mais suíte E2E nenhuma (KNOWN_ISSUES #13)
- [ ] Emissão de nota fiscal resolvida (B6)
- [ ] Parecer jurídico sobre a fronteira CVM 19/20 (A3) — obrigatório quando há remuneração

### Trilha C — antes de publicar nas lojas

> **Esta trilha virou a porta de entrada do produto.** Enquanto ela não fechar, não há como alguém
> de fora usar o fiance.

- [ ] Keystore de release Android gerado, guardado em cofre e configurado no Gradle
- [ ] `GoogleService-Info.plist` do iOS adicionado e push testado em aparelho real
- [ ] *Sign in with Apple* implementado (backend + mobile)
- [ ] URL de política de privacidade (`{SITE_URL}/privacidade`) preenchida nos dois formulários,
      e o canal de atendimento publicado nela (KNOWN_ISSUES #30)
- [ ] Ficha de segurança de dados preenchida
- [ ] Monitor externo cobrindo `/privacidade`: ela cai sem que nenhuma tela do produto perceba
- [ ] Decisão de IAP implementada conforme B1

---

## O que **não** é pendência

Registrado para que ninguém refaça:

- **Push exigir o app instalado** deixou de ser assimetria: só há o aplicativo.
- **O lock de job expirar por TTL em vez de ser liberado** é deliberado — o TTL é o intervalo do
  job. O custo está no KI#14 e a correção certa é heartbeat, não `release` no `finally`.
- **O universo hardcoded** (KI#4) é fallback defensivo intencional.
- **A posição é projeção do razão** e **as colunas monetárias são `Money`** — os dois já foram
  falsamente listados como pendência antes.
- **`/api` sem versão** continua respondendo de propósito: os apps instalados apontam para lá.
- **A paginação por payload** nas listas com agregado (KI#16) é limitação conhecida e consciente: o
  total por mês e a marcação a mercado precisam do conjunto inteiro por definição.

## O que saiu deste documento

Para não parecer que sumiu:

| Assunto | Foi para |
|---|---|
| Open Finance, extrato da B3, CVM Dados Abertos, Tesouro Direto, BRAPI paga | [DIRECAO.md](DIRECAO.md) |
| WhatsApp/Telegram, landing e conteúdo SEO, tempo real, IA de escopo estreito | [DIRECAO.md](DIRECAO.md) |
| Analytics de produto (PostHog × tela de operador) | [DIRECAO.md](DIRECAO.md) |
| Push só existir no mobile, token de push sequestrável (KI#15) | [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) |
| Leitor de tela (KI#17), os dois temas em navegador (KI#18), cobertura de teste | [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) |
