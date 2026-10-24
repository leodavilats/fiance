# Futuro

**Fonte de verdade** do roadmap, em todas as partes. Nada aqui existe — o que existe está em
[03-ESTADO](03-ESTADO.md); o que foi entregue sai daqui.
Última revisão: 2026-10-24

As seções são rígidas e não se misturam. Um item só muda de seção por decisão explícita. Cada item
diz a que parte pertence: **App**, **Base**, **Dados** (a API de dados) ou **Laboratório**.

**A fase é pessoal** ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md)): o que só serve à
abertura ao público está em *Fase pública — sem data*.

---

## Em desenvolvimento

### Dados · A API de dados aberta a terceiros

A API existe, com portal, console, o app como primeiro cliente e planos pagos sem gratuito; a
cobrança pelo Asaas está ligada, e só o autor paga ([dados/](dados/README.md)). O que falta para abrir é
da fase pública — ver abaixo.

---

## Planejado

### App · 4 · Confiança no preço justo

Um modelo por classe, faixa das premissas e confirmação por outro insumo
([ADR-014](decisoes/ADR-014-um-modelo-por-classe.md) a
[ADR-016](decisoes/ADR-016-a-confirmacao-da-acao-alarga-e-nao-derruba.md),
[ADR-019](decisoes/ADR-019-fii-de-papel-exige-yield-nominal.md)); a taxa de ação sai do juro real do
Tesouro ([ADR-028](decisoes/ADR-028-taxa-de-acao-pelo-juro-real-do-tesouro.md)).

**O limite medido:** de 2011 a 2017, o veredito não ordenou o retorno dos 12 meses seguintes, nem com
a taxa nova ([calibracao](pesquisa/estudos/calibracao.md),
[calibracao-com-a-taxa-nova](pesquisa/estudos/calibracao-com-a-taxa-nova.md)). Por protocolo, os
parâmetros não foram calibrados por retorno. O que o item ainda pede é decisão sobre o que fazer
com isso — e qualquer próxima medida, com protocolo novo, em período que nenhum estudo viu.

---

## Fase pública — sem data

Adiada pela [ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md): nada aqui tem prioridade enquanto o
uso é pessoal.

### Transversal · Backup antes do público

Agendar a exportação do `postgres-app`, com destino cifrado e retenção de no máximo 30 dias
([04-PROBLEMAS](04-PROBLEMAS.md#transversal)).

### App · 7 · Contas de desenvolvedor e publicação

Contas Google Play e Apple, um Mac, o botão de **Sign in with Apple** (o servidor está pronto), ficha
de segurança de dados e um canal de atendimento publicado
([app/operacao](app/operacao.md#publicação-nas-lojas)).

⚠️ **O aplicativo nunca rodou em iOS**, nem em simulador. Publicar nas duas lojas significa descobrir
o comportamento em iOS do zero, e é o item de maior incerteza deste roadmap.

### App · 8 · RevenueCat e cobrança real

O `payments/` atual (com `api/billing.py`) tem só `FakeProvider` e será descartado
([ADR-008](decisoes/ADR-008-monetizacao-por-loja.md)).

### Dados · Cobrança e cadastro aberto

**Cobrar de terceiros espera** a resposta da B3 sobre a licença, a leitura da ODbL, CNPJ e termos de
uso; **cadastro aberto espera** verificação de e-mail
([ADR-025](decisoes/ADR-025-cobranca-da-api-de-dados.md)). A cobrança em si já está ligada, para o
autor ([ADR-034](decisoes/ADR-034-cobranca-ligada-e-conferida.md)).

---

## Considerado

Sem decisão, mas com interesse declarado.

| Parte | Item | Observação |
|---|---|---|
| App | **Preço justo de BDR** | Exige juro em dólar para descontar lucro em dólar ([ADR-014](decisoes/ADR-014-um-modelo-por-classe.md)): descontar pela Selic fazia todo BDR parecer caro. Nenhuma fonte da base entrega juro em dólar |
| App | **Opções e derivativos** | Tensiona o limite "não é ferramenta de trade" de [app/produto](app/produto.md#o-que-o-produto-não-é) |
| App | **Controle de gastos completo** (tipo Mobills) | Aumentaria a atenção exigida de um público definido por não ter tempo |
| App | **Otimizador de carteira** (Sharpe, HRP, mínima volatilidade) | Removido em 2026-09-13 ([ADR-010](decisoes/ADR-010-remover-otimizador.md)). Reconstruir é decisão nova |
| Laboratório | **Tela para os seis estudos sem tela** | [04-PROBLEMAS](04-PROBLEMAS.md#laboratório) |
| Laboratório | **Seleção de carteira por fatores e ranking de tendência** | Medidos com protocolo, sem vantagem a explorar ([pesquisa](pesquisa/estudos/pesquisa.md), [ranking](pesquisa/estudos/ranking.md)). Não reabrir sem protocolo novo e período que nenhum estudo viu |

---

## Ideia

Sem compromisso nenhum. Listado para não ser esquecido, e para não ser confundido com plano.

| Parte | Item | Observação |
|---|---|---|
| App | Open Finance | Resolveria a tensão central do app — a atenção exigida — e é o item de maior esforço e maior regulação |
| Base | Cotação ao longo do pregão | Nenhuma fonte gratuita oficial entrega |
| Todas | Sair do Brasil / outros mercados | A premissa brasileira está em toda parte: IR, fuso, B3/CVM, BCB |

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
- Versão web do app — ver [ADR-003](decisoes/ADR-003-cliente-unico.md). O painel do laboratório é web,
  mas é ferramenta do autor, fora dos produtos ([ADR-023](decisoes/ADR-023-fase-pessoal-primeiro.md))

---

## Riscos

Na ordem da fase pessoal.

**Um autor só.** Uma pessoa escreve, mantém e usa as quatro partes — ninguém mais olha. Os testes
absorvem o tamanho, mas não há quem mantenha se o autor parar. **E nenhum banco tem backup
automático** ([07-OPERACAO](07-OPERACAO.md#backup-e-recuperação)).

**Preço justo sem poder preditivo.** Medido de 2011 a 2017, o veredito não ordenou o retorno seguinte,
nem com a taxa da ADR-028. Usá-lo como sinal de compra contraria a medida.

**Dependência de endpoints não documentados.** Proventos e eventos vêm de endpoints do site da B3
sem contrato; se mudarem, a série para de receber eventos novos — nos dois produtos.

**Custo.** O Railway roda backend, data-job, fiance-dados, fiance-trend, `postgres-app` e
`postgres-mercado`; a fonte de mercado custa zero.

**Regulatório.** Do app, registrado em [ADR-006](decisoes/ADR-006-recomendacao-personalizada.md); da
API de dados, a licença do dado da B3 ([ADR-024](decisoes/ADR-024-api-de-dados.md)).

### Ao abrir ao público

**Aquisição do app.** Sem gratuidade, sem landing page e sem presença em loja, não existe superfície
pela qual alguém descubra o produto. A decisão de não ter nada gratuito
([ADR-009](decisoes/ADR-009-trial-e-gratuidade.md)) aponta na direção oposta a esse risco, de forma
consciente e revisável.

**Sustentação do preço do app.** R$ 9,90 por mês, menos a comissão de loja de 15% a 30%, deixa cerca
de R$ 7 a R$ 8,40 por assinante. O ponto de equilíbrio não foi calculado.

**Compromisso da API de dados.** Serviço pago de uma pessoa: disponibilidade e correção do dado viram
obrigação com terceiros.
