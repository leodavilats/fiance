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
plataformas. Os documentos de projeto estão em [design/](design/); o log de execução, com o que
está no ar e o que não está, em [design/07-IMPLEMENTATION.md](design/07-IMPLEMENTATION.md).

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
confiança. Score com dado incompleto sai **cinza** e rotulado "dado insuficiente" em vez de
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
