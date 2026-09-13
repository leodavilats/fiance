# Problemas conhecidos

**Fonte de verdade** do que está aberto. Só pendências: nada de histórico, nada de item resolvido.
Última verificação contra o código: **2026-09-13**
Itens 1 a 33 herdados da verificação de 2026-09-11; itens A a E da auditoria do motor de cálculo de
2026-09-13.

> **Ao fechar um item, apague-o daqui.** Item resolvido que fica é pior que item ausente, porque
> manda alguém refazer o que já existe. Este arquivo tem histórico de apodrecer: numa revisão de
> agosto, oito de 24 itens já estavam feitos.

---

## A · Motor de cálculo — auditoria de 2026-09-13

### A1 · `MIN_DATA_COMPLETENESS` é declarado e nunca aplicado — **bug**

`analysis/scoring.py:98` define o piso de 0,5 e **nada o usa**. A completude é calculada, viaja até o
cliente em `data_completeness`, e nenhum corte acontece.

Um ativo com uma única dimensão disponível recebe score normalizado sobre o peso que sobrou e chega à
tela com a mesma aparência de confiabilidade de um ativo completo. Combinado com o item A2, isso é o
caso normal, não a exceção.

**Fechar é decidir o comportamento:** abster-se abaixo do piso, ou exibir o score com a completude
visível na interface. As duas são defensáveis; o silêncio atual não é.

### A2 · O "DCF" não é um DCF

`analysis/fair_price.py:184` desconta **lucro por ação**, não fluxo de caixa livre, e usa crescimento
de **receita** como proxy do crescimento de lucro. A taxa de desconto é fixa em 13% para qualquer
empresa — sem beta, sem WACC, sem prêmio por setor ou porte — e o P/L terminal é fixo em 15.

É uma heurística razoável com nome errado. O nome importa porque a interface promete "consenso de N
métodos", e o usuário supõe que um deles seja fluxo de caixa descontado.

**Fechar é escolher:** renomear para o que é (lucros descontados), ou implementar um DCF de verdade.

### A3 · O múltiplo de Graham não é ajustado ao juro brasileiro

`√(22,5 × LPA × VPA)` usa a constante de 1949, do mercado americano. Em juro alto, ela é generosa —
e o Brasil passou a maior parte da década recente em juro alto. O método participa do consenso de
toda ação e de todo BDR.

### A4 · O DCF é descartado sempre que há Bazin, e isso não está documentado na interface

`fair_price.py:307`: `if bazin is not None: dcf = None`. Na prática, o DCF só participa do consenso de
uma ação que **não paga dividendos**. É uma regra deliberada e invisível — a tela diz "consenso de 2
métodos" sem dizer que um terceiro foi descartado por regra.

### A5 · O perfil de risco não afeta FIIs nem ETFs

`scoring.py:95-96`: `_FII_WEIGHTS` e `_ETF_WEIGHTS` são fixos e `profile` não entra no ramo. Quem tem
carteira de FIIs muda de conservador para arrojado e **nada acontece**.

Junto com o item 29, isto compromete a personalização que é a hipótese de receita do produto.

---

## B · Dado e fonte

### 3 · A cobertura dos fundamentos por classe de ativo não foi medida

`roe`, `profit_margin`, `revenue_growth` e `debt_to_equity` passaram a chegar. O que foi conferido
contra a API real é **ação não-financeira**: WEGE3, VALE3, BBAS3. Não foi medido quanto disso existe
para BDR, FII e small cap de liquidez fina.

Dois limites conhecidos por construção: **banco não preenche as chaves de dívida financeira**, então
`debt_to_equity` fica nulo para instituição financeira — de propósito, porque somar ausência daria 0%
e o produto diria "dívida muito baixa, empresa sólida" para todo banco. E **fundamento anual é velho
por natureza**.

A medida é uma chamada: `GET /api/v1/data-quality` reporta cobertura campo a campo depois da primeira
varredura completa.

### 29 · Três das seis dimensões do score nunca têm dado, e o perfil de risco fica quase inerte

Consequência direta do item 3, e **mais grave que o item A5**. Com os pesos reais, sobra 0,60 de peso
no perfil conservador, 0,55 no moderado e 0,35 no arrojado. O que resta em todos é margem de
segurança, dividendos e técnico, renormalizados. **Crescimento vale 40% do peso arrojado e nunca
existe.**

O produto descreve "qualidade e endividamento ponderados pelo seu perfil" — que é o produto que
existirá quando houver segunda fonte de fundamentos.

### 28 · O ETF é estruturalmente mal avaliado, e o remendo tem consequência

Para `asset_type == "etf"` o único candidato a consenso é Bazin (`dividendo ÷ 0,04`); um ETF de
índice distribui na casa de 1% ao ano, então o preço justo sai em ~25% do preço e a margem de
segurança em −300%, sempre.

`opportunity_service` sobrescreve o veredito por RSI e tendência quando ele sai `UNKNOWN`, o que
produz duas coisas ruins: **o mesmo ETF recebe veredito diferente em `/descobrir` e em
`/ativo/:ticker`**, e o veredito por momentum sai **sem falsificador**, porque sem consenso não há
preço-limite.

Decidir o método — comparação com o índice, prêmio sobre valor patrimonial, ou abstenção explícita —
vem antes de mexer no falsificador.

### 1 · O caminho do Redis nunca rodou contra um servidor real fora do CI

Coberto: o contrato e a tradução do adaptador. Não coberto: rede instável, reconexão, failover.

### 4 · Universo hardcoded como fallback

`core/config.py::default_universe` mantém ~400 tickers, apesar de existir universo dinâmico via
BRAPI. Fallback defensivo intencional, mas extenso.

### 33 · A janela de pregão não conhece feriado da B3

`core/pregao.py` bloqueia a varredura em dia de feriado como se fosse pregão normal.

---

## C · Produto incompleto

### 30 · O passo de reserva da cascata é inalcançável

`cascata.montar` recebe `reserva_meses_alvo` e `reserva_atual`, a matemática está escrita e testada,
e **nenhuma rota passa os dois** — porque não há onde declarar quantos meses de gasto fixo a pessoa
quer guardar. Não há campo em `preferences`, em `goals`, em lugar nenhum.

A regra documentada ("a reserva vem depois da dívida cara, e só existe com alvo declarado") descreve
um passo que a Sobra **nunca mostra**.

Fechar é decisão de produto antes de código: quantos meses, contra qual base, e o que acontece com
quem não declara. Inventar "seis meses" é o número de mercado solto que a régua de dívida proíbe.

### 31 · A alocação-alvo cai no padrão e a tela não distingue

`GET /dashboard` monta as barras com `goal_service.get_goals()`, que devolve 30/35/15/15/5 quando nada
foi declarado. Quem nunca declarou meta vê barras "abaixo da meta" de uma meta que não escolheu, e o
alerta de rebalanceamento dispara sobre ela.

As metas **por setor** já distinguem (o `declared` da resposta); as de categoria não, e mudar isso
mexe no alerta do dashboard, no `whats_new` e no Quick Invest de uma vez.

### 15 · Sugestões seguidas dependem de lançamento manual

### 20 · A apuração de IR não cobre day trade nem IOF de renda fixa

### 27 · A cobrança é backend sem cliente

Existe a cerca, a régua de plano, o preço travado e o webhook — e nenhuma tela. Agravado pela decisão
de refazer tudo para RevenueCat ([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)): o que existe
hoje **não** será aproveitado.

### 16 · `detail_level` (Essencial / Completo / Avançado) não existe no backend

---

## D · Paridade perdida — o mais urgente

Nove funcionalidades que o backend serve e o aplicativo não alcança, todas por remoção do front web
em 2026-09-11. Inventário completo e com critério de morte em
[PARIDADE-WEB-APP](temporario/PARIDADE-WEB-APP.md).

O item mais grave: **o livro-razão, fonte da carteira e do imposto, não tem nenhuma tela**.

---

## E · Interface

### 7 · Três famílias de controle ainda são Material puro, com estilo só no tema

### 8 · A base do preço justo não chega às telas de posição da carteira

Em `/ativo` a cifra vem com "consenso de N métodos"; nas telas de posição, não.

### 9 · Falta a regra do alvo de toque de 44dp no Dart

### 10 · `/voce` são cinco entradas, e o desenho pede quatro eixos

### 11 · Dois comportamentos essenciais não têm componente

Faltam `Evidence` (o nível 2 da explicabilidade) e o par que o acompanha.

### 12 · A régua de afirmação anula `allocated_cash` e deixa a subtração de pé

### 17 · A régua não cobre o score em linha densa, e ali ele sai só como selo

### 26 · A aparência nos dois temas nunca foi conferida num aparelho

O contraste é verificado por máquina; a aparência não.

### 25 · A acessibilidade foi coberta por verificação, não por auditoria — e a verificação encolheu

---

## F · Teste, automação e operação

### 13 · Não existe mais teste de ponta a ponta

O que havia rodava no navegador e saiu com o front web.

### 14 · As regras de interface que só rodavam no front não foram portadas

Três não têm equivalente no Dart: **gráfico sem tabela equivalente**, **destino de navegação
inexistente** *(esta foi portada — regra 13 do lint)* e **controle montado à mão**.

### 5 · A API de produção sobe sem esperar o CI

O serviço tem gatilho em `main` e `checkSuites: false`. Um commit vermelho vai ao ar — e o
pre-deploy é `python -m app.release`, então **uma migração ruim é aplicada antes de qualquer teste
terminar**. É o item de maior risco operacional da lista.

### 18 · O contrato das rotas guarda campo que sai, não campo que entra

### 45 rotas sem contrato de resposta

`SEM_MODELO_HOJE = 45` em `tests/test_contrato_das_rotas.py`. Metade das rotas devolve `dict` solto,
sem `response_model` — o FastAPI não pode conferir, e o contrato não as cobre. A catraca impede
crescer; não faz o número cair.

### 24 · A paginação das listas com agregado limita o payload, não a consulta

### 23 · Token de push é reatribuído a quem o registrar

### Não existe rotina de backup própria nem restauração testada

O backup é o do provedor. Nunca foi exercitado.

### 21 · O mobile nunca teve um release de verdade

Não existe chave de assinatura, e nenhum evento de telemetria foi visto em produção.

---

## G · Código morto a remover

| Item | Ação |
|---|---|
| `backend/app/optimizer/` — diretório vazio, só `__init__.py` | Apagar · [ADR-010](decisoes/ADR-010-remover-otimizador.md) |
| `OptimizationStrategy` em `models/enums.py` — nada importa | Apagar |
| `MIN_DATA_COMPLETENESS` — declarado, nunca usado | Usar ou apagar (ver A1) |
| `api/demo.py` — sem cliente desde 2026-09-11 | Decidir |

---

## H · Pré-requisitos de loja não atendidos

### 32 · O texto jurídico não publica canal de atendimento, e a loja exige um

A Política diz que o canal "será publicado antes de o aplicativo ser distribuído", e **não existe
endereço nenhum no repositório**. Exportar e apagar a conta funcionam sem atendimento, o que cobre os
dois direitos mais pedidos; confirmação, correção e oposição não têm porta.

Fechar é decidir o endereço e escrevê-lo em `services/legal_pages.py` — uma linha, e **bloqueia
submissão**.

### O aplicativo iOS nunca foi executado

Nem em aparelho, nem em simulador. **Zero evidência** de que o produto funcione em iOS — e o roadmap
prevê publicar nas duas lojas.

O risco não é teórico: layout, fontes, rolagem, teclado, área segura, permissão de notificação e o
fluxo de login com Google se comportam de forma diferente no iOS, e nada disso aparece em
`flutter analyze` ou `flutter test`, que rodam sobre Dart. É a mesma classe de problema do build
Android — suíte verde, plataforma quebrada — só que sem nenhuma execução para contrariar.

Exige um Mac, que também não existe.

### Sign in with Apple não existe

A App Store exige quando há login social de terceiros. O sistema só tem Google. É um segundo provedor
de identidade, não uma configuração.

### Exclusão de conta não tem tela

Existe em `api/account.py`. As lojas exigem o caminho **dentro do aplicativo**.

### Não há contas de desenvolvedor, nem Mac

Ver [07-OPERACAO](07-OPERACAO.md).

---

## Armadilhas conhecidas

Não são bugs, mas mordem. Lista completa em [06-DESENVOLVIMENTO](06-DESENVOLVIMENTO.md) e no
`CLAUDE.md`.
