# fiance — o que está aberto

> **Só pendências.** Todo item aqui foi verificado contra o código em **2026-09-08**; nada de
> histórico, nada de ✅. O que já foi resolvido — e por quê — está em [CHANGELOG.md](CHANGELOG.md).
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

5. **O front de produção sobe sem esperar o CI.** Conferido contra o Railway em 2026-09-08, com
   push real e leitura da configuração do serviço: o auto-deploy do `main` para produção foi
   desligado em 2026-09-06 **só na API**. O `fiance` sobe homologação; o `fiance-web` sobe
   **produção** em todo commit que toque `web/**`, e **`checkSuites` está `false`** — ou seja,
   publica antes de qualquer teste terminar. Um commit vermelho no front vai ao ar. Esse é o pior
   caso, e é conserto de um clique (*Wait for CI*).

   O resto do arranjo: o front não tem serviço em homologação, então não tem para onde ir a não
   ser produção — e é onde mora toda a interface, que é o que muda mais. E o fluxo de promoção do
   [`deploy.yml`](../.github/workflows/deploy.yml) **não está utilizável**: os environments do
   Actions (`staging`, `production`) não existem — o que a API do GitHub lista é
   `fiance / production` e `fiance / staging`, criados pelo Railway, que são outra coisa — e
   `RAILWAY_TOKEN` não está configurado, então o `workflow_dispatch` para com a mensagem de token
   ausente. As três saídas, em ordem de valor, estão no
   [OPERACAO](OPERACAO.md#o-que-falta-configurar-uma-vez), item 1.

   **E o front vai ao ar sem a API que ele espera.** Aconteceu em 2026-09-09: um commit mudou
   `/quick-invest` nos dois lados, o `fiance-web` subiu sozinho e a API de produção ficou seis
   commits atrás, então a tela pedia `cash_available: null` a uma API que exigia número — 422 em
   produção. O `quickInvest` do web ganhou tolerância às duas versões, e os campos novos viraram
   opcionais no modelo, mas isso trata o sintoma: **toda mudança que atravessa front e back vai
   quebrar entre os dois deploys** enquanto um subir sozinho. Enquanto for assim, a regra é
   promover a API **antes** do push que toca `web/**`.

   Há também **4 mudanças de configuração STAGED e não implantadas** no `fiance-web`
   (`ALLOWED_HOSTS`, `NODE_ENV`, `SITE_URL`, e a porta do domínio): elas entram junto do próximo
   deploy de código, então um deploy de interface carrega mudança de ambiente sem ninguém pedir.

## Duplicação estrutural entre plataformas

6. **Rótulo e régua são escritos nos dois lados, e nenhuma máquina os compara.** Rótulo, ícone e
   cor de categoria, tipo de ativo, setor, tipo de renda fixa e liquidez viviam num gerador até
   2026-09-07, e voltaram a ser escritos quando ele saiu. O que os mantém em acordo é
   `analysis/score_ruler.py` como fonte e a disciplina de mudar as três plataformas no mesmo
   commit. O risco continua registrado: divergência aqui é um número errado, não uma tela feia.

7. **Restam 36 linhas com `fontSize:` solto no mobile, e seis delas abaixo de todo papel.**
   A escala já foi **recalibrada** para 360dp (`body` em 16, `moneyXl` em 32), e os 15 sítios que
   tinham papel equivalente foram trocados: `metricSm` para cifra, `metric` para score, `caption`
   para legenda, `ticker` para papel, `pageTitle` para cabeçalho de sheet. A catraca de
   `test/lint_ui_test.dart` desceu de 49 para **36**, e o teto só desce.

   O que sobra é onde a decisão é **de layout antes de tipo**, e por isso não é substituição
   mecânica. A escala do sistema começa em 11 (`eyebrow`); os seis abaixo disso estão em 9 e 10, e
   são justamente os pontos mais apertados, que é por que ninguém os subiu:
   - `features/mes/widgets/feed_charts.dart:108` e `:132` — rótulo de eixo do gráfico. Subir
     para `caption` (13) pode sobrepor o eixo, e o gráfico é onde a densidade importa;
   - `features/mes/widgets/feed_health.dart:258` e `:263` — rótulo e faixa de dimensão, numa
     linha de **quatro** colunas em 360dp. "Diversif." já é abreviação por falta de espaço;
   - `features/patrimonio/widgets/patrimonio_positions.dart:291` e `:392` — rótulo de categoria
     numa linha de posição.

   Ou a linha passa a ter menos colunas, ou o gráfico ganha mais espaço de eixo. Converter às
   cegas troca um defeito invisível (texto pequeno demais) por um visível (texto sobreposto), e o
   visível é o que se conserta correndo.

8. **"Fio + chão" não embarcou no mobile.** Contado em 2026-09-08: 26 `Card(`, **28** `ListTile`
   e **161** `Icons.*` crus. O caso exemplar é `FiInsightTile` (em
   `features/mes/widgets/feed_tiles.dart`) — `Card` + `CircleAvatar` com ícone colorido + título +
   detalhe —, que é a pilha inteira de cheiros de interface gerada e ainda se chama "Insight".
   Trocar exige um `FiSection` e um `FiDataRow` no mobile, equivalentes ao `<app-section>` e ao
   `.data-table` do web. *("Serifa decide" saiu daqui: os quatro usos de `FiType.verdict` aplicam
   a família serifada, e `test/lint_ui_test.dart` reprova o papel de veredito que saia em sans —
   declarar o papel não aplica a fonte.)*

9. **Falta a regra do alvo de toque de 44dp no Dart.** `test/lint_ui_test.dart` cobra **oito** —
    explicabilidade em julgamento, projeção sem faixa, promessa sobre o futuro, nome acessível em
    botão de ícone, serifa no papel de veredito, vocabulário de IA genérica, nome de destino
    aposentado e a catraca de tipo solto.

    A que falta precisa de uma decisão de layout **antes** da regra. `HelpTooltip` foi de 14 para
    32 e ganhou `Semantics`, mas 44 dobraria a altura do `Row` de rótulo de 11px onde ele vive.
    Chegar aos 44 é fazer o rótulo inteiro ser o alvo, em vez de pendurar um ícone ao lado — e só
    depois a regra tem o que cobrar.

10. **`/voce` são cinco entradas, e o desenho pede quatro eixos.** A reorganização de destinos
    foi feita, e `/voce/preferencias` já está partida em três eixos **dentro** da tela — Preço
    justo, Score de oportunidade, Avisos, mais "Esta tela" para a densidade. O que falta é a
    fronteira de **rota**: *como invisto · para onde vou · como o produto age · meus dados*. Hoje
    **Indicação** é par de Preferências em vez de assunto de Conta, e o yield desejado (que é
    "como invisto") mora na mesma rota que a cadência de aviso (que é "como o produto age").
    Mover isso é mover rota e partir o componente, não renomear seção. O desenho está em
    [design/INFORMATION-ARCHITECTURE.md](design/INFORMATION-ARCHITECTURE.md).

11. **Três comportamentos essenciais não têm componente.** Faltam `Range` (piso, teto, hipóteses
    e horizonte — hoje a faixa é escrita à mão em cada projeção), `Evidence` (o nível 2 da
    explicabilidade, entre conclusão e método) e `Decision` (veredito + falsificador num objeto
    só, para que um não possa ser renderizado sem o outro).

    *(A proveniência saiu daqui: `asOf` deixou a gaveta e é linha visível, e `/ativo/:ticker`
    passou a dizer quando o preço foi lido nas duas plataformas — o carimbo existia no snapshot
    desde sempre e parava no serviço.)*

12. **A tabela de posições mostra preço justo sem a base que o formou.** `<app-fair-price>`
    resolveu isso em `/ativo` e em `/descobrir` — a cifra nunca sai sem dizer quantos métodos
    entraram, e a ausência é razão nomeada e não traço. Na `.data-table` de
    `/patrimonio/posicoes` a coluna continua um número cru: o cabeçalho diz "Preço justo" e a
    tabela tem proveniência própria, então a explicabilidade está satisfeita, mas a **base por
    linha** não aparece. Célula de tabela não comporta legenda, então resolver é decidir entre uma
    coluna a mais e um `title` — e coluna a mais numa tabela que já rola é decisão de layout.

## Cobertura de testes

13. **O E2E cobre o esqueleto, não os fluxos.** `web/e2e/` roda Playwright contra o backend real e
   o build de produção com SSR, e cobre o que o resto da suíte não alcança: redirecionamento sem
   sessão, as cinco rotas principais e três aninhadas abrindo por **link direto**, e uma posição
   salva no servidor chegando à tela. O que **não** está coberto é o miolo — importar operações,
   passar pelo checkout, ver o gate aparecer, degradar de plano. São os fluxos que o plano lista, e
   eles dependem de cotação externa, que no ambiente de teste não é determinística.

14. **SQLite tranca sob concorrência de navegador.** Durante o E2E o backend loga
   `database is locked` em requisições paralelas. Não derruba os testes e não afeta produção, que é
   Postgres — mas torna o E2E local mais lento e potencialmente instável se ele crescer.

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

17. **Falta o componente `Range`, e ele é o último dos essenciais.** `MarginOfSafety`,
    `AllocationGap`, `GoalProgress`, `DipDiagnosis`, `ScoreRuler`, `Insight`, `Section` e
    `FairPrice` existem, e a tabela profissional de posições também. A faixa de projeção continua
    escrita à mão em cada tela que a mostra — e é o dado que o produto mais insiste em nunca
    reduzir a um número único, o que faz dele o candidato mais óbvio a componente. Ver o item 11.

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

> **Não é pendência:** push exigir o app instalado é **decisão**, e o web sinaliza isso em
> `/voce/alertas`. As demais assimetrias entre mobile e web fecharam em 2026-08-28 — metas ganharam
> tela própria e RF × Bolsa ganhou cliente Dart.

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

21. **A telemetria do mobile ainda não foi ligada nem verificada.** Backend e web já têm DSN; o
    mobile depende de `--dart-define=SENTRY_DSN=...` no build, e nenhum build assinado foi feito
    ainda. O código está pronto e testado — o que falta é o DSN e um build real.

22. **O lock de job periódico não é liberado ao terminar, só expira.** `_run_guarded` deixa o TTL
    vencer, e isso é **deliberado**: o TTL é o próprio intervalo do job, e liberar no fim do ciclo
    faria o worker seguinte repetir o trabalho segundos depois. O custo é real e continua aberto: se
    um worker morre logo após adquirir, o snapshot diário fica bloqueado por até 5,4h. A correção
    certa é heartbeat no lock, não release no `finally`. (O warm-up do scan é caso diferente — roda
    uma vez e **libera** no `finally`.)

23. **Token de push é reatribuído a quem o registrar.** `register_device_token()` move o token para
    o usuário da sessão se ele já existir — necessário para troca de dono do aparelho, mas significa
    que quem conhecer um token FCM alheio redireciona os alertas daquele aparelho para si. Entropia
    do token é a única proteção hoje.

24. **A paginação das listas com agregado limita o payload, não a consulta.** Proventos, renda fixa
    e sugestões seguidas ainda leem o conjunto inteiro do banco, porque os totais por mês, a marcação
    a mercado e a comparação com o Ibovespa precisam de todos os registros por definição. O que
    atravessa a rede está limitado; a consulta não. Resolver de verdade exige mover esses agregados
    para SQL — o que, no caso da renda fixa, significa mover a marcação a mercado junto.

25. **A acessibilidade foi coberta por verificação, não por auditoria.** Contraste (CI), nome
    acessível de botão (lint), alternativa textual de gráfico (lint) e foco visível estão de pé. O
    que **não** foi feito é percorrer cada fluxo só com teclado e com leitor de tela de verdade:
    ordem de foco em camadas empilhadas, anúncio de mudança de rota e armadilha de foco em modal
    ainda não têm cobertura automática nem verificação manual registrada. **Parcialmente
    endereçado:** a diretiva `fiDialog` (`core/directives/dialog.directive.ts`) prende o Tab,
    devolve o foco a quem abriu e dá papel e modalidade às seis superfícies sobrepostas; a mudança
    de rota é anunciada em região `aria-live`; e a **devolução do foco ao título** a cada navegação
    passou a ter cobertura em `e2e/acessibilidade.spec.ts`, medida por `document.activeElement` —
    ela estava morta em nove telas, porque `focus()` em elemento sem `tabindex` não faz nada e não
    avisa. O que continua aberto é a **inércia real do fundo**
    para o cursor virtual do leitor de tela — `aria-modal` promete uma inércia que o DOM não tem, e
    resolver isso exige tirar o diálogo da árvore da aplicação — e a verificação manual com leitor
    de tela de verdade.

26. **A aparência das telas nos dois temas nunca foi conferida em navegador.** O contraste é
    verificado no CI, mas **por par de token**: ele mede `ink-2` sobre `ground-1`, não a tela
    montada. *(A parte de `opacity: 0.5` no botão desabilitado saiu deste item: o estado inerte
    passou a ser token explícito — `control-fill-hover` com `ink-disabled` — e o verificador
    **mede** esse par nos dois temas.)*

    O que continua aberto é a suspeita, levantada por análise de composição e **não confirmada no
    olho**, de que a elevação de modais e drawers é fraca demais no tema claro: painel e véu ficam
    em 1,06:1 nos dois temas, então quem separa é a sombra — e a do claro tem 27% da opacidade da
    do escuro. Uma sombra não se mede por par de token, o que faz deste um caso genuíno de olhar
    em navegador, e não de escrever mais uma régua.

27. **A cobrança não tem caminho de ponta a ponta.** Existe backend, régua de plano, preço travado e
    webhook idempotente; não existe tela de plano, exibição de preço, checkout, gestão de assinatura
    nem cancelamento na interface — `billing` não aparece em `web/src` nem em `mobile/lib`, e o CTA
    do `gate.component.ts` aponta para `/voce/plano`, que não existe em `app.routes.ts`. Some-se a
    isto que o relógio do trial **já está correndo** com a cerca desligada: `start_trial()` é
    chamado na primeira posição salva, então virar `ENTITLEMENTS_ENABLED` hoje derrubaria a base
    inteira para Free no mesmo instante. O trial precisa ser reiniciado na ativação da cerca, antes
    de virar a flag — não depois.

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

## Armadilhas conhecidas

Não são bugs, mas mordem. A lista completa, com o que cada uma já quebrou, está em
[CLAUDE.md](../CLAUDE.md#armadilhas-que-não-quebram-o-build).

- Ícone do Lucide não registrado quebra a tela em runtime, não o build.
- Classe CSS inexistente quebra a tela em silêncio.
- `Modelo(**resultado.__dict__)` e `fromJson` descartam campo não declarado sem avisar.
- Coluna nova exige migração Alembic — mexer no model não basta.
