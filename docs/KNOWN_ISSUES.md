# fiance — o que está aberto

> **Só pendências.** Todo item aqui foi verificado contra o código em **2026-08-28**; nada de
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

3. **Unidade dos fundamentos da BRAPI não confirmada com chamada real.**
   `collectors/universal._ratio_to_pct` assume que `returnOnEquity` / `profitMargins` /
   `revenueGrowth` / `debtToEquity` vêm como razão decimal e multiplica por 100 — contrato
   explícito, no lugar da heurística antiga que lia um ROE de 120% como 1,2%. Vale confirmar contra
   uma resposta real; `GET /data-quality` dá a visibilidade.

4. **Universo hardcoded como fallback.** `core/config.py::default_universe` mantém ~400 tickers,
   apesar de já existir universo dinâmico via BRAPI (`core/universe.py`). Fallback defensivo
   intencional, mas extenso.

5. **`WatchlistItemDb` existe sem rota nem tela.** A feature nunca teve interface; a rota foi
   removida em 2026-08-19 e a tabela ficou de propósito, para que reativar não exija migração. É
   schema sem consumidor.

## Duplicação estrutural entre plataformas

6. **Labels e ícones duplicados** entre `web/src/app/core/services/ui-helper.service.ts` (297
   linhas) e `mobile/lib/core/labels.dart` (99). Cor, tipografia, espaçamento e as réguas semânticas
   já são **geradas** de `design-tokens/tokens.json` e não podem divergir; rótulo de setor,
   glossário e mapa de ícone continuam manuais nos dois lados. Adicionar um `AssetType` ou setor
   exige tocar os dois arquivos.

## Cobertura de testes

7. **Nenhum teste roda no navegador.** Backend tem 724 (`pytest`), web 90 (Vitest) e mobile 49
   (`flutter test`), e `backend/tests/test_jornadas.py` atravessa as jornadas críticas — primeira
   posição → trial → teto → checkout → webhook → cancelamento → exportação → exclusão — pelo app
   real, com HTTP, autenticação e banco. O que **não** é exercitado é a interface: nenhum teste abre
   o Angular num navegador, então quebra de renderização, foco, rota e formulário só aparece em uso.
   Vitest roda componentes em jsdom, o que não é a mesma coisa. Ligar Playwright exige backend e web
   servidos no CI e download de navegador — é trabalho de infraestrutura, não de teste.

## Automação que não existe

8. **Sugestões seguidas dependem de lançamento manual.** `/suggestions/followed` só tem o que a
   pessoa registra. O caminho automático — reconhecer que uma sugestão virou compra a partir do
   razão — não foi implementado, e a base para ele já existe. *(A metade dos proventos foi
   resolvida: `/dividends/pending` cruza o calendário da BRAPI com a projeção do razão. Como toda
   ressalva ali erra o valor para mais, nada vem pré-selecionado e não existe "aceitar todos".)*

## Pendências do redesign de UX/UI

Detalhe e justificativa em [design/07-IMPLEMENTATION.md](design/07-IMPLEMENTATION.md).

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

## Dívida aberta (auditoria de 2026-08-26)

12. **A posição corrente ainda não é a projeção do razão.** O livro-razão existe e a escrita é
    espelhada nele, mas `PortfolioPosition` continua sendo a fonte de leitura. É o passo 2 de 3 do
    plano, deliberado: `GET /transactions/reconciliation` compara os dois lado a lado e o teste de
    integração cobre o caminho, mas trocar a fonte é uma entrega própria. A importação de operações
    já grava `buy` de verdade (`importing/`, `/transactions/import`); `adjust` ficou para quando a
    pessoa declara estado direto na tela.

13. **Decimal cobre o caminho fiscal, não o schema.** A projeção do razão e a apuração de IR rodam
    em `Decimal` com escala e arredondamento em `core/money.py`. As **colunas do banco** continuam
    `Float`, e preço, patrimônio e indicadores de tela seguem em float — adequado para apoio à
    decisão, não para um extrato somado. Migrar as colunas monetárias para `Numeric` é uma migração
    grande e ainda não foi feita.

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
    ainda não têm cobertura automática nem verificação manual registrada.

## Armadilhas conhecidas

Não são bugs, mas mordem. A lista completa, com o que cada uma já quebrou, está em
[CLAUDE.md](../CLAUDE.md#armadilhas-que-não-quebram-o-build).

- Ícone do Lucide não registrado quebra a tela em runtime, não o build.
- Classe CSS inexistente quebra a tela em silêncio.
- `Modelo(**resultado.__dict__)` e `fromJson` descartam campo não declarado sem avisar.
- Coluna nova exige migração Alembic — mexer no model não basta.
