# fiance — o que está aberto

> **Só pendências.** Todo item aqui foi verificado contra o código em **2026-09-03**; nada de
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

## Duplicação estrutural entre plataformas

5. **Sobra o glossário e os rótulos de veredito.** Rótulo, ícone e cor de categoria, tipo de
   ativo, setor, tipo de renda fixa e liquidez passaram a ser **gerados** de `tokens.json`
   (2026-08-29), e o `--check` do CI reprova divergência. O que continua manual nos dois lados é
   o glossário de score e os rótulos de veredito, que são texto longo e não cabem bem num arquivo
   de tokens.

## Cobertura de testes

6. **O E2E cobre o esqueleto, não os fluxos.** `web/e2e/` roda Playwright contra o backend real e
   o build de produção com SSR, e cobre o que o resto da suíte não alcança: redirecionamento sem
   sessão, as cinco rotas principais e três aninhadas abrindo por **link direto**, e uma posição
   salva no servidor chegando à tela. O que **não** está coberto é o miolo — importar operações,
   passar pelo checkout, ver o gate aparecer, degradar de plano. São os fluxos que o plano lista, e
   eles dependem de cotação externa, que no ambiente de teste não é determinística.

7. **SQLite tranca sob concorrência de navegador.** Durante o E2E o backend loga
   `database is locked` em requisições paralelas. Não derruba os testes e não afeta produção, que é
   Postgres — mas torna o E2E local mais lento e potencialmente instável se ele crescer.

## Automação que não existe

8. **Sugestões seguidas dependem de lançamento manual.** `/suggestions/followed` só tem o que a
   pessoa registra. O caminho automático — reconhecer que uma sugestão virou compra a partir do
   razão — não foi implementado, e a base para ele já existe. *(A metade dos proventos foi
   resolvida: `/dividends/pending` cruza o calendário da BRAPI com a projeção do razão. Como toda
   ressalva ali erra o valor para mais, nada vem pré-selecionado e não existe "aceitar todos".)*

## Pendências do redesign de UX/UI

Estrutura de cada tela em [design/WIREFRAMES.md](design/WIREFRAMES.md); o contrato dos
componentes em [design/DESIGN-SYSTEM.md](design/DESIGN-SYSTEM.md).

9. **`detail_level` (Essencial / Completo / Avançado) não existe no backend.** É a alavanca que
   atenderia os três perfis de senioridade sem construir três produtos — número de métricas e
   verbosidade, além da densidade. **Densidade já existe** (`preferences.density`, aplicada como
   `[data-density]`), mas ela resolve só o espaçamento: quantas métricas aparecer e com quanto texto
   continua igual para todo mundo. Exige coluna em `PreferencesDb`, campo em `GET/PUT /preferences`
   e migração Alembic.

10. **Falta o componente `FairPrice`.** `MarginOfSafety`, `AllocationGap`, `GoalProgress`,
    `DipDiagnosis`, `ScoreRuler` e `Insight` existem, e a tabela profissional de posições também
    (colunas configuráveis e densidade, com o recorte na URL). Preço justo continua reimplementado
    caso a caso nas telas.

11. **As três classes de diagnóstico de queda não foram validadas.** "Queda saudável / para
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

12. **A apuração de IR é por operação; a lei é por mês.** `optimizer/cost_calculator.py` trata cada
    venda isoladamente: tributa o lucro na hora e só considera prejuízo já realizado e gravado
    antes. A regra brasileira compensa ganhos e perdas **dentro do mês e da categoria** e incide
    sobre o líquido do período. Vender com +R$ 10.000 no dia 5 e −R$ 10.000 no dia 20 informa
    R$ 1.500 de imposto onde o correto é zero, e inverter as datas produz o número certo — a ordem
    de registro dentro do mês muda o imposto informado. Consequências ligadas ao mesmo modelo:
    passar dos R$ 20.000 no mês não reavalia as vendas já gravadas como isentas, e não há noção de
    day trade nem de IOF em resgate de renda fixa com menos de 30 dias. Substituir "custo de uma
    venda" por "resultado do mês por categoria" resolve os três de uma vez, e é o que destrava o
    DARF.

13. **Vendas do razão não geram apuração.** Toda a apuração se apoia em `ClosedTradeDb`, e a única
    coisa que grava `ClosedTradeDb` é `POST /portfolio/sell`. Uma venda registrada por
    `POST /transactions` (`kind=sell`) ou vinda da importação de extrato não apura imposto, não
    conta para o teto mensal de R$ 20.000, não alimenta nem consome prejuízo compensável e não
    aparece em Encerradas. A escrita e a projeção da carteira já foram unificadas; a origem da
    apuração ainda não.

14. **O lock de job periódico não é liberado ao terminar, só expira.** `_run_guarded` deixa o TTL
    vencer, e isso é **deliberado**: o TTL é o próprio intervalo do job, e liberar no fim do ciclo
    faria o worker seguinte repetir o trabalho segundos depois. O custo é real e continua aberto: se
    um worker morre logo após adquirir, o snapshot diário fica bloqueado por até 5,4h. A correção
    certa é heartbeat no lock, não release no `finally`. (O warm-up do scan é caso diferente — roda
    uma vez e **libera** no `finally`.)

15. **Token de push é reatribuído a quem o registrar.** `register_device_token()` move o token para
    o usuário da sessão se ele já existir — necessário para troca de dono do aparelho, mas significa
    que quem conhecer um token FCM alheio redireciona os alertas daquele aparelho para si. Entropia
    do token é a única proteção hoje.

16. **A paginação das listas com agregado limita o payload, não a consulta.** Proventos, renda fixa
    e sugestões seguidas ainda leem o conjunto inteiro do banco, porque os totais por mês, a marcação
    a mercado e a comparação com o Ibovespa precisam de todos os registros por definição. O que
    atravessa a rede está limitado; a consulta não. Resolver de verdade exige mover esses agregados
    para SQL — o que, no caso da renda fixa, significa mover a marcação a mercado junto.

17. **A acessibilidade foi coberta por verificação, não por auditoria.** Contraste (CI), nome
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

18. **A aparência das telas nos dois temas nunca foi conferida em navegador.** O contraste é
    verificado no CI, mas por par de token — e o verificador, por construção, não enxerga estado
    composto por opacidade: `.btn-*:disabled` usa `opacity: 0.5` e o contraste real do botão
    desabilitado difere entre os temas, sem nunca ter sido medido. Há também a suspeita, levantada
    por análise de composição e **não confirmada no olho**, de que a elevação de modais e drawers é
    fraca demais no tema claro: o painel e o véu ficam em 1,06:1 nos dois temas, então quem separa
    é a sombra — e a do claro tem 27% da opacidade da do escuro.

19. **A cobrança não tem caminho de ponta a ponta.** Existe backend, régua de plano, preço travado e
    webhook idempotente; não existe tela de plano, exibição de preço, checkout, gestão de assinatura
    nem cancelamento na interface — `billing` não aparece em `web/src` nem em `mobile/lib`, e o CTA
    do `gate.component.ts` aponta para `/voce/plano`, que não existe em `app.routes.ts`. Some-se a
    isto que o relógio do trial **já está correndo** com a cerca desligada: `start_trial()` é
    chamado na primeira posição salva, então virar `ENTITLEMENTS_ENABLED` hoje derrubaria a base
    inteira para Free no mesmo instante. O trial precisa ser reiniciado na ativação da cerca, antes
    de virar a flag — não depois.

20. **O ETF é estruturalmente mal avaliado, e o remendo tem consequência.** Para `asset_type ==
    "etf"` o único candidato a consenso é Bazin (`dividendo / 0,04`); um ETF de índice distribui na
    casa de 1% ao ano, então o preço justo sai em ~25% do preço e a margem de segurança em −300%,
    sempre. `opportunity_service` sobrescreve o veredito por RSI e tendência quando ele sai
    `UNKNOWN`, o que produz duas coisas ruins: o mesmo ETF recebe veredito diferente em
    `/descobrir` e em `/ativo/:ticker`, e o veredito por momentum sai **sem falsificador**, porque
    sem consenso não há preço-limite. Decidir o método — comparação com o índice, prêmio sobre o
    valor patrimonial, ou abstenção explícita — vem antes de mexer no falsificador.

21. **Três das seis dimensões do score nunca têm dado, e o perfil de risco fica quase inerte.** A
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
