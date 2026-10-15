# Futuro

**Fonte de verdade** do roadmap. Nada aqui existe — o que existe está em
[08-ESTADO](08-ESTADO.md).
Última revisão: 2026-10-12

As seções são rígidas e não se misturam. Um item só muda de seção por decisão explícita.

**A fase é pessoal** ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)): o que só serve à
publicação está no bloco *Fase pública — sem data*.

---

## Em desenvolvimento

### Taxa de desconto do preço justo — decisão aberta

A medida de 2026-10-12 mostrou que o veredito de preço justo não ordenou o retorno de 2011 a 2017, e
que com a Selic média de 10 anos + 5 pontos o modelo punha 9 em 10 ações acima da faixa
([pesquisas/calibracao](pesquisas/calibracao.md)). **Falta decidir em ADR** se essa taxa continua sendo a
do modelo. Detalhe em [10-PROBLEMAS](10-PROBLEMAS.md), A12.

---

### O app como primeiro cliente da API de dados

A API de dados existe ([ADR-024](decisoes/ADR-024-api-de-dados.md)); o backend do app ainda lê o
banco direto (`collectors/mercado.py`). O passo seguinte é o app consumir a API com uma conta do
plano `interno` — prova o serviço com uso real antes de terceiros. Cobrar de terceiros espera a
resposta da B3 sobre a licença e a leitura da ODbL; cadastro aberto espera verificação de e-mail.

---

## Planejado

Ordem definida em 2026-09-13 e revista em 2026-10-12. Do 1 ao 6, **recuperação e amadurecimento do
que já existia**; o 9 e o 10, a plataforma de dados. Aberto hoje, só o 4. O 7 e o 8 foram para
*Fase pública — sem data*.

### ~~1 · Importação de extrato, reconciliação e reconstrução no aplicativo~~ — entregue em 2026-09-26

`/patrimonio/razao/importar` (prévia + commit, duplicidade para decisão) e
`/patrimonio/razao/conferir` (diferenças, levar ao razão, refazer). Com eles, a paridade com a web
fechou — registro em [historico/PARIDADE-WEB-APP-2026-09](historico/PARIDADE-WEB-APP-2026-09.md).

### ~~2 · Tela de proventos~~ — entregue em 2026-09-13

`/patrimonio/proventos` registra, lista e apaga o recebido (`/dividends/received`) e traz as
sugestões do calendário uma a uma, nada pré-selecionado.

### ~~3 · Oportunidades personalizadas~~ — entregue em 2026-09-26

A frase-alvo, declarada pelo autor:

> *"PETR4 está 20% abaixo do preço justo e cabe na sua meta de renda, e você tem ITSA4 que está 20%
> acima — avalie se vale fazer o ajuste."*

**Entregue:** `/sobra/desvio` diz a frase, montada no servidor (`adjustment_sentence`): a margem
do alvo e a da posição contra o preço justo, e se o alvo cabe na meta de renda declarada. Junto, o
alvo com a faixa de preço justo e a régua de score, as três razões, e o perfil de risco que ordenou
a lista.

A força da frase continua limitada pela confiança no número (item 4): ela descreve posição, em
modo analítico, e nunca vira ordem.

Esta é a hipótese de valor do produto; a de receita é da fase pública
([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)). Ver
[ADR-006](decisoes/ADR-006-recomendacao-personalizada.md).

### 4 · Confiança no preço justo

A revisão de 2026-09-23 refez o motor ([ADR-014](decisoes/ADR-014-um-modelo-por-classe.md)): um
modelo por classe, taxa ligada à Selic de longo prazo, faixa das premissas, e nenhum método que vote
de um lado só. O preço-teto da meta de renda passou a existir, e é a segunda metade da frase-alvo.

Em 2026-09-25 a faixa passou a cobrir os dois cenários de crescimento
([ADR-015](decisoes/ADR-015-a-faixa-cobre-os-dois-cenarios.md)) e o FII de papel passou a exigir
yield nominal ([ADR-019](decisoes/ADR-019-fii-de-papel-exige-yield-nominal.md)).

**A calibração foi medida em 2026-10-12 e parou por protocolo:** o veredito não ordenou o retorno de
2011 a 2017 ([pesquisas/calibracao](pesquisas/calibracao.md)). O aberto é a ADR da taxa de desconto
([10-PROBLEMAS](10-PROBLEMAS.md), A12), na seção *Em desenvolvimento*. O BDR continua sem juro em dólar
(*Considerado*).

O item 3 foi entregue com a força limitada pelo resultado da A12: a frase descreve posição e diz que
o preço justo não antecipa retorno.

### ~~5 · Simplificar a linguagem da análise de ativo~~ — entregue em 2026-09-26

A folha do ativo e as frases que o backend manda para ela passaram a se ler sem glossário: sigla só
com o nome por extenso ao lado, método chamado pelo que mede, "segunda conta, com outro dado" no
lugar de "insumo", número em português também na frase do servidor, margem em reais e o tipo do
ativo por extenso no cabeçalho. A evidência aberta passou a ser leitura, e as premissas detalhadas
foram para depois; todo termo técnico que ficou na tela abre verbete ao toque. Nenhum cálculo, campo
ou código mudou. As regras estão em [05-INTERFACE](05-INTERFACE.md#a-análise-se-lê-sem-glossário), e
dois testes as cobram, um em cada ponta.

### ~~6 · Onboarding no aplicativo~~ — entregue em 2026-09-26

`/voce/comecar`, com o passo derivado do servidor e nada travando.

### ~~9 · Coleta própria de dados de mercado — `data-job/`~~ — entregue em 2026-10-12

Decidido em 2026-10-09. Um serviço baixa B3 (COTAHIST), CVM (DFP, ITR, FCA) e BCB
SGS, guarda o bruto e grava no schema `mercado`; o aplicativo e a pesquisa de carteira de uso próprio
só leem. Revisa o invariante "só BRAPI e BCB SGS" —
[ADR-022](decisoes/ADR-022-dados-de-mercado-coletados-em-lote.md), aceita em 2026-10-12; a BRAPI
saiu do código. Plano, fases e
critério de pronto em [11-DADOS-DE-MERCADO](11-DADOS-DE-MERCADO.md).

### ~~10 · A plataforma: coleta completa, tendência como ranking, painel, app sem BRAPI~~ — entregue em 2026-10-12

Decidido em 2026-10-12. Quatro etapas: o data-job com tudo o que negocia na bolsa (ações, FIIs, ETFs,
BDRs, dólar, Tesouro); a tendência como ranking dos ativos, com acerto medido em protocolo novo; o
painel organizando o caminho e os dados; e o app fiance lendo só o dado da base própria. A tendência não
vai para o app. Plano em [plano da plataforma](historico/PLATAFORMA-2026-10.md).

**Resultado do ranking:** as 6 variações do teto foram usadas e nenhuma passou
([pesquisas/ranking](pesquisas/ranking.md)). A tendência ficou como contexto de risco, só no painel.

---

## Fase pública — sem data

Adiada pela [ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md): nada aqui tem prioridade enquanto o
uso é pessoal. Os números seguem os do *Planejado*.

### 7 · Contas de desenvolvedor e publicação

Bloqueadores listados em [07-OPERACAO](07-OPERACAO.md): contas Google Play e Apple, um Mac, o botão de **Sign in
with Apple** (o servidor, `POST /auth/apple`, está pronto), ficha de segurança de dados e um canal de atendimento publicado. A exclusão de conta
dentro do aplicativo saiu da lista em 2026-09-19.

⚠️ **O aplicativo nunca rodou em iOS**, nem em simulador. Publicar nas duas lojas significa descobrir
o comportamento em iOS do zero, e é o item de maior incerteza deste roadmap — pode custar horas ou
semanas, e não há como saber antes de executar.

### 8 · RevenueCat e cobrança real

O `payments/` atual (com `api/billing.py`) tem só `FakeProvider` e será descartado. Ver
[ADR-008](decisoes/ADR-008-monetizacao-por-loja.md).

**Sem data.** Não há prazo de publicação definido.

---

## Considerado

Sem decisão, mas com interesse declarado.

| Item | Observação |
|---|---|
| **Opções e derivativos** | Tensiona o limite "não é ferramenta de trade" de [01-PRODUTO](01-PRODUTO.md) |
| **Controle de gastos completo** (tipo Mobills) | Aumentaria a atenção exigida de um público definido por não ter tempo |
| **Otimizador de carteira** (Sharpe, HRP, mínima volatilidade) | Removido em 2026-09-13 ([ADR-010](decisoes/ADR-010-remover-otimizador.md)). Reconstruir é decisão nova — e é preciso responder se isso serve a quem não tem tempo |
| **Calibração empírica do preço justo** | Prêmio de 5 pontos, 3 pontos de FII, 1,5% de crescimento real, teto de 20%, choque de ±1 ponto e bandas de ±15% e ±30% são convenções. Validá-las exige retorno à frente por faixa de margem, fora da amostra, com fundamentos como estavam na data. **Medida em 2026-10-12: o modelo como está não ordena o retorno**, e por protocolo a calibração não seguiu ([pesquisas/calibracao](pesquisas/calibracao.md)). O que isso muda no app está em [10-PROBLEMAS](10-PROBLEMAS.md), A12 |
| **Preço justo de BDR** | Exige juro em dólar para descontar lucro em dólar ([ADR-014](decisoes/ADR-014-um-modelo-por-classe.md)): descontar pela Selic fazia todo BDR parecer caro, cerca de 0,67× o valor. Nenhuma fonte da base própria entrega juro em dólar |
| **Seleção de carteira por fatores e ranking de tendência** | Medidos com protocolo em 2026-10, sem vantagem a explorar: escolher ações não bateu o CDI depois de custo ([pesquisas/pesquisa](pesquisas/pesquisa.md)), e nenhuma das 6 variações do ranking passou ([pesquisas/ranking](pesquisas/ranking.md)). Não reabrir sem protocolo novo |

---

## Ideia

Sem compromisso nenhum. Listado para não ser esquecido, e para não ser confundido com plano.

| Item | Observação |
|---|---|
| Open Finance | Resolveria a tensão central do produto — a atenção exigida — e é o item de maior esforço e maior regulação |
| Sair do Brasil / outros mercados | A premissa brasileira está em toda parte: IR, fuso, BRT, B3/CVM, BCB |
| API para terceiros | `[EM DISCUSSÃO]` desde o início |

---

## Fora de escopo

Não é "ainda não": é **não**.

- Home broker, execução de ordem
- Ferramenta para profissional gerir carteira de terceiros
- Rede social de investidores
- Criptomoedas
- Ações internacionais diretas, fora de BDR
- Previdência
- Fiagro, Fi-Infra
- Curso ou conteúdo educacional
- Versão web do produto — ver [ADR-003](decisoes/ADR-003-cliente-unico.md). O painel `trend` é web,
  mas é ferramenta do autor, fora do produto ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md))

---

## Riscos

Na ordem da fase pessoal ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)).

**Um autor só.** Uma pessoa escreve, mantém e usa o sistema — ninguém mais olha. Em 2026-09-26, só
backend e mobile somavam cerca de 44 mil linhas de código e 20 mil de teste. Os testes absorvem o
tamanho, mas não há quem mantenha se o autor parar. **E nenhum banco tem backup automático:** perder o
volume do `postgres-app` perde carteiras e contas — risco aceito em 2026-10-12 enquanto o uso é
pessoal ([07-OPERACAO](07-OPERACAO.md#backup-e-recuperação)).

**Preço justo sem poder preditivo.** Medido de 2011 a 2017, o veredito não ordenou o retorno seguinte
([10-PROBLEMAS](10-PROBLEMAS.md), A12). Usá-lo como sinal de compra contraria a medida.

**Dependência de endpoints não documentados.** Desde 2026-10-12 a fonte de mercado é a base própria,
de arquivos públicos. Proventos e eventos vêm de endpoints do site da B3 sem contrato; se mudarem,
a série para de receber eventos novos. O disjuntor protege contra queda, não contra descontinuação.

**Custo.** O Railway roda backend, data-job, trend, `postgres-app` e `postgres-mercado`; a fonte de
mercado custa zero.

**Regulatório.** Registrado em [ADR-006](decisoes/ADR-006-recomendacao-personalizada.md).

### Ao abrir ao público

**Aquisição.** Sem gratuidade, sem landing page e sem presença em loja, não existe superfície pela
qual alguém descubra o produto. A decisão de não ter nada gratuito
([ADR-009](decisoes/ADR-009-trial-e-gratuidade.md)) aponta na direção oposta a esse risco, de forma
consciente e revisável.

**Sustentação do preço.** R$ 9,90 por mês, menos a comissão de loja de 15% a 30%, deixa cerca de
R$ 7 a R$ 8,40 por assinante. Contra isso, o custo acima. O ponto de equilíbrio não foi calculado.
