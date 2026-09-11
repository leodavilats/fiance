# fiance — o que está aberto

> **Só pendências.** Todo item aqui foi verificado contra o código em **2026-09-11**; nada de
> histórico, nada de ✅. O que já foi resolvido — e por quê — está em [CHANGELOG.md](CHANGELOG.md).
>
> A revisão de **2026-09-08/09** fechou seis itens (paridade de nome, proveniência no nível
> errado, `FairPrice`, os nomes de arquivo, o `FEATURES.md` desatualizado e a metade da home
> pública) e **corrigiu dois que estavam errados**: o item 5 afirmava que o auto-deploy de
> produção estava desligado na API — a configuração diz que não —, e o item 26 media um
> `opacity: 0.5` que já não existia. Os números liberados foram reaproveitados, como já é
> convenção aqui.
>
> A revisão de **2026-09-11** fechou dois itens do redesenho de interface — o tipo solto
> (catraca em zero) e "fio + chão" no mobile (nenhum `Card`/`ListTile`/`CircleAvatar` de layout
> restante) — e trocou o assunto de outros dois: o 7 passou a ser o controle de formulário do
> Material sem componente próprio, e o 8, a base do preço justo nas telas de posição. O **12**
> saiu inteiro: a tabela de posições que ele descrevia era do front, e o front não existe mais.
> Seu número fica livre para reuso.
>
> Este arquivo tem uma tendência conhecida a apodrecer. Na revisão de 2026-08-28, **oito dos 24
> itens já estavam feitos** — onboarding, busca global, drawer de atividade, gráfico de preço,
> reestruturação das telas mobile e indicação estavam descritos como inexistentes, e três outros
> descreviam um escopo maior do que o que ainda falta. É a mesma doença que motivou a reescrita de
> 2026-08-22, seis dias antes. **Ao fechar um item, apague-o daqui** e registre no CHANGELOG; item
> resolvido que fica é pior que item ausente, porque manda trabalho refazer o que existe.

## Limitações de dado e infraestrutura

1. **O caminho do Redis não foi exercitado contra um servidor real fora do CI.** O cache tem
   backend trocável (`core/cache_backends.py`): arquivo local por padrão, Redis quando `REDIS_URL`
   existir. O contrato é escrito uma vez e rodado contra os dois, e o CI sobe um Redis de serviço —
   mas **em produção ele nunca rodou**, porque ainda há um nó só. Coberto: o contrato e a tradução
   do adaptador (prefixo, envelope, padrão SQL virando glob). Não coberto: rede instável,
   reconexão e failover.

2. **`BRAPI_HISTORY_RANGE` default `3mo` torna a SMA200 incalculável.** O plano gratuito da BRAPI
   só aceita ranges curtos. O sistema é honesto sobre isso (`trend_basis` = `short`, rotulado na UI;
   `GET /data-quality` reporta a cobertura), mas tendência de longo prazo só existe de fato com
   plano pago e `BRAPI_HISTORY_RANGE=2y`.

3. **Metade dos fundamentos não chega da BRAPI.** `returnOnEquity`, `profitMargins`,
   `revenueGrowth` e `debtToEquity` voltam ausentes para **todo** ativo no plano atual —
   conferido em 2026-08-29 contra a API real, com ações, FII e BDR. O que chega é
   `priceEarnings` e `earningsPerShare`. Então `roe`, `profit_margin`, `revenue_growth` e
   `debt_to_equity` são sempre `null`, e as dimensões de qualidade e endividamento do score
   caem no caminho de dado ausente. Isso encerra a dúvida antiga sobre a **unidade** desses
   campos: `_ratio_to_pct` está correto e nunca é exercitado. Só sai daqui com plano pago ou
   segunda fonte; `GET /data-quality` dá a visibilidade.

4. **Universo hardcoded como fallback.** `core/config.py::default_universe` mantém ~400 tickers,
   apesar de já existir universo dinâmico via BRAPI (`core/universe.py`). Fallback defensivo
   intencional, mas extenso.

5. **A API de produção sobe sem esperar o CI.** Conferido com `get-service-config` em
   2026-09-09: o serviço `fiance` tem gatilho `main`, filtro `rootDirectory: /backend` e
   `checkSuites: false`. Um commit vermelho vai ao ar — e o `preDeployCommand` é
   `python -m app.release`, então uma migração ruim é aplicada antes de qualquer teste terminar.
   Conserto de um clique no serviço (*Wait for CI*).

   O cliente **não** sobe junto: o aplicativo chega por loja, com fila de revisão e com versões
   antigas instaladas por tempo indeterminado. Por isso mudança de contrato de API pede campo
   **opcional** no Dart — é o que fez `as_of` atravessar sem 422 —, e agora vale mais do que
   valia: não existe mais um cliente que se atualiza sozinho no próximo carregamento.

   O fluxo de promoção do [`deploy.yml`](../.github/workflows/deploy.yml) continua **não
   utilizável**: os environments do Actions (`staging`, `production`) não existem — o que a API do
   GitHub lista é `fiance / production` e `fiance / staging`, criados pelo Railway, que são outra
   coisa — e `RAILWAY_TOKEN` não está configurado, então o `workflow_dispatch` para com a mensagem
   de token ausente. As saídas, em ordem de valor, estão no
   [OPERACAO](OPERACAO.md#o-que-falta-configurar-uma-vez), item 1.

   Há **mudanças de configuração STAGED e não implantadas** no patch `27a43c52`, e eram **33**:
   13 no `fiance`, 4 no serviço do front (que saiu em 2026-09-11) e **13 no `Postgres`**,
   inclusive `POSTGRES_PASSWORD` e `DATABASE_URL` — o serviço de banco não estava na contagem
   anterior, e é o que mais importa dela.

   **Elas não entram no deploy de código**, ao contrário do que a revisão anterior deste item
   afirmava: o patch segue `STAGED` depois de oito deploys de git no mesmo dia, com o mesmo
   `patchId`. Patch de ambiente pede aprovação explícita. O que fica aberto é outro: ninguém sabe
   o que há dentro do patch. Os nomes staged são idênticos aos que estão no ar nos três serviços —
   cara de re-stage do conjunto inteiro —, mas o valor não se confere sem despejar segredo, e
   `list-variables` imprime `JWT_SECRET` e `POSTGRES_PASSWORD` em texto claro. Fechar é decidir o
   patch: aprovar sabendo o que muda, ou descartá-lo.

## Duplicação estrutural entre Python e Dart

6. **Rótulo e régua são escritos dos dois lados, e nenhuma máquina os compara.** Rótulo e
   cor de categoria, tipo de ativo, setor, tipo de renda fixa e liquidez viviam num gerador até
   2026-09-07, e voltaram a ser escritos quando ele saiu. O que os mantém em acordo é
   `analysis/score_ruler.py` como fonte e a disciplina de mudar Python e Dart no mesmo commit. O
   risco continua registrado: divergência aqui é um número errado, não uma tela feia. Com um
   cliente só, a distância encolheu de três cópias para duas.

   *(O **ícone** de categoria saiu do vocabulário em 2026-09-11: eram 24 glifos declarados que
   nenhuma tela lia depois que a identidade de categoria passou a ser cor de série mais rótulo
   escrito. Vocabulário sem consumidor é pior que vocabulário nenhum, porque parece resolvido.)*

7. **Três famílias de controle ainda são Material puro, com estilo só no tema.**
   `DropdownButtonFormField`, `Slider`, `showDatePicker` e o par `RadioListTile`/`CheckboxListTile`
   dentro de diálogo — 16 usos — não têm componente do sistema: o que os aproxima do resto é o
   `ThemeData`, não uma primitiva. Funciona enquanto o tema cobre tudo que eles desenham, e para
   de funcionar na primeira propriedade que o Material não expõe (a altura do item de menu, o
   calendário do seletor de data).

   Não é substituição mecânica: cada um é um comportamento — escolher entre poucos, escolher numa
   faixa contínua, escolher uma data — e escrever isso à mão custa mais que estilizar. O critério
   para atacar é o mesmo de sempre: quando a divergência aparecer na tela, e não antes.

8. **A base do preço justo não chega às telas de posição da carteira.** Em `/ativo`, em
   `/descobrir` e no sheet de detalhe a cifra nunca sai sem `consensusLabel` dizendo quantos
   métodos entraram. Na lista de ativos do `/patrimônio`, o objeto de posição mostra preço médio e
   preço de hoje, mas não o justo — então a explicabilidade não está violada, e sim ausente: quem
   quer a leitura do papel abre `/ativo/:ticker`. Se o preço justo entrar ali, entra com a base
   junto, e aí é decisão de layout numa linha que já carrega cinco números.

9. **Falta a regra do alvo de toque de 44dp no Dart.** `test/lint_ui_test.dart` cobra
    **catorze** — explicabilidade em julgamento, projeção sem faixa, promessa sobre o futuro, nome
    acessível em botão de ícone, serifa no papel de veredito, vocabulário de IA genérica, nome de
    destino aposentado, a catraca de tipo solto, a catraca de caixa do Material, paleta escrita à
    mão, esqueleto no lugar de disco girando, busca alcançável de todo destino de raiz, destino de
    navegação que o roteador não declara, e falha de leitura numa voz só.

    A **decisão de layout** que faltava foi tomada em 2026-09-11: `HelpTooltip` deixou de ser um
    ícone pendurado ao lado do rótulo e passou a ser o **rótulo inteiro**, sublinhado, com alvo de
    44. Era o caso que travava a regra — chegar aos 44 aumentando o glifo só deixaria o ícone
    maior. O que falta agora é a regra em si, e ela é difícil por outro motivo: alvo de toque é
    propriedade de **layout renderizado**, não de fonte. Ou ela vira teste de widget que monta cada
    controle e mede, ou ela é uma catraca de grafia (`minimumSize`, `ConstrainedBox`) que deixa
    passar o caso montado de outro jeito.

10. **`/voce` são cinco entradas, e o desenho pede quatro eixos.** A reorganização de destinos
    foi feita, e `/voce/preferencias` já está partida em três eixos **dentro** da tela — Preço
    justo, Score de oportunidade, Avisos, mais "Esta tela" para a densidade. O que falta é a
    fronteira de **rota**: *como invisto · para onde vou · como o produto age · meus dados*. Hoje
    **Indicação** é par de Preferências em vez de assunto de Conta, e o yield desejado (que é
    "como invisto") mora na mesma rota que a cadência de aviso (que é "como o produto age").
    Mover isso é mover rota e partir o componente, não renomear seção. O desenho está em
    [design/INFORMATION-ARCHITECTURE.md](design/INFORMATION-ARCHITECTURE.md).

11. **Dois comportamentos essenciais não têm componente.** Faltam `Evidence` (o nível 2 da
    explicabilidade, entre conclusão e método) e `Decision` (veredito + falsificador num objeto
    só, para que um não possa ser renderizado sem o outro).

    *(`Range` saiu daqui em 2026-09-09: `FiRange` carrega piso, teto, cenário base e hipótese.)*

    *(A proveniência saiu daqui: `asOf` deixou a gaveta e é linha visível. Em 2026-09-09 o
    carimbo passou de `/ativo` para **onde se comparam preços** — a tabela de posições e a lista
    de oportunidades, com `formatIdade` e o critério do carimbo mais antigo. No caminho, `Opportunity` (resposta) e `PortfolioPosition.fromJson`
    (Dart) não declaravam o campo, e o descartavam em silêncio.)*

## Cobertura de testes

13. **Não existe mais teste de ponta a ponta.** O que havia rodava no navegador (Playwright
   contra o backend real) e saiu com o front, em 2026-09-11. Ele cobria o que nenhuma suíte
   unitária alcança: subir o processo de verdade, abrir tela por **link direto**, e uma posição
   salva no servidor chegando à tela. O substituto no aplicativo é `integration_test` do Flutter
   rodando contra o backend local, e ele **não foi escrito** — o que sobrou é o teste de fumaça do
   deploy, que confere que o processo responde, e nada sobre o cliente.

14. **As regras de interface que só rodavam no front não foram portadas.** O verificador do web
   tinha 24 regras; `test/lint_ui_test.dart` cobra **catorze**, e o contraste é cobrado por
   `test/contraste_test.dart`. Nunca chegaram ao Dart: classe/ícone inexistente (que não tem
   equivalente em Flutter e morreu com o problema), **gráfico sem tabela equivalente** e
   **controle montado à mão em vez do componente do sistema** (item 7). A de gráfico sem tabela
   protege acessibilidade, e é a que mais falta.

   *(Duas entraram em 2026-09-11, e uma delas o web não tinha: a **catraca de caixa do Material**
   — `Card`, `ListTile`, `SwitchListTile` e `CircleAvatar` em zero, com `RadioListTile` e
   `CheckboxListTile` de fora por serem controle de formulário — e **paleta escrita à mão**, que
   reprova `Color(0x…)` solto e `Colors.*` fora da fundação. A **escala de tipo fora dos papéis**
   deixou de ser item aberto: a catraca chegou a **zero** quando a legenda de eixo ganhou papel
   próprio (`FiType.axis`), e catraca em zero é a proibição que faltava.)*

   *(A regra de **destino de navegação inexistente** saiu daqui em 2026-09-11, depois de o defeito
   que ela pega acontecer de verdade: `patrimonio_summary` levava a `/assets/renda-fixa`, que não
   existe, e o `go_router` lançava `GoException` no toque.)*

## Automação que não existe

15. **Sugestões seguidas dependem de lançamento manual.** `/suggestions/followed` só tem o que a
   pessoa registra. O caminho automático — reconhecer que uma sugestão virou compra a partir do
   razão — não foi implementado, e a base para ele já existe. *(A metade dos proventos foi
   resolvida: `/dividends/pending` cruza o calendário da BRAPI com a projeção do razão. Como toda
   ressalva ali erra o valor para mais, nada vem pré-selecionado e não existe "aceitar todos".)*

## Pendências do redesign de UX/UI

Estrutura de cada tela em [design/WIREFRAMES.md](design/WIREFRAMES.md); o contrato dos
componentes em [design/DESIGN-SYSTEM.md](design/DESIGN-SYSTEM.md).

16. **`detail_level` (Essencial / Completo / Avançado) não existe no backend.** É a alavanca que
   atenderia os três perfis de senioridade sem construir três produtos — número de métricas e
   verbosidade, além da densidade. **Densidade já existe** (`preferences.density`, aplicada como
   `[data-density]`), mas ela resolve só o espaçamento: quantas métricas aparecer e com quanto texto
   continua igual para todo mundo. Exige coluna em `PreferencesDb`, campo em `GET/PUT /preferences`
   e migração Alembic.

17. **A régua não cobre o score em linha densa, e ali ele sai só como selo.** Ela tinha **zero**
    consumidores até 2026-09-09, e desde 2026-09-11 é o elemento-assinatura do produto: serve
    score de oportunidade, saúde da carteira e suas quatro dimensões, desvio de alocação, progresso
    de meta, margem de segurança, carteira contra CDI e renda contratada contra CDI — sete leituras
    na mesma forma, com `FiMeasure` como a variante geral (valor, referência, banda) e `ScoreRuler`
    como a de score.

    O que sobra são as **linhas densas**: `feed_tiles` e `quick_invest_view` mostram a banda como
    `FiTag`, porque uma régua dentro de um objeto de três linhas rouba a atenção do número que o
    objeto existe para mostrar. É escolha, não pendência de implementação — mas é a única
    inconsistência viva na família, e fica registrada para que a próxima tela não decida sozinha.

18. **O contrato das rotas guarda campo que sai, não campo que entra.**
    `tests/contrato_das_rotas.json` registra os campos de cada rota `/api/v1` e o teste falha
    dizendo a rota e o campo quando um desaparece — que é o defeito perigoso, porque o FastAPI
    descarta em silêncio o que o `response_model` não declara. Mas adicionar campo **não** reprova:
    conferido em 2026-09-08 ao acrescentar `as_of` em `/asset/{symbol}`, a suíte passou verde com o
    JSON desatualizado. O arquivo só fica em dia porque o CLAUDE.md pede a regravação no mesmo
    commit, e isso é disciplina, não máquina. Fechar é decidir se o contrato é **piso** (o que não
    pode sair) ou **inventário** (o que existe) — hoje ele é escrito como inventário e cobrado como
    piso.

19. **As três classes de diagnóstico de queda não foram validadas.** "Queda saudável / para
    investigar / estrutural" pressupõe que `analysis/dip_analysis.py` permita separar as duas
    últimas. Se o veredito atual não sustentar, são dois grupos, não três — verificar antes de
    desenhar o terceiro.

> **Não é pendência:** push exigir o app instalado deixou de ser assimetria em 2026-09-11 — só há
> o aplicativo, e ele está sempre instalado.

## Dívida aberta (auditoria de 2026-08-29, revista em 2026-09-03)

> Os antigos itens 12 e 13 foram removidos porque já eram falsos quando escritos de novo: a posição
> **é** projeção do razão (`ledger_service.rebuild_projection`) e as colunas monetárias **são**
> `Money = ExactNumeric`. Item resolvido que fica manda refazer o que existe — que é exatamente a
> doença que o cabeçalho deste arquivo descreve. Os números foram reaproveitados pelo que ficou
> aberto no lugar.

20. **A apuração de IR não cobre day trade nem IOF de renda fixa.** A apuração passou a ser
    projeção do razão, por mês e categoria (CHANGELOG de 2026-09-05), e isso fechou os defeitos de
    ordem de registro, isenção não reavaliada e venda que não apurava. Duas lacunas continuam, e
    estão declaradas nos Termos de Uso: o razão **não distingue day trade** de swing trade, e não
    há IOF sobre resgate de renda fixa com menos de 30 dias. Enquanto isso durar, o número é
    estimativa de apoio e não substitui a apuração oficial.

21. **O mobile nunca teve um release de verdade: não existe chave, e nenhum evento foi visto.** A
    fiação foi feita e está coberta (CHANGELOG de 2026-09-09): o DSN vem embutido em
    `lib/core/telemetry.dart`, o app só reporta em release, o ambiente sai como `production` num
    build de release, e a assinatura lê `android/key.properties` — o App Bundle **falha** sem ela.

    O que falta é fora do código, e são duas coisas. A **chave de release não foi gerada**, então
    o `.aab` de loja ainda não pode ser produzido; guardar o `.jks` e a senha é o que decide se o
    app poderá ser atualizado depois de publicado (o passo está no
    [README](../README.md#assinatura-do-android)). E **nenhum evento do mobile foi visto no
    painel** do Sentry: confirmar exige um APK instalado num aparelho e um olhar no painel.
    Enquanto isso não acontecer, a telemetria do mobile é código testado, não canal verificado.

23. **Token de push é reatribuído a quem o registrar.** `register_device_token()` move o token para
    o usuário da sessão se ele já existir — necessário para troca de dono do aparelho, mas significa
    que quem conhecer um token FCM alheio redireciona os alertas daquele aparelho para si. Entropia
    do token é a única proteção hoje.

24. **A paginação das listas com agregado limita o payload, não a consulta.** Proventos, renda fixa
    e sugestões seguidas ainda leem o conjunto inteiro do banco, porque os totais por mês, a marcação
    a mercado e a comparação com o Ibovespa precisam de todos os registros por definição. O que
    atravessa a rede está limitado; a consulta não. Resolver de verdade exige mover esses agregados
    para SQL — o que, no caso da renda fixa, significa mover a marcação a mercado junto.

25. **A acessibilidade foi coberta por verificação, não por auditoria — e a verificação encolheu.**
    Contraste (`test/contraste_test.dart`) e nome acessível de botão de ícone
    (`test/lint_ui_test.dart`) estão de pé. O que **nunca** foi feito é percorrer cada fluxo com
    **TalkBack e VoiceOver de verdade**: ordem de leitura, anúncio de mudança de tela, foco preso
    em bottom sheet e alvo de toque real não têm cobertura automática nem verificação manual
    registrada.

    O que existia no front e **não** tem equivalente no aplicativo: salto para o conteúdo, foco
    preso em diálogo com devolução a quem abriu, anúncio de rota em região viva e alternativa
    textual obrigatória em gráfico. Parte disso o Flutter resolve sozinho (o `Navigator` devolve o
    foco; `Semantics` anuncia a rota), e parte não — a alternativa textual de gráfico é regra de
    produto, e é a mesma que o item 14 lista como não portada.

26. **A aparência das telas nos dois temas nunca foi conferida num aparelho.** O contraste é
    verificado no CI, mas **por par de token**: ele mede `ink-2` sobre `ground-0`, não a tela
    montada. A revisão de 2026-09-11 **reescreveu as duas paletas** — papel quente no claro, tinta
    azul-carvão no escuro, sem branco nem preto puros — e conferiu o resultado num espécime
    renderizado fora do CI; nenhuma das duas coisas é olhar a tela num aparelho com luz em volta. *(A parte de `opacity: 0.5` no controle desabilitado saiu deste item: o estado inerte
    é token explícito — `control-fill` com `ink-disabled` — e o teste **mede** esse par nos dois
    temas.)*

    O que continua aberto é a suspeita, levantada por análise de composição e **não confirmada no
    olho**, de que a elevação de sheets e diálogos é fraca demais no tema claro: painel e véu
    ficam em 1,06:1 nos dois temas, então quem separa é a sombra — e a do claro tem 27% da
    opacidade da do escuro. Sombra não se mede por par de token, o que faz deste um caso genuíno
    de olhar num aparelho, e não de escrever mais uma régua.

27. **A cobrança é backend sem cliente.** Existe a cerca, a régua de plano, o preço travado e o
    webhook idempotente; não existe interface: `billing` não aparece em `mobile/lib`. O que falta
    é o meio: decidir quais recursos a interface cerca, montar a tela de plano em `/voce/plano`
    (que não existe como rota) e ligar o checkout. **Com distribuição por loja, a decisão mudou de
    forma**: assinatura vendida dentro do app passa pela cobrança da própria loja e pela comissão
    dela, e cobrar por fora tem regra própria em cada uma. Decidir o meio vem antes de construir a
    tela.

    *(O `GateComponent` do front saiu junto com ele em 2026-09-11; o equivalente em Dart não
    existe. O que ele resolvia — montar o bloqueio a partir do corpo do 402 — continua valendo,
    e o corpo continua sendo emitido pelo backend.)*

    *(O alçapão do trial saiu daqui, e era a parte urgente: `start_trial` é chamado na primeira
    posição salva **sem consultar a flag**, e não re-arma, então virar `ENTITLEMENTS_ENABLED`
    derrubaria a base inteira para Free no mesmo instante. Resolvido por âncora, sem migração:
    `ENTITLEMENTS_ENABLED_AT` declara quando a cerca subiu e o relógio conta do mais tarde entre
    qualificar e essa data; a flag ligada sem a data **falha alto** no startup.)*

28. **O ETF é estruturalmente mal avaliado, e o remendo tem consequência.** Para `asset_type ==
    "etf"` o único candidato a consenso é Bazin (`dividendo / 0,04`); um ETF de índice distribui na
    casa de 1% ao ano, então o preço justo sai em ~25% do preço e a margem de segurança em −300%,
    sempre. `opportunity_service` sobrescreve o veredito por RSI e tendência quando ele sai
    `UNKNOWN`, o que produz duas coisas ruins: o mesmo ETF recebe veredito diferente em
    `/descobrir` e em `/ativo/:ticker`, e o veredito por momentum sai **sem falsificador**, porque
    sem consenso não há preço-limite. Decidir o método — comparação com o índice, prêmio sobre o
    valor patrimonial, ou abstenção explícita — vem antes de mexer no falsificador.

29. **Três das seis dimensões do score nunca têm dado, e o perfil de risco fica quase inerte.** A
    ausência de `roe`, `profit_margin`, `revenue_growth` e `debt_to_equity` está no item 3; a
    consequência sobre a personalização não estava. Com os pesos reais, sobra 0,60 de peso no
    perfil conservador, 0,55 no moderado e 0,35 no agressivo — e o que resta em todos é margem de
    segurança, dividendos e técnico, renormalizados. Crescimento vale 40% do peso agressivo e nunca
    existe. O glossário descreve "qualidade e endividamento ponderados pelo seu perfil", que é o
    produto que existirá quando houver segunda fonte.

30. **O passo de reserva da cascata é inalcançável: não existe alvo declarado.** `cascata.montar`
    recebe `reserva_meses_alvo` e `reserva_atual`, a matemática está escrita e testada, e
    **nenhuma rota passa os dois** — porque não há onde declarar quantos meses de gasto fixo a
    pessoa quer guardar. Não há campo em `preferences`, em `goals`, em lugar nenhum. O invariante
    ("a reserva vem depois da dívida cara, e só existe com alvo declarado") descreve um passo que
    a Sobra nunca mostra.

    Fechar é decisão de produto antes de código, e a
    [arquitetura de informação](design/INFORMATION-ARCHITECTURE.md) a deixou em aberto de
    propósito: quantos meses, contra qual base, e o que acontece com quem não declara. Inventar
    "seis meses" é o número de mercado solto que a régua de dívida proíbe.

31. **A alocação-alvo por categoria cai no padrão do produto e a tela não distingue.** `GET
    /dashboard` monta as barras com `goal_service.get_goals()`, que devolve 30/35/15/15/5 quando
    nada foi declarado — então quem nunca declarou meta vê barras "abaixo da meta" de uma meta que
    nunca escolheu, e o alerta de rebalanceamento dispara sobre ela. As metas **por setor** já
    distinguem desde 2026-09-11 (o `declared` da resposta); as de categoria não, e mudar isso mexe
    no alerta do dashboard, no `whats_new` e no Quick Invest de uma vez.

32. **O texto jurídico não publica canal de atendimento, e a loja exige um.** `/termos`,
    `/privacidade` e `/aviso-cvm` são servidos pelo backend e abrem sem sessão — o que a ficha de
    segurança de dados pede. Mas a Política diz que o canal "será publicado antes de o aplicativo
    ser distribuído", e não existe endereço nenhum: não há e-mail de contato em lugar algum do
    repositório. Exportar e apagar a conta funcionam sem atendimento, o que cobre os dois direitos
    mais pedidos; os demais (confirmação, correção, oposição) não têm porta. Fechar é decidir o
    endereço e escrevê-lo em `services/legal_pages.py` — uma linha, e bloqueia submissão.

## Armadilhas conhecidas

Não são bugs, mas mordem. A lista completa, com o que cada uma já quebrou, está em
[CLAUDE.md](../CLAUDE.md#armadilhas-que-não-quebram-o-build).

- `Modelo(**resultado.__dict__)` e `fromJson` descartam campo não declarado sem avisar.
- Coluna nova exige migração Alembic — mexer no model não basta.
- `flutter analyze` e `flutter test` nunca tocam o Gradle: o build Android é outra metade.
- Dependência nova no `pubspec.yaml` pede `flutter build apk --release` antes do commit.
