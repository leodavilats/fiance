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

5. **Todo push no `main` publica interface em produção.** O auto-deploy do `main` para produção
   foi desligado em 2026-09-06 **só na API**: conferido contra o Railway em 2026-09-08, com um
   push real, o serviço `fiance` sobe homologação e o `fiance-web` sobe **produção**. O front não
   tem serviço em homologação, então não tem para onde ir a não ser produção — e é onde mora toda
   a interface, que é o que muda mais. A tranca de "promover, olhar, e só então promover" protege
   hoje a metade do sistema que muda menos. Pior: o fluxo de promoção do
   [`deploy.yml`](../.github/workflows/deploy.yml) **não está utilizável** — os environments do
   Actions (`staging`, `production`) não existem, e `RAILWAY_TOKEN` não está configurado, então o
   `workflow_dispatch` para com a mensagem de token ausente. As duas saídas estão no
   [OPERACAO](OPERACAO.md#o-que-falta-configurar-uma-vez), item 1.

## Duplicação estrutural entre plataformas

6. **Sobra o glossário e os rótulos de veredito.** Rótulo, ícone e cor de categoria, tipo de
   ativo, setor, tipo de renda fixa e liquidez passaram a ser **gerados** de `product-rules.json`
   (2026-08-29), e o `--check` do CI reprova divergência. O que continua manual nos dois lados é
   o glossário de score e os rótulos de veredito, que são texto longo e não cabem bem num arquivo
   de tokens.

7. **O mobile não tem caixa: nem `/mes`, nem `/sobra`.** O web adotou o ciclo do dinheiro e o
   mobile ficou sem as duas telas do topo da navegação — nenhum lançamento, nenhuma sobra, nenhuma
   dívida, nenhum molde de mês. Metade do produto (`cashflow/`, `cashflow_service`, a régua de
   dívida, a cascata) sem cliente móvel. A ausência **passou a ser cobrada**:
   `design-tokens/check-parity.mjs` a registra em `DIVIDA_HOJE`, e a lista só encolhe. Construir
   exige modelos, métodos em `api_repository`, providers e as telas — e é a maior pendência aberta
   do produto. Antes dela, trabalho visual no mobile é polir uma casa sem dois quartos.

8. **A escala de tipo do mobile está invertida, e há 65 tamanhos soltos.** `FiType.caption` (12px)
   é usada 44 vezes e `body` 14 — o aplicativo é dominado por legenda. O topo da escala
   (`moneyXl`, `moneyLg`, `pageTitle`, `bodyLg`, `verdictSm`) soma **zero** usos: eram valores de
   CSS transliterados para 360dp, grandes demais para caber. Em paralelo há 65 `fontSize:` soltos
   em 15 tamanhos distintos — incluindo 22 ocorrências de 11px e uma de 9px — contra 83 usos de
   papel. É a mesma doença que o web curou com uma regra de lint, e a regra só roda no web.
   Consertar são duas coisas: **recalibrar** os papéis para telefone (`body` em 16 para `caption`
   deixar de ser o corpo, `moneyXl` perto de 32) e **reatribuir** os 65 sítios soltos. A
   recalibração muda o desenho de toda tela, então pede uma passagem visual em aparelho — não é
   substituição mecânica.

9. **"Serifa decide" e "fio + chão" não embarcaram no mobile.** `fiSerif` aparece 3 vezes contra
   20 usos de `fi-verdict` no web; e há 26 `Card(`, 36 `ListTile` e 150 `Icons.*` crus. O caso
   exemplar é `FiInsightTile` — `Card` + `CircleAvatar` com ícone colorido + título + detalhe —,
   que é a pilha inteira de cheiros de interface gerada e ainda se chama "Insight". Trocar exige
   um `FiSection` e um `FiDataRow` no mobile, equivalentes ao `<app-section>` e ao `.data-table`
   do web.

10. **Sete regras do `lint:ui` não têm equivalente no Dart.** As que protegem contrato de produto e
   acessibilidade: explicabilidade em julgamento, projeção sem faixa, promessa sobre o futuro,
   nome acessível em botão de ícone, tipografia fora da escala, serifa fora de conclusão e alvo de
   toque. O mobile tem **3** chamadas de `Semantics(` em 12.745 linhas de Dart. `FiProvenance` já
   existe e está ligado ao veredito de saúde; falta ligá-lo às outras oito telas que julgam, e
   falta a máquina que cobre isso.

11. **`/voce` ainda não está nos quatro eixos, e a home pública continua a antiga.** A
    reorganização de destinos foi feita — `/sobra` caiu de seis subseções para três,
    `/patrimonio` agrupou Posições/Encerradas/Proventos em **Movimento**, `/descobrir` ganhou
    renda fixa e `/voce` ganhou `Objetivos`. Falta o recorte de `/voce` em *como invisto · para
    onde vou · como o produto age · meus dados*: hoje são cinco entradas, porque **Estratégia**
    (perfil, yield desejado, alocação-alvo) está dentro de Preferências e **Indicação** é par de
    Preferências em vez de assunto de Conta. Separar exige partir o `preferences.component`, não
    só mexer em rota. E a home pública segue como herói-features, quando deveria responder: qual
    problema · como o produto pensa · **por que ele não inventa número** · o que ele não faz ·
    como começar. O desenho está em [design/INFORMATION-ARCHITECTURE.md](design/INFORMATION-ARCHITECTURE.md).

12. **Três comportamentos essenciais não têm componente, e a proveniência está no nível errado.**
    Faltam `Range` (piso, teto, hipóteses e horizonte — hoje a faixa é escrita à mão em cada
    projeção), `Evidence` (o nível 2 da explicabilidade, entre conclusão e método) e `Decision`
    (veredito + falsificador num objeto só, para que um não possa ser renderizado sem o outro).
    E `<app-provenance>` funde quatro coisas de níveis diferentes numa gaveta: método e fonte são
    níveis 3 e 4, mas **momento é nível 1** — um preço de anteontem muda a decisão, não a nota de
    rodapé dela.

13. **`styles.css` tem grafias que se sobrepõem.** `.tag`/`.tag-brand`/`.tag-neutral` e
    `.verdict-pill`/`.v-buy`/`.v-sell`/`.v-hold`/`.v-unknown` são a mesma ideia — uma coisa
    pequena e rotulada, com cor de estado — em dois vocabulários; e `.pagination-btn` é
    `.btn-secondary` com um estado ativo. Consolidar em `.chip` com modificador, e dobrar a
    paginação no botão secundário, sem inventar controle novo.

14. **Os nomes de arquivo não acompanharam os destinos.** No web, `/sobra` é servida por
    `strategy-shell.component` e `/patrimonio` por `portfolio-shell`. No mobile, a rota virou
    `/patrimonio` mas a pasta continua `features/carteira/`, e `features/hoje/` e
    `features/estrategia/` nomeiam destinos que o produto não tem mais. É a deriva de nome entre
    rota e código — barata agora, confusa para sempre.

## Cobertura de testes

15. **O E2E cobre o esqueleto, não os fluxos.** `web/e2e/` roda Playwright contra o backend real e
   o build de produção com SSR, e cobre o que o resto da suíte não alcança: redirecionamento sem
   sessão, as cinco rotas principais e três aninhadas abrindo por **link direto**, e uma posição
   salva no servidor chegando à tela. O que **não** está coberto é o miolo — importar operações,
   passar pelo checkout, ver o gate aparecer, degradar de plano. São os fluxos que o plano lista, e
   eles dependem de cotação externa, que no ambiente de teste não é determinística.

16. **SQLite tranca sob concorrência de navegador.** Durante o E2E o backend loga
   `database is locked` em requisições paralelas. Não derruba os testes e não afeta produção, que é
   Postgres — mas torna o E2E local mais lento e potencialmente instável se ele crescer.

## Automação que não existe

17. **Sugestões seguidas dependem de lançamento manual.** `/suggestions/followed` só tem o que a
   pessoa registra. O caminho automático — reconhecer que uma sugestão virou compra a partir do
   razão — não foi implementado, e a base para ele já existe. *(A metade dos proventos foi
   resolvida: `/dividends/pending` cruza o calendário da BRAPI com a projeção do razão. Como toda
   ressalva ali erra o valor para mais, nada vem pré-selecionado e não existe "aceitar todos".)*

## Pendências do redesign de UX/UI

Estrutura de cada tela em [design/WIREFRAMES.md](design/WIREFRAMES.md); o contrato dos
componentes em [design/DESIGN-SYSTEM.md](design/DESIGN-SYSTEM.md).

18. **`detail_level` (Essencial / Completo / Avançado) não existe no backend.** É a alavanca que
   atenderia os três perfis de senioridade sem construir três produtos — número de métricas e
   verbosidade, além da densidade. **Densidade já existe** (`preferences.density`, aplicada como
   `[data-density]`), mas ela resolve só o espaçamento: quantas métricas aparecer e com quanto texto
   continua igual para todo mundo. Exige coluna em `PreferencesDb`, campo em `GET/PUT /preferences`
   e migração Alembic.

19. **Falta o componente `FairPrice`.** `MarginOfSafety`, `AllocationGap`, `GoalProgress`,
    `DipDiagnosis`, `ScoreRuler` e `Insight` existem, e a tabela profissional de posições também
    (colunas configuráveis e densidade, com o recorte na URL). Preço justo continua reimplementado
    caso a caso nas telas.

20. **[FEATURES.md](FEATURES.md) está uma revisão de navegação atrás.** Foi escrito quando os
    destinos eram Hoje e Estratégia, e não descreve as telas do caixa (`/mes`, `/mes/lancar`,
    `/mes/repetir`, `/mes/dividas`, `/sobra`). O que cada tela faz continua verdadeiro em
    [design/WIREFRAMES.md](design/WIREFRAMES.md) e no código; o inventário é que envelheceu.

21. **As três classes de diagnóstico de queda não foram validadas.** "Queda saudável / para
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

22. **A apuração de IR não cobre day trade nem IOF de renda fixa.** A apuração passou a ser
    projeção do razão, por mês e categoria (CHANGELOG de 2026-09-05), e isso fechou os defeitos de
    ordem de registro, isenção não reavaliada e venda que não apurava. Duas lacunas continuam, e
    estão declaradas nos Termos de Uso: o razão **não distingue day trade** de swing trade, e não
    há IOF sobre resgate de renda fixa com menos de 30 dias. Enquanto isso durar, o número é
    estimativa de apoio e não substitui a apuração oficial.

23. **A telemetria do mobile ainda não foi ligada nem verificada.** Backend e web já têm DSN; o
    mobile depende de `--dart-define=SENTRY_DSN=...` no build, e nenhum build assinado foi feito
    ainda. O código está pronto e testado — o que falta é o DSN e um build real.

24. **O lock de job periódico não é liberado ao terminar, só expira.** `_run_guarded` deixa o TTL
    vencer, e isso é **deliberado**: o TTL é o próprio intervalo do job, e liberar no fim do ciclo
    faria o worker seguinte repetir o trabalho segundos depois. O custo é real e continua aberto: se
    um worker morre logo após adquirir, o snapshot diário fica bloqueado por até 5,4h. A correção
    certa é heartbeat no lock, não release no `finally`. (O warm-up do scan é caso diferente — roda
    uma vez e **libera** no `finally`.)

25. **Token de push é reatribuído a quem o registrar.** `register_device_token()` move o token para
    o usuário da sessão se ele já existir — necessário para troca de dono do aparelho, mas significa
    que quem conhecer um token FCM alheio redireciona os alertas daquele aparelho para si. Entropia
    do token é a única proteção hoje.

26. **A paginação das listas com agregado limita o payload, não a consulta.** Proventos, renda fixa
    e sugestões seguidas ainda leem o conjunto inteiro do banco, porque os totais por mês, a marcação
    a mercado e a comparação com o Ibovespa precisam de todos os registros por definição. O que
    atravessa a rede está limitado; a consulta não. Resolver de verdade exige mover esses agregados
    para SQL — o que, no caso da renda fixa, significa mover a marcação a mercado junto.

27. **A acessibilidade foi coberta por verificação, não por auditoria.** Contraste (CI), nome
    acessível de botão (lint), alternativa textual de gráfico (lint) e foco visível estão de pé. O
    que **não** foi feito é percorrer cada fluxo só com teclado e com leitor de tela de verdade:
    ordem de foco em camadas empilhadas, anúncio de mudança de rota e armadilha de foco em modal
    ainda não têm cobertura automática nem verificação manual registrada. **Parcialmente
    endereçado:** a diretiva `fiDialog` (`core/directives/dialog.directive.ts`) prende o Tab,
    devolve o foco a quem abriu e dá papel e modalidade às seis superfícies sobrepostas; a mudança
    de rota é anunciada em região `aria-live`. O que continua aberto é a **inércia real do fundo**
    para o cursor virtual do leitor de tela — `aria-modal` promete uma inércia que o DOM não tem, e
    resolver isso exige tirar o diálogo da árvore da aplicação — e a verificação manual com leitor
    de tela de verdade.

28. **A aparência das telas nos dois temas nunca foi conferida em navegador.** O contraste é
    verificado no CI, mas por par de token — e o verificador, por construção, não enxerga estado
    composto por opacidade: `.btn-*:disabled` usa `opacity: 0.5` e o contraste real do botão
    desabilitado difere entre os temas, sem nunca ter sido medido. Há também a suspeita, levantada
    por análise de composição e **não confirmada no olho**, de que a elevação de modais e drawers é
    fraca demais no tema claro: o painel e o véu ficam em 1,06:1 nos dois temas, então quem separa
    é a sombra — e a do claro tem 27% da opacidade da do escuro.

29. **A cobrança não tem caminho de ponta a ponta.** Existe backend, régua de plano, preço travado e
    webhook idempotente; não existe tela de plano, exibição de preço, checkout, gestão de assinatura
    nem cancelamento na interface — `billing` não aparece em `web/src` nem em `mobile/lib`, e o CTA
    do `gate.component.ts` aponta para `/voce/plano`, que não existe em `app.routes.ts`. Some-se a
    isto que o relógio do trial **já está correndo** com a cerca desligada: `start_trial()` é
    chamado na primeira posição salva, então virar `ENTITLEMENTS_ENABLED` hoje derrubaria a base
    inteira para Free no mesmo instante. O trial precisa ser reiniciado na ativação da cerca, antes
    de virar a flag — não depois.

30. **O ETF é estruturalmente mal avaliado, e o remendo tem consequência.** Para `asset_type ==
    "etf"` o único candidato a consenso é Bazin (`dividendo / 0,04`); um ETF de índice distribui na
    casa de 1% ao ano, então o preço justo sai em ~25% do preço e a margem de segurança em −300%,
    sempre. `opportunity_service` sobrescreve o veredito por RSI e tendência quando ele sai
    `UNKNOWN`, o que produz duas coisas ruins: o mesmo ETF recebe veredito diferente em
    `/descobrir` e em `/ativo/:ticker`, e o veredito por momentum sai **sem falsificador**, porque
    sem consenso não há preço-limite. Decidir o método — comparação com o índice, prêmio sobre o
    valor patrimonial, ou abstenção explícita — vem antes de mexer no falsificador.

31. **Três das seis dimensões do score nunca têm dado, e o perfil de risco fica quase inerte.** A
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
