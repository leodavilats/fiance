# fiance — histórico de mudanças

> Registro datado do que mudou e **por quê**, incluindo as decisões que foram tomadas e depois
> revertidas. É aqui que mora o contexto: por que a categoria `acoes_int` foi renomeada sem alias,
> por que o script de limpeza de cripto foi escrito e apagado no mesmo dia, por que o motor de
> otimização quantitativa foi removido.
>
> **O que está aberto hoje** fica em [KNOWN_ISSUES.md](KNOWN_ISSUES.md), não aqui. Este arquivo é
> só passado — nada nele deve ser lido como pendência.
>
> Mais recente primeiro.

---

## O produto passa a ser um aplicativo, e o front web sai inteiro (2026-09-11)

Decisão de produto, tomada para andar mais rápido: **o fiance é um aplicativo de celular**,
distribuído pela App Store e pelo Google Play. O front Angular saiu do repositório, com os 191
testes, o E2E de navegador, as 24 regras do `lint:ui`, a renderização no servidor e a landing.
Sobraram duas pernas: a API em FastAPI e o Flutter.

O motivo não é técnico. Manter duas interfaces custa cada tela duas vezes, cada regra de produto
duas vezes, e — o que é pior — mantém a **paridade** como trabalho permanente: um documento, uma
disciplina e uma classe inteira de defeito que só existe porque há dois lugares para a mesma ideia.
O repositório tem o registro de que a paridade quebrava sempre no mesmo lugar (o conceito, nunca a
cor), e de que o mobile passou meses sem `/mes` e sem `/sobra` com a paleta perfeitamente
sincronizada. Com um cliente só, esse custo desaparece em vez de ser administrado.

### O que o front carregava e não era tela

Três coisas, e cada uma teve destino diferente.

**O texto jurídico passou para o backend.** `/termos`, `/privacidade` e `/aviso-cvm` agora são HTML
servido pelo próprio processo da API (`api/legal.py` + `services/legal_pages.py`), fora de `/api`.
Não é conveniência: `mobile/lib/core/legal_links.dart` já apontava para
`https://fiance.up.railway.app/termos` — o domínio da **API** —, então os três links de dentro do
aplicativo estavam quebrados antes desta mudança, e ninguém tinha percebido. As lojas exigem uma
URL de privacidade que abra sem login, e agora ela existe onde o aplicativo sempre disse que
estava.

São páginas de documento, e a forma segue disso: sem JavaScript, sem asset externo, sem paleta. A
cor vem do agente do usuário (`color-scheme: light dark`), porque uma segunda cópia dos tokens
envelheceria calada — é a mesma razão pela qual o Aviso CVM lê `affirmation.current()` no servidor
em vez de repetir a frase do nível em vigor. `test_paginas_juridicas.py` cobra que as três abrem
sem sessão, que não carregam script, e que a de privacidade diz como apagar a conta.

**A landing e o que a sustentava saíram.** Com ela foram `POST /public/interest` e a tabela
`interest_signups` (migração `0009_sem_landing`), `GET /public/universe` (que existia para montar o
sitemap) e `GET /public/asset/{t}/og.png` com o `og_image.py` inteiro — cartão de link para uma
página que não existe mais. Ficou `GET /public/asset/{ticker}`: é a leitura sem titular, é o que o
teste de fumaça do deploy exercita, e é o que sustenta compartilhar um ativo por link.

**A paleta mudou de casa.** `web/src/foundation.css` era a fonte da cor, e tinha três consumidores
fora do web. Agora a fundação é `mobile/lib/core/design_tokens.dart`, que já existia como espelho
escrito à mão — e a varredura de conferência não achou uma divergência: os 11 SVG da marca saíram
byte a byte idênticos depois de o gerador passar a ler o Dart. O espelho estava certo; o que
sobrava era a duplicação.

### O que a máquina deixou de cobrar, e está declarado

O verificador do front tinha 24 regras; o Dart tem 11, em `test/lint_ui_test.dart`, mais o
contraste em `test/contraste_test.dart`. Cinco regras não têm equivalente escrito, e três delas
protegiam acessibilidade ou erro silencioso — gráfico sem tabela, destino de navegação inexistente,
controle montado à mão. Isso é **dívida registrada**, não decisão: está no
[KNOWN_ISSUES](KNOWN_ISSUES.md), item 14, junto do E2E que também deixou de existir (item 13).

Registrar em vez de portar às pressas é deliberado. Uma regra de lint nasce de um sinal no código —
um seletor CSS, um nome de classe —, e traduzir "controle montado à mão" para Flutter exige decidir
antes o que corresponde àquele sinal. Regra escrita contra o que a extensão sugere, e não contra o
que o repositório tem, já passou meses aqui lendo um arquivo só.

### O que isto muda em decisões que ainda não foram tomadas

Duas, e as duas ficaram mais caras.

**A cobrança perdeu a opção de 0% de comissão.** O plano registrado em 2026-08-27 assumia vender a
assinatura numa página própria, com o aplicativo apenas lendo o estado — Google Play e App Store
proíbem checkout externo aberto de dentro do app, mas não proíbem que a venda aconteça fora dele.
Sem site, sobram a compra in-app (15–30%) e a hipótese de republicar uma superfície de venda. A
arquitetura aguenta as duas: o direito mora no backend, ligado ao `user_id`, e o gateway continua
sendo detalhe de canal.

**A compatibilidade de contrato deixou de ser precaução e virou regra.** Enquanto havia web, um
campo novo obrigatório chegava a todo mundo no próximo carregamento. Agora o cliente passa por fila
de revisão de loja e convive com versões antigas instaladas por tempo indeterminado: campo novo
nasce **opcional** no Dart, e campo que some do backend derruba a versão anterior do aplicativo.

### O que mudou de lugar

| O quê | Antes | Agora |
|---|---|---|
| Marca (ícone e kit) | `assets/brand/` na raiz | `mobile/assets/brand/` |
| Gerador de ícones | `design-tokens/build-icons.py` | `mobile/tool/build_icons.py`, lendo a cor do Dart |
| Fundação visual | `web/src/foundation.css` | `mobile/lib/core/design_tokens.dart` |
| Texto jurídico | componentes Angular | `backend/app/services/legal_pages.py` |
| Contrato de paridade | `docs/design/PARIDADE.md` | apagado — sobrou uma plataforma |

O favicon e as cópias em `web/public/` saíram com o front: favicon sem site é arquivo que ninguém
pede. O CI foi de seis jobs para quatro (marca, backend, aplicativo, build Android).

**O serviço `fiance-web` do Railway não foi apagado**, e é o único fio solto desta mudança:
apagá-lo é ação fora do repositório, e está registrado como item 31 do KNOWN_ISSUES. Enquanto
estiver de pé, ele serve a última build publicada — um produto que não existe mais.

---

## Quatro pendências fechadas, e um erro de idioma achado no caminho (2026-09-09)

Passagem sobre a lista aberta: o lock de job, a régua de score sem consumidor no mobile, o título
que prometia score, e o componente `Range`. O quinto item não estava na lista — apareceu porque um
teste do `Range` falhou por um motivo que não era o teste.

### O lock de job tinha dois prazos num só

`_run_guarded` não liberava o lock ao terminar: deixava vencer, com TTL igual a 0,9 × o intervalo
do job. Isso é o **certo** para espaçar ciclos — liberar no fim faria o worker seguinte repetir o
trabalho segundos depois — e o **errado** para exclusão mútua: um worker que morresse logo após
adquirir deixava `daily_snapshot` bloqueado por até 5,4h, em silêncio.

São duas funções diferentes pedindo prazos diferentes, e agora têm. Enquanto o corpo roda, o lock
vale 120s e um batimento de 30s o renova; parado o batimento, outro worker assume em ≤2min.
Terminado o corpo, o prazo longo entra como espaçamento, que é o que ele sempre foi. `renew_job_lock`
recusa renovar lock alheio — renovar o de outro seria roubá-lo.

### A régua de score do mobile não tinha um único consumidor

`ScoreRuler` são ~120 linhas com trilho por banda, marcador, semântica e degradação por
completude — e nada a instanciava. Três telas desenhavam score à mão: `feed_health` escrevia
`'${score.round()}/100'` mais uma pílula montada na unha, `feed_tiles` e `quick_invest_view` faziam
duas outras variações. É o "vocabulário sem consumidor" outra vez, na peça que a
[DESIGN-SYSTEM](design/DESIGN-SYSTEM.md) chama de elemento-assinatura.

Adotada em dois lugares, e **só nos dois em que cabe**: o bloco de saúde do `Mês`, que é o análogo
do `portfolio-summary` do web, e o card de Descobrir — que **não mostrava score nenhum**, embora a
lista seja ordenada por ele: o critério de ordenação era invisível, e com a régua vem junto a
degradação por completude. Os outros dois sítios mostram só o rótulo de banda dentro de uma linha
densa, e ali a régua cheia seria pior que o texto; forçá-la seria trocar um defeito por outro.

### O título prometia um score que a rota não devolve

`/ativo/:ticker` saía com `— preço justo, valuation e score | fiance`, e a descrição repetia
"Score, margem de segurança e histórico de proventos". `/asset/{symbol}` **não tem campo `score`**:
devolve `decision`, `fair_price`, `technical`, `fundamentals`, `price_history`. A página mostra
veredito, preço justo, margem e falsificadores — nunca score.

É pequeno e é o pior lugar para ser pequeno: título é o que o buscador indexa, na página pública de
aquisição. Agora diz o que a tela tem, e a descrição troca a promessa vazia por "o que derrubaria o
veredito", que é o que ela de fato mostra e é o que o produto tem de diferente.

### `Range`, o último dos componentes essenciais

A faixa de projeção era escrita à mão em cada tela, e as duas plataformas divergiram: o web mostrava
`cenário base: R$ X` sob a faixa, o mobile não — a mesma projeção contava duas histórias. No mobile
a "faixa" era um `closure` de duas linhas dentro de `_buildResult`.

`<app-range>` e `FiRange` fecham isso. No web é **atributo**, e não elemento, para o par nome/valor
continuar sendo `<dt>`/`<dd>` dentro do `<dl>`: um elemento no meio quebraria a lista de definição,
que é como o leitor de tela pareia rótulo e cifra. O mobile ganhou o cenário base que lhe faltava, e
a faixa passou a ser anunciada como uma coisa só — piso e teto lidos separados perdem que são as
pontas de uma mesma faixa.

### E o que apareceu sem ser procurado: o produto falava inglês nos números

O primeiro teste do `Range` falhou esperando `120.000` e recebendo `120,000`. O teste estava certo.

**Não havia `LOCALE_ID` na aplicação.** O Angular assume `en-US`, e os pipes `number`, `currency` e
`percent` saíam assim em **171 usos, de 29 arquivos**. Ponto e vírgula trocam de papel entre os dois
idiomas, então o erro não deforma o número — ele o divide por mil: `R$ 120,000` é lido como cento e
vinte reais por quem escreve `R$ 120.000,00`. Num produto de dinheiro brasileiro, é o pior tipo de
defeito de formatação, porque o número continua plausível.

Passou despercebido porque parte das telas não usa pipe: `month`, `surplus` e outras formatam com
`toLocaleString('pt-BR')` à mão, e essas sempre estiveram certas. A correção é de três linhas —
`registerLocaleData(localePt)` e `{ provide: LOCALE_ID, useValue: 'pt-BR' }` — e conserta os 171 de
uma vez. Um teste sobre o `appConfig` trava a regressão, porque o modo de errar aqui é não notar.

---

## Ligar a cobrança era um alçapão, e agora não é (2026-09-09)

A pergunta era para onde seguir depois do passe de UX. A resposta veio de conferir o KNOWN_ISSUES
contra o código em vez de acreditar nele — que é a disciplina que o próprio arquivo pede — e o que
apareceu não era uma pendência de interface: era uma armadilha embaixo do gesto mais provável do
próximo mês.

### O alçapão

`record_portfolio_milestones` chama `start_trial(uid)` na primeira posição salva e **não consulta
`ENTITLEMENTS_ENABLED`**. A cerca está desligada desde sempre, então:

- toda conta que já salvou uma posição tem `trial_started_at` gravado e `trial_ends_at` no passado;
- `start_trial` não re-arma — `if row.trial_started_at is not None: return`;
- com a cerca ligada, `resolve()` calcula `in_trial = moment < trial_ends_at`, que é falso, e sem
  assinatura nem crédito o plano cai para `FREE`.

Somando: **virar `ENTITLEMENTS_ENABLED=true` derrubaria a base inteira para Free no mesmo
instante**, e nenhum caminho de código devolveria o trial. O KNOWN_ISSUES mencionava isso como nota
dentro de "falta tela de plano". A ordem estava invertida: era a única coisa que precisava existir
*antes* de qualquer tela, porque o modo de errar é silencioso, atinge todo mundo de uma vez, e o
gesto que o dispara — "vamos ligar a cobrança" — é exatamente o que se faz sem cerimônia.

### A âncora, e por que não é migração

Um trial que correu enquanto nada era cercado não foi um trial: foi um carimbo sem efeito. Então o
relógio conta do **mais tarde** entre qualificar e a cerca subir. Quem já tinha carteira ganha os 14
dias a partir da cerca; quem qualificar depois conta dos seus.

`ENTITLEMENTS_ENABLED_AT` (ISO ou epoch) declara quando a cerca subiu, e `fim_do_trial()` é
`max(trial_started_at, cerca) + TRIAL_DAYS`. Isso é **cálculo, não escrita**: sem migração Alembic,
sem backfill, sem tocar em linha nenhuma, e reversível — desligar a flag volta tudo ao que era.

Uma migração resolveria o dado de hoje e não o mecanismo: se a cerca subisse semanas depois, quem
qualificasse no intervalo queimaria o trial de novo. Não iniciar o trial com a cerca desligada é
pior ainda — aí ninguém o teria, porque `start_trial` só é chamado no marco da primeira posição, que
é uma vez só.

**A flag ligada sem a data falha alto no startup.** É a mesma disciplina de `APP_ENV` sem default e
de `SENTRY_DSN` sem o pacote: não se pode ligar a cerca sem declarar quando ela subiu, porque a
alternativa é descobrir o esquecimento pelo suporte.

### O CTA do paywall levava ao Mês

O `gate.component.ts` apontava para `/voce/plano`, que **não está em `app.routes.ts`**. Com o
curinga `{ path: '**', redirectTo: '/mes' }`, quem decidisse assinar era despejado no Mês sem
explicação. Link morto é ruim em qualquer lugar e péssimo num paywall.

Consertar só aquele literal seria consertar o sintoma, então virou a **24ª regra do `lint:ui`**:
`routerLink` para rota que não existe reprova. Ela lê a árvore de `app.routes.ts` de verdade, com
`children`, porque é a composição pai/filho que decide se `/voce/plano` existe — e varreu o produto
inteiro achando exatamente aquele um.

O gate agora recebe `upgradeRoute` como entrada, e **sem destino não desenha botão**: diz que a
assinatura ainda não está aberta e que nada do que a pessoa cadastrou depende dela. Inventar uma
tela de plano aqui seria inventar preço e forma de pagamento, que são decisão de produto; o que não
se podia manter era um botão que promete uma saída inexistente.

### O que a conferência ainda achou

**Nada renderiza `<app-gate>`.** O único `app-gate` do repositório é a própria declaração do
seletor. É a armadilha do "vocabulário sem consumidor" na sua forma mais caro — um componente de
paywall que ninguém usa, apontando para uma rota que não existe. O KNOWN_ISSUES 27 foi reescrito
para dizer o que a cobrança é de fato: três metades que não se falam, e o que falta é o meio.

**`/patrimonio` pedia proventos duas vezes.** `reload()` chamava `loadDividends()` antes de a
avaliação chegar — com a estimativa vazia — e o resultado era descartado pelo chamado que vem depois
de `evaluate()`. Removê-lo cru deixaria quem só tem renda fixa sem proventos, porque essa conta não
passa pela avaliação: o chamado desceu para os dois caminhos que existem, um por caminho, sempre com
a estimativa em mão.

---

## Quando a leitura falha, a tela para de mentir que está vazia (2026-09-09)

Uma auditoria de UX das três plataformas procurava o que reformular na interface. O que ela achou
não foi aparência: foi que **o produto tratava "não consegui ler" e "você não tem nada" como a
mesma tela**, e essa tela era em branco.

### O estado que não existia

`CarteiraStore.loadFailed` era um booleano, alimentado por quatro leituras e consumido por **uma**
tela — `/patrimonio` (Resumo). As outras seis seções da mesma loja renderizavam a carteira como se
estivesse vazia quando a rede caía. Em Posições, Encerradas e Proventos não havia sequer estado
vazio: a página abria com o título e o corpo em branco, sem uma frase, sem um botão, sem nada a
fazer.

O padrão se repetia fora da loja, sempre na mesma forma — `error: () => this.loading.set(false)`:

- **`/mes`**, a primeira tela do produto. `@if (carregando()) … @else if (mes())` não tinha `@else`:
  com a leitura falhada, a tela era o cabeçalho e o vazio.
- **`/patrimonio/desempenho`** engolia a falha do dashboard (`error: () => undefined`) e mostrava
  *"Ainda não há histórico suficiente"* para quem tinha história e não conseguiu lê-la.
- **`/sobra/desvio`** mostrava *"Nenhuma estratégia calculada ainda"* quando o cálculo falhou.
- **Projeção, Quedas, Comparar e Oportunidades** desligavam o botão e não diziam nada: a pessoa
  clicava, o botão parava de girar, e a tela ficava igual.
- **`/voce/alertas`** dizia *"Nenhum alerta configurado"* quando a leitura da lista falhou, e
  reportava a falha de criação com `'✗ Não conseguimos criar o alerta'` — um glifo carregando
  estado, contra a regra de que estado é papel de cor, e ainda por cima morto: a classe que o lia
  testava `startsWith('x')` e o caractere é `✗`, então a frase saía sem cor nenhuma.
- **`/aviso-cvm`**, texto jurídico, omitia em silêncio a postura de afirmação em vigor quando a
  leitura de `/public/affirmation` falhava — justamente o número que o documento existe para não
  duplicar.

A falha era **anunciada e jogada fora**: o interceptor mostrava um toast que sumia em segundos e
deixava a tela vazia atrás. E o texto do toast era de quem desenvolve, não de quem usa —
`'Sem conexão com o servidor. Verifique se o backend está rodando.'`, `'Erro interno do servidor.'`,
`` `Erro ${error.status}` ``.

### A voz é uma só, e o mobile já a tinha

O aplicativo estava **à frente** do web nisto: `FiErrorState` traduzia `DioException` em frase
humana e oferecia "Tentar de novo" em quinze telas. O conserto foi trazer o padrão para o web, e
não inventar um terceiro.

- `core/error-message.ts` — `mensagemDeErro(erro, acao)`, espelho de `fiErrorMessage`. Status 0 é
  rede de quem usa, não processo de quem opera. `detalheUtil` deixa passar o `detail` de 4xx de
  domínio, que é escrito para ser lido, e barra o de 5xx, que é rastreamento.
- `<app-async-state>` — os quatro estados num contrato só: esqueleto com a forma do que vem, falha
  com frase e "Tentar de novo", vazio via `<app-empty-state>`, e o conteúdo. Adotado em treze telas.
- O interceptor passou a tirar a frase do mesmo lugar, e só decide o efeito colateral do 401.
- `CarteiraStore` guarda o **erro**, não o booleano, e ganhou `carregando` — as sete telas de
  `/patrimonio` passaram a acertar de uma vez, porque o defeito estava na loja que todas leem.

### Duas regras que existiam e não rodavam

`missingExplainers` e `certaintyLanguage` filtravam `.html`. Este repo escreve o template dentro do
`.ts` por contrato, e o único `.html` de `src/` é o `index.html`: as duas regras varriam o
`index.html` havia meses. Uma delas é a que o CLAUDE.md chama de invariante de explicabilidade, e as
telas carregavam `<!-- design-exception: explicabilidade -->` para uma máquina que não lia.

Apontadas para o template inline, **as duas passam sem uma correção sequer** — o código já cumpria a
regra que ninguém conferia. O custo aqui não foi dívida acumulada; foi a garantia ter sido
imaginária.

Uma regra nova, `telaSemTratarFalha`, reprova alvo de rota que lê dado e não trata a falha. Ela
encontrou nove telas além das quatro que a auditoria já tinha achado à mão.

### O momento do dado, onde ele decide

`as_of` viajava do coletor até o cliente em `PortfolioPosition`, estava declarado no modelo do web,
e **não chegava a nenhuma tela fora de `/ativo`**. Trinta preços comparados sem dizer de quando são.
Em Oportunidades era pior que ausente: a linha *"Atualizado agora"* marcava o fetch do navegador, e
com o scan servido do cache do servidor ela afirmava frescor que o dado não tinha.

- `core/data-age.ts` (`idadeDoDado`, `dadoEnvelhecido`, `carimboMaisAntigo`) e `<app-data-age>`. A
  idade de um conjunto é a do carimbo **mais antigo** — dizer a do mais novo promete um frescor que
  a linha de baixo não tem. É o critério que `opportunity_service.market_data_age_seconds` já usava.
- No backend, `Opportunity` (o modelo de resposta) não declarava `as_of`, embora `_MarketRecord` o
  carregasse desde sempre: o `response_model` descartava o campo em silêncio, em cinquenta linhas de
  preço. Declarado, e coberto por teste.
- No mobile, `PortfolioPosition.fromJson` não declarava a chave — a armadilha que o CLAUDE.md nomeia,
  na quarta ocorrência. Declarada, e coberta por teste.
- Os *stubs* de `conftest.py` não carimbavam, então a suíte exercitava um caminho que a produção não
  tem, e um campo de momento perdido passaria verde. Agora carimbam.

### O esqueleto tem forma, e a busca tem porta

Duas correções de paridade, cada uma na direção em que a plataforma estava atrás:

- **O mobile ganhou esqueleto.** Treze telas abriam com um `CircularProgressIndicator` centralizado
  — disco no meio da tela não diz o que está vindo, e a página salta quando o dado chega. `FiSkeleton`
  espelha os papéis de `<app-skeleton>`: a altura de cada forma é a do papel de tipografia que vai
  ocupar o lugar. `desvio_screen` tinha um `_Skeleton` e um `_ErrorState` privados, segunda grafia da
  mesma coisa; saíram.
- **O web ganhou salto para o conteúdo.** Não havia *skip link*: o teclado atravessava cabeçalho e
  navegação inteiros a cada troca de rota.
- **A busca global do mobile tinha uma porta só** — a barra de `/mes/feed`, tela secundária de um
  destino, enquanto no web ela é botão de cabeçalho mais `⌘K` em qualquer tela. Achar um ativo exigia
  saber onde a porta estava. `FiSearchAction` está nos cinco destinos de raiz.

### O que a máquina passou a cobrar

O `lint:ui` foi de 22 para 23 regras, e duas das antigas passaram a rodar de verdade. O
`lint_ui_test.dart` foi de 8 para 11: esqueleto no lugar de disco, busca alcançável de todo destino
de raiz, e falha de leitura numa voz só.

**Nenhuma delas é preferência visual.** Todas protegem o mesmo defeito — a tela que não diz o que
aconteceu — e por isso todas reprovam, em vez de avisar.

---

## O build Android estava quebrado, e a suíte não tinha como saber (2026-09-09)

`flutter build apk --release` falhava em `:sentry_flutter:compileReleaseKotlin` com *"Language
version 1.6 is no longer supported"*. A causa é um encontro de duas datas: o projeto declara
Kotlin **2.2.20**, que removeu o suporte a linguagem abaixo de 1.8, e `sentry_flutter` 8.14.2 fixa
`languageVersion = "1.6"` no `build.gradle` do próprio plugin.

**O que importa aqui não é o erro, é por quanto tempo ele coube no verde.** O CI do mobile era
`flutter analyze && flutter test`, e nenhum dos dois invoca o Gradle: eles rodam sobre Dart. O
produto tinha, ao mesmo tempo, 111 testes passando e nenhum artefato Android possível. Uma suíte
que não constrói o que se distribui mede a metade que não é entregue.

**O primeiro conserto foi um contorno, e ele foi desfeito.** Elevar o piso de linguagem dos
subprojetos abaixo de 1.8, no `build.gradle.kts` da raiz, fazia o APK sair — mas deixava no repo um
remendo cujo defeito estava a um upgrade de distância. `sentry_flutter` **9.29.0** já não fixa
versão de linguagem nenhuma, e uma varredura nos onze plugins Android do projeto não achou outro
que fixe. Sem consumidor, o remendo saiu: o conserto é o upgrade.

**Numa subida de major, a telemetria se confere de novo.** O `before_send` é lista de permissão, e
major é exatamente onde um canal novo de payload entra sem ser pedido — então foram conferidos os
padrões do 9.x: captura de tela, hierarquia de view, replay de sessão e logs estruturados estão
todos **desligados**. A API mudou uma coisa: `SentryEvent.copyWith` foi deprecado porque o evento
passou a ser mutável, e `limparEvento` agora atribui direto.

### O que a passagem encontrou na telemetria do mobile

**Todo build de release se anunciava como `development`.** `APP_ENV` caía num `defaultValue` fixo,
e nenhum build passava `--dart-define`. O painel receberia evento de produção etiquetado como
desenvolvimento — que é a forma de ter telemetria e não ter aviso. Agora o padrão segue o modo do
build (`production` em release), como o web já fazia com `environment.production`.

**A redação cobria breadcrumb e mais nada.** O web redigia `message` e o valor das exceções desde
sempre; o mobile, só a mensagem do breadcrumb. Uma exceção "Quantidade de venda (300) maior que a
carteira (100)" saía com os dois números — que é dado de carteira, o que a Política de Privacidade
promete não sair. Fechado, com teste dos dois lados: a mensagem do evento, o valor da exceção, e os
parâmetros de interpolação descartados, porque parâmetro **é** o valor cru e nenhuma redação de
texto alcança ele.

### A assinatura de release deixou de ser a do template

O `signingConfig` era `signingConfigs.getByName("debug")`, com o TODO do template ainda ao lado: o
APK saía assinado com a chave de debug. A chave de verdade agora vem de `android/key.properties`,
fora do git, e a validação **falha alto** quando o arquivo existe pela metade — campo ausente ou
`.jks` inexistente dizem qual, porque assinar com a chave errada em silêncio é pior que não assinar.

**A fronteira é entre artefato de aparelho e artefato de loja, e a assimetria é de propósito.** O
APK continua caindo na chave de debug quando não há keystore — serve para instalar no telefone, e
`flutter run --release` segue funcionando num clone novo. O **App Bundle** não: sem chave ele para,
porque é ele que vai para a Play Store. A primeira versão disto era um aviso no `logger.lifecycle`,
e ele foi trocado justamente por não aparecer: `flutter build` engole a saída do Gradle, e aviso
que ninguém lê é pior que aviso nenhum — dá a sensação de proteção sem a proteção.

### O CI ganhou o job que enxerga essa metade

`Mobile (build Android)` compila o APK de release a cada push. Ele custa minutos, e é o preço de
não repetir a situação de abrir esta entrada. Duas coisas o tornaram possível: o
`google-services.json` é segredo e não está no repositório, e sem **nenhum** arquivo o plugin do
Firebase interrompe o build — então há um `google-services.ci.json` que não fala com projeto nenhum
e serve só para compilar. Ele também destrava quem clona sem acesso ao Firebase.

---

## A documentação volta a descrever o produto que existe (2026-09-08)

Passagem de verdade em `docs/`, conferida rota por rota contra `app.routes.ts` e `router.dart` — e
ela encontrou mais defeito de produto do que de texto, o que é o argumento contra deixar
documentação envelhecer: ela para de descrever e passa a esconder.

**`FEATURES.md` estava duas revisões de navegação atrás.** Descrevia **Hoje** e **Estratégia**,
que não existem, e não mencionava nenhuma tela do caixa — `/mes`, `/mes/lancar`, `/mes/repetir`,
`/mes/dividas`, `/sobra`. Reescrito inteiro. `ARCHITECTURE.md` tinha o mesmo problema na tabela
rota → componente, e ainda afirmava que "cores, tipografia e réguas semânticas são geradas da
mesma fonte", o que deixou de ser verdade quando o gerador saiu.

**`PARIDADE.md` afirmava que a verificação de contraste acima da norma tinha sido removida.** Foi
— e voltou no commit anterior, porque apagá-la tinha sido erro de classificação. O documento
descrevia o erro como decisão.

### O que a passagem encontrou no código

**A aba do navegador dizia "Carteira" e o `<h1>` dizia "Patrimônio".** O título da rota
`/patrimonio` nunca acompanhou a renomeação do destino.

**Quatro nomes de tela do mobile divergiam do web** — e nome é a parte da paridade que o contrato
exige igual. A barra de `/voce` dizia **"Configurações"**, a de `/sobra/desvio` dizia
**"Estratégia"** e a de `/mes/feed` dizia **"Hoje"**: dois destinos que o produto removeu, ainda
nomeando telas vivas. Mais "Minhas metas" onde o web diz Objetivos, e "Renda Fixa" com F maiúsculo.
Virou regra no Dart, porque nome é literal e literal se confere: `test/lint_ui_test.dart` reprova
tela cujo `AppBar` carregue nome de destino aposentado. Ela achou a de `/mes/feed`, que eu não
tinha visto.

**O carimbo de quando o preço foi lido existia e parava no serviço.** `collectors/universal` sempre
gravou `as_of` no snapshot; `AssetAnalysis` não o declarava, então ele morria na fronteira — a
armadilha do "campo calculado que some em silêncio", ao contrário. E `<app-provenance>` tinha um
campo `asOf` que **nenhuma tela preenchia**, no quarto item de uma gaveta fechada. Momento é nível
1: um preço de anteontem muda a decisão, não a nota de rodapé dela. O campo saiu da gaveta, o
backend passou a mandar o carimbo, e `/ativo/:ticker` diz a idade do preço ao lado do preço nas
duas plataformas. O campo é opcional nos dois clientes, que é o que faz ele atravessar a assimetria
de deploy sem 422.

**O mesmo ativo tinha dois níveis de honestidade em duas telas.** `/ativo` mostrava "consenso de 3
métodos"; `/descobrir` mostrava Bazin cru, sem dizer que Bazin sozinho é um método e não consenso.
`<app-fair-price>` resolve: a cifra não sai sem a base, e a ausência é razão nomeada — "sem
histórico de proventos" e "não se aplica a este tipo de ativo" são respostas diferentes, e as duas
são melhores que um traço.

**A home pública ganhou o argumento que faltava.** Ela já respondia qual é o problema, como o
produto pensa e como começar; não respondia **por que ele não inventa número** — fonte com nome,
estimativa como faixa, julgamento com o que o derrubaria, e as três coisas que ele não faz. E o
`e2e/ssr.spec.ts` passou a conferir o que a página **diz**, não só que ela tem bytes: a seção podia
sair inteira e o teste seguiria verde, porque havia HTML.

**E o documento de operação estava errado sobre produção.** `KNOWN_ISSUES` e `OPERACAO`
afirmavam que o auto-deploy do `main` para produção tinha sido desligado *só na API*, e que a API
subia homologação. Conferido com `get-service-config` nos dois serviços: **os dois sobem produção
direto do `main`, e nenhum espera o CI** (`checkSuites: false` em ambos) — o que o push de
`43f50a4` confirmou, deployando os dois. Duas consequências trocam de sinal: a assimetria
front/back encolheu (commit que toca os dois lados sobe os dois juntos), e o pior caso piorou,
porque no `fiance` o `preDeployCommand` é `python -m app.release` — migração ruim é aplicada antes
de qualquer teste terminar. Documento de operação errado é pior que ausente, porque quem lê age em
cima dele.

**Os nomes de arquivo acompanharam os destinos.** No web, `strategy-shell` → `surplus-shell` e
`strategy.component` → `deviation.component`. No mobile, `features/carteira/` → `patrimonio/`,
`features/hoje/` virou o feed dentro de `mes/`, e `features/estrategia/` se dividiu entre `sobra/`
e `config/`. O compilador é o verificador aqui, então o risco é zero e a confusão que se evita é
permanente.

---

## Tela a tela, depois da fundação (2026-09-08)

A fundação visual trocou de voz no commit anterior. Este é o passe de tela, e ele encontrou mais
defeito de produto do que de aparência.

**`/patrimonio` abria pelo valor, e o veredito ficava na terceira seção.** A tela também se chamava
"Carteira" no `<h1>` e "Patrimônio" na navegação, desde a migração para o ciclo do dinheiro. Agora
abre pelo julgamento, com a régua ao lado — a mesma forma de `/mes` e de `/sobra/aporte`, o que a
paridade chama de hierarquia igual.

**`razoesDaSaude` existia, era testada, e nenhuma tela a chamava.** Foi extraída de `/hoje` quando
`/hoje` se dissolveu e nunca foi religada; `/patrimonio` mostrava `health.warnings` cru no lugar
dela. A diferença é concreta: a função nomeia o papel e o setor que concentram ("PETR4 concentra
18,4% da carteira"), e os campos `top_position_ticker` e `top_sector` já vinham na resposta sem
consumidor. É a armadilha de "vocabulário sem consumidor" na forma inversa — função calculada e
descartada.

**As quatro dimensões da saúde eram uma grade de quatro células, e viraram tabela.** A grade era o
cheiro de painel que o contrato reprova; a tabela ganha uma coluna com o que cada dimensão mede, e
isso dissolve o botão "o que cada dimensão considera" — o significado passa a ser coluna em vez de
divulgação progressiva.

**`/voce/preferencias` era o pior caso do produto.** Seis assuntos sob um título, a cor da mensagem
decidida por `message().startsWith('✓')`, `*ngIf` convivendo com `@if`, um aviso montado à mão ao
lado de um `.notice` na ramificação seguinte, e quatro campos numéricos em `grid-cols-4` **sem
breakpoint** — quatro caixas de 60px em 360px de tela. Virou três eixos nomeados (preço justo,
score de oportunidade, avisos) mais "Esta tela", que é o único que salva na hora e passou a dizer
isso: o formulário tinha dois modelos de gravação sem nenhuma pista de qual era qual.

**A ordem da cascata em `/sobra` eram três cards.** Card é para o que é **objeto** — uma posição,
uma opção de renda fixa. Um passo de uma ordem é passo, e agora é linha numerada sobre fio. Duas
telas também tinham duas cabeças para uma seção só (`app-section` já emite o `<h2>`, e havia um
`<h2 class="fi-title">` logo abaixo).

**A landing não tinha como entrar.** O construtor redireciona quem já está autenticado, e por isso
a ausência de um link para `/login` passou: quem chega pela raiz sem sessão só via o formulário de
interesse. Também caíram seis larguras escritas à mão (`max-w-[52ch]`, `max-w-[34ch]`) em favor da
medida do sistema.

### Duas larguras, e não uma

`--fi-layout-reading-max-width` virou `70ch` na fundação, e isso **quebrou sete telas** — elas
usavam `max-w-reading` como contêiner de página, não como medida de prosa, e uma lista de
oportunidades a 70ch é uma lista estrangulada. O papel estava faltando, não o valor: existe agora
`max-w-column` (1120px) para tela que não é prosa — lista, tabela, gráfico — e `max-w-reading`
volta a significar só a medida do parágrafo.

A coluna do aplicativo caiu de 1600px para 1240px. Em 1600px a cifra de abertura e a linha de
figuras flutuavam sozinhas num monitor comum, e o olho percorria meia tela entre o rótulo e o
número. Tabela larga já rola no próprio contorno, então nada perdeu coluna.

### O controle segmentado entra no sistema

`.subtab-btn` servia de aba **e** de opção escolhida em quatro telas — densidade da tabela, recorte
da composição, período do gráfico, densidade da conta. O mesmo fio da marca dizia "esta é a página
atual" na trilha de seção e "esta é a opção escolhida" numa barra de ferramentas. Agora o escolhido
é um preenchimento (`.segmented` / `.segmented-option`), que não se confunde com aba, e o `lint:ui`
conhece a classe nova.

### A lista de vocabulário proibido virou máquina

`AI-TELLS.md` se declara não-checável por máquina, e para composição e redação isso é verdade. A
**lista de frases proibidas** não é, e a diferença apareceu no lugar mais visível possível:
`login_screen` e `splash_screen`, as duas primeiras telas do aplicativo móvel, abriam com "Ações,
FIIs, BDRs, ETFs e renda fixa — **tudo em um só assistente**". São dois itens da lista numa frase
de dez palavras: o "tudo em um só lugar" de marketing genérico e a persona de assistente
conversacional, que o documento nomeia como *o tell mais específico deste produto*. Passou por
todas as revisões porque nenhuma máquina lia aquele documento.

A regra entrou nas duas plataformas — `lint:ui` no web, `test/lint_ui_test.dart` no mobile — e
varre **só literal de string**, porque varrer o fonte inteiro faria a regra reprovar a própria
justificativa de por que uma frase é proibida. Emoji entra; seta **não**, porque a seta é a
informação em "condição → veredito" e no rótulo de tendência lateral.

E o glifo carregando estado saiu de três telas. `preferencias`, `objetivos` e `conta` decidiam a
cor de uma mensagem por `message().startsWith('✓')` — o símbolo dentro da string era o estado, e a
classe saía de reparsear o próprio texto. Agora é um sinal de `'ok' | 'erro' | null`, e o texto de
erro diz o que continua valendo em vez de só anunciar a falha. Sete setas decorativas em rótulo de
link também saíram: o link já diz que é link.

### O foco na troca de rota falhava em nove telas

`moverFocoParaOTitulo` faz `querySelector('main h1').focus()` a cada `NavigationEnd`, para o leitor
de tela não perder o lugar. Só que `focus()` em elemento sem `tabindex` **não faz nada, e não
avisa** — e nove telas escrevem o próprio `<h1>` em vez de usar `<app-page-header>`, que é quem
traz o `tabindex="-1"`. Nelas o mecanismo estava morto desde sempre, com o teste de navegador
verde, porque medir por seletor não pega isto: a régua é `document.activeElement`.

A correção não foi carimbar `tabindex` em nove templates — foi o shell garantir o próprio alvo,
porque quem devolve o foco é quem sabe que ele precisa ser aceito. Coberto por dois casos em
`e2e/acessibilidade.spec.ts`, com navegação por **clique** e não por `goto`, que é a troca de rota
que o mecanismo existe para cobrir.

### A escala do mobile chega às telas

A fundação recalibrou a escala para 360dp — `body` em 16, e não 15, porque em telefone o corpo
precisa de corpo — e 15 tamanhos escritos soltos ignoravam isso por completo. Foram trocados pelo
papel equivalente: `metricSm` para cifra, `metric` para o score de saúde, `caption` para legenda,
`ticker` para papel, `pageTitle` para cabeçalho de sheet. A catraca de `fontSize:` solto desceu de
**49 para 36**, e o que resta é legenda de gráfico abaixo de 11px, que não tem papel porque a
escala tem piso.

### O contraste voltou ao CI

`check-contrast.mjs` foi apagado junto com o gerador de design, e o CI ficou dois commits **sem
piso de contraste** — enquanto o CLAUDE.md continuava mandando rodá-lo em três lugares. Foi um erro
de classificação: o verificador nunca gerou nada, ele **mede** a paleta escrita à mão das duas
plataformas, nos dois temas, contra o piso do sistema. Voltou como `web/tools/check-contrast.mjs`,
ao lado do `lint:ui`, ligado em `npm run lint:contrast` e no CI.

Com ele volta também a guarda das duas cópias do tema claro do CSS, e por isso a regra que eu havia
escrito no `lint:ui` para a mesma coisa saiu: ela cobria só o CSS, e o verificador cobre o CSS e o
Dart. O `lint:ui` está em 21 regras.

Toda a documentação que descrevia `product-rules.json`, `build-rules.mjs` e `check-parity.mjs` como
presentes foi corrigida — CLAUDE.md, ARCHITECTURE, DESIGN-SYSTEM, INFORMATION-ARCHITECTURE, os dois
README e KNOWN_ISSUES. O CHANGELOG fica como está: é passado, e o passado aconteceu.

---

## O `styles.css` estava certo, e a auditoria estava errada (2026-09-08)

A auditoria de design afirmou que `styles.css` tinha "grafias que se sobrepõem": `.tag` e
`.verdict-pill` seriam "a mesma ideia — uma coisa pequena e rotulada, com cor de estado — em dois
vocabulários", e `.pagination-btn` seria `.btn-secondary` com um estado ativo. A recomendação era
consolidar tudo em `.chip` com modificador.

Medido, quase nada disso se sustenta.

**`.tag` e `.verdict-pill` não são a mesma ideia.** `.tag` tem `radius-sm` e peso 500 e rotula uma
**categoria**; `.verdict-pill` tem `radius-pill` e peso 600 e carrega um **veredito**. A diferença
de forma é exatamente o que a régua dos quatro raios estabelece — `sm` marca, `pill` é outro papel
— e fundir as duas em `.chip` perderia a distinção ou a recriaria como `-pill`, que é renomear e
chamar de consolidação. Ficam como estão.

**Varrendo as 50 classes declaradas contra todo o produto, 48 têm consumidor.** As duas mortas
saíram:

- **`.pagination-btn`** — 8 blocos de CSS, incluindo estados de hover, active, disabled e foco, e
  **zero** usos. A paginação é por cursor keyset e não desenha número de página, então uma pilha
  de botões numerados nunca teve onde aparecer;
- **`.floating`** — era a caixa que flutua (raio `lg` + fio + chão), e o papel passou a ser
  `.card` para o que está assentado, ou o próprio drawer e popover, que trazem a sombra consigo.

`styles.css` foi de 854 para 830 linhas. Vinte e quatro linhas não é o achado; o achado é que a
camada de componentes deste produto **não** virou um segundo framework CSS, que era o risco
declarado. Quatro por cento de código morto em 50 classes é manutenção normal, não dívida.

Vale registrar por que a auditoria errou aqui: ela leu os nomes e a forma dos seletores, e nomes
parecidos sugerem duplicação. O que decide é o **papel** — e papel se descobre contando
consumidores, não lendo CSS. A mesma auditoria acertou onde contou (a proveniência ausente no
mobile, os 49 tamanhos soltos, os redirects relativos) e errou onde inferiu.

---

## O mobile ganha caixa, e a catraca cobra a própria baixa (2026-09-08)

A maior pendência do produto fecha. O web adotou o ciclo do dinheiro em agosto e o mobile ficou
sem as duas telas do topo da navegação: nenhum lançamento, nenhuma sobra, nenhuma dívida. Metade
do produto — `cashflow/`, `cashflow_service`, a régua de dívida, a cascata — sem cliente móvel.

`/mes` e `/sobra` existem, e `DIVIDA_HOJE` do `check-parity.mjs` está vazia.

### A catraca funcionou como catraca

No instante em que as telas passaram a existir, a verificação **reprovou**:

```text
✗ mobile: "mes" está em DIVIDA_HOJE e existe — apague a linha,
  lista de dívida que não encolhe é a documentação mentindo
```

É o comportamento que se queria dela quando foi escrita, e é o que separa uma catraca de um
comentário: ela cobrou a própria baixa em vez de esperar que alguém lembrasse.

### Camada de dados: o contrato inteiro, e não só o que a primeira tela usa

`core/cash_models.dart` declara **todos** os campos de `models/cashflow.py`, inclusive os que
nenhuma tela lê ainda. Campo calculado que o cliente não declara é descartado em silêncio pelo
`fromJson` — já aconteceu sete vezes neste repositório, e nenhuma delas deu erro.

`core/mes.dart` espelha `core/mes.ts`: mesmo conceito, mesmos nomes, implementação de cada
plataforma. Sem `Intl` de propósito — seriam duas fontes para o nome do mês, e o web escreve a
lista à mão.

`core/month_verdict.dart` espelha `core/month-verdict.ts`, e a banda sai de
`fiMonthPressureBands`, gerado de `product-rules.json`. Os limiares são iguais nas duas
plataformas **por construção**, não por disciplina — o que se escreve nos dois lados é a
apresentação. `test/month_verdict_test.dart` roda os mesmos casos do spec do web: paridade de
conceito inclui paridade de verificação.

### As telas usam a forma do telefone, não a do desktop estreito

| Conceito | Web | Mobile |
|---|---|---|
| Linha do tempo do mês | `.data-table`, cinco colunas | lista com disclosure — cinco colunas em 360dp é scroll horizontal que esconde a coluna que decide |
| Lançar | rota `/mes/lancar` | sheet, e volta para onde estava. É a ação mais repetida do produto |
| Trocar de mês | `<select>` no cabeçalho | sheet de meses, e o recorte vive num provider |
| A cascata | subnav com que competir | **sequência vertical** — é onde o mobile ganha do web, porque rolar é o gesto certo para percorrer uma sequência |
| Seção | `<app-section>` → `<h2>` | `FiSection` → `Semantics(header: true)` |

A hierarquia é a mesma: veredito, evidência, atenção, a vencer, o mês. E as regras de UX
atravessaram inteiras — a sobra sai como **faixa**, o veredito vem com `FiProvenance`, e a
cascata que termina sem passo de aporte diz que isso é a resposta certa, em serifa.

O formulário muda de forma pelo `kind`, e isso é regra de domínio: com `income` ele pede um dia
só, o do crédito, porque vencimento é obrigação a cumprir e dinheiro que se recebe não tem uma.
Trocar de `kind` troca a categoria junto — manter a antiga mandaria `moradia` como categoria de
entrada, e o backend recusaria com 422 sem a pessoa entender por quê.

### A regra da faixa nasceu larga demais, e o próprio teste mostrou

Com projeção existindo no mobile, a sétima regra do `lint:ui` passou a ter sujeito. A primeira
versão vigiava `surplus` junto de `portfolioValue` e `passiveIncomeMonthly` — e reprovou o `/mes`
que eu tinha acabado de escrever.

Estava errada a regra, não a tela. "A sobra **parte de** X" nomeia o número como piso, e a faixa
inteira vive na Sobra, onde é o assunto. O escopo ficou o mesmo do web: os dois números que estão
a anos de distância. Vigiar o piso de sobra reprovaria uma frase correta, e regra que reprova o
certo é pior que regra ausente — gasta a autoridade das outras seis.

### Navegação: os cinco destinos, e todo redirect absoluto

A barra inferior passou a ser `Mês · Sobra · Patrimônio · Descobrir · Você`. `/estrategia` se
dissolveu como no web: aporte e desvio foram para `/sobra`, metas para `/voce/objetivos`, renda
fixa para `/descobrir`, projeção para `/patrimonio`.

Todos os alvos de redirect são **absolutos**, pela lição que a produção deu hoje mesmo: alvo
relativo resolve contra o segmento casado e manda o link salvo para lugar nenhum.

Cinco arquivos e os destinos da busca foram religados. Na busca, `Mês` e `Sobra` entraram como os
dois primeiros destinos, e os termos antigos continuam buscáveis — quem procura "hoje" ou
"estratégia" tem de achar a casa nova.

### O caixa do mobile fica completo, e o item fecha

Na mesma passagem entraram as três metades que faltavam, e o item saiu do KNOWN_ISSUES:

**Molde do mês** — prévia e commit, como a importação de extrato. `GET /cashflow/month/template`
lê e não grava; `POST /cashflow/entries/batch` grava o lote inteiro ou nenhum. Vem marcado só o
que repete por natureza; o gasto variável fica **visível e desmarcado**, porque o valor do mês que
passou é fato daquele mês e copiá-lo inventaria despesa. O copiado nasce a vencer, e o que já está
no mês de destino não se oferece de novo.

**Cadastro e quitação de dívida** — o mobile *lia* a dívida e a mostrava em "Exige atenção", mas
não deixava cadastrar: quem só usa o telefone não conseguia declarar a dívida que o veredito
precisa para julgar. O formulário não tem campo "caro": a classe sai da taxa contra o que a
carteira rende, e a taxa é **opcional** com o motivo escrito no campo — sem ela não há classe,
porque o produto não estima taxa de rotativo. A tela vazia diz o que a ausência custa: "a ordem da
sobra começa pela dívida que custa mais do que sua carteira rende".

**Apagar lançamento** — o método estava no repositório e nenhuma tela o chamava. Editar existia;
apagar, não. Entrou no sheet de edição, com confirmação modal porque é destrutivo real, e o botão
diz o que acontece ("Apagar lançamento"), nunca "OK".

E a regra de explicabilidade ganhou um sinal: `DebtClass` é julgamento do sistema sobre o custo da
dívida — "caseira" contra "administrável" — e não estava na lista. Com ela dentro, a tela de
dívidas precisa da proveniência que já tem; sem, a regra deixava passar exatamente a tela que
classifica dinheiro alheio. Provado quebrando de propósito.


---

## As regras de produto passam a rodar no Dart (2026-09-08)

O defeito das máquinas deste produto era **geográfico**: 22 regras no web, nenhuma no mobile. A
consequência era medível e sempre na mesma direção — todo princípio que o web cobra por máquina,
o mobile não embarcava.

`mobile/test/lint_ui_test.dart` leva cinco delas para lá. Vive como **teste**, não como script
próprio, porque `flutter test` já é o comando do CI: uma regra que exige mexer na esteira para
rodar é uma regra que não roda.

| Regra | O que cobra |
|---|---|
| Explicabilidade | Arquivo em `features/` que coloca um número numa faixa nomeada (`scoreBand`, `fiBandFor`, `fiDecision`, `fairPrice`) precisa de explicador |
| Promessa sobre o futuro | Mesma lista do web; a negação explícita passa, a afirmação não |
| Nome acessível | `IconButton` sem `tooltip:` nem `Semantics` |
| Serifa no veredito | `FiType.verdict` sem `fiFontSerif`/`fiSerif` |
| Tipo solto | Catraca em 49 linhas com `fontSize:` literal |

Cada uma foi provada quebrando o código de propósito e conferindo que reprova. **A catraca não
reprovou na primeira tentativa** e isso era o defeito dela: o teto estava em 65, que era a
contagem de *ocorrências*, enquanto o teste conta *linhas* — 49. Teto folgado não é catraca, é
decoração. Ajustado, e a camada de design (`design_tokens.dart` e `theme.dart`) ficou de fora,
porque é ali que tamanho se declara.

### Três coisas que as regras acharam de imediato

**A tela "onde aportar" não explicava nada.** `quick_invest_view` mostra a ordem de aporte com o
score de cada ativo numa faixa nomeada, e é o julgamento mais consequente do produto — onde pôr
dinheiro. Zero explicador. Ganhou `FiProvenance` dizendo o método (compara alocação atual com as
metas e distribui no que está mais abaixo do alvo, com o score como desempate), a fonte, e a
limitação que importa: **é ordem de prioridade, não recomendação de compra**.

**Dois botões de apagar anunciavam só "botão".** O de apagar alerta em `config_screen` e o de
remover título da comparação em `tools_views` não tinham `tooltip`. É exatamente o caso que a
regra do web cita — "a pessoa tem que adivinhar se aquilo apaga a posição ou fecha o modal" — e
aqui os dois *apagavam*.

**Um falso alarme, que vale registrar.** A auditoria de manhã apontou `FiType.verdict` sem serifa
em `estrategia_screen.dart:65`. Não era: a família vinha na linha seguinte, dentro do `.copyWith(`.
A regra por isso olha uma janela de quatro linhas, não a linha isolada — e os quatro usos do papel
de veredito estão corretos.

### O explicador do glossário sai de 14px e ganha semântica

`HelpTooltip` era um `GestureDetector` sobre um ícone de 14px: sem `Semantics`, portanto invisível
ao TalkBack, e com alvo de toque abaixo dos 44 que `FiLayout.minTouchTarget` declara no arquivo ao
lado. Virou `InkWell` com `Semantics(button: true, label:)` e alvo de 32.

**32, e não 44, de propósito.** O gatilho vive num `Row` ao lado de um rótulo de 11px, e 44 de
altura dobraria a linha inteira. Chegar aos 44 é repensar aquela linha — fazer o rótulo todo ser o
alvo, em vez de pendurar um ícone ao lado dele — e isso é decisão de layout, não de
acessibilidade. Fica no KNOWN_ISSUES, junto da regra que só faz sentido escrever depois dela.

### O contrato de link salvo, conferido de ponta a ponta

Com o acesso à rede restabelecido, os **24 redirects** foram conferidos em produção, sem
JavaScript: todos respondem 302 para o destino declarado, e todos os 17 destinos respondem 200. O
defeito dos alvos relativos está fechado onde importa, que é no ar.

---

## Sobra tinha seis subseções, e duas não eram sobra (2026-09-08)

Segunda passagem da auditoria de design, agora na arquitetura de informação. Seis pares num subnav
não são hierarquia — são uma lista — e duas das seis de `/sobra` respondiam pergunta de outro
destino.

| Saiu de | Foi para | Por quê |
|---|---|---|
| `/sobra/metas` | `/voce/objetivos` | **Declarar** um objetivo é armar a estratégia; **ler** a distância até ele é leitura de sobra e de patrimônio. A declaração passa a ter uma casa, a leitura continua nas duas |
| `/sobra/projecao` | `/patrimonio/projecao` | "Aportando assim, onde eu chego" é pergunta de patrimônio |
| `/sobra/renda-fixa` | `/descobrir/renda-fixa` | Comparar títulos à venda é descoberta — e sem isso metade das aplicações do produto não tinha porta de entrada, embora renda fixa seja entidade de primeira classe no backend desde sempre |

`/sobra` ficou com os **três passos de uma decisão só**: A ordem, Aporte, Alocação × meta.

`/patrimonio` receberia Projeção e viraria uma lista de sete. Em vez disso, Posições, Encerradas e
Proventos passaram a ser um **grupo**: são três leituras do *mesmo* razão, e agrupá-las diz uma
verdade da arquitetura em vez de esconder o número de itens. `SectionNavItem` ganhou um `group`
opcional, e o subnav desenha o grupo com um fio e um rótulo em `fi-eyebrow` — nenhum papel visual
novo, e nenhum terceiro nível de URL, que é o sintoma de IA errada.

`/voce` ganhou `Objetivos` como eixo. Não ficou nos quatro eixos do desenho porque Estratégia
(perfil, yield, alocação-alvo) está dentro de Preferências e separá-la exige partir o componente,
não mexer em rota — está no KNOWN_ISSUES.

**Toda URL que mudou de casa continua resolvendo, num salto só.** As três de `/sobra` viraram
redirect dentro do próprio shell, e as de `/estrategia/*` passaram a apontar direto para o destino
final em vez de saltar duas vezes. Cinco componentes e a busca global foram religados para as
rotas canônicas; na busca, o rótulo e a seção acompanharam a casa nova e o termo antigo continua
buscável — quem procura "metas" acha `Objetivos`.

O teste que guarda isso reprovou na hora, e foi um bom sinal: `app.routes.server.spec.ts` afirmava
`estrategia/metas → sobra/metas`. Ganhou um caso irmão que cobra os redirects novos **e** que
`/sobra` tenha exatamente os três passos — a primeira versão comparava a lista em ordem, que não é
contrato, e foi corrigida para comparar como conjunto.

`INFORMATION-ARCHITECTURE.md` é declarado a autoridade da navegação, então foi atualizado junto,
com um inventário da forma corrente de cada destino. Documento de design responde *como a interface
deveria ser*; o histórico é este arquivo.

### Todo redirect de dois segmentos do produto estava quebrado

Achado ao conferir em produção para onde os links antigos iam de fato — que é diferente de ler o
que a rota declara. `redirectTo` **relativo** resolve contra o primeiro segmento do caminho
casado, então:

```text
/carteira/posicoes  -> /carteira/patrimonio/posicoes   (não existe)
/hoje/atividade     -> /hoje/mes/atividade             (não existe)
/estrategia/aporte  -> /estrategia/sobra/aporte        (não existe)
```

Todos caíam no curinga e levavam a `/mes`. Quem tinha um link salvo para a tabela de posições
abria o mês e não entendia por quê — e "link salvo é contrato" é invariante escrito deste
repositório. Valia para os oito redirects de dois segmentos; os de um segmento (`/carteira`,
`/hoje`) funcionavam por acidente da resolução, o que é pior, porque dava a impressão de que o
bloco todo funcionava.

Não veio da mudança de hoje: já era assim desde a migração dos cinco destinos. **O teste
comparava a string declarada e nunca a resolução**, então passava verde com o contrato quebrado
em produção. É o modo de falha mais caro que uma verificação pode ter: dar confiança onde não há.

Os 24 alvos de topo — mais o próprio curinga — passaram a ser absolutos, e o teste ganhou um caso
que reprova qualquer `redirectTo` de topo que não comece com `/`. Os dois relativos que sobram são
os `''` de dentro dos shells, onde relativo é o certo. Conferido depois do deploy: os seis links
antigos chegam ao destino declarado, sem JavaScript.

### O auto-deploy para produção estava desligado só na metade

Conferido contra o Railway com um push real: o serviço `fiance` (API) sobe **homologação**, como
o `OPERACAO.md` descreve — mas o `fiance-web` sobe **produção** em todo commit que toque
`web/**`. O front não tem serviço em homologação, então não tem para onde ir a não ser produção,
e é onde mora toda a interface. A tranca de "promover, olhar, e só então promover" protegia a
metade do sistema que muda menos.

E o achado pior veio ao ler a configuração do serviço, não os deploys: **`checkSuites` está
`false`**. O front de produção sobe sem esperar o CI — um commit vermelho que toque `web/**` vai
ao ar antes de qualquer teste terminar. É o conserto de um clique, e é o primeiro da lista.

E o fluxo de promoção do `deploy.yml` **não está utilizável**: os environments do Actions
(`staging`, `production`) não existem — o que a API do GitHub lista é `fiance / production` e
`fiance / staging`, criados pelo Railway, que são outra coisa — e `RAILWAY_TOKEN` não está
configurado, então o `workflow_dispatch` para com a mensagem de token ausente em vez de promover.

O `OPERACAO.md` afirmava as duas coisas resolvidas. Corrigido, com as duas saídas escritas, e
registrado no KNOWN_ISSUES.

---

## A paridade deixa de ser de valor e passa a ser de conceito (2026-09-08)

Uma auditoria de design leu as duas plataformas e achou a assimetria que organiza todo o resto:
**os 176 valores de cor espelhados à mão entre `foundation.css` e `design_tokens.dart` não tinham
uma única divergência — e o mobile não tinha `/mes` nem `/sobra`**, as duas telas no topo da
navegação do web. Metade do produto sem cliente móvel, com `docs/ARCHITECTURE.md` afirmando que o
shell do mobile espelhava os destinos do web.

A camada que estava sendo mantida com disciplina perfeita era a que menos carregava significado.
O gerador removido em agosto resolvia o problema errado, e o espelho escrito à mão que o
substituiu herdou o mesmo escopo errado.

### O padrão: todo princípio é cobrado por uma máquina que só roda no web

| Princípio | Web | Mobile |
|---|---:|---:|
| Explicabilidade em julgamento renderizado | 15 | **0** |
| Serifa carregando conclusão | 20 | 3 |
| Tamanho de tipo escrito solto, fora dos papéis | 0 | **65** |

A última linha é a doença que este arquivo registra como curada no web — "384 utilitárias de
tamanho conviviam com 372 papéis". A cura foi uma regra de lint, a regra só roda no web, e a
doença segue no mobile na mesma proporção. O defeito das máquinas deste produto é **geográfico**.

### O contraste passa a medir as duas plataformas, cada uma contra o piso

`check-contrast.mjs` lia só `foundation.css`, e dentro dele só a cópia do tema claro que está no
atributo — decisão documentada, e que deixava **44 papéis sem guarda**: quem editasse a consulta
de mídia e não o atributo quebrava o contraste de quem está no padrão do sistema, que é a maioria,
sem nenhuma máquina reclamar. Agora ele lê os três blocos e exige que as duas cópias do claro
sejam idênticas.

E passou a ler `design_tokens.dart` também — **contra o piso, não contra o web**. Isto é o que
permite o mobile divergir de propósito: um telefone sob sol pode precisar de mais contraste que um
monitor, e exigir o mesmo hexadecimal impediria a correção. O contrato virou "cada plataforma é
legível e completa", não "as duas são idênticas". É verificação, não geração — e por isso não
reintroduz o gerador por outra porta.

### `check-parity.mjs`: a única automação nova, e a justificativa é empírica

Ela responde uma pergunta só: os cinco destinos existem nas duas plataformas? Não compara
aparência, não compara valor, não gera nada. Existe porque a resposta já foi *não* por meses, e
porque a revisão humana falhou justamente nela.

Rodou pela primeira vez e achou uma terceira divergência que a auditoria tinha subestimado: o
mobile chamava o destino de `/carteira` enquanto o web já o chamava de `/patrimonio`. Renomeado,
com `/carteira` seguindo como redirect — link salvo é contrato.

O que sobra é dívida registrada em `DIVIDA_HOJE`, no padrão de `SEM_MODELO_HOJE`: não conserta
hoje, não deixa crescer, e **só encolhe**. Um item da lista que passe a existir reprova, porque
lista de dívida que não encolhe é a documentação mentindo de novo.

### A seção era uma classe, e classe não obriga cabeçalho

`/mes` — a primeira tela depois do login — tinha **cinco seções e nenhuma parada de navegação**
abaixo do título. `/ativo/:ticker`, a página mais importante do produto, tinha oito seções e um
`<h2>`. Os títulos eram `<p class="fi-eyebrow">`: "Valuation", "Fundamentos", "Tendência" e
"Proventos" eram parágrafos.

A regra de lint não pegava, e não era bug dela — `ordemDeCabecalho` verifica que níveis não sejam
pulados, e uma página com zero `<h2>` passa trivialmente. O que faltava era uma regra de
**presença**, e a correção proporcional não era uma regra: era um componente. `.fi-block` é uma
classe, então a seção do sistema era um *acordo* ("use `.fi-block` e ponha um eyebrow dentro"), e
acordo não é verificado.

`<app-section title="…">` emite o `<h2>`, e as 15 seções migradas se corrigiram por construção,
sem nova regra e sem redesenhar tela nenhuma. O papel visual continua `fi-eyebrow` de propósito:
a correção aqui é semântica, e mudar a aparência de toda seção do produto no mesmo commit
misturaria duas decisões. `.fi-block` fica no host do componente, não num `<section>` interno,
senão `.fi-block:first-child` passaria a olhar o wrapper.

Sobreviveram como `<p>` os eyebrows que são **rótulo de valor**, não título de seção — "Livre
agora", "Aplicado", "Valor da carteira". A distinção é a regra: eyebrow rotula uma cifra, título
nomeia uma seção. E os dois `<nav class="fi-block">` de `/patrimonio` mantiveram o landmark e
ganharam o cabeçalho, em vez de trocar um pelo outro.

### `/mes` passa a julgar, e a ordem para de inverter importância

A tela perguntava "como estou agora, e o que exige atenção?" e respondia com `free_now` em corpo
grande. Não havia veredito: o produto interpretava patrimônio, ativo, dívida e alocação, e
entregava o mês como extrato.

O veredito é `monthPressureRuler` — sexta leitura da mesma régua, gerada para as duas plataformas
como as outras cinco. Os limiares são escolha de apresentação, no mesmo precedente do
`healthRuler`: o backend devolve `committed` e `received` sem faixas, e a razão entre os dois é
aritmética, não regra nova. **Não** virou uma função de limiar em TypeScript, que seria regra de
negócio no cliente.

Sem entrada lançada a banda é a de leitura ausente: dividir por zero daria 0% e "Mês folgado" para
quem não lançou nada. Dívida caseira não muda a banda — a régua mede pressão do mês, e
`class === 'expensive'` já é julgamento do backend sobre outra coisa — mas assume a razão, porque
um mês folgado com dívida a 14,9% ao mês não é um mês resolvido.

E "O que mudou" foi para o fim. Um feed vinha antes de "Exige atenção", que é dívida com taxa
mensal nomeada.

### A régua de saúde do mobile tinha duas versões, e elas se contradiziam na mesma tela

`hoje_health.dart` tinha `fiHealthBandLabel` escrita à mão com limiares 70/40, ao lado de um uso
correto de `fiBandFor(score, fiHealthBands)`, que é a régua gerada em 75/60/40. A mesma classe
usava a gerada para a **cor** e a escrita à mão para o **rótulo**: um score de 65 saía favorável
na cor e "Atenção" no texto.

O score de saúde passou a ler a banda gerada. A função à mão virou `fiDimensionBandLabel` e ficou
só para as quatro dimensões, que são outro número e não têm faixa do backend — e ela compartilha
os limiares com a cor da própria dimensão, que é por que as duas andam juntas.

### Proveniência embarca no mobile

"Julgamento renderizado exige explicabilidade" é invariante deste repositório, o `lint:ui` o cobra
no web, e no mobile ele simplesmente não existia: nove telas renderizavam score, veredito ou preço
justo sem como conferir a conta. O que havia era um `HelpTooltip` de glossário em três pontos —
um `GestureDetector` sobre um ícone de 14px, abaixo do mínimo de toque declarado no arquivo ao
lado, e sem `Semantics`, portanto invisível ao TalkBack.

`FiProvenance` carrega os mesmos quatro campos do web — método, fonte, momento, limitação — em
forma nativa: no web é uma gaveta `<details>`, aqui é um sheet, porque no telefone o que se abre
para conferir volta para onde estava. É o contrato de paridade funcionando: mesmo conceito, forma
de cada plataforma.

### Os tokens de desktop saem do aplicativo

`design_tokens.dart` carregava `readingMaxWidth: 1120`, `denseMaxWidth: 1600`, `drawerWidth: 600`,
`subnavWidth: 200` e um `FiBreakpoint` que ia até `desktopLg: 1440`. Zero consumidores, todos —
um telefone não tem subnav. `fiTypeFamily`, um mapa de string para string, também tinha zero.

`FiDensity` era o caso que doía: densidade é preferência da conta no web, o enum estava declarado
com os dois níveis e os três valores certos, e **nada no mobile o lia**. É a armadilha do
"vocabulário gerado sem consumidor" viva no espelho escrito à mão — o gerador saiu, e a *forma*
que ele impunha ficou. No telefone a régua equivalente pertence ao sistema operacional, e é de lá
que ela deve vir.

Ficou `minTouchTarget: 44`, que é norma de acessibilidade e não aparência.

### O lint: 23 regras viram 22, e duas passam a avisar

A leitura fácil era "são muitas regras". Não eram: cinco formas de escape estavam declaradas, três
eram usadas, e o total de escapes no produto era **oito**. Um conjunto que quase não é escapado
está calibrado, não inflado. Nenhuma regra foi removida.

As duas de camada eram uma falha só — `z-[201]` e `z-50` erram igual, e os dois reabrem a ordem de
empilhamento a cada tela. Uma regra, uma mensagem.

Raio fora da escala e ícone decorando título passaram a **avisar sem reprovar**. Quatro raios é
preferência bem fundamentada, não erro silencioso; e a regra de ícone mantém lista de exceção por
nome de arquivo, que é revisão com passos extras disfarçada de regra. Bloquear o CI por gosto
gasta a autoridade das dezesseis que valem. Descobriu-se no caminho que `rounded-xl` já era pego
pela regra de classe não emitida — o tema só emite quatro raios — então a regra de raio era em
boa parte redundante.

Os cinco escapes viraram um: `<!-- design-exception: regra — motivo -->`. Nomear a regra mantém o
escape estreito (escapar de cabeçalho não escapa de contraste) e exigir o motivo mantém a exceção
visível. O objetivo nunca foi impedir exceções; é impedir exceção invisível.

### A busca dentro da página de ativo sai, e `/ativo` sem ticker vira redirect

Havia um campo de busca no fim de `/ativo/:ticker`, em paralelo à busca global — e o próprio bloco
dizia isso ao leitor ("a busca do topo procura em qualquer tela"). Camada contextual se entra pelo
contexto e se sai para ele. Com ele saíram o formulário, o `search$`, as sugestões e quatro
métodos; `retry()` passou a ler o ticker da rota.

A rota `/ativo` sem ticker era sustentada por esse campo — sem ele não havia como usá-la. Virou
redirect para `/descobrir/oportunidades`, que é o destino de quem quer achar um ativo.

O `<h1>` da página era `fi-money-lg`, o papel de **cifra**, sobre um ticker. A auditoria prescreveu
`fi-ticker`, e a prescrição estava errada: `fi-ticker` tem 14px, e um `h1` desse tamanho
reintroduziria o defeito que este arquivo já registra ("com 15px de `h1` a página não tinha
primeiro nível"). Ficou `fi-page-title`, que é o papel do título de uma tela.

### Documentação: quatro caminhos mortos que ainda instruíam

`README.md` mandava rodar `node design-tokens/build.mjs`, que não existe desde agosto, descrevia
os cinco destinos com os nomes antigos e trazia contagens de teste de 724/90/49.
`docs/design/README.md` tinha uma seção "Tokens" inteira instruindo editar `tokens.json` — "uma
fonte, três alvos", exatamente a arquitetura que foi abandonada. `web/tailwind.config.js` apontava
para três caminhos mortos, incluindo um `docs/design/06-DESIGN-SYSTEM.md`.

O contrato de paridade virou documento: `design/PARIDADE.md` (removido em 2026-09-11, quando
sobrou uma plataforma). Este arquivo
ficou intacto: aqui `tokens.json` é narrativa do que era verdade na época, e história não é
pendência.

---

## O mês vira editável, e o caixa deixa de ser digitado em dois lugares (2026-09-07)

Cinco correções vindas do uso, todas na mesma superfície: o mês.

### O `<h1>` recebia foco a cada rota — e desenhava anel de controle

Toda tela abria com o título aparentemente selecionado, e o destaque voltava a cada retorno para a
aba. O foco programático no título **fica**: é o que impede quem usa leitor de tela de perder o
lugar quando a rota troca. O que não devia ficar era o desenho. O `<h1>` tem `tabindex="-1"`, está
fora da ordem de tabulação e não é operável pelo teclado, então o anel ali não indica onde a tecla
vai agir — indica onde a rota pousou, que é informação para o leitor de tela, não para o olho.
A WCAG 2.4.7 pede indicador em componente **operável**; um título de pouso não é um.

A primeira guarda que escrevi passava sem o conserto: media `main h1` por seletor, e o elemento
com foco era outro. Medir `document.activeElement` mostrou `outline: auto 1px` já na abertura, e
com a régua certa a guarda reprova com a mensagem certa.

### Caixa sai de Preferências: preferência é o que persiste

`cash_available` era um número digitado à mão em Preferências e lido pela Estratégia. Com o módulo
de caixa, a mesma pergunta — *quanto tenho para aportar?* — passou a ter duas respostas, e a
digitada envelhece sem avisar: distribuir dinheiro que já foi gasto é pior que não responder.

O campo saiu da tela. A Estratégia pergunta ao caixa (`available_to_invest` da cascata, que já é o
que sobra **depois** da dívida cara e da reserva) e diz de onde o número veio. A coluna continua
existindo como último recurso — para quem ainda não lançou nenhum mês, o valor informado ao
distribuir um aporte é melhor que zero —, mas aparece rotulada como informada, não como derivada.

### Editar um lançamento

Só havia lançar, marcar como paga e apagar. Errar o valor obrigava a apagar e relançar, o que muda
o id e perde a ordem. `PUT /cashflow/entries/{id}` e o mesmo formulário em modo de edição, com o
id na URL (`/mes/lancar?editar=12`). Provento não é editável ali: ele vem do razão, e é lá que se
corrige — editar no caixa criaria segunda verdade sobre o mesmo dinheiro.

### Entrada não tem vencimento

O formulário pedia vencimento e dia do pagamento para **entrada**, e vencimento é obrigação a
cumprir — dinheiro que se recebe não tem uma. Com tipo `entrada`, o campo vira um só, "Dia", e é a
data do crédito. A distinção entre recebido e a receber continua, no mesmo interruptor de sempre.

### O mês anterior como molde

`GET /cashflow/month/template` lê um mês como molde do outro, sem gravar nada; `POST
/cashflow/entries/batch` grava o lote inteiro ou nenhum. Prévia e commit, como a importação de
extrato — meio molde de mês é pior que molde nenhum, porque a pessoa não teria como saber o que
entrou e o que ficou de fora.

Três decisões dentro do molde:

- **Vem marcado só o que repete por natureza** — o fixo, a dívida e o salário. Gasto variável fica
  desmarcado e visível: o valor do mês que passou é fato daquele mês, e copiá-lo inventaria
  despesa. Décimo terceiro e férias também não repetem: acontecem uma vez no ano.
- **O copiado nasce a vencer**, nunca pago. Copiar o pagamento junto diria que o dinheiro se moveu
  num mês que ainda não aconteceu.
- **A identidade que evita duplicata ignora o valor** (tipo, categoria e descrição). A conta de luz
  muda de valor todo mês; se o valor entrasse na identidade, o molde ofereceria a mesma conta de
  novo.

O dia viaja para o mês de destino preso ao último dia quando o destino é mais curto — 31/01 vira
28/02, ou 29 em ano bissexto.

### A régua do contrato de rotas só olhava o 200

`tests/contrato_das_rotas.py` lia a resposta `200` de cada rota, e escrita responde `201`. Toda
rota de criação ficava sem contrato nenhum, e a catraca `SEM_MODELO_HOJE` contava isso como
normal. Consertada a régua — lê a primeira resposta 2xx —, seis rotas que já tinham `response_model`
entraram no registro e a catraca caiu de 51 para 45.

---

## `cashflow/` nasce, e as duas perguntas pendentes viraram decisão (2026-09-07)

Começo da Fase 3 do [ROADMAP](produto/ROADMAP.md): o módulo de caixa, como
matemática pura e irmão de `ledger/` — não sabe que existe banco de dados. Quatro arquivos:
o lançamento e o vocabulário fechado, a projeção do mês, a régua de dívida, e a cascata.

### `provento` no caixa: o caixa **lê** o razão

Das três saídas possíveis, é a única que não cria segunda verdade — e é a mesma forma que o
produto já usa duas vezes (a posição é projeção do razão; a apuração de IR também). O que **não**
se fez foi deixar a regra numa convenção de camada de serviço: ela vive no tipo. `CashEntry`
recusa categoria `provento` sem `derived=True`, e recusa `derived` em qualquer outra categoria.

`cashflow/` continua não importando `ledger/`: a leitura derivada é da camada de serviço, que é
quem tem os dois lados. Os módulos puros seguem independentes, como `analysis` e `optimizer`.

E `provento` e `reembolso` entram no caixa mas **não** entram na base de renda. Provento não se
repete por contrato e reembolso é dinheiro que voltou, não dinheiro que se ganhou — somá-los à
renda recorrente inflaria a projeção do mês seguinte.

### Reserva de emergência: depois da dívida cara, e só com alvo declarado

A ordem tem argumento: a reserva existe para a pessoa **não precisar tomar** dívida cara. Quem já
tem a dívida não precisa se proteger do risco de contraí-la — pagá-la é o mesmo ato, com retorno
garantido igual à taxa. Poupar a juros de poupança enquanto se paga 14,9% ao mês é perder nas duas
pontas.

E o alvo é **declarado**, em meses do próprio gasto fixo da pessoa, que o caixa agora conhece. O
produto não inventa seis meses: número de mercado solto é exatamente o que a régua de dívida
proíbe. Sem alvo declarado, ou sem mês fechado para medir o gasto fixo, o passo simplesmente não
existe — a mesma disciplina de dívida sem taxa.

### O que os testes provaram, e o que corrigiram

Trinta e sete testes novos, e dois achados:

**O wireframe tinha um número inventado.** Ele trazia um teto de sobra de R$ 1.984,32; a
matemática, rodando sobre o mesmo histórico, derivou R$ 1.788,19. O documento se corrigiu — número
em wireframe que o código contradiz é segunda verdade, e envelhece calado. O piso, o
R$ 1.647,32, fechou exatamente como desenhado, e há um teste que confere a soma inteira: dívida +
ordens em cota inteira + o resto que fica abaixo da ordem mínima.

**Uma guarda minha era inalcançável.** `derived` com saída nunca poderia disparar, porque
`provento` só existe em entradas e a checagem de categoria vem antes. Saiu: guarda que não pode
falhar é ruído que parece proteção.

A régua de dívida tem um teste que é o resumo dela: o **mesmo instrumento** muda de classe com a
taxa. Se o tipo decidisse, consignado a 0,4% e a 3,5% sairiam iguais.

---

## O mês desenhado, o vocabulário decidido, e duas perguntas que bloqueiam a Fase 3 (2026-09-07)

Fecha a Fase 2 do [ROADMAP](produto/ROADMAP.md).

### `/mes`: duas telas não podem liderar com a mesma cifra

A [IA nova](design/INFORMATION-ARCHITECTURE.md) já havia recusado o sexto destino `/dinheiro` por
criar "dois resumos rivais". `/mes` e `/sobra` correm o mesmo risco: se as duas liderarem com
"quanto sobra", a segunda é decoração da primeira.

A separação ficou por **natureza do número**, não por recorte de assunto. A cifra de `/mes` é
**fato** — livre agora: o que entrou, menos o que saiu, menos o que já está comprometido e datado.
A de `/sobra` é **projeção** — o mesmo número, menos o gasto variável ainda esperado. E a
diferença entre as duas **é exatamente a estimativa**, o que dá uma frase que liga as telas sem
repetir nada: *"livre agora R$ 2.047,32; descontando o que ainda deve sair, a sobra parte de
R$ 1.647,32"*.

Consequência: `/mes` não carrega faixa, porque fato não tem faixa. A faixa nasce em `/sobra`,
junto com a estimativa que a cria. Um número que às vezes é fato e às vezes é projeção seria a
pior das duas coisas.

A ordem dos blocos é por **custo de não ver**, não por assunto: `Exige atenção` (a dívida a 14,9%
ao mês) vem antes de `A vencer` (a conta de dois dias), e as duas antes da linha do tempo. E
`hoje` é uma divisa desenhada dentro de uma lista só — duas listas escondem a coisa mais útil de
um mês, que é a **sequência**: o salário cai no dia 5 e o aluguel sai no mesmo dia.

### O vocabulário do caixa: decidido, e de propósito não gerado

Dez categorias de despesa, seis de entrada, sete tipos de dívida, em
[DESIGN-SYSTEM](design/DESIGN-SYSTEM.md#o-vocabulário-do-caixa--decidido-ainda-não-declarado). Não
entrou em `product-rules.json`, e é decisão: o CLAUDE.md registra que vocabulário gerado sem
consumidor é pior que não gerado, porque *parece* resolvido — `fiTiposDeRendaFixa` e `fiLiquidez`
já custaram isso. A entrada acompanha o commit que constrói a primeira tela que a consome.

**O tipo de dívida deliberadamente não carrega se ela é cara.** A
[regra](produto/REGRAS_DE_DOMINIO.md#dívida) manda classificar por **custo, não por
tipo**, e um campo `caro: true` no vocabulário faria o código classificar por instrumento —
consignado a 1,2% ao mês e consignado a 3,5% ao mês não são a mesma decisão. Cara e administrável
são derivadas da taxa contra o que a carteira rende, e sem taxa informada não há classe.

### Duas perguntas de domínio que bloqueiam `cashflow/`

Ficam declaradas em vez de decididas na surdina, porque as duas mudam o módulo:

**`provento` no caixa.** Provento creditado é entrada de caixa **e** lançamento do razão — e o
razão já é a fonte da carteira. Sem regra, o mesmo dinheiro conta duas vezes: infla a renda do mês
e a sobra junto. Três saídas possíveis, e só uma não cria segunda verdade — o caixa **lê** o
razão, e a entrada é derivada, não lançada. É também a que acopla os dois módulos, e por isso é
decisão, não detalhe.

**Reserva de emergência.** Não é passo da cascata da `Sobra` porque não há decisão sobre quantos
meses, contra qual base, e antes ou depois da dívida cara.

---

## A ponte desenhada, e o critério que diz se ela existe (2026-09-07)

O portão da Fase 3 do [ROADMAP](produto/ROADMAP.md): a tela de `Sobra`, em
[WIREFRAMES](design/WIREFRAMES.md#n1-sobra--a-ponte).

**O achado que orientou o desenho** foi comparar o Quick Invest construído com o wireframe dele.
O wireframe dizia *"três campos, uma resposta, a lógica atrás de um acordeão — a tela mais curta do
produto"*; o que existe abre com um parágrafo explicativo, dois checkboxes e um botão "Gerar
Sugestão". Ela **pergunta** em vez de responder, e a primeira pergunta — *"quanto você quer
aportar?"* — é justamente a que a ponte torna desnecessária: a pessoa responde de cabeça, uma vez
por mês, com o número errado, porque a sobra mora em outro app.

Daí sai o critério de aceite, que ficou escrito na tela: **se em algum estado ela voltar a pedir o
valor do aporte a quem tem caixa lançado, a ponte não está construída** — está desenhada em cima
da mesma lacuna.

Quatro decisões de projeto, e duas delas são de domínio, não de layout:

**A ordem é o produto.** A tela não mostra "sua sobra e onde investir": mostra uma cascata em que
cada passo consome parte da sobra e declara o que o derrubaria. É a
[regra de dívida](produto/REGRAS_DE_DOMINIO.md#dívida) renderizada, com a comparação
contra o que a carteira **da pessoa** rende. Consequência aceita: a tela pode terminar dizendo
*não aporte este mês*, e isso é sucesso dela — um destino chamado `Aporte` não conseguiria dizer
isso, e é por isso que ele se chama `Sobra`.

**A cifra grande é o piso da faixa, e o aporte se calcula sobre ela.** Por assimetria de erro:
comprar cota com dinheiro que talvez não chegue custa vender no prejuízo ou atrasar uma conta,
enquanto aportar menos custa um mês de rendimento. O excedente vira um bloco N3 — não some, e
também não é gasto antes de existir.

O exemplo da tela é o **mesmo mês da landing** (salário de R$ 6.418,73, sobra de R$ 1.647,32),
recortado no dia 20, com parte realizada e parte projetada. E ele fecha na conta: R$ 890,00 de
dívida + R$ 464,40 + R$ 197,00 de ordens em cota inteira + R$ 95,92 que ficam abaixo da ordem
mínima = R$ 1.647,32. Um exemplo de produto que não fecha é o tell que o
[AI-TELLS](design/AI-TELLS.md) chama de valor redondo demais; a primeira versão deste wireframe
tinha exatamente esse defeito e foi refeita.

Oito estados estão especificados, e os quatro que mais importam são os de **ausência**: sem caixa
lançado a tela vira o Quick Invest e **diz por que está pedindo o valor**; com sobra negativa a
cascata não aparece; sem dívida cadastrada o passo 1 não existe, sem convite nem placeholder; e
dívida sem taxa informada não vira régua, porque o produto não estima taxa de rotativo.

**O que ficou aberto, declarado:** a reserva de emergência não é um passo da cascata, porque não
há decisão de produto sobre ela — quantos meses, contra qual base, e antes ou depois da dívida
cara. Uma ponte caixa→investimento sem esse passo é discutível, e a pergunta é de produto, não de
design.

---

## O sistema de design refeito, e as duas queixas que viraram número (2026-09-07)

A direção veio em duas frases: *"o gerador de tokens e as automações no design limitaram muito"*
e, da rodada anterior, *"botão que não parece ser botão. Barra de progresso que não deixa evidente
o progresso"*. As duas estavam certas, e nenhuma pelo motivo que parecia.

### `tokens.json` era dois arquivos num só

Metade dele era design, e o schema fechava o vocabulário: doze papéis de tipo, quatro raios, duas
sombras, e **nada para estado de interação**. Não havia como declarar contorno de controle,
preenchimento pressionado ou poço de barra, porque o gerador não tinha essas chaves. Essa metade
saiu para `web/src/foundation.css`, escrita à mão, com espelho à mão em
`design_tokens.dart`.

A outra metade é **dado de produto**, consumido por 48 arquivos do web: as bandas das cinco
réguas, que espelham `score_ruler.py`, e o vocabulário de categoria, setor, tipo de ativo, renda
fixa e liquidez. Essa continua gerada, de `product-rules.json`, porque limiar mantido à mão em N
lugares diverge em N−1 deles e o sintoma é um **número errado**, não uma tela feia.

O custo está aceito e registrado: a paridade com o mobile deixou de ter máquina. Foi decisão
explícita, pedida com o resto da direção.

O que ganhou máquina foi o contraste. `check-contrast.mjs` passou a ler o CSS e a cobrar três
coisas que não existiam — e as três **reprovavam a paleta anterior**:

| Regra nova | O que a paleta antiga marcava |
|---|---|
| contorno de controle ≥ 3:1 | **1,20:1** no claro, **1,67:1** no escuro |
| preenchimento contra poço ≥ 3:1 | **2,28:1** |
| papel declarado nos dois temas | — |

E a paleta nova foi **derivada** de contraste-alvo, não escolhida de olho: 64 pares conferidos nos
dois temas. `ground-0` claro aprofundou para `#EDF2F5`, que é o conserto de uma linha que o
próprio [VISUAL-LANGUAGE](design/VISUAL-LANGUAGE.md) previa para a queixa *"o plano de fundo se
confunde com os componentes"*. `ground-2` **não** pôde acompanhar: ele carrega texto, e os pisos
do sistema o fixam em `#EFF3F5` — um passo mais fundo derruba `ink-2` de 8:1. É isso que justifica
`control-fill-hover` e `control-fill-active` como papéis separados: eles carregam rótulo em tinta
primária, que tem folga, e podem ir mais fundo do que qualquer superfície de corpo de texto.

### O botão que não parecia botão

O contorno de `.btn-secondary`, `.btn-icon` e `.input` saía em `hairline` — o **mesmo token do
separador de linha de tabela**. E o secundário não tinha superfície nenhuma: `transparent` sobre o
chão da página. Nenhuma revisão visual pegou porque a borda existia; ela só não era visível.

Saiu também o `opacity: 0.5` do estado desabilitado, que derruba o contraste do texto junto com o
do fundo, e entrou o estado pressionado — que **não existia em nenhum controle do produto**.

### A barra de progresso não era uma barra de progresso

`<app-goal-progress>` usava a régua, que pinta faixas de julgamento e crava um risco onde o valor
caiu. Régua responde *"onde isto está na escala"*; progresso responde *"quanto do todo já foi"*.
Não havia preenchimento de zero até o valor, então não havia o que ler como progresso.

A régua ganhou duas leituras em vez de uma, mantendo o instrumento único: `marker` para valor numa
escala, `fill` para proporção de um todo. E as zonas inativas deixaram de ser pintadas — saíam
todas em `ink-3` a 70%, o que dava uma barra cinza sólida com um único bloco colorido: não se lia
nem a escala nem o valor. As divisas agora são tiques finos sobre o poço, que é o *"zonas por peso
de tinta"* que a identidade pedia e nunca teve.

### Três defeitos que não eram de estilo

**A classe de controle derrotava as utilitárias.** `styles.css` escrevia `.btn-*` e `.input`
soltas **depois** de `@tailwind utilities`, e por ordem de cascata venciam:
`class="btn-secondary hidden sm:inline-flex"` ficava **visível**. Valia para todo botão do produto
— esconder controle por breakpoint não fazia nada, sem erro nenhum. O sintoma que denunciou foi
outro: o cabeçalho vazando 3px em 320px, nas cinco rotas. A camada de controle passou para dentro
de `@layer components`.

**`passiveIncomeTarget` era um `computed()` lendo um `FormControl`.** Signal não rastreia form
control: o valor era avaliado uma vez e ficava cacheado, e a régua dizia *"nenhum alvo definido"*
com a meta preenchida no campo ao lado. Só apareceu porque o teste novo tentou declarar a meta
pela tela.

**`<img [src]="user.picture">` com foto vazia** desenha o texto alternativo dentro do botão: quem
não tem foto no Google via uma imagem quebrada no cabeçalho, 41px numa caixa de 34. Conta sem foto
passa a renderizar a inicial.

### Hierarquia e escala

O `h1` usava `fi-title`, que é o papel do título de **seção**: 15px de primeiro nível, do mesmo
tamanho de cada `h2` abaixo dele — a página não tinha topo. Entrou `fi-page-title`, e como
`app-page-header` cobre 20 telas, a troca alcança quase todo o produto de uma vez. O `h1` do
`asset` fica de fora de propósito: ali o título é o **preço**, e é a única tela em que o dado é o
título.

`body` foi de 14 para 15 e `title` de 15 para 16. O que continuava escrito cru — 14px em célula de
tabela, `0.875rem` na navegação de cima, `0.75rem` no selo — era tamanho sem papel. A folha global
agora usa cinco tamanhos, e os cinco são papéis. A navegação de cima passou a usar `fi-label`, o
mesmo papel da de baixo: cinco destinos iguais nas duas plataformas também no tipo.

### O que o mobile recebeu, e o que ficou

O tema do Flutter tinha os **mesmos** três defeitos, um a um: campo com borda `hairline`, trilho de
deslizador em `hairline` e nenhum botão secundário declarado — o `OutlinedButton` caía no padrão do
Material, com outra altura e outro contorno ao lado do primário do sistema. A camada de tema foi
fechada junto, porque a correção é a mesma.

A passada tela por tela do mobile ficou adiada, por decisão. O que **não** ficou adiado é o
contrato: `mobile/test/contraste_test.dart` cobra em Dart os mesmos pisos que o
`check-contrast.mjs` cobra no CSS. A paridade de **valor** continua sendo disciplina; a de **regra**
passou a ser verificada.

### As travas

Cada uma foi conferida contra o defeito que a motivou, revertendo o conserto e vendo o teste
acusar o número exato:

- `e2e/afordancia.spec.ts` mede o que chega na tela, nos dois temas: contorno e preenchimento de
  cada controle, o par preenchido/vazio da barra, e se uma utilitária de layout alcança um `.btn-*`
- a regra `contornoDeSeparador` do `lint:ui` varre a folha inteira e pega o controle novo no dia em
  que ele nascer. Nasceu larga demais, acusou os próprios blocos `:disabled`, e foi estreitada — a
  WCAG isenta controle desabilitado, e o rótulo inerte já é cobrado a 3:1 no `check-contrast`
- o teste de reflow **passava por sorte**: media assim que o cabeçalho ficava visível, antes de os
  controles da direita resolverem. Só começou a falhar quando o botão ficou 3px mais largo, ou
  seja, o vazamento já existia. Agora espera a rede assentar

---

## A IA nova, e a landing que testa a aposta (2026-09-06)

Fase 2 do [ROADMAP](produto/ROADMAP.md) começou sem a Fase 1 ter fechado —
decisão consciente, com uma ressalva registrada: o portão que protege de verdade é o da Fase 3,
quando isso vira `cashflow/`. Design errado custa dias; módulo errado custa meses.

### A navegação passa a ser o ciclo do dinheiro

As três opções levantadas no planejamento (mexer no `Hoje`, criar um sexto destino, ou pôr abas
dentro de `Carteira`) partiam todas de que a resposta era um arranjo dos cinco destinos atuais.
Nenhuma questionava o princípio de agrupamento, e é ele que quebra: o caixa acrescenta três
perguntas — quanto sobra, o que vence, a dívida é cara — e "um destino, uma pergunta" com oito
perguntas dá oito destinos.

A decisão em [INFORMATION-ARCHITECTURE](design/INFORMATION-ARCHITECTURE.md) é que **a navegação é
o ciclo**: `Mês` → `Sobra` → `Patrimônio`, mais `Descobrir` e `Você`. Continuam cinco.

Duas consequências não óbvias:

**`Hoje` deixa de existir.** Ele responde "o que mudou e o que merece atenção", que é um feed, não
um lugar — e o produto já sabia disso quando transformou `Atividade` em drawer, com o argumento de
que uma central de notificações como destino seria uma sala vazia. Com um mês no produto, `Hoje` e
a linha do tempo do mês disputam a mesma frase. Os quatro conteúdos de `Hoje` se distribuem sem
sobra.

**A ponte vira destino, e chama `Sobra`.** Não `Aporte`: a resposta nem sempre é aportar — com
dívida cara a regra manda quitar antes, e um destino chamado `Aporte` embutiria no mapa uma
conclusão que o produto contradiz. `Sobra` nomeia o insumo, que é o que a pessoa já diz.

O risco que essa estrutura cria está declarado no documento: quem só investe cai numa tela vazia. A
mitigação é **derivar o destino inicial** do que existe no razão do caixa, e não perguntar o perfil
na entrada — a visão decidiu atender amplo e derivar por dentro.

### A landing existe, e é uma demonstração

`/` deixou de redirecionar para `/hoje` e passou a ser a landing de validação — quinta rota
pública renderizada no servidor.

O [AI-TELLS](design/AI-TELLS.md) avisava que essa é a maior chance de "cara de template gerado" do
roadmap inteiro, e dava a saída: *"a frase do mês-corrente que já existe no produto tem mais força
que qualquer headline genérica, e é verdadeira, o que uma headline de marketing raramente é"*. A
página segue isso ao pé da letra — o centro dela é **um mês de exemplo que fecha na conta**, com a
sobra saindo da soma, e a resposta do produto sendo *quitar o rotativo antes de aportar*. Sem hero
com gradiente, sem grade de três colunas, sem número redondo.

O e-mail é gravado em `interest_signups` — tabela **global**, porque quem deixa o e-mail ainda não
tem conta e portanto não tem dono. Cadastrar duas vezes devolve `registered: false` e não erro:
quem não lembra se já cadastrou tenta de novo, e isso não pode parecer falha.

Coletar e-mail de quem não é usuário é tratamento de dado novo, então entrou na Política de
Privacidade com base legal, finalidade e prazo — guardado só até o aviso ser enviado, sem virar
conta e sem ir para serviço de newsletter.

---

## O CSP bloqueava o próprio login, e o hash agora se calcula sozinho (2026-09-06)

Com o front no ar, a tela de login apareceu quebrada no console: o CSP recusava três coisas de uma
vez.

**A folha de estilo do Google.** O `style-src` liberava `fonts.googleapis.com` e não
`accounts.google.com`, de onde o Google Identity Services carrega o próprio CSS. Sem ela o botão
de entrar não se desenha.

**O script inline do tema.** O `index.html` tem um `<script>` que lê `localStorage` e aplica o tema
**antes da primeira pintura** — é o que evita o flash de claro para escuro. O `script-src` não
tinha nem `'unsafe-inline'` nem hash, então o navegador o bloqueava e o flash acontecia em toda
visita.

A saída fácil seria `'unsafe-inline'`, que desarma o CSP inteiro para script. A saída certa é o
hash — mas hash escrito à mão quebra **em silêncio** no dia em que alguém mexer no script: o CSP
continua válido, o navegador só bloqueia, e o sintoma é um flash que ninguém associa a segurança.

Por isso o hash é **derivado do arquivo construído**, no boot do servidor: `server.ts` lê o
`index.server.html`, extrai todo `<script>` sem `src` e calcula o SHA-256 de cada um. Mexer no
script passa a ajustar o CSP junto, sem ninguém lembrar.

O teste em `e2e/ssr.spec.ts` fecha o laço pelo outro lado: pede `/login`, extrai os scripts inline
do **HTML servido**, recalcula os hashes e exige que estejam no cabeçalho. Se as duas pontas
divergirem, ele reprova.

### O CSS crítico do Angular também batia no CSP

Sobrou um terceiro bloqueio, e o autor era o próprio Angular: com `inlineCritical` ligado, ele
embute o CSS crítico e adia a folha completa com
`<link media="print" onload="this.media='all'">`. Isso é **handler inline**, e para eles hash não
vale — o CSP exigiria `'unsafe-hashes'`. Com o handler bloqueado, o `media="print"` nunca virava
`all`: a folha de estilo completa **jamais era aplicada**, e a página ficava só com o crítico.

Havia duas saídas. `'unsafe-hashes'` mantém o ganho de primeira pintura e cobra dois preços: afrouxa
a diretiva e exige um hash escrito à mão que pode derivar numa atualização do Angular — silêncio de
novo. Desligar `inlineCritical` custa uma folha de 42 KB (≈9 KB comprimidos) bloqueando a pintura,
numa conexão já aberta.

Para 42 KB o ganho do CSS crítico é marginal, e o que se compra desligando é uma diretiva que não
precisa de exceção nenhuma e nada para manter. Ficou desligado.

O teste que guarda isso não olha o CSP: olha o HTML servido e exige **zero** handler inline. Se
alguém religar `inlineCritical`, ele reprova antes de o sintoma virar página sem estilo.

### O tamanho da página deixou de ser o sinal

Desligar o CSS crítico encolheu as páginas e reprovou um teste que media bytes totais — ele usava
tamanho como proxy de "renderizou". A medida certa é estrutural: o conteúdo **dentro do
`<app-root>`**. Rota servida tem de 3 a 6 KB ali; rota de sessão tem exatamente zero. Isso não se
mexe quando a otimização muda.

### O que não é código

`[GSI_LOGGER]: The given origin is not allowed for the given client ID` — o domínio novo precisa
entrar em *Authorized JavaScript origins* do cliente OAuth, no Google Cloud Console. É configuração
de console, e sem ela o login não funciona por mais correto que o CSP esteja.

---

## A renderização no servidor nunca tinha funcionado (2026-09-06)

Ao publicar o front pela primeira vez, o healthcheck reprovou — e a investigação mostrou que o
invariante *"a página de ativo é a única rota pública, e é renderizada no servidor"* estava
**configurado, não verdadeiro**. Contra o código commitado, antes de qualquer conserto:

| Rota | Modo | O que devolvia |
|---|---|---|
| `/hoje` | cliente | 200, 20 KB — correto |
| `/ativo/PETR4` | servidor | 200, **0 bytes** |
| `/termos` | servidor | 302 para `/login` |

A página que o produto chama de canal de aquisição entregava **corpo vazio** para qualquer robô. O
defeito nunca apareceu porque nada o exercitava: o front jamais esteve publicado, e o `e2e` — que
sobe o servidor SSR de verdade — navega com JavaScript ligado, então a página hidratava no
navegador e os testes passavam sobre um HTML vazio.

### Três violações da mesma armadilha

O contrato de trabalho já registrava: *"o código do web roda também no Node. Use `DOCUMENT` e
`isPlatformBrowser`; nunca `document` ou `localStorage` direto."* Faltava a guarda em três lugares,
e `navigator` não estava na lista:

- **`app.component.ts`** — `navigator.platform` num **inicializador de campo**. Roda em toda
  construção do componente raiz, então derrubava o render de qualquer rota servida.
- **`auth.service.ts`** — `renderGoogleButton` tocava `window` e, pior, reagendava a si mesma por
  `setTimeout` enquanto `window.google` não existisse. No servidor isso é recursão infinita: o app
  nunca estabiliza e o render nunca termina.
- **`entitlement.service.ts`** — disparava HTTP no SSR sem guarda de plataforma, ao lado de
  `density.service.ts`, que tem a guarda. Requisição de titular no servidor não tem titular:
  responde 401 e ainda segura o render esperando a rede.

E o 302 para `/login` vinha do `httpErrorInterceptor`, que trata 401 navegando para a tela de
login — comportamento certo no navegador, sequestro do render no servidor.

### O que passou a existir

`e2e/ssr.spec.ts` pede as rotas com `request.get`, que **não executa JavaScript**, e exige conteúdo
no HTML cru. É a única forma de o teste enxergar o que um robô enxerga. Conferido que ele reprova
sem os consertos: quatro dos cinco falham.

Depois: `/ativo/PETR4` saiu de 0 para 53 KB com o ticker no `<h1>`, e as três páginas legais
passaram a chegar prontas, entre 32 e 35 KB.

### O front foi publicado

Serviço `fiance-web` no Railway, raiz `web`, com `SITE_URL` e `ALLOWED_HOSTS` — as duas
obrigatórias, e a segunda precisa aceitar `healthcheck.railway.app`, senão a proteção contra SSRF
do Angular recusa a sonda do próprio Railway. A API caiu para um worker: com um usuário, o segundo
não compra nada e custa ~US$ 2,50/mês de RAM.

---

## O `release:` do Procfile nunca teria rodado no Railway (2026-09-06)

Com acesso à CLI do Railway, o estado real do serviço apareceu — e desmentiu duas coisas que
estavam escritas como fato.

**A migração não rodaria.** A correção de A6 tirou a migração do `lifespan` e a declarou em
`release:` no Procfile. O Railway **não executa** essa linha: o mecanismo dele é o campo
**Pre-Deploy Command** do serviço, que estava `null`. O startup, que agora só confere a revisão e
falha alto, teria derrubado o processo com `BancoAtrasado` no primeiro deploy que carregasse
migração — a `0006`, que apaga `closed_trades`. Ou seja: o conserto de ontem trocou "migração
concorrente com duas réplicas" por "não migra, e o app não sobe". O campo foi apontado para
`python -m app.release`, e o comentário do Procfile passou a dizer qual dos dois manda.

**O Railway não espera o CI.** O gatilho de `main` tem `checkSuites: false`, então um commit
vermelho vai para produção do mesmo jeito. Isso agrava o A7 do PRE_PRODUCAO, que descrevia o
problema como "sem etapa intermediária": não é só a falta de homologação, é que nem o portão que já
existe é consultado.

### Três coisas que a leitura do ambiente revelou de passagem

- **`SITE_URL` e `ALLOWED_HOSTS` estavam no checklist de go-live e o código não lê nenhuma das
  duas.** Eram item falso desde que foram escritas. O `SITE_URL` do `deploy.yml` é outra coisa —
  variável do GitHub Actions para o teste de fumaça —, e essa continua necessária.
- **`FINNHUB_API_KEY` e `GEMINI_API_KEY` seguem no ambiente de produção.** As duas fontes foram
  descontinuadas e nada no código lê as chaves: é segredo morto guardado, superfície sem dono.
- **`ALLOWED_ORIGINS` aponta para `fiance-production.up.railway.app`, e o domínio é
  `fiance.up.railway.app`.** Não morde hoje porque o front não está publicado (a raiz responde
  404; só a API está no ar), e é exatamente o tipo de erro que só aparece no dia da publicação.
  Junto disso, `http://localhost:4200` está liberado em produção com credenciais — uma página local
  pode conversar com a API de produção.

O DSN do Sentry e o `RELEASE` entraram no ambiente, sem disparar deploy.

---

## O Sentry ligou, e o Angular não estava reportando nada (2026-09-06)

Os três projetos foram criados e os DSN colados. Ao seguir o guia de onboarding do Sentry, ficou
claro um defeito no que tinha sido entregue no dia anterior: **a integração do web chamava
`Sentry.init()` e não registrava `ErrorHandler`.**

Isso importa porque o Angular captura o que estoura dentro da própria zona e encaminha para o
`ErrorHandler` dele. Sem `Sentry.createErrorHandler()` provido, `Sentry.init` sozinho só pega o que
escapa para `window.onerror` — ou seja, quase nada do que de fato quebra numa tela. A integração
teria subido parecendo pronta e reportando pouquíssimo, que é o pior modo de falha para
observabilidade: o painel existe, fica vazio, e o vazio é lido como "não há erros".

Junto disso, o `import()` dinâmico do SDK saiu. Ele existia para não baixar o pacote sem DSN, e
`createErrorHandler` precisa do módulo no momento em que os providers são montados. Com DSN
configurado — que é o caso agora — o pacote seria baixado de qualquer jeito; a troca custa o
tamanho do SDK no bundle e paga com erro de Angular efetivamente capturado.

### O que do guia do Sentry não foi adotado, e por quê

O onboarding sugere `send_default_pii=True` no backend e deixa `dataCollection.httpBodies` ligado
no web. Os dois são o oposto do que este produto pode fazer: ticker e valor são dado financeiro
pessoal, e a Política de Privacidade promete que nenhum terceiro os recebe. Ficou `sendDefaultPii:
false` nos três, com a limpeza por lista de permissão por cima.

O guia do mobile propõe rodar `sentry-wizard`, que reescreve `main.dart` e o `pubspec.yaml`. Ele
desfaria `rodarComTelemetria` e o `beforeSend` que redige ticker e valor. **Não rodar o wizard** —
o mobile precisa só do DSN por `--dart-define`.

### Verificar deixou de depender de esperar um erro real

`POST /api/telemetry/verify` estoura de propósito, atrás de `require_admin`. O guia do Sentry
sugere uma rota pública de divisão por zero; uma rota que devolve 500 para qualquer um é coisa que
fica no ar e é encontrada. Atrás do gate de operador ela verifica o caminho inteiro em produção sem
virar superfície de ataque.

### `closed_trades` saiu do schema

A consulta na base de produção confirmou o que a VISAO_NOVA assumia: duas contas, nove posições,
treze lançamentos — tudo de teste. Com isso, a migração `0006` apaga a tabela que a apuração
projetada tornou inútil, e o item de Fase 0 fecha. **Some junto o risco de B4**: não há base para
o trial vencido derrubar.

Os dois testes de exatidão monetária que usavam `closed_trades` como cobaia passaram a usar
`transactions`, que é onde o dinheiro de verdade mora agora.

---

## A trilha A do go-live: suíte honesta, imposto certo, texto legal e olhos abertos (2026-09-05)

Cinco dos oito bloqueios de "colocar no ar" fechados de uma vez. O que liga os cinco é a mesma
doença: **o produto declarava uma coisa e fazia outra**, e nada quebrava.

### A suíte estava vermelha, e mentia nos dois sentidos

O `ci.yml` declarava, em comentário, que "a suíte não depende de rede nem de segredo real". Era
falso: `core/universe._fetch_brapi_list()` chamava `https://brapi.dev/api/quote/list` durante o
pytest, e o verde do CI passava a depender de o que um terceiro publicou naquele dia — vermelho sem
ninguém tocar em código, e verde com o código errado.

A declaração virou verdade por bloqueio no **transporte** do httpx (o `TestClient` usa
`ASGITransport` e continua funcionando), e o universo virou catálogo fixo no `conftest`. O bloqueio
revelou um segundo caminho escondido na hora: `/alerts/check` e o job de notificação chamavam
`fetch_many` direto, pulando o `AssetRepository` que é a costura que a suíte stuba — o teste de
alerta **passava porque alcançava a internet**.

Junto veio o defeito real que o teste vermelho apontava: **ETF de renda fixa era classificado como
FII em produção.** A BRAPI simplesmente não lista IMAB11, IRFM11, LFTS11, FIXA11, B5P211 nem
IB5M11; sem eles no mapa, `detect_type` caía no `_ENDS_11` e devolvia `fii`. Esses papéis entravam
na categoria errada, contavam na alocação errada e eram avaliados por Bazin sobre a distribuição de
um fundo de índice de renda fixa. `KNOWN_ETFS` resolve pelo mesmo padrão de `KNOWN_UNITS`, e vale
também com a fonte fria — classificação não pode depender do dia da BRAPI.

### A apuração de IR deixou de ser por operação

Era o defeito mais caro do produto, e tinha três sintomas com uma causa só. `cost_calculator`
tributava cada venda **no momento em que ela era gravada**: vender com +R$ 10.000 no dia 5 e
−R$ 10.000 no dia 20 informava R$ 1.500 de imposto onde o correto é zero, e inverter as datas dava
o número certo. Passar dos R$ 20.000 no mês não reavaliava as vendas já gravadas como isentas. E
venda lançada por `POST /transactions` ou vinda da importação de extrato **não apurava nada** — a
apuração só enxergava `POST /portfolio/sell`.

A causa era guardar imposto num campo. A correção é a mesma que já valia para a carteira: **a
apuração é projeção do livro-razão**, do mesmo jeito que a posição é. `ledger/apuracao.py` é a
matemática — sem banco, sem sessão, sem usuário — e agrupa por **mês e categoria**, que é a unidade
da lei. Os três sintomas somem por construção, porque não há mais momento em que o imposto seja
gravado antes de o mês fechar.

`ClosedTradeDb` deixou de ser escrita e `optimizer/cost_calculator.py` foi apagado: código morto que
calcula imposto errado é armadilha, não histórico. A linha de Encerradas continua mostrando um valor
de IR, mas agora **rateado** e rotulado como rateio; o número que vai para o DARF está na tabela de
apuração mensal, que é nova nas duas plataformas.

Um efeito colateral honesto: o "R$ X de prejuízo disponível para compensar IR" do feed somava toda
venda com resultado negativo, **inclusive as de mês isento**, que a lei não deixa compensar. O
produto anunciava um crédito que não existe. Agora ele lê o saldo compensável de verdade — e por
isso o aviso deixou de aparecer em alguns casos em que aparecia antes.

O que continua fora, e está escrito nos Termos: day trade (o razão não distingue) e IOF de resgate
de renda fixa com menos de 30 dias.

### A migração saiu do startup

`init_db()` chamava `command.upgrade(config, "head")` dentro do `lifespan`. Com `--workers 1`
funcionava; com duas réplicas subindo juntas, são duas migrações concorrentes, e o Alembic não
coordena isso — quebrando no pior momento possível, o primeiro dia com tráfego suficiente para
escalar. Agora `python -m app.release` é o *release command* e o startup apenas **confere** a
revisão, falhando alto se o banco estiver atrasado. Banco local em SQLite continua se criando
sozinho, porque é de um processo só.

O `Procfile` justificava `--workers 1` com "o cache é um SQLite local". Deixou de ser verdade
quando o cache passou a morar no banco da aplicação: o comentário mandava não escalar por um motivo
já resolvido.

### O texto jurídico passou a existir

Zero ocorrência de "privacidade", "termos de uso" ou "LGPD" em todo o repositório. Agora há três
páginas públicas e renderizadas no servidor — `/termos`, `/privacidade`, `/aviso-cvm` —, ligadas do
login (antes do consentimento) e de Você → Conta, nas duas plataformas.

**Isso muda um invariante de propósito:** a página de ativo deixou de ser a única rota pública com
SSR. O motivo é diferente do dela — robô de loja não faz login, e a ficha de segurança de dados das
lojas pede uma URL de privacidade que abre sozinha —, e o teste de fronteira foi atualizado
listando as quatro, para que a próxima adição também seja deliberada.

O texto está marcado como **minuta pendente de revisão jurídica**, num componente único que sai de
uma vez quando o parecer chegar. Publicar minuta sem dizer que é minuta seria pior que não publicar.

E o Aviso CVM **não repete o disclaimer à mão**: ele busca `GET /api/public/affirmation` e mostra a
postura vigente. `AFFIRMATION_LEVEL` é configuração; uma segunda cópia da mesma frase acabaria
desatualizada justamente onde a pessoa a lê. Fica registrado por escrito, atendendo A3 do
PRE_PRODUCAO: **o nível publicável é o 2**, e o nível 3 permanece desligado até haver parecer.

### O sistema deixou de operar cego

Sentry nas três plataformas, inerte sem DSN, com `before_send` próprio em cada uma. A limpeza é
**lista de permissão**, e não "tudo menos o que eu lembrei de proibir": ticker no caminho vira
`{id}`, valor em reais e número citado em mensagem de erro são redigidos, corpo de request e
`extra` não saem, do usuário sai só o identificador opaco, e variável local de stack frame é
descartada. Três suítes travam isso — é a Política de Privacidade escrita como código.

`SENTRY_DSN` configurado **com o pacote faltando falha alto**, pelo mesmo motivo de `REDIS_URL`:
um sistema que se acha observado e não está é pior que um assumidamente cego.

O resto de A5, A7 e A8 é conta e execução humana, e está em [OPERACAO.md](OPERACAO.md): monitor de
disponibilidade, agregação de log, canal de alerta, o caminho de homologação → promoção → rollback
(com `.github/workflows/deploy.yml`, manual de propósito) e o roteiro de restore de backup com
RPO/RTO propostos. **Backup nunca restaurado não é backup**, e três documentos deste repositório o
usavam como justificativa de arquitetura.

### O template do Angular voltou para o componente

Os 30 `.html` de `web/src/app/components` viraram `template` inline no próprio `.ts`. Decisão de
padrão, a pedido: um componente, um arquivo.

---

## Os neutros saem do papel morno e entram na família da marca (2026-09-04)

Decisão de produto, tomada contra a recomendação registrada em
[VISUAL-LANGUAGE](design/VISUAL-LANGUAGE.md): a paleta clara era **papel morno** — a escolha mais
incomum do sistema, feita para o produto ler como relatório impresso — e passou a ser **near-white
frio**, derivada da marca. O escuro acompanhou, saindo do grafite verde-ardósia para o azul-ardósia.
`brand` **não mudou**: `#295D7C` já era a identidade, e é o que a troca preserva.

`brand-strong` e `brand-light` entraram como papéis novos (o "Primary Dark" e o "Primary Light" do
briefing), disponíveis nas duas plataformas e no Tailwind.

### O que não foi aceito do briefing, e por quê

As **tintas** vieram propostas como `#667085` (secundária) e `#98A2B3` (legenda). Medidas contra o
chão mais claro do tema, dão **4,97:1** e **2,58:1**, contra pisos declarados de 8:1 e 6:1 —
`check-contrast.mjs` reprova as duas, e o próprio briefing pede contraste em §19. Foram derivadas na
mesma família fria até cumprirem o piso: `#414956` e `#525B6C`. Afrouxar o limiar não entrou em
discussão, e o briefing autoriza ajuste de valor.

A distinção **estado ≠ direção** ficou de pé. O briefing pede "Positivo → Success, Negativo → Error"
(§15), que é exatamente a conflação desfeita em 2026-08-xx: P&L é aritmética e usa `direction-*` com
croma baixo; julgamento é `state-*` e tem prioridade cromática. Trocar isso reabriria o defeito em
que uma perda aparecia como aviso, nas três plataformas.

### O custo que a troca tem

`ground-0` e `ground-1` ficaram a **1,06:1**. Isso já produziu queixa de usuário quando foram
`#FAF8F5` e `#FFFFFF` — *"o plano de fundo se confunde com os componentes"*. O que segura a
hierarquia é a estrutura não depender de card: a página se organiza por **fio e espaço**
(`.fi-block`), e o card que resta tem `hairline` na borda. Se a separação incomodar, o conserto é
aprofundar `ground-0` em `tokens.json` — uma linha, e o gerador propaga.

### Limpeza que veio junto

`AppColors`, no tema do mobile, era uma camada de **alias de cor** com o vocabulário que o
[CLAUDE.md](../CLAUDE.md) proíbe (`panel`, `muted`, `border`, `accent`, `warn`, `danger`): 20
declarações servindo 9 usos em três arquivos. Pior, `darkAccent2 == darkAccent`, então os três
ícones da tela de login alternavam duas variáveis que pintavam **a mesma cor** — resquício da era em
que a marca tinha duas. Removida; cada uso passou ao papel real do tema (`surface`, `outline`,
`surfaceContainerHighest`, `primary`, `fiInk2()`), sem mudança de pixel.

---

## A auditoria vira código: integridade, configuração e o canal de aquisição (2026-09-03)

Uma auditoria conduzida contra `a1ee50a` levantou 48 achados. Esta entrada registra o que foi
fechado e — mais importante — por que cada correção tem a forma que tem. O que ficou aberto está no
[KNOWN_ISSUES](KNOWN_ISSUES.md), e a maior massa pendente é a apuração fiscal mensal.

### A falha que era de arquitetura, não de detalhe

A sessão de banco nascia e commitava no **middleware de observabilidade**, e só o ramo
`except BaseException` fazia rollback. Só que os handlers de `DomainError` e `ValueError` vivem no
`ExceptionMiddleware` do Starlette, que é *interno* ao middleware de usuário: o erro nunca subia. O
middleware via uma resposta 4xx normal e **commitava a escrita parcial**.

O efeito onde mais dói: `sell_position` grava o `ClosedTradeDb` — com IR já apurado — e só depois
chama o razão. Quando o razão recusava a venda, o usuário levava 400, o trade encerrado ficava
gravado com imposto calculado, e a venda não existia no razão. Carteira e apuração fiscal saíam de
sincronia permanentemente.

A correção é uma linha de conceito, não de código: **quem decide commit ou rollback é o status da
resposta**, não a ausência de exceção. E ela abriu um segundo problema que precisava de resposta
própria — o contador que sustenta o teto de requisições e a marca de que alguém esbarrou na cerca
*precisam* sobreviver ao 4xx que eles mesmos provocam. Daí `independent_session()` e
`outside_request_transaction()`: transação própria para o que documenta a recusa, unidade de
trabalho do request para todo o resto.

Isso passou por 797 testes porque a suíte exercita rotas e confere respostas, não o estado do banco
depois de um erro de domínio no meio de uma escrita composta. `test_atomicidade_da_escrita.py`
existe para fechar essa classe, e foi escrito de forma a falhar com a correção revertida.

### Uma porta só para o razão

Três escritas passavam por `ledger_service` e reprojetavam a carteira; três iam direto ao
`ledger_store` e não reprojetavam nada — `POST /transactions`, o lote, a importação e o `DELETE`. O
desfecho era o pior possível para a confiança: a pessoa colava o extrato da corretora, o produto
respondia com a contagem de importados, e a tela de Carteira não mudava. Nada avisava que faltava
chamar `POST /transactions/rebuild`.

Agora `record_entry`, `record_entries`, `delete_entry` e `import_entries` são a porta única, e
`rebuild_projection` aceita um conjunto de símbolos para que uma escrita em lote custe **uma**
passada de projeção em vez de uma por ticker.

Um teste consagrava o defeito: `test_a_carteira_importada_aparece_na_projecao` afirmava que a
reconciliação acusava divergência depois de importar. Foi reescrito para o comportamento certo.

### A âncora de posição, e a assimetria que ela precisa ter

`_sequence` cortava o razão no último `ADJUST` **por ordem de gravação**. Declarar hoje 100 PETR4 e
depois importar o extrato do ano passado — que contém a compra dessas mesmas 100 — somava 200.
Declarar primeiro e importar o histórico depois é exatamente o fluxo que o produto convida.

A primeira tentativa cortou por data e quebrou a venda retroativa, que é comportamento declarado. A
regra correta é assimétrica e agora está escrita como tal: lançamento **anterior** à declaração que
*soma* posição (compra, bonificação, transferência de entrada) já está dentro do que foi declarado
e é descartado com aviso; o que *reduz* continua valendo. O canal `PositionProjection.warnings`
existia, era serializado e nunca era preenchido — passou a ser, aqui e na amortização que excede o
custo restante.

### Um default de ambiente que desarmava três defesas

`app_env` tinha default `"development"`, e `validate_for_startup()` retorna cedo em development. Um
deploy que esquecesse `APP_ENV` subia, em silêncio, com JWT `change-me`, CORS `*` e todo usuário
autenticado virando operador. Não havia falha barulhenta: o produto funcionava.

`APP_ENV` passou a **não ter default**. Vazio falha alto no startup e, se algo escapar, falha
**fechado** — vazio não é development. A suíte declara o próprio ambiente como qualquer outro
consumidor faria.

### O webhook de cobrança

Três defeitos empilhados: segredo default versionado no repositório, ausente da validação de
startup, e `parse()` lendo o titular **do corpo**. Quem conhecesse o repositório concedia ou
revogava plano de qualquer usuário.

O segredo entrou na validação de startup com o mesmo rigor do JWT, a rota ganhou teto por IP — a
assinatura é forçável offline sem custo se não houver —, e o titular passou a sair da tabela
`checkout_sessions`, que guarda quem abriu o checkout. A assinatura protege a integridade da
mensagem, não a autoridade sobre quem ela nomeia. `WebhookEvent` perdeu o campo de titular de
propósito: um campo que não existe não pode ser confiado por engano.

### O teto das rotas caras estava morto no caminho canônico

`EXPENSIVE_PREFIXES` casava `/api/opportunities` por prefixo. No prefixo canônico o caminho é
`/api/v1/opportunities`, que não casa. Hoje não morde porque nenhum cliente usa `/api/v1` — a
armadilha é o inverso: no dia da migração, que é o objetivo declarado, a proteção das seis rotas
mais caras sumiria sem teste vermelho. O casamento passou a ser por **sufixo**.

Na mesma passada, `/auth/google`, `/auth/refresh` e o webhook ganharam teto por IP: `rate_limit`
depende de `get_current_user` e por construção só limitava quem já entrou.

### "Tem carteira" é uma pergunta só

A cerca de plano, o início do trial e o marco de ativação perguntavam a `list_positions`, que lê só
a tabela `portfolio`. Renda fixa é entidade de primeira classe desde que ganhou tabela própria —
então quem tinha R$ 300 mil em CDB e nenhuma ação **nunca havia começado**: usava o produto inteiro
sem cerca e sem nunca ganhar trial. Agora existe `has_holdings()`, e é ela que os três consultam.

Junto: `POST /transactions/batch` aceitava a mesma lista de `/transactions/import` sem cerca
nenhuma. A cerca estava no parser, não no direito de escrever em lote.

### O sistema deixa de inventar CDI em silêncio

`collectors/rates.py` não seguia nenhuma das três disciplinas aplicadas à BRAPI: sem disjuntor, sem
cache vencido, sem faixa de plausibilidade. BCB fora do ar produzia 14,40% literal, carimbado
`estimativa`, alimentando comparação de renda fixa, marcação a mercado, RF × Bolsa, painel e a
linha de CDI do gráfico.

Ganhou as três. A degradação agora é **cache vencido antes de constante**, e o rótulo de fonte
distingue os dois (`bcb` / `bcb_cache_vencido` / `estimativa`). `BenchmarkResponse` ganhou
`cdi_source` e `cdi_basis` — o primeiro por simetria com `ibov_available`, que existia "porque
fonte externa pode falhar"; o segundo porque a curva é extrapolada da taxa de hoje e composta para
trás, o que é referência e não o CDI acumulado histórico. A curva continua contrafactual; parou de
mentir sobre a origem.

### Duas afirmações falsas ao lado do veredito

`decide()` escrevia "Tendência de alta (média 50 acima da 200)" sem consultar `trend_basis` — e com
`BRAPI_HISTORY_RANGE=3mo`, que é o padrão de produção, a classificação sai de SMA 20/50. O produto
tinha construído a honestidade certa (o campo existe, viaja no contrato, tem rótulo pronto nos dois
clientes) e a camada de explicação não a usava.

E `falsifiers()` derivava os preços-limite assumindo que o veredito era o da banda de margem de
segurança, mas `decide()` o altera depois por tendência e RSI. Resultado: a tela mostrava "Manter.
Isto vira Comprar se o preço cair para R$ 102,00" com o preço em R$ 100,00 — a condição já
satisfeita, contradizendo o veredito, com os dois números no mesmo componente. Agora a álgebra sai
da banda (`Decision.band_verdict`), uma condição já satisfeita não é emitida, e quando o técnico
segura o veredito fora da banda é **ele** que aparece como o que o derrubaria.

### O canal de aquisição

`describePage()` só rodava dentro do `next` do subscribe. Um 404 de ticker ou uma queda da fonte
devolvia **HTTP 200 com o título genérico do index.html** — e o sitemap anuncia ~400 tickers, então
uma indisponibilidade durante uma varredura produzia centenas de páginas idênticas, sem `noindex`
para conter. Exatamente o conteúdo duplicado que a canônica existe para evitar.

Agora o status é real (404 ou 503, via `RESPONSE_INIT`), a página se marca `noindex`, a canônica é
absoluta, há JSON-LD, e existe **imagem de compartilhamento por ticker**:
`/public/asset/{symbol}/og.png`, 1200×630, com o ticker, o veredito e o preço justo contra o de
mercado, nas cores de `tokens.json` e cacheada por seis horas. Num país onde a distribuição
orgânica de conteúdo financeiro é WhatsApp, LinkedIn e X, todo link compartilhado saía como um
retângulo de texto.

O `robots.txt` passou de lista negra a lista branca — enumerar as rotas privadas faz toda rota nova
nascer rastreável —, `SITE_URL` deixou de ter default silencioso, e o `fetch` do sitemap ganhou
timeout. O E2E passou a tocar a rota SSR, que era justamente a que ele não cobria.

### O que faltava no navegador

- **Duas abas derrubavam a sessão.** O `_refreshInFlight` coalesce a renovação dentro de uma aba, e
  o comentário explicava exatamente por quê; duas abas têm dois nulos e o mesmo refresh no
  `localStorage`. Agora um Web Lock serializa, e quem entra depois encontra o token já rotacionado
  e o aproveita em vez de apresentar um queimado.
- **Cabeçalhos de segurança.** Não havia nenhum. Com o refresh de 30 dias em `localStorage`, a CSP
  é a segunda linha que faltava.
- **O tema só era aplicado depois do bootstrap.** Não existia `@media (prefers-color-scheme: light)`
  em lugar nenhum: quem usa claro via flash escuro em todo carregamento, a rota SSR pública abria
  sempre escura, e quem navega sem JavaScript via só o escuro. O gerador passou a emitir o bloco de
  mídia, e um script inline lê a escolha guardada antes da primeira pintura.
- **Tokens de camada gerados e ignorados.** Cinco `--fi-z-*` contra onze templates escrevendo o
  número mágico direto — mais um valor fora da escala. Já tinha produzido um defeito: o indicador
  de carregamento em 100, desenhado atrás de modais que ficam em 200–300. A escala virou utilitária
  nomeada e o `lint:ui` ganhou a décima terceira regra.
- **Nenhum diálogo prendia o foco**, e dois nem se anunciavam como diálogo. A diretiva `fiDialog`
  dá papel, foco inicial, ciclo de Tab preso e devolução do foco às seis superfícies. A mudança de
  rota passou a ser anunciada em região `aria-live`. A inércia real do fundo para o leitor de tela
  continua aberta e está anotada como tal.
- **402 virava um toast ilegível** — o corpo é o dicionário da decisão, e o `switch` não tinha caso
  para ele. Não se manifestava só porque a cerca está desligada.

### E a documentação

O `KNOWN_ISSUES` tinha apodrecido de novo: os itens 12 e 13 afirmavam que a posição não era
projeção do razão e que as colunas monetárias eram `Float` — as duas coisas já eram falsas. Foram
substituídos pelo que ficou de fato aberto. O checklist do CLAUDE.md omitia `ruff format --check`,
que o CI roda: quem seguia o contrato à risca não rodava o comando que reprovava.

---

## O cache sai do disco e a coleta passa a ser em lote (2026-09-03)

O teto da BRAPI é de 3.000 requisições por dia. A conta de quanto o produto gastava não fechava:
o scan varre o universo inteiro — ~285 tickers — pedindo **um ticker por requisição**, e o dado cru
vale 2h. São 12 varreduras por dia, ~3.420 requisições, com **zero usuários**. O teto era estourado
pela linha de base, não pelo uso.

Duas coisas pioravam isso, e ambas eram invisíveis:

- **Falha não era guardada.** Ticker que a fonte recusa fazia `return {}` sem gravar nada. Como o
  job roda de 15 em 15 minutos, cada ticker morto custava 96 requisições/dia para ouvir o mesmo
  "não". Vinte deles são ~1.900 requisições jogadas fora.
- **O cache morria a cada deploy.** O arquivo SQLite vive no disco do contêiner, que é efêmero.
  Toda publicação reconstruía tudo do zero.

### O que mudou

**O cache passa a morar no banco.** `DatabaseBackend` grava em `cache_entries`, e o padrão agora é:
se `DATABASE_URL` é Postgres, o cache vai para lá; se o banco também é local, segue em arquivo.
`CACHE_BACKEND` força a escolha, e nome errado **falha alto** — cair em silêncio para cache por nó
é defeito que só aparece num gráfico de latência semanas depois.

Escolher o banco, e não Redis, foi decisão de operação: o Postgres já está de pé, já tem backup, já
é alcançável por todos os nós. Redis seria mais rápido e um serviço a mais para manter; continua
disponível por `REDIS_URL` para quando latência de cache virar o problema. A sessão do backend é
sempre própria, nunca a do request — cache dentro da transação de quem chama faria um rollback de
negócio apagar dado de mercado, e um erro de cache derrubar uma escrita de carteira.

`cache_entries` já estava em `account_store.GLOBAL_TABLES` desde antes de existir. Agora existe.

Um limite apareceu ao escrever o teste, e ficou documentado em vez de escondido: sobre **SQLite**
o backend de banco sofre com *database is locked*, porque o SQLite serializa escritores e a
gravação de cache é uma transação à parte por desenho. Falha assim é registrada e engolida — vira
uma leitura externa a mais, não erro na tela. No Postgres o caso não existe. É mais um motivo para
o padrão só escolher o banco quando ele é compartilhado.

**A coleta passa a ser em lote.** `prefetch_brapi_raw` pede até 20 tickers por chamada. O ponto que
fez isso caber em pouca linha é que tudo — cotação, fundamento, histórico, proventos — é derivado
de `brapi_raw:{base}`: aquecer essa chave em lote faz o resto do módulo trabalhar sem tocar na
rede, sem que nenhum caminho de leitura mude. A varredura do universo saiu de ~285 requisições para
~15. O caminho avulso continua valendo para ticker fora do universo.

**A ausência passa a ser lembrada**, por 30 minutos — TTL menor que o do dado bom, porque listagem
muda mais devagar do que a fonte se recupera. E a distinção que o teste protege: **falha de rede
não vira ausência**. Não saber se um ticker existe é diferente de saber que não existe; carimbar o
primeiro como o segundo esconderia uma fonte fora do ar por meia hora, com preço velho na tela e
ninguém avisado.

Estimativa do efeito: ~3.420 requisições/dia → ~200. O número real sai de `external.brapi.*` em
`GET /metrics`.

## Seis defeitos achados usando o produto (2026-08-29)

Vieram de uso real do mobile, não de teste. Cinco eram defeito; um era desenho.
Todos ganharam teste que reprova a volta.

### A renda fixa não entrava na Estratégia

`/strategy` e `/rebalance-suggestions` montavam a carteira só com
`portfolio_repo.list_positions()`, que é a tabela `portfolio`. Renda fixa é
entidade de primeira classe desde a fase 2 da auditoria e mora em
`fixed_income_positions` — nunca chegava lá. A meta de `renda_fixa` lia sempre
0%, que foi o sintoma relatado.

**O estrago maior não era esse.** `total_capital` também saía menor que a
carteira real, então o alvo **em reais de todas as outras categorias** vinha
subestimado: o gap estava errado para todo mundo, não só para a renda fixa.

Consertar expôs um segundo erro no mesmo lugar. O denominador era **custo**
(`quantity * avg_price`) enquanto a alocação de cada categoria era medida a
**valor de mercado** — com a carteira valorizada os percentuais não fechavam em
100. Agora as duas pontas usam a mesma régua: `_capital_investido` tira o total
da avaliação, que já traz a renda fixa e já está a mercado, e cai no custo só
quando não há avaliação.

A renda fixa viaja pela avaliação, não como `PortfolioItem`. A primeira
tentativa foi essa e o teste reprovou: o ticker sintético `RF-*` não é ticker de
B3 e não passa no padrão do modelo.

### Salvar uma preferência derrubava as outras — com 500

O cliente do mobile montava o corpo do `PUT /preferences` com **todas** as
chaves, mandando `null` nas que a tela não editou. O `exclude_unset=True` do
endpoint não descarta isso: `null` explícito *foi* enviado, então conta como
set. O `set_preferences` então fazia `setattr` de `None` em coluna `NOT NULL`.

Só não quebrou antes porque o primeiro salvamento é `INSERT`, e aí o SQLAlchemy
aplica o default da coluna no lugar do `None`. **Do segundo em diante é
`UPDATE`, que não aplica default** — e aí 500 sempre. Era o que impedia salvar
as categorias preferidas.

Corrigido dos dois lados de propósito: o cliente só manda o que a tela editou, e
o servidor descarta `null` de campo não-anulável. Um lado sozinho deixaria o
outro errado por contrato. `passive_income_goal` continua limpável — é o único
campo anulável de verdade, e `_PREF_ANULAVEIS` diz isso por extenso.

### Nenhum ativo tinha dividend yield

`_brapi_raw` mandava `fundamental=true`, `range` e `interval` — e não
`dividends=true`. Sem esse parâmetro a BRAPI não devolve `dividendsData`.
Conferido contra a API real: sem ele, ausente; com ele, 175 pagamentos para
PETR4.

Como `_brapi_raw` é a chamada única que alimenta o snapshot **e** o
`fetch_dividends`, o efeito era duplo e silencioso: `dividend_yield` `None` em
todo ativo, lista de proventos vazia, `monthly_dividends_estimate` zero por
aritmética — e **sem Bazin**, que é um dos métodos do preço justo.

**Achado junto, sem conserto de código:** `roe`, `profit_margin`,
`revenue_growth` e `debt_to_equity` voltam `null` para todo ativo. A BRAPI só
devolve `priceEarnings` e `earningsPerShare` neste plano. Isso responde o item 3
do KNOWN_ISSUES, que perguntava a *unidade* desses campos: a resposta é que eles
não chegam.

### Título sem seção embaixo

"Estou rendendo mais que o CDI?" era renderizado pela tela da Carteira, e o
`FiBenchmarkSection` devolvia `SizedBox.shrink()` com menos de dois pontos de
histórico. Sobrava o título colado em "Ativos negociados". O título mudou-se
para dentro do widget: some junto com o conteúdo. A seção vizinha já fazia
assim (`if (data.snapshots.length > 1)`), então era esquecimento, não desenho.

### `unknown` na tendência era a tela, não o cálculo

O backend nunca devolveu `unknown` para os 16 tickers testados em produção —
incluindo FII, BDR e small cap de liquidez fina. O que havia era **divergência
entre plataformas**: o web traduzia (`trendLabel`), o mobile mostrava o valor
cru em três lugares. Com histórico aparecia "downtrend"; sem, "unknown".

O web também vazava, por outro caminho: `return map[t] || t` devolvia o valor
cru no fallback. Aparecia menos porque a tendência ocupa menos lugares lá.

Nos dois, ausência de histórico virou **"sem histórico suficiente"** — a mesma
frase que `trendBasisLabel` já usava. `unknown` não é uma quarta direção, e a
palavra crua fazia a tela afirmar o que o sistema não sabe.

### A barra de meta: o problema era a escala, não o desenho

O relato foi "fica um ponto solto e uns números". A barra existia — track,
preenchimento e um fio de 2px na meta — mas a régua ia de **0 a 100%**. Com
metas reais de 10% a 30%, cada barra ocupava um sétimo da faixa e o desvio de
3 p.p. que a linha existe para mostrar virava dois pixels entre a ponta cinza e
o fio. Lia como marca solta, não como medida.

Duas mudanças, nas duas plataformas:

- **Escala compartilhada.** A lista inteira usa uma régua que sobe até o maior
  valor presente (atual ou meta, com 15% de folga, no mínimo 10 e no máximo
  100). As linhas continuam comparáveis entre si — que era o ponto da escala
  fixa — e param de se espremer à esquerda.
- **O desvio virou área.** A faixa entre onde você está e a meta é desenhada,
  em cor de atenção quando relevante, em vez de ser distância a medir no olho.
  É o número que decide o aporte; agora é ele que ocupa espaço.

A barra cheia usa a identidade de série da categoria, a meta é um fio de `ink`
atravessando a faixa, e embaixo vai a leitura em palavras ("faltam 8,0 p.p. para
a meta" / "dentro da meta").

O `AllocationGapComponent` do web tinha exatamente a mesma régua e serve três
telas, então mudou junto — a paridade entre plataformas é invariante, e o
`unknown` da tendência acabou de mostrar o que custa deixá-la escorrer.

## O banco publicado ficou para trás do colapso de migrações (2026-08-29)

O deploy do Railway estava em `● Crashed` desde o colapso do histórico de migrações
(`51a9461`, no dia anterior). O Postgres estava carimbado em `0007_loss_compensable`,
revisão que deixou de existir quando as doze migrações viraram uma; o `init_db`
encontrava tabelas, chamava `upgrade(head)` e o Alembic morria com
`Can't locate revision identified by` no meio do lifespan.

O commit do colapso registrou ter renomeado o banco de **desenvolvimento** para
`.antes-do-squash`. O publicado não foi tocado — e ninguém percebeu, porque a única
forma de descobrir era um deploy, e não houve nenhum entre o colapso e o dia seguinte.

**O banco estava em `0007` de verdade, não só de nome.** Faltavam nele todas as tabelas
de `0008` a `0012` — `subscriptions`, `referrals`, `instruments`, `ledger_entries`,
`audit_log`, sessões, contadores e eventos — e ainda existia `watchlist`, removida em
`5b3219f`. Carimbar a revisão atual por cima seria mentir: o Alembic passaria a acreditar
em 26 tabelas onde havia 16, e o erro voltaria como coluna inexistente em runtime.

Havia dois caminhos. Trazer o banco para a frente pela cadeia antiga — recuperável no git,
`0008`→`0012`, depois `stamp 0001_esquema_inicial` e `upgrade head` — ou recriar o schema.
Como não havia dado a preservar, foi `DROP SCHEMA public CASCADE`. As quatro contas que
existiam eram de teste. **Se houvesse assinante, o caminho teria sido o outro**, e o passo
delicado seria a `0002_dinheiro_exato`, que reescreve as colunas monetárias para `Numeric`.

### O guarda, que é o que sobra disso

O conserto do banco não deixa nada no código; o que ficou foi a verificação que faltava.
`init_db` agora confere de onde vai migrar **antes** de tentar, e falha com uma frase:

- banco carimbado em revisão que a cadeia não conhece — a mensagem **nomeia a revisão** e
  diz que o histórico foi colapsado depois do último deploy daquele banco;
- banco com tabelas e sem `alembic_version` — o estado que o próprio commit do colapso
  queria que falhasse alto, mas que até aqui falhava como "tabela já existe" três camadas
  abaixo do que interessa.

O ramo do banco vazio (`create_all` + `stamp head`) não mudou: é por ele que o Railway
subiu depois do reset.

## Segredo em URL não chega mais ao log (2026-08-29)

Nos logs do deploy recuperado, o token da BRAPI aparecia em claro em **toda** requisição —
o `httpx` loga a URL inteira em INFO, e a BRAPI põe a chave na query string. Eram ~286
linhas com o segredo a cada aquecimento de cache, retidas por quem tivesse acesso ao painel.

A correção é um `logging.Filter` nos handlers da raiz, e não um `setLevel` no logger do
`httpx`. Calar o `httpx` resolveria o vazamento de hoje e deixaria o de amanhã em pé: o
mesmo token também sai por `core/universe.py`, e qualquer biblioteca nova que logue uma URL
reintroduziria o problema. Em handler, vale para todo logger. `token`, `api_key`, `apikey`,
`access_token`, `refresh_token`, `secret`, `password` e `senha` viram `[redigido]`; o resto
da linha sobrevive, porque URL sem o segredo ainda é diagnóstico.

O `httpx` desceu para WARNING **também**, mas por outro motivo — 286 linhas por aquecimento
é ruído, não risco.

A redação impede vazamento novo; não desfaz o antigo. **O token que já vazou precisa ser
rotacionado** — está nos logs retidos do Railway desde sempre.

## `docs/design/` deixa de ter status e passa a ter só especificação (2026-08-28)

Quatro dos nove documentos do redesign foram removidos: `00-DISCOVERY`, `01-UX-AUDIT`,
`03-USER-JOURNEYS` e `07-IMPLEMENTATION` — 1.078 das 2.342 linhas da pasta.

Os três primeiros são **artefato de processo**: auditam o produto anterior, com evidência de
arquivo e linha de um código que em boa parte não existe mais. Cumpriram a função — os 36 achados
viraram trabalho, e o que restou deles está aqui e no KNOWN_ISSUES.

O `07-IMPLEMENTATION` saiu por um motivo diferente, e mais importante: ele era uma **terceira
fonte de verdade** sobre o que está no ar, ao lado do CHANGELOG e do KNOWN_ISSUES. E já tinha
divergido das outras duas — declarava "19 rotas endereçáveis" e "36 rotas no `app.routes.ts`"
(são 30 de conteúdo e 40 entradas), listava como assimetria aberta as metas e o RF × Bolsa do
mobile que fecharam em 2026-08-28, e dava como não feitos a busca global, o drawer de Atividade e
a reestruturação de Hoje e Carteira, todos construídos. É a mesma doença que motivou a reescrita
do KNOWN_ISSUES em 2026-08-22 e a de 2026-08-28: **arquivo que registra status apodrece, arquivo
que registra decisão não.**

O que sobra em `docs/design/` é especificação, e é por isso que sobra: `INFORMATION-ARCHITECTURE`
é a autoridade da navegação — quando web e mobile divergem, é contra ele que se confere, e foi
assim que a Estratégia sem rota apareceu —, `WIREFRAMES` é a estrutura de cada tela,
`VISUAL-LANGUAGE` o racional da identidade e `DESIGN-SYSTEM` o contrato dos componentes.
Nenhum deles afirma o que está construído.

Os quatro perderam o prefixo numérico na mesma passagem. O número indicava a fase do processo de
redesign, e sem as fases ele numerava uma sequência que ninguém segue — a pasta não se lê em ordem,
lê-se o documento que corresponde ao que se está fazendo. Ele também já não batia: o arquivo `02`
era a "Fase 3" e o `04` a "Fase 5". O resto de `docs/` nunca usou número.

### Decisões que estavam só no 07, preservadas aqui

Sem isto registrado, as quatro seriam re-litigadas na próxima vez que alguém olhar as réguas:

- **Desvio de alocação nunca é `adverse`.** O pior estado da régua `AllocationGap` é "atenção":
  estar fora da meta não é perda. Um teste no mobile trava isso.
- **`GoalProgress` não tem zona "no ritmo".** O produto sabe o alvo e o prazo, mas não a data em
  que a meta começou — qualquer ritmo seria inventado. O prazo aparece como contexto, não como
  julgamento.
- **Margem de segurança trunca em ±50%.** Margem maior que isso quase sempre é dado ruim, não
  pechincha, e a régua não deve premiar dado ruim com a barra cheia.
- **Máximo de 6 séries por gráfico.** A agregação de setores é top-6 + "Outros", não top-8 —
  alinhada à regra do design system.

E duas de layout, que são não-mudanças deliberadas e por isso somem com mais facilidade:

- **`screens.sm` continua 640px.** Remapear para 420px moveria o layout de todas as telas (46 usos
  de `sm:`). As faixas novas entraram como `xs` (420) e `2xl` (1440).
- **`EmptyState` tem CTA obrigatório por construção, e `Skeleton` tem a forma do conteúdo**, não um
  retângulo genérico. As duas primeiras versões desses componentes foram removidas por não terem
  consumidor **e** por contradizerem o próprio contrato; foram reconstruídas com consumidor real.

Uma afirmação do 07 que já era falsa quando foi apagada, e que fica corrigida: ele dizia que **não
há verificação automática de ícone do Lucide**, registrando que um checker estático fora escrito e
removido. Hoje há — `npm run lint:ui` cobre ícone não registrado, entre outras quatro coisas.

---

## G2 fechado: proventos por calendário, contraste e densidade (2026-08-28)

Os três últimos itens do portão de retenção que não dependiam do entitlement.
Sobrou só a indicação, bloqueada por dependência declarada do G3.

### Proventos sugeridos pelo calendário

Provento é a coisa mais fácil de esquecer de lançar: chega no extrato da
corretora, não no app. O calendário da fonte sabe o que foi pago, a carteira
sabe quanto a pessoa tinha — cruzar os dois produz "isto provavelmente entrou na
sua conta".

Nada é gravado sem confirmação, e isso não é cautela: é correção. Três fontes de
erro, e as três erram o valor **para mais**. A fonte publica `paymentDate` e não
a data-com, então quem comprou entre uma e outra aparece com direito que não
tem. A quantidade vem do razão, que pode estar incompleto. E JCP tem 15% retidos
na origem, enquanto a fonte publica o bruto.

Provento inventado infla renda passiva, distorce a meta de renda e vira número
errado na declaração. Então cada linha mostra a conta — quantidade × valor por
ação — e as ressalvas daquela linha; nada vem pré-selecionado; e não existe
"aceitar todos", que seria o caminho curto para lançar o que não se recebeu.

É aqui que o livro-razão paga a conta de existir: a quantidade na data sai da
projeção dos lançamentos anteriores àquele dia. Sem ele, a única resposta
possível seria a quantidade de hoje, que erra todo provento anterior ao último
aporte.

### Contraste verificado, não recomendado

Cor é gerada de `tokens.json`, então contraste também pode ser verificado de lá.
A diferença entre 4,4 e 4,6 não se enxerga numa revisão visual, mas separa quem
lê a tela de quem não lê.

O verificador encontrou sete pares abaixo do mínimo, todos sobre `ground-2`, que
é a superfície mais profunda — mais `series-other`, o cinza do balde "Outros",
abaixo de 3:1 nos dois temas. **A paleta foi corrigida, não o limiar.** Os
ajustes preservam matiz e croma: só a luminosidade se move, o mínimo para cruzar
com folga de 0,05. Como os tokens são gerados, web e mobile receberam a correção
juntos.

Os limiares seguem a WCAG 2.1 AA aplicada ao que cada papel de fato é. `ink-3`
entra como texto e não como decoração, porque legenda é texto pequeno — e a
regra para texto pequeno é mais rígida, não menos. Séries de gráfico entram como
forma (1.4.11), e podem, porque nunca são a única informação. `hairline` fica de
fora: é separador decorativo, e exigir 3:1 dele produziria uma borda que grita
numa interface que depende de silêncio.

### Duas verificações novas no lint de runtime

O gráfico de benchmark ganhou tabela de dados — os outros dois já tinham. Ele
tinha só `aria-label`, que resume, e resumo não é o dado: quem usa leitor de
tela precisa comparar ponto a ponto. Ícone não conta como gráfico, senão a regra
vira ruído que se aprende a ignorar.

Dez botões só de ícone não diziam o que faziam, e três deles apagavam alguma
coisa. Ganharam rótulo descrevendo a ação sobre o objeto certo — "Remover
provento", não "Excluir": o problema não é a falta de rótulo, é não saber o que
some. A checagem é por ausência de **texto**, não por presença de ícone, porque
exigir `aria-label` em botão com palavra dentro produziria anúncio duplicado —
que é como uma regra de acessibilidade acaba piorando a acessibilidade.

### Densidade ponta a ponta

A densidade existia só na tabela de posições. Os tokens já definiam os perfis e
o CSS já reagia a `[data-density]`; faltava alguém escrever o atributo a partir
de uma fonte que fizesse sentido.

A preferência mora na conta e não no navegador: densidade é apetite por
informação, e isso acompanha a pessoa — quem lê tabela densa lê densa no
notebook e no celular. É o oposto do tema, que é preferência do dispositivo.

Na tabela de posições a URL vence a preferência quando o parâmetro existe: link
salvo é contrato, e quem compartilhou a tabela compacta espera que ela chegue
compacta do outro lado.

### Um item do backlog que já estava pronto

"Gráfico de preço com preço médio e preço justo como referências" já existia:
`asset-price-chart` tem as duas linhas com semântica visual distinta — justo
tracejado porque é estimativa, preço médio pontilhado porque é fato mas é seu —
e a tela de ativo as passa. Não foi refeito.

---

## G2, segunda metade: contrato, entrada e explicabilidade (2026-08-28)

Três itens que têm a mesma natureza: transformam uma regra que estava escrita
em prosa numa regra que o sistema garante.

### Paginação por cursor e versão no caminho

As duas coisas andam juntas porque paginar muda a forma da resposta, e mudar a
forma sem versionar o caminho só tem dois destinos ruins: quebrar cliente
publicado, ou nunca mais mudar nada.

O cursor é keyset — a última chave lida, `(ordenação, id)` — e não offset.
`OFFSET n` relê e descarta n linhas a cada página e, pior, **pula ou repete**
itens quando algo é inserido no meio: numa lista por data decrescente, registrar
um provento enquanto se folheia empurra tudo para baixo e o item da borda
aparece duas vezes. O `id` está lá como desempate; sem ele, dois registros do
mesmo dia fariam a paginação travar ou pular, e há teste para os dois casos.

**Onde o corte acontece é decisão, não detalhe.** `/portfolio/trades` e
`/transactions` cortam no banco, porque não há agregado sobre a lista — e para
isso os totais de operações encerradas passaram a vir de `SUM`. Proventos, renda
fixa e sugestões seguidas cortam só o payload: os totais por mês, a marcação a
mercado e a comparação com o Ibovespa precisam do conjunto inteiro por
definição, e cortar a consulta faria o total falar apenas da página. Um total que
encolhe conforme a rolagem é pior que uma lista longa — é o número que a pessoa
leva para a declaração. A limitação ficou registrada como pendência, não
disfarçada.

O padrão não trunca quem cabe numa página: 200 itens, teto de 500, `has_more`
dizendo a verdade sobre o resto. Nos clientes, o campo chegou aos modelos e ao
store, e a tela de encerradas diz quantas está mostrando de quantas — lista
truncada em silêncio é indistinguível de operações perdidas, e é essa a
conclusão que o usuário tira.

`/api/v1` é canônico e `/api` segue como alias, porque derrubar os apps
instalados num deploy seria trocar um problema por outro. É a **mesma** montagem
do router: duas cópias divergiriam na primeira mudança, e há teste comparando as
respostas. `X-API-Deprecation` existe para ser medido — é o que dirá quando o
alias pode sair.

Erro no caminho: o cabeçalho de aviso tinha "sairá" com acento, e cabeçalho HTTP
é latin-1. Derrubou 162 testes de uma vez com `UnicodeDecodeError`. Agora é
ASCII, com teste que falha se voltar a não ser.

### Onboarding em três passos e carteira de demonstração

O critério é chegar ao primeiro diagnóstico em menos de três minutos, e isso só
funciona se pular for barato e se pular levar a uma tela com conteúdo.

**O passo é derivado, não guardado.** Não existe contador: o passo sai do que a
pessoa já fez — tem posição? tem meta? Um contador criaria uma segunda verdade
que diverge da primeira no primeiro caso interessante, que é alguém importar a
carteira pelo CSV e o onboarding continuar pedindo isso. Tem teste que importa
por fora e confirma que o passo avança sozinho.

O estado é do servidor: progresso em `localStorage` recomeçaria a cada aparelho
e faria a métrica de ativação medir dispositivo em vez de pessoa.

O recorte mora na URL (`?passo=2`), como todo recorte neste produto — refresh no
passo 2 volta ao passo 2. A URL manda sobre o servidor: ele diz onde a pessoa
*deveria* estar, a URL diz onde ela *está olhando*. Passo fora da faixa ou
não-numérico cai no estado do servidor em vez de virar NaN na barra.

Pular também conclui. O carimbo serve para não repetir a sequência, e insistir
com quem já disse não é o caminho curto para a desinstalação. Falha ao carimbar
também não prende ninguém.

A demonstração roda a análise de verdade, pelo mesmo caminho da carteira real —
um cálculo simplificado mostraria uma tela que o produto não entrega. Nunca é
gravada, porque semear exemplo na conta de alguém depois aparece na declaração.
E os cinco ativos são declarados, não sorteados: uma seleção aleatória poderia
montar cinco bancos, e o veredito de risco sobre isso ensinaria a coisa errada.

### Explicabilidade exigida por lint

Score, veredito, preço justo e sugestão são opinião do sistema sobre o dinheiro
de alguém. Opinião sem método à vista é fé, e essa regra escrita só na
documentação se perde na terceira tela nova.

O lint reprova template que **renderiza** julgamento sem oferecer como conferir
a conta. A distinção entre renderizar e mencionar é o que faz a regra ser
seguida em vez de contornada: a tela de preferências fala sobre o score sem
exibir nenhum, e reprová-la ensinaria a ignorar o lint. A detecção olha
interpolação, binding e `@if` — não a prosa.

Ele encontrou cinco telas sem explicação: Quick Invest, rebalanceamento, RF ×
Bolsa, sugestões seguidas e diagnóstico de queda. Todas ganharam método, fonte e
— a parte que importa — a limitação. Quick Invest e rebalanceamento não
descontam corretagem nem imposto; RF × Bolsa compara rendimento contratado com
estimativa; sugestões seguidas só contam o que foi registrado, então sobrando os
acertos o número fica otimista; e o diagnóstico de queda pode estar olhando um
fundamento que ainda não mudou, porque o balanço sai semanas depois.

O escape existe e exige motivo escrito. Escape sem justificativa não é escape, é
esquecimento com sintaxe.

---

## G2, primeira metade: aquisição, importação e integridade do dado (2026-08-27)

Quatro itens do portão de retenção. O primeiro é o que o plano identificou como
maior risco de execução — e não é técnico.

### Renderização no servidor: o canal de aquisição

O modelo financeiro fecha com folga: margem de ~92%, break-even em 93
assinantes. Mas fecha **desde que os usuários apareçam de graça**. Com LTV
líquido de R$ 288 e razão saudável de 4:1, o teto de CAC é R$ 72, e instalação
qualificada em finanças no Brasil custa entre R$ 500 e R$ 1.500. Mídia paga está
fora do alcance, e isso transforma "página indexável" de refinamento técnico em
pré-requisito de negócio.

`/ativo/:ticker` passou a ser renderizada no servidor; todo o resto continua no
cliente. A fronteira é regra de negócio escrita como código, com teste: renderizar
no servidor uma tela de carteira significaria buscar dado de titular durante o
SSR, e é assim que se serve a carteira de uma pessoa para outra assim que
houver um cache na frente. O teste também falha se alguém recolocar o
`authGuard` na rota do ativo — o que derrubaria a indexação sem quebrar nenhum
teste de tela.

O backend ganhou uma leitura sem titular. `analyze_asset(personalized=False)`
roda sem o yield desejado de ninguém, porque a mesma URL precisa devolver o
mesmo conteúdo ao robô e a quem chega pelo link: se o preço justo variasse com a
preferência de quem pediu, o que o Google indexasse não seria o que o visitante
encontraria. O teto de abuso dessas rotas é por IP, sobre a mesma primitiva do
teto por usuário — `usage.increment` não precisou saber a diferença.

Metadados por ticker: título, descrição, Open Graph e canônica saem do próprio
ativo. É o que separa "uma página indexada" de "seiscentas páginas iguais", que a
busca trata como duplicado e não indexa. A canônica é `<link>` e não `<meta>` —
o `Meta` do Angular só gerencia meta tags, e pedir a ele um rel=canonical produz
uma tag que nenhum buscador lê.

Verificado de ponta a ponta e não por inspeção: backend local mais servidor de
renderização, `curl` sem JavaScript devolvendo a análise completa em HTML, com
título e canônica próprios e zero erro no log.

Três coisas apareceram ao ligar. `document is not defined` no drawer de
atividade, que roda no shell da página pública — passou a injetar `DOCUMENT`. O
Angular 22 recusa `Host` desconhecido para não virar proxy de SSRF, e o domínio
é fato de deploy e não de build, então vem de `ALLOWED_HOSTS`. E sitemap
indisponível responde 503 em vez de um sitemap vazio: vazio o robô lê como "o
site encolheu" e desindexa.

Nas dependências, o tree misturava framework 22.1.2 com ferramental 22.1.4 — só
apareceu porque `@angular/ssr` tem peer exato. Alinhado em 22.1.4.

### Importação: colar lista ou CSV

O livro-razão existia sem porta de entrada em volume. O parser é tolerante com
**forma** e intolerante com **ambiguidade**, e a assimetria tem motivo: adivinhar
errado a forma custa uma mensagem de erro; adivinhar errado o valor custa o
preço médio, que é o IR.

Aceita vírgula ou ponto no decimal, três separadores de campo, data em três
formatos e cabeçalho em português ou inglês. Recusa `1.234`, porque com três
casas depois do ponto não dá para saber se é milhar ou decimal — e um fator de
mil no preço médio é um extrato errado.

O erro diz a linha e o que corrigir; "formato inválido" não ajuda quem tem
trezentas linhas. A prévia devolve as boas e as ruins ao mesmo tempo, porque
parar no primeiro erro faria corrigir uma linha por vez. E a gravação é tudo ou
nada: num produto que calcula IR, meia importação é pior que nenhuma.

Duplicidade é apresentada, nunca silenciada. Reimportar a mesma nota é o engano
mais comum, mas duas compras iguais no mesmo dia acontecem — a decisão fica com
quem sabe o que aconteceu, e o padrão é deixar de fora. A chave de duplicidade
ignora taxas de propósito: a mesma nota vinda de outra fonte pode trazer a
corretagem arredondada diferente e ainda ser a mesma operação.

O teste achou um bug: `40/13/2024` passava, porque eu validava o formato da data
e não o calendário. `2024-13-40` ordena depois de tudo, jogaria a operação para
o fim do razão e mudaria o preço médio de todas as que vieram depois dela de
verdade.

### Plausibilidade e disjuntor

A validação do dado externo era por tipo, não por magnitude: um ROE de 12.000%
ou um preço de R$ 0,0001 passam pelo `float()` e viram patrimônio. O modo de
falha é o pior possível — o número absurdo não levanta exceção, vira um veredito.

Duas severidades. Campo implausível vira `None`, porque o produto sabe conviver
com indicador ausente e não sabe conviver com número errado. Preço implausível
rejeita o snapshot inteiro, porque sem preço não há tela nenhuma.

Os limites são largos: o alvo é o absurdo — erro de unidade, campo trocado,
valor sentinela — e não o extremo legítimo. A B3 tem empresa com ROE de 80% e
ação de R$ 0,90, e rejeitá-las seria trocar um erro por outro.

O disjuntor troca "lento e quebrado" por "rápido e explícito": aberto, nem tenta,
e quem chama cai no cache vencido. Duas calibrações que valem registrar — 400 por
range **não** abre o circuito, porque é limitação do plano gratuito e não fonte
fora do ar; e voltar do aberto exige dois sucessos, porque uma resposta boa
isolada durante uma queda parcial reabriria a torneira cedo demais.

`GET /data-quality/source` responde a saúde sem varrer o universo: quando a
fonte caiu, disparar o scan completo é justamente o que não se quer fazer para
descobrir isso.

### O scanner deixou de ser custo marginal

O scanner é a única feature cujo custo cresceria com o uso. A correção não é
cobrar por ela: um job periódico recalcula o scan **antes** do TTL vencer, de
modo que a varredura aconteça N vezes por dia, sempre a mesma quantidade, e
nenhuma requisição de usuário espere por ela. O intervalo é menor que o TTL de
propósito, e há teste para essa relação — invertê-la reabriria a janela que o
job veio fechar.

Feito isso, o Free pode ter prévia sem medo e o Premium pode ter filtro sem teto:
nenhum dos dois é o que custa.

---

## Do redesign à primeira cobrança: portões G0 e G1 (2026-08-27)

O redesign está no ar e o modelo de receita foi decidido — freemium, R$ 19,90/mês, sem anúncio.
A consequência que reordena o plano é que **cobrar não é uma feature no fim da fila, é uma
restrição de projeto**: o Premium vendável inteiro roda sobre uma tabela de transações que não
existia, e aquisição orgânica vira decisão de arquitetura. O plano tem cinco portões; estes são
os dois primeiros.

### G0 — o que bloqueia publicar

Nada visível ao usuário, tudo pré-requisito de loja ou de medição.

**Sessão.** O JWT tinha TTL de 30 dias e nenhuma revogação: token vazado valia até expirar. E
`jwt.decode()` não exigia claim nenhuma — um token sem `sub` levantava `KeyError` e virava 500,
quando erro de autenticação tem que ser 401. Agora `sub`, `exp` e `iat` são obrigatórios; o token
ganhou `typ` e `jti`, de modo que refresh não passa por acesso nem o contrário; o acesso caiu para
1 hora com refresh rotacionado, e reapresentar um refresh já usado cai na denylist.

"Sair" ganhou efeito de servidor por duas vias, porque são dois problemas: `jti` em denylist para
este dispositivo, e um corte em `session_cuts` para todos. O corte mora em tabela própria e não em
`users` por dois motivos concretos — precisa existir para quem ainda não tem linha de titular
(conta criada implicitamente por escrita) e precisa sobreviver à exclusão da conta, que anonimiza
`users`.

`iat` passou a ser emitido com fração de segundo. Truncado ao segundo, o corte de revogação fazia
um token emitido logo depois de um "sair de todos" nascer morto — o teste pegou isso na primeira
execução.

Tokens legados de 30 dias sem `typ` continuam valendo até expirar: derrubá-los deslogaria a base
inteira num deploy.

**Conta.** Exportação e exclusão nos dois planos, nunca atrás de gate — é direito do titular e
exigência das duas lojas. A exclusão apaga tudo que é do titular e deixa `users` como lápide
anonimizada; apagar a linha inteira ressuscitaria a conta, porque `_ensure_user` recria o titular
na primeira escrita. A lista de tabelas é explícita e há um teste que falha quando uma tabela nova
com `user_id` não aparece nela — ele já pegou `transactions` e `audit_log` no commit seguinte.

**Contadores.** `usage_counters` é uma primitiva só para dois tetos que sempre foram o mesmo
problema: abuso (por rota e minuto) e plano (5 páginas de ativo por mês, que chega no G3). A
granularidade mora no formato de `window_key`, não no schema, e o mês é o brasileiro — pelo mesmo
motivo que a isenção de IR é.

**Eventos.** Dicionário fechado de 27 eventos, cada um respondendo uma das seis perguntas do
funil; nome fora do dicionário e propriedade com ticker ou valor devolvem 422. Ativação é gravada
pelo servidor e não pelo cliente: é a métrica que decide o portão G2 e não pode depender de qual
app disparou. O funil e a correlação de *aha* contra D30 são endpoints de operador — funil que
ninguém vê não é consultado, e analytics que ninguém olha custa privacidade sem produzir decisão.

**Warm-up.** Rodava em todo worker sem lock: subir três réplicas disparava três varreduras do
universo ao mesmo tempo, que é o pico de consumo de cota mais caro do produto. Agora roda sob lock
e o libera no `finally`. O lock dos jobs periódicos continua expirando por TTL de propósito — ali
o TTL é o intervalo, e liberar faria o worker seguinte repetir o ciclo.

**Clientes.** O TTL curto obrigou web e mobile a saber renovar. Os dois guardam o refresh, renovam
uma vez ao levar 401 e repetem a requisição, com a renovação compartilhada: duas chamadas que
falham juntas não podem disparar dois refreshes, porque o servidor rotaciona e o segundo
apresentaria um token já queimado.

A ordem dos interceptors do Angular estava invertida para isso — o de erro era o mais interno e
deslogava o usuário antes de o de autenticação tentar renovar.

**Lint e testes do web.** Ícone do Lucide não registrado e classe CSS inexistente não quebram o
build; quebram a tela. `web/tools/lint-ui.mjs` reprova os dois, e a fonte de verdade das classes
não é lista escrita à mão: é o CSS que o build de fato emitiu. Para os ícones, o lint reimplementa
o mesmo `toPascalCase` do lucide-angular — um kebab ingênuo reprovaria `trash2`, que funciona.
E `ng test` sobre Vitest com 35 testes na régua de score, no store da carteira e nos cálculos de
Hoje: a camada que mais mudou em agosto era a única sem teste.

### G1 — o livro-razão

**Por que é pré-requisito de receita e não fundação genérica.** Extrato fiscal, importação de CSV
e nota, histórico completo de desempenho e eventos corporativos — todo o Premium vendável — rodam
sobre uma tabela de transações. Sem ela, o Premium é uma promessa com três telas vazias.

A matemática mora em `app/ledger`, que não conhece banco, sessão nem usuário. É o que permite
conferir uma carteira sintética de cinco anos contra valores calculados à mão, sem rede. O preço
médio segue a convenção brasileira — venda reduz quantidade e custo, nunca a média — e a
corretagem entra no custo de aquisição, porque ignorá-la infla o lucro tributável.

Evento corporativo virou lançamento, não correção manual. Desdobramento 1:2 dobra a quantidade e
deixa o custo total intacto, então a média cai pela metade. O teste de contraste mostra o tamanho
do erro: sem o ajuste, uma venda pós-desdobramento apareceria como prejuízo de R$ 1.000 onde houve
lucro de R$ 1.000 — e é esse número que vai para a declaração.

Instrumentos ganharam identidade separada do ticker, com janela de validade, porque a B3
reaproveita código: somar o histórico de duas companhias sob o mesmo ticker daria preço médio de
ninguém.

`adjust` existe porque a tela de posição declara estado, não operação. A pessoa diz "eu tenho 100
a 10,00", e inventar uma compra que não aconteceu seria mentir sobre a origem do número.

A escrita é **espelhada, não substituída** — passo 1 de 3. A posição corrente segue sendo a fonte
de leitura e o razão corre em paralelo; `GET /transactions/reconciliation` compara os dois lado a
lado. Trocar a fonte antes de a comparação estar verde é como se perde a confiança no número. O
backfill semeia contas anteriores ao razão, senão o alarme tocaria para todo mundo — e alarme
assim acaba desligado.

**Decimal veio depois, nunca junto.** Dois refactors de escrita ao mesmo tempo em código
financeiro é exatamente como se perde a confiança no número. `app/core/money.py` é o único lugar
com escala e convenção, e tem duas regras que são o motivo de ele existir: nunca construir
`Decimal` a partir de `float` sem passar por texto (`Decimal(0.1)` carrega o erro do binário, e
trocar float por Decimal assim só muda o lugar onde o erro aparece), e arredondar só na borda.
O arredondamento é meio para cima, que é a convenção da apuração brasileira e não o bancário do
`round()` do Python, que devolve 2 para 2,5.

Os 39 testes do razão passaram sem uma linha alterada na troca — a borda em float segurou.

O contraste em float dos testes usa cem parcelas de R$ 0,07 e não mil de R$ 0,01: em mil os erros
de binário se cancelam por acaso, e um teste que depende desse acaso não prova nada. É assim que o
erro chega ao extrato — em alguns totais e não em outros, sem aviso.

**Dois erros que se escondiam bem.** `datetime.fromtimestamp(ts, tz=UTC)` num snapshot das 22h de
Brasília devolve o dia seguinte, então a busca do fechamento do Ibovespa errava a chave e devolvia
`None` — o gráfico simplesmente não mostrava o índice, sem erro nenhum. E provento pago saía da
carteira sem ser contabilizado: o preço cai no ex-dividendo, o patrimônio cai junto, e o dinheiro
não está em `total_current` — o TWR mostrava a carteira perdendo exatamente o que tinha ganhado,
punindo justamente o segmento de renda, que é quem mais olha esse gráfico.

A convenção de borda ficou escrita e não implícita: `paid_at` é dia, `captured_at` é instante,
então um provento pago no dia D pertence ao primeiro período cujo snapshot de fechamento caia em D
ou depois, em BRT. Sem isso, o mesmo provento entra ou sai do período conforme a hora arbitrária em
que o job rodou.

**Log append-only** sem update e sem delete na camada de escrita; a única saída é a exclusão de
conta. Falha de auditoria nunca derruba a operação que a originou — perder um registro é ruim,
perder o aporte do usuário é inaceitável.

**A tela.** `/carteira/transacoes` mostra todo movimento e refaz a conta do preço médio passo a
passo, em número e em frase. Preço médio que ninguém consegue conferir é preço médio em que
ninguém confia. Divergência entre a posição salva e a projeção aparece na própria tela, dizendo
qual número está valendo — esconder seria pior, já que dado errado em produto pago é a reclamação
número 1 dos concorrentes brasileiros.

`book-open` não estava registrado no `LucideAngularModule.pick`; o lint que entrou no G0 pegou
antes de a tela quebrar, que era o propósito.

---

## O launcher continuava verde: o gerador para em `assets/icon/` (2026-08-27)

A entrada anterior gerou a marca azul e conferiu os hex — e o ícone do app continuou verde. O
gerador nunca esteve errado; ele simplesmente não alcança os artefatos que o sistema operacional
usa.

`build-icons.py` emite as **fontes**: `mobile/assets/icon/icon.png` e `icon_foreground.png`. Quem
transforma essas fontes nos ícones instalados é o `flutter_launcher_icons`, e ele só roda quando
alguém o chama. Ninguém chamou. Então os PNGs versionados de
`android/app/src/main/res/mipmap-*` e de `ios/Runner/Assets.xcassets/AppIcon.appiconset` (28
arquivos) seguiram com o gradiente verde→ciano e glifo escuro `#0B0E14`, e o
`values/colors.xml` seguiu com `ic_launcher_background: #1CB899` — o terceiro verde, que a entrada
anterior corrigiu no `pubspec.yaml` mas não no recurso Android que o `pubspec` alimenta.

`cd mobile && dart run flutter_launcher_icons` resolveu os 28 PNGs e o `colors.xml`, todos agora em
`#2C6485` com glifo branco.

**O `--check` passava porque olhava para o lugar errado.** Conferia `theme-color` e
`adaptive_icon_background`, que são entrada do gerador nativo, e nada da saída. Agora confere
também `ic_launcher_background` no `colors.xml`: dos três artefatos nativos ele é o único que é
texto, então é ele que denuncia o atraso do conjunto — se o `colors.xml` está na cor velha, os
PNGs ao lado dele também estão. Os PNGs continuam fora da comparação byte a byte, pelo mesmo
motivo de antes.

A lição é a mesma da entrada anterior, um nível acima: **gerar não é publicar.** Da primeira vez o
artefato existia no repo e não no `dist/`; desta vez existia em `assets/` e não no `res/`. Marca
muda em dois passos, e o segundo está escrito no CLAUDE.md.

---

## A marca nos ícones: favicon que nunca subiu e launcher com a cor antiga (2026-08-27)

Ao alinhar `mobile/assets/icon` com `web/public/favicon.svg` apareceram três coisas, e nenhuma era
estética.

**O favicon nunca chegou ao build.** `angular.json` tinha `"assets": []`, então `web/public/` não
era copiado para `dist/`. O `<link rel="icon" href="/favicon.svg">` no `index.html` apontava para um
404 em toda build publicada — o arquivo existia no repo e em lugar nenhum além dele.

**Favicon e launcher ainda traziam a marca abandonada.** Os dois carregavam o gradiente verde→ciano
(`#4ade80` → `#22d3ee`) com glifo escuro, a marca que o web largou na Etapa 1 e que o `AppLogo` do
mobile deixou de usar na Etapa 10. O `adaptive_icon_background` no `pubspec.yaml` era `#1CB899`, um
terceiro verde que não corresponde a token nenhum. Ou seja: o mesmo produto tinha três marcas — a
dos logos em app (`brand`, hoje `#2C6485`), a dos ícones e a do fundo adaptativo.

Pior, o glifo era escuro. Sobre o `brand` atual, cujo `ink-on-brand` é branco, o contraste estava
invertido.

**A causa era não haver gerador.** Os artefatos eram escritos à mão, então não havia o que
regerar quando a cor mudou — e ninguém percebeu. `design-tokens/build-icons.py` passa a emitir os
cinco a partir de `tokens.json`, com a mesma marca dos logos em app: quadrado arredondado,
`brand` de fundo, `trending-up` do Lucide em `ink-on-brand`.

Decisões de formato ficaram no script: `icon.png` e `apple-touch-icon.png` vão full-bleed e sem
alfa, porque launcher e iOS aplicam a própria máscara; a camada adaptativa do Android usa glifo
menor (42% contra 58%), porque só os 66% centrais são garantidos contra o recorte circular.

O `--check` do CI confere o favicon (texto, determinístico) e os dois hex que não cabem em token
— `theme-color` e `adaptive_icon_background`. **Não** compara PNG byte a byte: a rasterização muda
com a versão do Pillow e o job ficaria intermitente. O que precisa não divergir é a cor.

Junto, `index.html` ganhou fallback PNG, `apple-touch-icon` (iOS ignora favicon SVG na tela de
início) e `theme-color`.

---

## Paridade web/mobile: o quinto destino, o trilho de seção e a comparação por classe (2026-08-27)

Auditoria de UX/UI do web contra o mobile. Três coisas apareceram, e duas delas eram divergência
declarada de identidade, não estética.

**`/voce` não existia no desktop.** O header trazia quatro destinos; o bottom nav do mobile trazia
cinco. O avatar abria um modal com nome, e-mail e "sair" — nenhum caminho para Preferências,
Alertas ou Conta e dados. Na prática, um dos cinco destinos da arquitetura de informação só era
alcançável por URL digitada, pela busca global (Ctrl+K) ou por link vindo de outra tela. O mesmo
produto tinha quatro destinos num dispositivo e cinco no outro. `Você` entrou na navegação
principal e o modal do avatar ganhou as três sub-rotas — o bottom nav do mobile deixou de repetir
o item à mão e passa a ler a mesma lista.

**O desktop era o mobile esticado.** `layout.subnavWidth: 200` estava em `tokens.json` desde o
redesign, sem nenhum consumidor: a navegação de seção era pill horizontal em qualquer largura, e
Carteira, com sete seções, quebrava em duas linhas. Agora `SectionNav` projeta o conteúdo e vira
**trilho vertical a partir de 1024px**, consumindo o token. No trilho o item ativo é marcado por
posição (fundo `ground-2` e fio de marca à esquerda), não por preenchimento sólido — uma coluna de
blocos cheios competiria com o conteúdo ao lado. Abaixo de 1024px nada muda: a leitura no toque
continua sendo a de pills.

Na mesma linha, `/hoje` deixou de ser uma coluna única esticada até 1600px. A partir de 1280px a
narrativa (patrimônio → saúde → o que mudou → próxima ação) fica em coluna de largura de leitura e
**"Em destaque" vira painel complementar** à direita, separado por fio. A ordem de leitura da
narrativa não foi partida em duas colunas de propósito: ela é uma sequência, e coluna dupla a
embaralharia.

**A comparação tratava FII como ação.** `/descobrir/comparar` era uma tabela achatada em que
"Decisão" era só mais uma linha entre P/L e P/VP, e em que P/L e ROE de um FII apareciam como "—"
— indistinguível de dado que a fonte não trouxe. Agora a tela separa **decisão de evidência**: o
veredito, a classe e a régua de margem de segurança de cada ativo vêm primeiro, lado a lado; os
indicadores vêm depois, agrupados por Valuation, Qualidade, Risco e Proventos.

A diferença que importa é semântica: cada indicador declara **em que classe tem significado**.
Fora dela a célula diz "não se aplica a FII" por extenso, em vez de um traço. O melhor valor de
cada linha ganha um ponto de marca — comparação visual sem gráfico — mas só quando há direção
declarada e ao menos dois valores comparáveis: marcar o "melhor" entre um só é ruído, e empate não
tem vencedor. O recorte também passou a viver na URL (`?tickers=`), que a tela lia na entrada mas
nunca escrevia: uma comparação tem que ser um link salvável.

O mobile recebeu a mesma mudança conceitual — decisão acima, evidência agrupada, "não se aplica"
por extenso — mantendo a tabela com rolagem horizontal, que é a forma certa no estreito. A tabela
de significados virou `mobile/lib/core/compare_metrics.dart`, espelhando
`web/.../compare-metrics.ts`, e cinco testes travam a regra: P/L e ROE não se aplicam a FII nem a
ETF, P/VP se aplica a FII porque FII tem patrimônio, e nenhum indicador é declarado sem classe em
que valha. `AssetAnalysis` no Dart ganhou `assetType` — o backend já mandava `asset_type`, e o
cliente descartava.

**Score continua fora da comparação.** `/compare` devolve `AssetAnalysis`, que não carrega score —
ele vive em `Opportunity`. Mostrá-lo exigiria calcular no cliente, o que a arquitetura proíbe, ou
mudar o backend. Ficou declarado, não improvisado.

---

## Auditoria adversarial de segurança e integridade financeira (2026-08-26)

Varredura procurando ativamente o que estava errado, não confirmação do que estava certo. O
isolamento multi-tenant passou no exame — todo caminho de escrita e leitura resolve o tenant em
`storage/portfolio_store.py`, e os recursos com id inteiro na URL (renda fixa, proventos, sugestões
seguidas) filtram por `user_id` na cláusula, não depois. O que não passou foi a apuração fiscal e
o cálculo de retorno.

**A isenção de IR era apurada no mês errado.** `sum_gross_sales_this_month()` somava as vendas do
mês **corrente**, mas a API aceita `sold_at` retroativo em até 90 dias. Uma venda registrada hoje
com data do mês passado era conferida contra um mês que não é o dela: se o mês passado já tinha
estourado os R$ 20 mil, a venda aparecia isenta; e a partir do momento em que existisse venda
retroativa, os dois meses se contaminavam. Virou `sum_gross_sales_in_month(categoria, at=sold_at)`,
com limite superior no mês (`core/brt.month_bounds()`), porque o mês relevante é o **da operação**.

**Prejuízo de operação isenta entrava no saldo compensável.** A IN RFB 1.585 não deixa abater ganho
futuro com perda apurada em operação isenta — venda de ações BR dentro do limite mensal. O código
somava toda perda em `tax_loss_balances()`, então o saldo de compensação era maior do que a lei
permite e o IR devido saía **subestimado**. `calculate_sell_cost()` agora devolve
`loss_compensable`, gravado em `closed_trades.loss_compensable` (migração `0007`). Linhas antigas
recebem `true` de propósito: reapurar mês a mês o histórico e mexer em saldo fiscal retroativamente
é pior do que carregar o dado como está — a regra vale das próximas vendas em diante.

**Duas vendas simultâneas gastavam o mesmo saldo de prejuízo.** A isenção do mês e o prejuízo
disponível eram lidos, usados e só então gravados, sem trava. `portfolio_store.lock_tenant()` trava
a linha do usuário (`SELECT ... FOR UPDATE` no Postgres; no SQLite a escrita já é serializada) no
começo de `sell_position`.

**O TWR tratava venda como se só o custo tivesse saído da carteira.** `total_invested` é custo
(Σ quantidade × preço médio), então numa venda ele cai pelo custo baixado — mas o dinheiro que
saiu é o **produto** da venda. Sendo `ΔI = compras − custo_das_vendas`, o fluxo externo correto é
`ΔI − lucro_bruto_realizado`. Usar `ΔI` fazia venda com lucro virar retorno negativo e venda com
prejuízo, retorno positivo. Corrigido com `realized_gross_profit_between()`. Proventos ainda não
entram no fluxo — ver [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

**`/cache/clear` estava aberto a qualquer sessão autenticada.** O cache de mercado é global e
compartilhado entre tenants: uma chamada esvaziava tudo e forçava o universo inteiro a ser
recoletado da BRAPI, para todo mundo. `admin_router` ganhou `Depends(require_admin)`, com allowlist
em `ADMIN_USER_IDS` — sem allowlist, libera em `development` e nega em produção.

**`GET /alerts/check` escrevia.** Marcava `triggered_at`, e um GET que muda estado é disparado por
prefetch de navegador e por retry de proxy. O POST virou o caminho do web; o GET segue registrado
como `deprecated` por compatibilidade. Alertas também ganharam validação de ticker contra o padrão
da B3, teto de preço plausível e limite de 100 por usuário — cada alerta ativo é uma cotação
buscada a cada ciclo de 15 minutos.

**O resumo de oportunidades reiniciava o relógio sem enviar nada.** `mark_digest_sent()` rodava
mesmo quando o ciclo não achava nada para notificar, empurrando o próximo resumo por uma semana
inteira. Agora só marca se o push saiu.

Testes: 215 → 250. Três arquivos novos — `test_tax_compliance.py` (mês fiscal, isenção, prejuízo
compensável), `test_twr_flows.py` (fluxo de venda contra casos de retorno conhecidos) e
`test_tenant_isolation_resources.py` (cada recurso com id na URL, em GET/PUT/POST/DELETE, mais
token forjado e token expirado). Os testes de apuração e de TWR foram verificados contra o código
anterior: eles reprovam sem a correção.

---

## Redesign de UX/UI (2026-08-21 e 2026-08-22)

Auditoria completa de experiência e reformulação da arquitetura de informação nas duas
plataformas. Os documentos de projeto estão em [design/](design/). O log de execução que existia
ao lado deles foi removido em 2026-08-28 — era uma terceira fonte de verdade sobre status, e tinha
divergido; o que está aberto vive em [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

O resumo do que mudou de contrato ou de estrutura:

- **Web: 6 rotas → 36.** Cinco destinos por intenção (`/hoje`, `/carteira`, `/descobrir`,
  `/estrategia`, `/voce`) mais `/ativo/:ticker`. `/market` dissolvido; as tabs que guardavam
  estado em `signal` viraram rotas. URLs antigas seguem como redirect.
- **Mobile: 4 abas → 5 destinos, 19 rotas.** `market_screen`/`rebalance_tab` removidos;
  Estratégia criada (não existia em nenhuma plataforma).
- **Estratégia e Quick Invest do web voltaram a existir.** `strategy.component` nunca tinha sido
  roteado — era código morto de 1092 linhas, apesar de `GET /strategy` e `POST /quick-invest`
  estarem no ar.
- **Contrato (aditivo):** `consensus_methods` em `FairPriceBlock` e `trend_basis` em
  `TechnicalBlock`. Os dois eram calculados e descartados em silêncio por
  `Modelo(**resultado.__dict__)`, porque o Pydantic ignora chave não declarada. Regressão em
  `test_fair_price.py`.
- **Cliente Dart:** `RebalanceSuggestions` passou a ler `allocation_gaps`, que também era
  descartado. Regressão em `test_allocation_gap_test.dart`.
- **Design tokens gerados** de `design-tokens/tokens.json` para CSS, TypeScript e Dart, com job
  próprio no CI. A régua de score havia divergido entre web e mobile por ser mantida à mão em três
  arquivos.
- **Removidos por não terem consumidor:** `dip.component` (485 linhas, renderizava IA e notícias
  cujo backend saiu em 2026-08-19), `market.component`, `analyze-asset`, `assets.component`,
  `config.component`, `SkeletonComponent`, `EmptyStateComponent`.
- **Defeitos silenciosos corrigidos:** `.card`, `.btn-primary`, `.btn-secondary` e
  `.pagination-btn` eram usados em 13 templates e **não existiam em nenhum CSS**; cinco variáveis
  CSS inexistentes em `assets.component.scss`; 16 ícones Lucide não registrados (seis anteriores ao
  redesign); `rgba(var(--accent) / 0.5)`, sintaxe inválida desde sempre.

---

## Auditoria de produto e engenharia (2026-08-19 → 2026-08-20)

### Correção de premissa

O documento anterior (e o `CLAUDE.md`) afirmava que não havia testes automatizados relevantes.
Havia — e agora são **206**, rodando em CI (`.github/workflows/ci.yml`: ruff + pytest no backend,
build e formatação no web, analyze + test no mobile) em todo push. O `conftest` também deixou de
stubar `get_dividends → []` e `get_history → {}`: PETR4 traz histórico de proventos e série de
preços, então a bateria passa pelo caminho onde os bugs de valuation moravam.

### Achados P0 — todos resolvidos

| Achado | Resolução |
|---|---|
| D1/D2 — renda fixa sem rendimento e presa ao `localStorage` | Tabela `fixed_income_positions` + CRUD `/fixed-income`, marcada a mercado no backend reusando `analyze_one()`. `AssetType.renda_fixa` criado (as posições apareciam como `br_stock`). Posições `RF_*` legadas removidas pela migração `0002`. |
| D3 — dois caminhos de perda da carteira inteira | `POST /portfolio/position` e `DELETE /portfolio/position/{ticker}` como escrita por item; `PUT /portfolio` fica só para importação e **rejeita lista vazia**. Mobile: FAB só com `dashboard.hasValue` e cadastro por item. Web: o branch de erro não marca `_initialized`, mostra banner e bloqueia edição. |
| D4 — quatro erros de unidade/janela no preço justo | Média de dividendos sobre anos-calendário completos com denominador correto; DY somando os últimos 12 meses **por data**; guard do DCF aceitando percentual; `range` do histórico configurável com degradação, e tendência de curto prazo rotulada quando falta série para a SMA200. |
| D5 — cache global com cálculo personalizado | O cache passou a guardar **dado de mercado** por ticker; preço justo e score são calculados por request. As metas de yield voltaram a ter efeito e o cálculo deixou de vazar entre tenants. |
| POST `/api/cache/clear` público | Movido para o `admin_router`, dentro do router protegido. `jwt_secret` default agora aborta o startup fora de `development`. |
| `cash_available` destruído a cada salvamento | Campo entrou em `PreferencesRequest` e o PUT passou a ser parcial (`exclude_unset`). |
| `/projection/passive-income` devolvendo zero | Era `item.ticker` sobre um dict; o `AttributeError` caía num `except` e virava `continue`. Corrigido, com `gather` sobre as posições. |

### Demais dores (D6–D10)

- **D6** — benchmark passou a usar retorno **ponderado no tempo**: aporte não é mais
  rentabilidade. A resposta expõe `method` e `net_contributions`.
- **D7** — a escrita de snapshot saiu do caminho de request (`services/snapshot_job.py`, job
  diário com lock), sempre sobre `list_positions()` + renda fixa. O cliente não controla mais o
  que entra na série histórica.
- **D8** — pesos do score renormalizados sobre as dimensões disponíveis, com
  `data_completeness` na resposta; a UI mostra score incompleto em cinza com o motivo.
- **D9** — % do CDI multiplicativo, IPCA+ compondo inflação, constante única de dias por mês,
  benchmark `0.85` substituído por dois números explícitos, liquidez no critério de melhor
  opção, e o cálculo duplicado no Angular **apagado**.
- **D10** — alertas agrupados com contagem, teto e uma ação cada; régua única de score nas três
  plataformas; setor traduzido nos alertas do backend; `confidence`/`data_years`/
  `consensus_methods` expostos ao lado de todo veredito.

### Itens acima que ficaram obsoletos

- **Item 1 (testes)** — ver "Correção de premissa".
- **Item 3 (duplicação de regra de RF)** — resolvido: `calcularRendimento()`/
  `calcularValorFinal()` foram removidos do Angular. A cadeia de `computed()` que dependia deles
  foi reescrita sobre `GET /fixed-income`, que já devolve tudo marcado a mercado.
- **Item 8 (labels duplicados)** — segue estrutural (TS↔Dart), mas os pontos que mais divergiam
  ganharam fonte única de referência: régua de score e tradução de setor existem nos três lados
  com o mesmo valor, e o backend deixou de emitir setor cru.
- **Item 14 (`create_all` não migra colunas)** — obsoleto: **Alembic** foi introduzido
  (`backend/migrations/`). `init_db()` marca bancos pré-Alembic na revisão baseline e aplica as
  migrações. A ressalva sobre "default simples" não vale mais — migração com backfill agora é
  suportada (a `0004` faz isso).
- **Item 16, último bullet (`DELETE /notifications/register-token`)** — a rota **voltou**, agora
  com consumidor: o logout do mobile desregistra o aparelho. Sem isso, depois do logout o
  aparelho continuava recebendo o resumo de carteira da conta anterior.

### Features entregues


#### "O que mudou" — primeiro bloco do Dashboard
`GET /whats-new` compara o estado atual com o anterior e devolve até 5 linhas: variação de
patrimônio (já descontando aportes), posições com sinal de venda, vencimento de renda fixa
próximo, categoria fora da meta, prejuízo disponível para compensar IR e destaque de
oportunidade. **Cada linha tem uma ação** que leva à tela onde a decisão acontece. Sem nada a
dizer, o bloco diz isso — em vez de sumir. Web e mobile.

#### Renda fixa de verdade (`/fixed-income`)
Tabela própria no servidor com tipo, valor, taxa, tipo de taxa, % do CDI, data de aplicação,
vencimento, liquidez e isenção. **Marcada a mercado no backend**: rendimento acumulado, valor
hoje, projeção até o vencimento e aviso de vencimento próximo. Entra no patrimônio total, no
P&L, na alocação, na saúde da carteira, na projeção de renda passiva e no Quick Invest.
Cadastro no web (`/assets/cadastro`) e tela dedicada no mobile.

#### Proventos recebidos
Antes todo número de renda era estimativa derivada de dividend yield. Agora dá para lançar o
que caiu na conta (`/dividends/received`), ver total do mês, dos últimos 12 meses, média
mensal, quebra por ativo — e **confrontar com a estimativa do próprio app**.

#### Renda fixa × bolsa na mesma tela (Mercado → Ferramentas → RF x Bolsa)
"Com a Selic a 14,4%, vale mais o CDB ou o FII?" — ambos os lados na mesma unidade (renda
recorrente líquida a.a.), com valorização potencial mostrada **separada** (renda fixa não tem, e
a tela diz isso) e um veredito em texto.

#### Resultado das sugestões seguidas (Mercado → Rebalanceamento)
Registre o que você executou a partir de uma sugestão e o app mostra o resultado contra o
Ibovespa, agregado por origem da sugestão. Torna o produto auditável por quem usa.

#### Compensação de prejuízo de IR
Prejuízo realizado passa a abater ganho futuro da mesma categoria, como a legislação permite —
o app superestimava o IR devido de quem já havia realizado prejuízo. O saldo por categoria
aparece em Operações Encerradas, e cada venda mostra quanto foi compensado.

#### Proveniência e frescor do dado
Ao lado de cada veredito: anos de proventos encontrados, quantos métodos entraram no consenso e
confiança. Score com dado incompleto sai **cinza** e rotulado "sem dado" em vez de
colorido com a nota. O dashboard mostra a idade das cotações e se o CDI/Selic vem do BCB ou é
estimativa.

#### Alertas com desfecho
Agrupados por tipo, com contagem e teto de 4 — e cada um com uma ação (ver análise, simular
venda, rebalancear, ajustar meta). Antes eram alertas sem limite e a única ação da tela era ir
para Mercado.

#### Cadastro separado de análise (web)
`/assets` é leitura (o retorno diário); `/assets/cadastro` é escrita (tarefa rara), com
salvamento explícito por linha. O autosave por debounce sobre um PUT destrutivo saiu.

#### Desktop mais aproveitado
Tabela de posições ordenável por qualquer coluna, seleção de até 4 ativos para comparar (leva
direto ao comparador) e exportação CSV da carteira.

#### Quick Invest no mobile
"Recebi meu salário, onde aporto" foi implementado primeiro no web, apesar de ser um caso de uso
mais de celular. Disponível no mobile em Mercado → Ferramentas. **Nota de 2026-08-21:** a versão
web nunca foi alcançável — vive dentro do `strategy.component` não roteado (ver acima), então
hoje o Quick Invest é de fato mobile-only.

#### Push honesto no web
A tela de Configurações agora informa que notificações requerem o app instalado, em vez de
oferecer cadência e alerta sem efeito para quem usa só o navegador. E o logout no app
desregistra o aparelho, que antes continuava recebendo o resumo da conta anterior.

#### Qualidade de dado (`GET /data-quality`)
Taxa de preenchimento por campo no universo, com o impacto de cada ausência descrito — a
instrumentação que faltava para distinguir "o modelo está errado" de "o dado não chegou".

---

## Remoção de Finnhub/CoinGecko/Gemini, BDR-only e adição de ETF (2026-08-19)

Pedido do usuário: simplificar as fontes de dados para só **BRAPI + BCB SGS**, unificar toda exposição internacional em **BDR** (removendo `us_stock`/Finnhub) e remover **cripto** (`crypto`/CoinGecko) por completo, adicionando uma nova classe de ativo **ETF** com categoria de alocação própria.

- **Enums**: `AssetType` perdeu `us_stock`/`crypto`, ganhou `etf`. `AssetCategory` perdeu `cripto`/`acoes_int`, ganhou `etfs`/`bdrs`. A categoria antes chamada `acoes_int` foi **renomeada de verdade para `bdrs`** (não só o texto visível) — decisão tomada no mesmo dia, já que o sistema não tinha usuários em produção ainda: nenhum dado real de `Goal.category`/`PortfolioPosition.category` para migrar, então **sem alias legado** — `_LEGACY_MAP`/`resolve_category()` não ganharam entrada `acoes_int`→`bdrs` (seria proteção para um cenário que não existe).
- **Detecção (`collectors/universal.py::detect_type`)**: sem Finnhub, não há mais fallback "internacional genérico" — ticker que não bate BDR/FII/unit/br_stock/`KNOWN_ETFS` levanta `UnsupportedTickerError` (400/404 explícito na API, ignorado silenciosamente em varreduras em lote que já tratavam exceção por item). ETF é detectado via `KNOWN_ETFS` (lista curada, mesmo papel que `KNOWN_UNITS` tem para units) e via `subType` da BRAPI em `core/universe.py`.
- **Fair price/score/dip (`analysis/`)**: ETF não tem EPS/book_value de empresa — fair price usa só `bazin` (dividend yield histórico, sem Graham/DCF); `scoring.py::_score_etf` usa dividend yield + liquidez (sem value/quality/growth tradicionais); `dip_analysis.py` reusa o ramo padrão (o `_crypto_score` dedicado foi removido).
- **IR (`optimizer/cost_calculator.py`)**: ETF e BDR (`AssetCategory.bdrs`) tributados a 15% flat sem isenção mensal; a isenção de R$35k/mês de cripto deixou de existir.
- **Gemini removido por completo**: `app/llm/gemini_client.py` deletado; `collectors/news.py::analyze_news_with_ai` e `analysis/strategy.py::_rank_category_opportunities` promoveram o fallback determinístico (que já existia e era testado) a caminho único — não há mais tentativa de chamada de IA externa.
- **Preferences**: `desired_yield_int` renomeado para `desired_yield_bdr` (nome antigo era um resquício de quando a categoria cobria BDR+ações US) em `PreferencesDb`/`Preferences`/`PreferencesRequest`/`portfolio_store.py`; nova coluna `desired_yield_etf` (default 0.04). Ambas cobertas automaticamente por `_add_missing_columns()` no próximo boot — sem migração manual (a coluna antiga `desired_yield_int`, se já existir em algum banco, fica órfã e sem uso).
- **Sem script de limpeza de dados**: um script de migração (`cleanup_crypto_us_stock.py`) foi escrito, validado manualmente contra o SQLite de dev (dry-run e execute) e depois **removido** no mesmo dia — o sistema ainda não tem usuários em produção, então não existe posição real de `crypto`/`us_stock` para apagar; mantê-lo seria código morto para um cenário que não existe. Se o sistema já estiver em uso quando `crypto`/`us_stock` precisarem ser removidos de novo (não é o caso aqui, é só uma nota para o futuro), esse script precisaria ser reescrito do zero — recuperável via git history desta mesma data, não existe mais no código atual.
- **Web/mobile**: `AssetType`/`AllocationCategory` (TS) e os mapas de label/ícone/cor espelhados (`ui-helper.service.ts` ↔ `labels.dart`, ver item 8 abaixo) perderam `us_stock`/`crypto`/`cripto`/`acoes_int` e ganharam `etf`/`etfs`/`bdrs`. `desired_yield_int`→`desired_yield_bdr` e o form control `yield_int`→`yield_bdr` (web) / `desiredYieldInt`→`desiredYieldBdr` (mobile) renomeados junto. Corrigido de brinde: `strategy.component.ts::assetLabel` não tinha entrada para `bdr` (caía cru na tela de Estratégia).
- Suite de testes (`pytest -q`, 87 testes), `ruff check` e `flutter analyze` passando; build do Angular (`ng build`) validado sem erros de tipo.

---

## Score de oportunidades unificado, cadência de notificação e limpeza de "caixa disponível" nas Oportunidades (2026-08-19)

Pedido do usuário: usar todos os indicadores calculáveis no score de oportunidade, permitir configurar cadência de ajuste de carteira (diária/semanal/mensal) e considerar preferências de ativos/categorias na recomendação.

- **`opportunity_service.py` parou de usar um score ad-hoc** (`mos*60 + dy*1.5 + rsi_bonus*10 + trend_bonus`) e passou a chamar `scoring.py::score_opportunity()` — combina margem de segurança, qualidade (ROE/margem), endividamento, crescimento de receita, dividend yield e técnico, ponderados por perfil de risco (`OPPORTUNITY_WEIGHTS`). `score_company()`/`rank()` (baseados em P/L·P/VP) continuam no arquivo mas seguem sem nenhum consumidor real — candidatos a remoção numa próxima rodada se continuarem órfãos.
- **`PreferencesDb` ganhou** `risk_profile`, `preferred_categories`, `preferred_sectors`, `excluded_tickers` (boost de +5/+3 no score por categoria/setor preferido; exclusão remove o ticker da lista e do resumo de notificação) e `opportunities_frequency` (`off`/`daily`/`weekly`/`monthly`, substitui o booleano `notify_new_opportunities`). `notify_price_alerts` continua imediato (é alerta de risco, não sugestão de ajuste).
- **`notification_job.py`**: alertas de preço continuam a cada ciclo de 15min; o resumo de oportunidades só dispara quando a cadência configurada venceu desde `last_digest_sent_at`, agregando as melhores em um único push (antes eram até 3 pushes individuais por ciclo).
- **Vestígio morto removido**: `cash_available` de `PreferencesDb` nunca foi resettável de fato desde a remoção de 2026-08-12 (ver seção abaixo) — `PUT /preferences` nunca recebia esse campo, então ficava sempre em 0. Isso tornava `Opportunity.suggested_quantity`/`suggested_invest` e `OpportunitiesResponse.cash_available` permanentemente inertes (a condição `cash > 0` nunca era verdadeira), incluindo o bloco correspondente em `dashboard.component.html` que nunca renderizava. Removidos dos dois lados (backend e web) — a coluna `cash_available` na tabela `preferences` continua existindo (sem migração de drop), mas nada mais a lê para esse fim.

---

## Ajustes de usabilidade — caixa/metas/notificações/mercado/IA (2026-08-12)

Pedido do usuário para simplificar e corrigir usabilidade em mobile/web/backend:

- **"Caixa disponível" removida** — nunca ficava atualizada como preferência persistida. Quick invest e `/strategy` agora recebem o valor pontualmente na requisição (query param `cash_available` em `/strategy`, corpo em `/quick-invest`), não mais de preferences. `DashboardSummary.cash_available` removido da resposta do backend e dos models web/mobile.
- **Notificação de teste removida** (ver seção anterior); pushes reais ganharam campo `type` consistente (`price_alert`, `new_opportunity`) no payload `data`, preparando terreno para novos tipos.
- **Metas por categoria/setor** saíram do Dashboard e passaram a aparecer só em Ativos, que ganhou agrupamento por categoria/setor com indicador "atual X% · meta Y%" (mobile e web). Edição de metas continua em Configurações.
- **Autocomplete de ticker** ligado na busca do Mercado (mobile e web) e, na rodada seguinte (ver abaixo), também no diálogo de criar alerta de preço — reusando `TickerAutocompleteField`/`searchTickers()` já existentes, sem endpoint novo.
- **Estratégia de IA** (`analysis/strategy.py::build_investment_strategy`) deixou de escolher só a primeira oportunidade disponível por gap de alocação — agora usa o Gemini (`rank_opportunities_for_gap` em `llm/gemini_client.py`) para ponderar score/DY/margem de segurança/sentimento de notícias entre as candidatas do gap, com fallback determinístico (ordem por score) se a chamada falhar ou o Gemini estiver indisponível.
- **Regressão real encontrada e corrigida no mesmo dia**: `DashboardSummary.fromJson` no mobile ainda fazia cast não-nulo de `cash_available`, que o backend parou de enviar — quebrava Dashboard e Meus Ativos com `type Null is not a subtype of type num`. Motivou a rodada de testes de API abaixo.

---

## Robustez e usabilidade — testes de API, split do market, limpeza, evolução de patrimônio (2026-08-12)

- **Testes de API** — ver item 1 da lista de débito técnico, acima.
- **`market.component` quebrado em subcomponentes** — ver item 4 da lista de débito técnico, acima.
- **`opportunities.component` (web) removido** — código morto confirmado (só era exportado pelo barrel `components/index.ts`, sem nenhum consumidor real nas rotas ativas).
- **Gráfico de evolução de patrimônio**: dado já existia (`PortfolioSnapshot`, embutido em `GET /dashboard`/`GET /portfolio`, sem endpoint novo). Web trocou o SVG manual (`snapshotPath()`/`snapshotAreaPath()` em `ui-helper.service.ts`, removidos) por `PatrimonyChartComponent` (segue a skill `dataviz`: crosshair, tooltip, tabela alternativa para acessibilidade, cores 100% via tokens de tema). Mobile ganhou a mesma visualização do zero (não existia nada antes) via `fl_chart` em `dashboard_screen.dart`.

---

---

## Mobile — auto-login, splash animado, Configurações por módulos, diagnóstico de push (2026-08-11)

- **Auto-login corrigido**: o app sempre abria em `/login`, mesmo com sessão válida salva (`AuthService.readToken()` nunca era checado no boot). Novo `authStatusProvider` (`core/providers.dart`) lê o token salvo e, se existir, valida contra o novo endpoint `GET /auth/me` (também restaura o perfil do usuário sem precisar logar de novo). Nova `SplashScreen` (`features/auth/splash_screen.dart`) é a rota inicial (`/splash`) e decide automaticamente entre `/dashboard` (token válido) e `/login` (sem token ou token expirado/inválido — nesse caso desloga localmente).
- **Visual do login/splash**: novo `core/widgets/brand_background.dart` (glow radial nas cores da marca) e `core/widgets/brand_loading_indicator.dart` (logo pulsando, sem depender de pacote de animação) substituem o fundo liso e o `CircularProgressIndicator` genérico. Tagline trocada de "Análise de investimentos B3 na sua mão" (mencionava só B3) para "Ações, FIIs, cripto e renda fixa — tudo em um só assistente" (decisão do usuário, cobre o escopo real do app).
- **Configurações reorganizada em módulos** (`_SettingsCard`): Conta, Aparência, Preferências financeiras, Notificações, Metas de alocação por categoria, Metas de alocação por setor, Alertas de preço — cada um em um `Card` com cabeçalho ícone+título, substituindo a `ListView` plana de `Divider`s. Nenhuma lógica interna das seções (`_GoalsSection`, `_SectorGoalsSection`, `_AlertsSection`) foi alterada.
- **Diagnóstico de push**: novo botão "Enviar notificação de teste" no módulo Notificações, chamando `POST /notifications/test` (novo endpoint — busca os tokens do usuário atual via `list_device_tokens(user_id)` e usa `send_push` já existente). A resposta distingue os dois pontos de falha possíveis: `tokens_found == 0` → o token nunca foi registrado no servidor (permissão negada ou erro de rede no aparelho); `tokens_found > 0` mas nada chega → problema de credencial/entrega no servidor (conferir `FIREBASE_SERVICE_ACCOUNT_JSON` no Railway). `notifications_service.dart` agora guarda `permissionStatus`/`tokenRegistered`/`lastError` em vez de só logar com `debugPrint`. **Removido em 2026-08-12** (decisão do usuário: a integração já estava validada, o botão de teste não tinha mais utilidade) — `POST /notifications/test` e o botão não existem mais; `permissionStatus`/`tokenRegistered`/`lastError` permanecem, ainda usados pelo fluxo real de registro de push.
- **Bug real corrigido**: faltava `com.google.firebase.messaging.default_notification_channel_id` no `AndroidManifest.xml` — sem isso, pushes recebidos com o app em background caem no canal de fallback do FCM em vez do canal `fiance_default` já criado em `notifications_service.dart` (não impedia a entrega, mas descasava o canal/importância).
- **Ainda não verificado end-to-end**: se `FIREBASE_SERVICE_ACCOUNT_JSON` está de fato salvo no ambiente do Railway (só confirmamos que funciona com o `.env` local) — o botão de teste (removido em 2026-08-12, ver acima) era a ferramenta pra descobrir isso sem adivinhar; sem ele, essa verificação exigiria olhar os logs do backend em produção diretamente.

---

## Assistente de finanças — venda/P&L realizado/IR + explicações educacionais (2026-08-10)

Pedido do usuário: transformar o produto em assistente de finanças mais completo (registrar venda de ativos, explicações mais ricas, notificações push). Planejado em 3 fases (ver plano salvo na sessão); Fases 1 e 2 executadas nesta sessão, Fase 3 (push) depende de credenciais do Firebase que só o usuário pode gerar.

**Fase 1 — venda de ativos, P&L realizado, IR, trade log:**
- Nova tabela `closed_trades` (`ClosedTradeDb`), sem migração manual (o projeto usa `Base.metadata.create_all()`).
- `cost_calculator.calculate_sell_cost()` ganhou o parâmetro `gross_value_month_before` para aplicar corretamente a isenção mensal de IR (R$20k ações BR, R$35k cripto) sobre o **acumulado do mês**, não por transação isolada como antes (uso só em simulação de estratégia).
- Novos endpoints `POST /portfolio/sell` e `GET /portfolio/trades`. Nova função de storage `reduce_position_quantity()` (decrementa ou remove a posição ao vender).
- Web e mobile: botão "Vender" por posição (parcial ou total) + seção "Operações Encerradas" com totais de lucro/prejuízo realizado e IR pago.
- 5 novos testes (`test_cost_calculator.py`, `test_portfolio_sell.py`) cobrindo isenção mensal acumulada e o fluxo completo de venda (parcial, total, quantidade insuficiente, ticker inexistente).

**Fase 2 — explicações educacionais (usa o que já existia, sem nova lógica de negócio):**
- Web: `p.reasons` (já vinha da API, nunca era exibido) agora aparece expansível ao clicar na pill de Decisão em Meus Ativos; tooltip de glossário adicionado no cabeçalho "P. justo".
- Mobile: `PortfolioPosition.reasons` adicionado ao model (fonte já mandava o campo, só faltava mapear); botão "Por quê?" no card de ativo abre um bottom sheet com os motivos. Novo `core/glossary.dart` (espelha 1:1 o glossário do web) + widget `core/widgets/help_tooltip.dart` (toque em vez de hover, adequado a touch); tooltips de DY e MS adicionados nos cards de Oportunidades.

**Fase 3 — notificações push (alertas de preço + novas oportunidades):**
- Usuário criou o projeto Firebase (`fiance-89340`) e forneceu `google-services.json` (`mobile/android/app/google-services.json`, **não commitado** — está no `.gitignore` do mobile). Plugin `com.google.gms.google-services` aplicado em `settings.gradle.kts`/`app/build.gradle.kts`; `minSdk` elevado para 23 (exigido por `firebase_messaging`); core library desugaring habilitado (exigido por `flutter_local_notifications`).
- Mobile: `firebase_core`, `firebase_messaging`, `flutter_local_notifications` adicionados. `core/notifications_service.dart` inicializa o FCM, pede permissão, registra o token no backend (`POST /notifications/register-token`) logo após entrar na `AppShell` (ou seja, só com usuário autenticado), reage a `onTokenRefresh`, e mostra notificação local quando o app está em primeiro plano. Toggles "Notificar alertas de preço" / "Notificar novas oportunidades" em Configurações.
- Backend: nova tabela `device_tokens` (token FCM por usuário, com realocação se o mesmo token aparecer para outro usuário — troca de conta no aparelho) e `notified_opportunities` (evita notificar a mesma oportunidade repetidamente). `PreferencesDb` ganhou `notify_price_alerts`/`notify_new_opportunities` (default `True`). `app/notifications/push.py` encapsula o Firebase Admin SDK — **se `FIREBASE_SERVICE_ACCOUNT_JSON` não estiver configurado no `.env`, o envio é apenas logado, não falha** (mesmo padrão de degradação graciosa usado em `gemini_client.py` para a IA opcional). `app/services/notification_job.py` roda a cada 15 min (`asyncio.create_task` em `main.py`, sem dependência externa de scheduler) verificando alertas de preço não disparados (reaproveita a lógica de `alerts.py::check_alerts`, e agora **de fato marca `triggered_at`**, que antes existia no schema mas nunca era setado) e oportunidades novas (`STRONG_BUY` ou score≥75+DY≥6%, limitado a 3 por ciclo por usuário para não inundar).
- **Concluído (2026-08-11):** usuário gerou a chave de conta de serviço e ela foi configurada em `FIREBASE_SERVICE_ACCOUNT_JSON` no `.env` local do backend (não commitado — `.env` já é gitignored). Validado que o Firebase Admin SDK inicializa de verdade com a credencial (`_get_firebase_app()` retorna uma instância válida). **Em produção (Railway ou outro host), a mesma variável de ambiente precisa ser configurada manualmente** — o `.env` local não é deployado. Também não há suporte iOS ainda (só `google-services.json`/Android; faltaria `GoogleService-Info.plist` se o app for publicado na App Store).
- 9 novos testes (`test_push.py`, `test_notification_storage.py`) cobrindo o fallback sem credencial e o CRUD de tokens/oportunidades notificadas.

---

## Unificação visual web↔mobile — Fase 1 (2026-08-10)

Varredura visual completa encontrou: paletas de cor divergentes entre web e mobile (nenhuma cor de marca/ganho/perda/categoria batia, exceto na logo), mobile sem dark mode (tema indigo padrão do Material, não a marca verde/ciano), ícones de navegação diferentes, e uma **inconsistência interna no próprio web** (`categoryBarColor()` tinha FIIs e Cripto trocados em relação a `categoryBarClass`/`categoryColor`).

Ações tomadas (só tokens de design — sem reestruturar telas, por decisão do usuário):
- `web/src/app/core/services/ui-helper.service.ts::categoryBarColor()` corrigido para bater com as outras 3 funções de cor de categoria (FIIs=laranja, Cripto=amarelo).
- `mobile/lib/core/theme.dart` (novo) — tokens espelhando 1:1 as CSS custom properties de `web/src/styles.css` (`--bg`, `--panel`, `--accent`, `--accent-2`, `--warn`, `--danger`, `--radius`), para dark e light. Fonte trocada para Inter (`google_fonts`), igual ao web.
- `mobile/lib/core/theme_provider.dart` (novo) — dark como padrão + toggle persistido (`shared_preferences`), espelhando `theme.service.ts`. Toggle exposto em Configurações.
- `mobile/lib/core/labels.dart` — cores de categoria trocadas para os hex exatos do Tailwind `*-400` usados no web (`acoes_int` e `fiis` e `cripto` estavam com cores erradas: `fiis` era âmbar em vez de laranja, `cripto` era rosa em vez de amarelo).
- Cores de ganho/perda/alerta hardcoded (`Colors.green.shade700`/`Colors.red.shade700`/etc., ~20 ocorrências em 9 arquivos) substituídas por `gainColor()`/`lossColor()`/`warnColor()` do tema — reagem automaticamente ao dark/light mode agora.
- Ícones de navegação (`app_shell.dart`) trocados para os equivalentes Material mais próximos dos ícones Lucide do web (`briefcase`→`work_outline`, `target`→`track_changes_outlined`).
- `pubspec.yaml`: adicionadas `google_fonts` e `shared_preferences`.
- Validado com `flutter analyze` (0 erros, só warnings pré-existentes não relacionados) e `flutter build apk --debug`.

**Não feito nesta fase** (ficou fora do escopo combinado): quebra de `market.component.html` (1627 linhas) e dos arquivos grandes do mobile em componentes menores; padronização de espaçamento/`BoxDecoration` no mobile (ainda cada widget define os próprios valores, sem spacing scale); teste visual manual completo em dispositivo/emulador (recomenda-se rodar `flutter run` e navegar as 4 abas em dark e light antes de considerar fechado).

---

## Correções anteriores a 2026-08-10

Levantadas na primeira varredura do projeto (2026-07) e todas resolvidas depois:

| Limitação (registrada em 2026-07) | Status |
|---|---|
| BDR (ex. AAPL34) classificado como `br_stock`; units (SANB11, TAEE11, BPAC11...) classificadas como `fii` | ✅ **Corrigido.** `collectors/universal.py::detect_type()` testa BDR antes de FII; set `KNOWN_UNITS` trata as units conhecidas como `br_stock`; camada extra em `_fetch_brapi` reclassifica por nome (`UNIT/UNT/UNITS`) se necessário. |
| CDI fixo 13,5% no web vs 14,40% no backend | ✅ **Corrigido.** Ambos convergem via `GET /renda-fixa/taxas` → `collectors/rates.py` (BCB SGS real, fallback 14.40). O `signal(14.4)` no Angular é só valor inicial pré-fetch. |
| `fair_price` aplicando Graham em FII | ✅ **Corrigido.** FII usa exclusivamente `[bazin, pvp_fair]`; Graham só roda para ações BR/internacionais. |
| Fundamentos de BDR inconsistentes (LPA/VPA na escala do recibo, não da ação-mãe) | ✅ **Resolvido (validado com dado real em 2026-08-10).** Testado AAPL34 (BRAPI) vs AAPL (Finnhub): a BRAPI já retorna EPS escalado ao próprio preço da BDR (P/E implícito ≈33,8 vs P/E real da Apple ≈35,5 — coerente). `book_value` costuma vir `None` para BDRs na BRAPI (gap de dado, não erro de escala); `graham_fair_price()` já trata isso retornando `None` quando falta book_value, e o DCF segue funcionando só com EPS. Nenhuma correção de código necessária — a causa raiz (yfinance) já não existe mais. |
| Componentes compartilhados (RF form, allocation-view) não extraídos | ✅ **`market.component` corrigido em 2026-08-12** — quebrado em subcomponentes (`opportunities-list`, `dip-scanner`, `analyze-asset`, `renda-fixa`, `dip-analysis-modal`), sem mudança de comportamento. `quick-invest`/`investment-strategy` foram removidos de Mercado em 2026-08-19 (ver item novo abaixo), não existem mais como subcomponentes dessa tela. `assets.component.html`/`strategy.component.html` ainda têm formulários inline sem extração — não fizeram parte desta rodada. |
