# fiance — a direção proposta: de análise de ativos a planejador financeiro

> Análise da proposta levantada em **2026-09-04**, contra o código em `5f2b0bb`. Isto **não é uma
> decisão** — é o material para tomá-la: o que a ideia acerta, o que ela subestima, o que já existe
> e serve, o que teria de ser construído, e em que ordem.
>
> O que for decidido vai para o [CHANGELOG](../CHANGELOG.md), com data. O que virar trabalho
> vai para [KNOWN_ISSUES](../KNOWN_ISSUES.md). Este arquivo é o raciocínio, não o registro.
>
> **Aviso sobre números de mercado:** as afirmações sobre concorrentes, disposição a pagar e
> tamanho de público neste documento são leitura de mercado, não medição. Nenhuma delas foi
> verificada contra fonte primária aqui. Confira antes de usar em decisão de investimento de tempo
> ou em material de venda.
>
> **Atualização de 2026-09-04, mais tarde no mesmo dia:** as sete perguntas do §11 foram
> respondidas — ver [VISAO.md](VISAO.md#as-sete-perguntas-do-direcao_produto-11--respondidas).
> O que foi decidido a partir daqui está em VISAO_NOVA e nos arquivos que ela referencia; este
> documento continua valendo como o raciocínio que levou lá, e o §11 abaixo fica como registro do
> que foi perguntado, não como pendência aberta.

---

## 1. A proposta, como entendida

1. **Diagnóstico:** fora o destaque de oportunidades, o produto não entrega nada que o site da B3 (e
   os agregadores gratuitos) já não entreguem.
2. **Novo público:** pessoa comum, assalariada, que **não tem tempo** de acompanhar o mercado de
   perto.
3. **Novo escopo:** gastos fixos, gastos eventuais e investimentos **no mesmo lugar**.
4. **Insumos declarados:** dia do salário, valor do salário, **regime de contratação**, gastos fixos
   e eventuais.
5. **Onboarding por perguntas** que traçam perfil e necessidades — inclusive se os gastos costumam
   variar muito.
6. **Sem digitação de operação:** as compras e vendas de ativos entram automaticamente, "de alguma
   forma".
7. **Alerta de troca:** avisar quando um ativo valorizar muito e talvez valha vender para comprar
   outro com potencial maior.
8. **Papel duplo:** organizador financeiro **e** educador para quem não conhece o mercado.

---

## 2. O diagnóstico está certo? Em parte — e a parte errada importa

**Contra o site da B3, o diagnóstico é falso.** A B3 não consolida carteira, não calcula preço
justo por quatro métodos, não marca renda fixa a mercado, não compara alocação com meta, não apura
IR, não projeta renda passiva com faixa. O produto entrega bastante mais que a B3.

**Contra o concorrente real, o diagnóstico está certo.** O concorrente não é a B3 — é Status Invest,
Investidor10, Kinvo, Gorila, Real Valor e o app da própria corretora. Todos gratuitos ou baratos,
todos com consolidação, proventos, IR e indicadores. Diante deles, o que o fiance tem de próprio se
resume a: oportunidades com preço justo, falsificadores do veredito, e a disciplina de
explicabilidade — que é excelente engenharia e **invisível para quem nunca comparou**.

Mas a conclusão certa não é "faltam features". São dois furos diferentes, e só um deles se resolve
construindo mais análise:

| Furo | Sintoma | Features de análise resolvem? |
|---|---|---|
| **Frequência** | uma carteira de longo prazo não muda toda semana; não há motivo para abrir o app | **não** |
| **Diferenciação** | tudo que o produto faz, alguém já faz de graça | parcialmente, e devagar |
| **Atrito de entrada** | o produto só funciona depois que a pessoa **digita a carteira inteira** | **não** |

O terceiro é o mais grave e não aparece na proposta como problema separado, embora o item 6 dela
seja exatamente a tentativa de resolvê-lo. Hoje o funil é: cadastrar → digitar posição por posição →
só então ver valor. Todo o esforço de onboarding derivado, importação tolerante e edição por linha é
um remendo bom num problema que continua sendo o maior motivo de abandono do segmento.

---

## 3. O que a proposta acerta — e acerta forte

### 3.1 Ela resolve o furo de frequência, que análise nenhuma resolve

Dinheiro entra e sai todo mês; carteira de longo prazo, não. Um app que sabe o dia do salário e as
contas do mês tem motivo para ser aberto semanalmente — e, com isso, ganha o direito de falar sobre
investimento no momento em que a pessoa tem dinheiro na mão. Hoje o app fala de aporte sem saber se
existe aporte.

### 3.2 Ela dá conteúdo ao começo, que hoje é vazio

Quem não tem carteira não tem produto: `entitlement.check` libera tudo com carteira vazia
justamente porque não há o que cercar. Com a camada de caixa, o app **serve a pessoa antes de ela
investir** — e é ela quem descobre, dentro do produto, que sobra dinheiro. O primeiro aporte deixa
de ser pré-requisito e vira conversão.

### 3.3 A ponte entre os dois lados é o produto — e ninguém a faz

Esta é a tese mais forte que a proposta contém, e vale escrevê-la explicitamente:

> **App de orçamento sabe quanto sobra e não sabe o que fazer com a sobra.
> App de investimento sabe o que fazer com a sobra e não sabe se ela existe.**

O fiance é o caso raro em que **metade da ponte já está construída**: `optimizer/`, `quick_invest`,
`goals`, `sector_goals`, `analysis/scenarios.py` com projeção em faixa, e a tela de Aporte que já
pergunta "quanto você tem para investir" — hoje respondida à mão em `preferences.cash_available`.
Trocar esse campo digitado pela **sobra calculada do mês** é, conceitualmente, uma linha; e é o
diferencial inteiro.

### 3.4 O regime de contratação é um detalhe melhor do que parece

A proposta cita "regime de contratação" de passagem, e é o item com maior potencial de
diferenciação da lista — porque quase nenhum app de orçamento brasileiro trata disso a sério:

| Regime | O que muda no planejamento |
|---|---|
| CLT | 13º e férias são **dois eventos de sobra grande por ano** — o melhor gancho de aporte que existe; FGTS é patrimônio que a pessoa esquece que tem |
| PJ / MEI | não há 13º nem férias: o planejamento precisa **provisionar** os dois, além de DAS/pró-labore e do IRPF; renda é mais volátil |
| Autônomo / comissionado | renda variável obriga o orçamento a raciocinar por média e piso, não por valor fixo |

"Seu 13º cai em novembro; nesse mês sua sobra é o dobro" e "você é PJ e ainda não separou o imposto
deste mês" são frases que um app de investimento nunca disse a essa pessoa. Isso é utilidade
imediata, não análise.

### 3.5 O papel de educador já tem esqueleto no repositório

A disciplina de explicabilidade não é discurso aqui: o `lint:ui` **reprova** julgamento renderizado
sem `<app-provenance>` ou equivalente, `analysis/falsifiers.py` entrega o que derrubaria cada
veredito, e a projeção sai em faixa por invariante. Educação contextual — explicar no momento em que
o número aparece — é exatamente o formato que essa arquitetura favorece, e é o oposto de "seção de
cursos", que ninguém abre.

---

## 4. O que a proposta subestima

### 4.1 O mercado de orçamento é mais disputado e paga menos que o de investimento

Mobills, Organizze, Minhas Economias, mais o app de todo banco digital com "planejamento" embutido
de graça. A disposição a pagar por controle de gastos é baixa e o churn é alto — a pessoa resolve o
problema, ou desiste dele, em poucos meses. O contraexemplo mais instrutivo é o Guiabolso: tinha a
melhor agregação bancária do país e não sobreviveu ao modelo.

Isto não invalida a direção. Invalida a versão dela em que **orçamento é o produto**. O que se
vende é a ponte (§3.3), não a planilha.

### 4.2 Lançamento manual de gasto morre em três semanas

É o padrão mais conhecido da categoria: a pessoa anota tudo por duas semanas, esquece um fim de
semana, os números param de bater, e o app vira mentira. Ninguém volta.

A proposta diz "ela anotaria os gastos mensais". **Essa é a parte que não funciona.** Se o gasto
depende de digitação, o produto tem prazo de validade curto — e a ponte, que precisa da sobra real
para funcionar, se alimenta de dado errado.

Consequência direta: **a nova direção depende de importação automática de transação bancária.** Não
é melhoria futura, é requisito. O que nos leva ao próximo item.

### 4.3 "Pegar as operações automaticamente de alguma forma" — não existe "de alguma forma" grátis

Há exatamente três caminhos no Brasil, e nenhum é o que a frase sugere:

| Caminho | Cobre | Automático? | Custo | Esforço |
|---|---|---|---|---|
| **Extrato de Movimentação da B3 (XLSX)** | operações, proventos, eventos corporativos, todas as corretoras | **não** — a pessoa baixa e envia | zero | dias: `importing/parser.py` hoje só lê CSV genérico |
| **Open Finance via agregador** (Pluggy, Belvo, Klavi, Quanto) | **transação bancária e de cartão** + investimentos | sim, com reconexão periódica | **por conexão ativa/mês** | alto: consentimento, sincronização, revogação, reconciliação |
| **Nota de corretagem por e-mail/PDF** | operações | quase | zero | alto e frágil: um layout por corretora |

E um caminho que **não** deve ser considerado: raspar o site da corretora com a senha da pessoa.
Viola termo de uso, quebra a cada MFA, e guarda credencial de terceiro — risco jurídico e de
segurança desproporcional.

O ponto que a proposta não enxerga: **o Open Finance é o único que atende os dois lados ao mesmo
tempo.** A mesma conexão que traz o extrato do cartão (que resolve §4.2) traz a posição na
corretora (que resolve o item 6 da proposta). Isso é um argumento forte *a favor* da direção — um
custo que antes serviria só à carteira agora se divide entre as duas metades do produto.

Mas é **custo recorrente por usuário ativo**, e isso muda a natureza do negócio:

| Modelo | Consequência |
|---|---|
| Free com Open Finance para todos | cada usuário gratuito custa dinheiro todo mês; não fecha |
| Free manual, pago automático | a conexão vira **a** razão de assinar — e é a mais fácil de explicar em uma frase |
| Pago desde o início | mata o funil do §3.2, que é a maior vantagem da direção |

A linha do meio é a única que fecha, e ela **precisa estar decidida antes de a camada de caixa ser
construída**, porque define o que fica de que lado da cerca. Note que a arquitetura já suporta isso
sem gambiarra: a régua é dado em `entitlement/plans.py`.

### 4.4 O alerta de "valorizou muito, talvez valha vender e comprar outro" é o item mais perigoso

Ele colide com quatro coisas ao mesmo tempo:

1. **Regulatório.** "Venda X e compre Y" é recomendação individualizada de valor mobiliário — o
   nível 3 de `affirmation.py`, o que o próprio repositório já isola atrás de configuração
   justamente para não decidir isso sob pressão. Ver A3 do [PRE_PRODUCAO](PRE_PRODUCAO.md).
2. **O público declarado.** A proposta descreve alguém que *não tem tempo de acompanhar o mercado*.
   Empurrar troca de posição para essa pessoa é o contrário do que ela precisa: giro alto destrói
   retorno de pessoa física por custo, imposto e erro de tempo.
3. **Imposto.** Vender realiza ganho, consome o teto de R$ 20 mil e gera DARF — e a apuração de IR
   do produto está estruturalmente errada hoje (A4 do PRE_PRODUCAO). Sugerir venda sem saber o
   imposto que ela gera é sugerir um prejuízo invisível.
4. **A promessa do produto.** Vale-do-preço-justo e falsificadores existem para dizer *por que* um
   preço está caro. Um alerta de troca sem essa cadeia é palpite com cara de sistema.

**O reenquadramento — que entrega a mesma utilidade e nada disso:** o gatilho não é "valorizou
muito", é **"mudou de estado"**, e a frase é sobre a regra da própria pessoa, não sobre o mercado:

> *"PETR4 subiu 34% e agora está 22% acima do preço justo estimado por três métodos. Com isso,
> Energia passou a ser 19% da sua carteira, contra a meta de 10% que você definiu. Rebalancear
> significaria vender cerca de R$ X — o que geraria IR de cerca de R$ Y. O que derrubaria essa
> leitura: [falsificador]."*

Mesmo dado, mesma ação disponível, mas o produto informa e a pessoa decide — que é a postura do
nível 2, é o que a explicabilidade já cobra, e é o que dispensa parecer para funcionar. **Recomendo
construir essa versão e não a outra**, independentemente do resto da decisão.

### 4.5 O questionário longo mata o funil, e conflita com um invariante existente

O CLAUDE.md registra: *"Onboarding é derivado, não guardado. Um contador criaria segunda verdade."*
Um questionário extenso vai na direção oposta e, pior, pergunta o que dá para medir:

| Pergunta proposta | Melhor caminho |
|---|---|
| "seus gastos variam muito?" | **medir** depois de dois meses de dado; a resposta declarada é ruim e a medida é grátis |
| "qual seu perfil de risco?" | já existe em `preferences.risk_profile`; manter uma pergunta, não seis |
| dia e valor do salário, regime | **perguntar** — é fato, não opinião, e sem isso nada funciona |
| gastos fixos | perguntar os 3 maiores; descobrir o resto do extrato |

Regra prática: no máximo cinco perguntas antes de a pessoa ver algo útil. Tudo que puder ser
derivado do dado depois, derive — é a mesma disciplina que já vale para `/onboarding`.

Nota de coerência: guardar *respostas de fato* (salário, regime, dia de pagamento) **não** viola o
invariante. O invariante é sobre não guardar **progresso**; salário é dado declarado, como meta.
Vale escrever isso no CLAUDE.md junto com a mudança, para ninguém "consertar" depois.

### 4.6 O risco de virar dois produtos com um time

A direção nova não dispensa nenhuma manutenção da direção velha. O motor de análise continua com
buracos reais — KI#3 e KI#21 registram que `roe`, `profit_margin`, `revenue_growth` e
`debt_to_equity` voltam nulos da BRAPI, sobrando **0,60 de peso** no perfil conservador: metade do
score não existe e o perfil de risco é quase inerte. Se metade da atenção for para caixa, esse
buraco não fecha, e o lado que supostamente diferencia o produto continua manco.

Isso não é argumento contra a direção. É argumento contra fazer as duas coisas em paralelo, e a
favor da sequência do §10.

### 4.7 A LGPD sobe de patamar

Carteira de investimento é dado sensível. **Extrato bancário e de cartão é mais**: revela saúde,
religião, orientação política, endereço, hábitos. Some-se que o consentimento de Open Finance tem
regras próprias — prazo, escopo, revogação a qualquer momento, e a revogação precisa funcionar de
verdade no produto.

O repositório começa bem posicionado: exportação e exclusão fora de qualquer gate, dicionário
fechado de eventos que **recusa** propriedade com ticker ou valor, lápide anonimizada, tabelas com
dono declaradas em `account_store.USER_SCOPED_MODELS`. Mas o texto jurídico não existe (A2 do
PRE_PRODUCAO), e agora precisa cobrir muito mais. Toda tabela nova de caixa **precisa entrar em
`USER_SCOPED_MODELS`** — é o que faz exportação e exclusão continuarem verdadeiras, e há teste que
cobra.

---

## 5. Pivô ou extensão? — a recomendação

**Não é pivô. É extensão com inversão de fachada.** A distinção não é semântica; ela decide o que se
apaga.

| | Pivô (como proposto) | Extensão com inversão (recomendado) |
|---|---|---|
| Motor de análise | vira acessório | **continua sendo o cérebro**, e é o que ninguém copia rápido |
| Camada de caixa | é o produto | é a **porta de entrada** e o motivo de voltar |
| O que se vende | organizador financeiro | **a ponte**: sua sobra vira aporte, seu aporte vira meta |
| Herança de código | ~45k linhas viram contexto | ~45k linhas seguem no caminho crítico |
| Público | troca | **soma** — o investidor atual não perde nada |

Concretamente, o que muda de lugar:

- **Sobe:** caixa do mês, sobra projetada, aporte planejado, meta de renda passiva, educação
  contextual.
- **Desce, mas não sai:** varredura de oportunidades deixa de ser a estrela e vira o que responde
  *"onde colocar a sobra deste mês"* — que é, aliás, um uso melhor dela do que o atual.
- **Não sai de jeito nenhum:** preço justo, falsificadores, régua de score, renda fixa marcada a
  mercado, livro-razão, IR. É o que faz a sugestão de aporte valer alguma coisa; sem isso a ponte
  desemboca num app de orçamento com um botão.

E o cenário honesto oposto, para ficar registrado: **se a convicção for que o negócio é orçamento**,
então a decisão certa é começar outro produto, porque quase nada do que existe hoje serve — e vale
saber disso antes, não depois de seis meses tentando encaixar.

---

## 6. O que já existe e serve à nova direção

Inventário concreto, porque é a maior vantagem desta ideia sobre começar do zero:

| Peça | Onde | Como serve |
|---|---|---|
| Razão como fonte única, com porta de escrita única | `ledger/`, `ledger_service` | o **padrão** se repete para caixa: lançamento é a verdade, saldo é projeção |
| Importação prévia + commit, tolerante com forma, duplicidade apresentada | `importing/` | é exatamente o que extrato bancário exige; `import_entries` já é o alvo natural de qualquer sincronização automática |
| `Money`/`Decimal`, `sum_money`, arredondamento meio para cima | `core/money.py` | gasto é dinheiro fiscal; a disciplina já está pronta e testada |
| Mês calendário BRT | `core/brt.py` | o mês do orçamento é o mês fiscal brasileiro, não UTC |
| Metas, otimizador, aporte rápido, projeção em faixa | `goals`, `optimizer/`, `quick_invest`, `analysis/scenarios.py` | **o lado direito da ponte, construído** |
| Perfil de risco e preferências | `preferences` | base do perfil, sem tabela nova |
| Cerca de plano como dado, desligada | `entitlement/plans.py` | dá para mover a linha do free/pago sem tocar em regra de negócio |
| Dicionário fechado de eventos que recusa ticker e valor | `core/events.py` | analytics de um app financeiro sem vazar dado financeiro |
| Tokens, vocabulário gerado e `lint:ui` | `design-tokens/` | tela nova nasce coerente nas três plataformas; **categoria de despesa deve nascer aqui**, como já nascem categoria de ativo e tipo de renda fixa |
| Tabelas com dono, exportação e exclusão | `account_store` | LGPD do §4.7 sai quase de graça, se as tabelas novas forem registradas |
| Push, alertas, cadência configurável | `notifications/` | canal do alerta reenquadrado do §4.4 |
| Níveis de afirmação | `affirmation.py` | a fronteira do §4.4 já é configuração, não refactor |

---

## 7. O que precisa ser construído

Ordem de grandeza, não estimativa fechada:

| Peça | Decisão de arquitetura | Tamanho |
|---|---|---|
| **`cashflow/`** — razão de caixa (entrada, saída, transferência) | módulo **irmão** de `ledger/`, **não** dentro dele | grande |
| Recorrência: salário no dia X, contas fixas, parcelas | expansão de série no tempo, em BRT, com "previsto × realizado" | média |
| Categoria de despesa | **vocabulário gerado** em `tokens.json`, como as demais | pequena |
| Orçamento por categoria e **sobra projetada do mês** | é o insumo da ponte; sai como faixa quando a renda é variável | média |
| Reserva de emergência | regra simples sobre gasto essencial; precede qualquer sugestão de aporte | pequena |
| Dívida (rotativo, empréstimo) | **decisão de escopo**, ver §11 | média |
| Perfil (≤5 perguntas) + derivação | respostas são fato declarado; o resto se mede | pequena |
| Conexão Open Finance | consentimento, sincronização, revogação, reconexão, reconciliação | grande |
| Nova arquitetura de informação | §9 | média |
| Educação contextual | conteúdo, não código | contínua |

**Por que `cashflow/` fora de `ledger/`:** o invariante mais estável do repositório é *"o livro-razão
é a fonte da carteira; a posição é projeção dele"*, com uma porta de escrita única que existe porque
já foi violada e a Carteira parou de mudar em silêncio. Caixa tem outra unidade (só dinheiro, sem
quantidade), outra semântica de tempo (competência × caixa) e outra reconciliação (saldo bancário).
Enfiar as duas no mesmo razão troca um invariante testado por um genérico. Irmãos, com o **mesmo
padrão** e um ponto de encontro explícito: *aporte* é saída de caixa **e** entrada de posição — e
esse é o único lançamento que os dois lados compartilham.

---

## 8. Integrações, reordenadas pela nova direção

Esta seção veio do documento de pré-produção e foi **reordenada**: sob a direção nova, as
prioridades mudam de lugar.

| Integração | Custo | Papel na direção nova | Quando |
|---|---|---|---|
| **Extrato B3 (XLSX) no parser** | zero | mata o atrito de entrada **hoje**, sem depender da decisão | **já** — melhor razão valor/esforço do repositório |
| **Tesouro Direto** (API pública) | zero | **sobe muito**: o público novo entra por Tesouro Selic, não por ação; a arquitetura de renda fixa já está de pé | fase 2 |
| **Open Finance (Pluggy/Belvo/Klavi)** | por conexão/mês | deixa de ser opcional: é o que torna a camada de caixa verdadeira (§4.2) **e** resolve o item 6 da proposta | fase 3, atrás de validação |
| **CVM Dados Abertos** (DFP/ITR em CSV) | zero | fecha KI#3/KI#21 — os quatro fundamentos nulos passam a ser derivados de fonte oficial, e "fonte: CVM, DFP 2025" é credibilidade que agregador não dá | quando o motor voltar ao foco |
| **BRAPI paga** | mensalidade | preço e histórico; resolve KI#2 (SMA200) | quando houver receita |
| **E-mail transacional** | barato | pré-requisito de cobrança (B5) **e** o canal do público novo que não instala app | com a cobrança |
| **WhatsApp (Meta Cloud API)** | por conversa | **sobe**: o público novo é WhatsApp-first, e "sua sobra deste mês é R$ X" é mensagem que se lê ali | após validar |
| **Telegram (bot)** | zero | alternativa subestimada para testar o canal sem custo | experimento |
| **Landing pública + conteúdo** | zero | hoje a raiz redireciona para `/hoje`, que exige sessão: o robô só alcança `/ativo/:ticker`. A promessa nova precisa de uma página que a explique | fase 1 |
| **Analytics de leitura** (PostHog ou tela de operador) | free tier | os 27 eventos já existem; falta **ler** funil e retenção — e a nova direção é uma aposta que só se confirma medindo | fase 1 |
| **Sentry, uptime, log** | free tier | pré-requisito de subir, independente de direção (A5) | agora |
| **IA de escopo estreito** | por uso | **um uso novo e legítimo**: classificar transação bancária em categoria de despesa — não há julgamento de investimento envolvido, então não fere a fronteira do §4.4. Também: normalizar cabeçalho de CSV que o parser não reconhece, e redigir em português o que o backend já calculou | fase 3 |
| **Cotação em tempo real** | alto | continua **fora** — contradiz o público que "não tem tempo de acompanhar" | nunca, provavelmente |

---

## 9. O que a direção nova mexe nos invariantes

Não dá para adotar isto e deixar o [CLAUDE.md](../../CLAUDE.md) como está. O que muda:

| Invariante hoje | Impacto | Proposta |
|---|---|---|
| **Cinco destinos por intenção** | "para onde foi meu dinheiro este mês" é uma **sexta** intenção | duas saídas, ver abaixo |
| **Onboarding é derivado, não guardado** | o perfil é a primeira coisa guardada | manter o invariante para **progresso**; salário e regime são fato declarado, como meta. Escrever isso |
| **Escrita do razão passa por `ledger_service`** | o caixa precisa da mesma porta única | replicar o padrão em `cashflow_service`, e testar |
| **Dinheiro fiscal é `Decimal`** | vale igual para gasto | nada muda, só aplicar |
| **Regra de negócio só no backend** | orçamento também | nada muda |
| **Push exige app instalado** | o público novo instala menos e responde mais no WhatsApp | e-mail e WhatsApp deixam de ser opcionais |
| **Modo de afirmação** | o alerta do item 7 é nível 3 | construir a versão do §4.4, que é nível 2 |

**Sobre a sexta intenção**, as duas saídas:

| Opção | Como fica | A favor | Contra |
|---|---|---|---|
| **A — sexto destino** (`/dinheiro`) | Hoje · Dinheiro · Carteira · Descobrir · Estratégia · Você | separação limpa, cada destino segue com uma intenção | seis é o teto da barra inferior no mobile; a IA foi desenhada para cinco |
| **B — Hoje muda de dono** (recomendado) | Hoje passa a abrir pelo mês corrente (sobra, contas a vencer, salário), e patrimônio desce um nível | não cria destino, e é honesto: para o público novo o mês **é** o "hoje" | mexe na tela mais madura do produto, e o investidor atual estranha |

A B é a recomendada porque a IA atual foi desenhada por intenção, e a intenção do público novo ao
abrir o app é *"como estou este mês"*. Mas isso é decisão de design e precisa passar por
[docs/design/](../design/) antes de virar código — é o que o próprio contrato de trabalho
manda.

---

## 10. Sequência recomendada

O ponto da sequência é **não construir a parte cara antes de a tese estar validada**.

### Fase 0 — agora, independente da decisão (1–2 semanas)

- Trilha A do [PRE_PRODUCAO](PRE_PRODUCAO.md): subir de graça, com observabilidade e texto jurídico.
- **Pausar a trilha B.** Tela de plano e provedor de pagamento dependem do que se vende.
- **Extrato B3 no parser** — serve às duas direções, custa dias, e é o maior alívio de atrito
  disponível hoje.

### Fase 1 — validação, antes de código pesado (~2 semanas)

A direção nova é uma aposta num público que o time ainda não entrevistou. Barato descobrir agora:

- 10 a 15 conversas com o público-alvo descrito (assalariado, investe pouco ou nada, não acompanha
  o mercado). A pergunta a responder não é "você usaria?" — é **"o que você usa hoje, e o que te
  fez parar de usar?"**.
- Landing pública com a promessa nova, e medição de quem se cadastra por ela.
- Ligar a leitura de funil e retenção sobre os eventos que já existem.

### Fase 2 — a ponte, sem automação (4–6 semanas)

Camada de caixa **manual**, deliberadamente simples: salário, regime, contas fixas, gastos
eventuais, sobra projetada — e a sobra alimentando o aporte que o produto já sabe planejar. Mais
Tesouro Direto, porque é onde esse público começa.

Vale-tudo aqui é medir **uma** coisa: a pessoa volta no mês seguinte? Se a ponte não segura sem
automação, ela não vai segurar com automação — só vai custar mais.

### Fase 3 — automação, quando a ponte provar valor

Open Finance, com a decisão de preço já tomada (§4.3). É aqui que o custo recorrente entra, e é aqui
que ele passa a ser justificável.

### Fase 4 — perfil, educação e o alerta reenquadrado

Perfil curto, educação contextual, e os alertas na forma do §4.4.

### Fase 5 — cobrança

Trilha B do PRE_PRODUCAO, com a régua de `plans.py` refeita para a proposta nova.

---

## 11. Perguntas que precisam de resposta humana

Nenhuma destas se resolve lendo código:

1. **Quem é a pessoa, exatamente?** Faixa de renda, idade, se já investe. "Pessoa comum" é público
   grande demais para desenhar uma tela.
2. **O produto aceita dívida?** Quem tem rotativo de cartão não deve investir — é a orientação
   correta e é o oposto do que o produto vende. Se o app vai dizer isso, precisa saber dizer bem; se
   não vai, precisa ao menos não sugerir aporte para quem está no vermelho.
3. **Qual o preço-alvo, e ele cobre o custo de conexão do Open Finance?** Isso decide se a conexão é
   o gancho do plano pago ou uma feature que dá prejuízo.
4. **O produto calcula renda líquida** (INSS, IRRF, DAS, pró-labore) **ou só registra o valor que
   caiu na conta?** Calcular diferencia e cria obrigação de estar certo — e imposto errado, como
   registra A4 do PRE_PRODUCAO, gera dano.
5. **A educação é própria ou curada?** Conteúdo próprio é custo recorrente de redação; curado é mais
   barato e menos diferenciado.
6. **Quem é o dono do parecer sobre a fronteira CVM** (A3)? A direção nova aumenta a exposição, não
   diminui.
7. **O investidor atual continua atendido?** Se sim, há duas ofertas de valor num app só — o que é
   possível, mas precisa estar escrito antes de virar duas telas iniciais brigando.

---

## 12. Veredito

- **O diagnóstico está certo pelo motivo errado.** O problema não é feature faltando; é frequência,
  diferenciação e atrito de entrada — e a proposta ataca os três.
- **A direção é boa, e a moldura de "pivô" é ruim.** O motor de análise é o que ninguém copia
  rápido; ele deve virar o cérebro por trás da ponte, não ser aposentado.
- **A ponte — sobra do mês vira aporte, aporte vira meta — é a tese.** Ninguém no mercado brasileiro
  faz os dois lados bem, e metade dela já está construída aqui.
- **O ponto mais frágil da proposta é o lançamento manual de gasto**, que morre em semanas; e a
  consequência é que o Open Finance vira requisito de negócio, com custo por usuário, o que **obriga
  a decidir preço antes de construir**.
- **O alerta de "venda X e compre Y" deve ser reenquadrado**, não construído como descrito: mesma
  informação, dita como mudança de estado contra a regra da própria pessoa, com o imposto visível.
- **A sequência importa mais que a decisão.** Validar antes de automatizar custa duas semanas;
  descobrir depois custa um trimestre.

**Recomendação:** adotar a direção como **extensão**, executar as fases 0 e 1 antes de qualquer
decisão irreversível, e não começar a trilha B do PRE_PRODUCAO até a fase 1 responder.

---

## O que **não** fazer

- **Não** apagar `analysis/` e `optimizer/` para "focar no orçamento" — é a única parte difícil de
  copiar.
- **Não** construir OCR de nota fiscal, cupom ou comprovante. Custa caro, encanta em demo e não
  segura ninguém.
- **Não** fazer do lançamento manual de gasto o caminho principal (§4.2).
- **Não** raspar site de corretora com a senha da pessoa (§4.3).
- **Não** ligar o nível 3 de afirmação para viabilizar o alerta de troca (§4.4).
- **Não** transformar o app em painel de BI do orçamento: a hierarquia é fio e chão, e a grade de
  KPI é o cheiro de painel — está no contrato de trabalho e vale igual para a tela nova.
- **Não** construir a camada de caixa e o Open Finance ao mesmo tempo — o segundo só se justifica
  depois que o primeiro provar retenção.
