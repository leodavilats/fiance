# fiance — o que está aberto

> **Só pendências.** Todo item aqui foi verificado contra o código em 2026-08-22; nada de
> histórico, nada de ✅. O que já foi resolvido — e por quê — está em
> [CHANGELOG.md](CHANGELOG.md).
>
> Antes deste arquivo existir nesta forma, ele misturava as duas coisas: 227 linhas em que a
> maioria dos itens estava marcada como corrigida, com um aviso no topo dizendo "leia a seção
> final, ela substitui vários itens abaixo". Seis itens contradiziam o código atual.

## Limitações de dado e infraestrutura

1. **Cache é um SQLite local, não compartilhado.** Tem arquivo dedicado (`.cache/http_cache.db`,
   sobrescrevível por `CACHE_DB_PATH`), WAL, `busy_timeout` e conexão por thread. Mas continua
   **local ao processo**: com mais de um worker na mesma máquina, cada um mantém a própria cópia e
   refaz o scan. Os jobs de background já são protegidos por lock no banco, então múltiplos
   workers não duplicam notificação. Escalar horizontalmente exige volume compartilhado para
   `CACHE_DB_PATH` ou trocar por Redis — decisão consciente de manter SQLite por ora.

2. **`brapi_history_range` default `3mo` torna a SMA200 incalculável.** O plano gratuito da BRAPI
   só aceita ranges curtos. O sistema é honesto sobre isso (`trend_basis` = `short` e rotulado como
   tal na UI; `GET /data-quality` reporta a cobertura), mas tendência de longo prazo só existe de
   fato com plano pago e `BRAPI_HISTORY_RANGE=2y`.

3. **Unidade dos fundamentos da BRAPI não confirmada com chamada real.**
   `collectors/universal._ratio_to_pct` assume que `returnOnEquity` / `profitMargins` /
   `revenueGrowth` / `debtToEquity` vêm como razão decimal e multiplica por 100 — contrato
   explícito, no lugar da heurística antiga que lia um ROE de 120% como 1,2%. Vale confirmar contra
   uma resposta real; `GET /data-quality` dá a visibilidade.

4. **Universo hardcoded como fallback.** `core/config.py::default_universe` mantém ~400 tickers,
   apesar de já existir universo dinâmico via BRAPI (`core/universe.py`). Fallback defensivo
   intencional, mas extenso.

5. **`WatchlistItemDb` existe sem rota nem tela.** A feature de watchlist nunca teve interface; a
   rota foi removida em 2026-08-19 e a tabela ficou de propósito, para que reativar não exija
   migração. É schema sem consumidor.

## Duplicação estrutural entre plataformas

6. **Labels e ícones duplicados** entre `web/.../ui-helper.service.ts` (393 linhas) e
   `mobile/lib/core/labels.dart` (92). Cores, tipografia, espaçamento e as réguas semânticas já
   são **geradas** de `design-tokens/tokens.json` e não podem mais divergir; rótulo de setor,
   glossário e mapa de ícone continuam manuais nos dois lados. Adicionar um `AssetType` ou setor
   exige tocar os dois arquivos.

## Cobertura de testes

7. **O web não tem nenhum teste.** Backend tem 208 (`pytest`), mobile tem 13
   (`flutter test`), web tem zero `*.spec.ts`. Com a arquitetura de informação recém-reescrita e
   três telas novas, é o alvo natural — em especial `CarteiraStore`, `ScoreRuler` e os `computed`
   de `/hoje`, que carregam regra de apresentação de verdade.

## Automação que não existe

8. **Proventos e sugestões seguidas dependem de lançamento manual.**
   `/dividends/received` e `/suggestions/followed` só têm o que o usuário registra. O caminho
   automático (calendário de proventos da BRAPI × quantidade em carteira, com confirmação) não foi
   implementado — a base de dados para ele já existe.

## Pendências do redesign de UX/UI

Detalhe e justificativa em [design/07-IMPLEMENTATION.md](design/07-IMPLEMENTATION.md).

9. **`detail_level` (Essencial / Completo / Avançado) não existe no backend.** É a alavanca única
   que atende os três perfis de senioridade sem construir três produtos — densidade, número de
   métricas e verbosidade. Exige coluna em `PreferencesDb`, campo em `GET/PUT /preferences` e
   migração Alembic. Sem ela, todo usuário recebe a mesma densidade.

10. **Onboarding não existe, e precisa de um marcador de conclusão.** O primeiro acesso cai numa
    tela vazia. O fluxo de 3 passos está especificado e usa endpoints existentes, mas sem um
    `onboarded_at` (ou equivalente) ele reapareceria a cada login.

11. **Busca global não existe.** `GET /universe/search` só alimenta autocomplete de campo. Para
    ativo o backend já serve; setores e telas seriam índice de cliente.

12. **Drawer de Atividade não existe.** Alertas e eventos entram hoje no feed de `/hoje`; o
    histórico agrupado por urgência (Agora / Hoje / Informativo) está especificado e não construído.

13. **Componentes de domínio pendentes:** `MarginOfSafety`, `AllocationGap`, `GoalProgress`,
    `DipDiagnosis`, `FairPrice` e a tabela profissional (colunas configuráveis, densidade
    compacta, fixar coluna). A régua (`ScoreRuler`) e o `Insight` existem; os outros são
    reimplementados caso a caso nas telas.

14. **Gráfico de preço na página do ativo.** `/ativo/:ticker` mostra valuation por método, mas não
    a série de preço com preço médio e preço justo como linhas de referência — o elemento visual
    central que o wireframe pede.

15. **Mobile: Hoje e Carteira ainda têm o conteúdo antigo.** `dashboard_screen.dart` (1214 linhas)
    e `assets_screen.dart` (1231) não foram reestruturados nos três níveis, e `/carteira` não foi
    fatiada como no web. A régua e o `FiErrorState` já estão disponíveis para isso.

16. **Assimetrias mobile↔web declaradas:** metas no mobile ainda vivem em Configurações
    (`/estrategia/metas` redireciona para lá); RF × Bolsa (`GET /income-compare`) não tem cliente
    Dart. Push exigir o app instalado **não** é pendência — é decisão, e o web sinaliza isso em
    `/voce/alertas`.

17. **As três classes de diagnóstico de queda não foram validadas.** "Queda saudável / para
    investigar / estrutural" pressupõe que `dip_analysis.py` permita separar as duas últimas. Se o
    veredito atual não sustentar, são dois grupos, não três — verificar antes de desenhar o
    terceiro.

## Dívida de integridade financeira (aberta em 2026-08-26, revisada em 2026-08-27)

> O que a auditoria de 2026-08-26 encontrou e ainda **não** foi corrigido. Oito dos doze itens
> originais saíram nos portões G0 e G1 de 2026-08-27; o que saiu está no
> [CHANGELOG.md](CHANGELOG.md), com o porquê.

18. **A posição corrente ainda não é a projeção do razão.** O livro-razão existe e a escrita é
    espelhada nele, mas `PortfolioPosition` continua sendo a fonte de leitura. É o passo 2 de 3 do
    plano, deliberado: `GET /transactions/reconciliation` compara os dois lado a lado e o teste de
    integração cobre o caminho, mas trocar a fonte é uma entrega própria. Enquanto isso, o razão
    grava `adjust` quando o usuário declara estado na tela — quando a importação de nota e CSV
    chegar (G2), ela grava `buy` de verdade e `adjust` vira exceção.

19. **Decimal cobre o caminho fiscal, não o schema.** A projeção do razão e a apuração de IR rodam
    em `Decimal` com escala e arredondamento em `app/core/money.py`. As **colunas do banco**
    continuam `Float`, e preço, patrimônio e indicadores de tela seguem em float — o que é
    adequado para apoio à decisão e não para um extrato somado. Migrar as colunas monetárias para
    `Numeric` é uma migração grande e ainda não foi feita.

20. **O lock de job periódico não é liberado ao terminar, só expira.** `_run_guarded` deixa o TTL
    vencer, e isso é **deliberado**: o TTL é o próprio intervalo do job, e liberar no fim do ciclo
    faria o worker seguinte repetir o mesmo trabalho segundos depois. O custo é real e continua
    aberto: se um worker morre logo após adquirir, o snapshot diário fica bloqueado por até 5,4h.
    A correção certa é heartbeat no lock, não release no `finally`. (O warm-up do scan é caso
    diferente — roda uma vez e **libera** no `finally`, corrigido em 2026-08-27.)

21. **Token de push é reatribuído a quem o registrar.** `register_device_token()` move o token
    para o usuário da sessão se ele já existir — necessário para troca de dono do aparelho, mas
    significa que quem conhecer um token FCM alheio redireciona os alertas daquele aparelho para
    si. Entropia do token é a única proteção hoje.

22. **Dado externo não tem faixa de plausibilidade.** A BRAPI é validada por tipo
    (`_safe_float`), não por magnitude: preço, market cap, ROE ou dividend yield absurdos entram
    no cálculo e no patrimônio sem barreira. Falta um teto/piso declarado por campo, e um caminho
    para rejeitar o snapshot inteiro em vez de aceitar o número. Está no portão G2.

23. **Listas sem paginação.** `/portfolio/trades`, `/dividends/received`, `/fixed-income`,
    `/suggestions/followed` e agora `/transactions` devolvem tudo (o razão tem teto de 2000, que é
    limite, não cursor). Crescem com o uso. Versão da API e paginação por cursor estão no G2.

24. **Não existe canal de aquisição orgânico.** As rotas `/ativo/:ticker` são renderizadas no
    cliente e portanto invisíveis para busca. O modelo de receita não comporta mídia paga — teto
    de CAC de R$ 72 contra R$ 500–1.500 de instalação qualificada em finanças no Brasil —, então
    renderização no servidor deixa de ser refinamento técnico e vira pré-requisito de negócio.
    Está no portão G2 e é o item de maior risco de execução do plano.

## Armadilhas conhecidas (não são bugs, mas mordem)

- **Ícone do Lucide precisa ser registrado à mão** em `LucideAngularModule.pick({...})`
  (`web/src/main.ts`). Nome ausente ou errado **não quebra o build** — quebra a tela em runtime.
  Ao adicionar um `<lucide-icon>`, registre o import e abra a tela.
- **Construtor que ignora chave não declarada.** `Modelo(**resultado.__dict__)` no Pydantic e
  `fromJson` no Dart descartam campo não declarado **em silêncio**. Três campos calculados nunca
  chegaram ao cliente por causa disso (`consensus_methods`, `trend_basis`, `allocation_gaps`). Ao
  adicionar campo a um resultado interno, verifique se o modelo de resposta o declara.
- **Coluna nova exige migração Alembic.** Mexer no model não basta.
