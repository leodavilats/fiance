# Produto

**Fonte de verdade** para visão, público, limites e modelo de negócio. Não há código que responda
estas perguntas.
Última revisão: 2026-09-26

---

## O problema

Uma pessoa com salário e sem tempo quer investir. Ela abre o Status Invest, encontra quarenta
indicadores, não sabe quais importam, procura a recomendação de alguém e monta a carteira por
confiança. Em paralelo, controla os gastos numa planilha que ninguém atualiza no dia 20.

São três ferramentas e nenhuma se fala: a planilha não sabe quanto sobra para investir, o site de
análise não sabe o que ela já tem, e a recomendação de terceiro não sabe nada sobre ela.

**O fiance existe para responder uma pergunta só: *que ativo eu compro agora?*** — com o motivo
junto, considerando o que sobra do mês, o que já está na carteira e o perfil declarado.

## Para quem

Assalariado com pouco tempo, que investe ou quer começar. Duas pontas da mesma pessoa:

- quem **nunca investiu** e não sabe por onde começar;
- quem **já tem carteira** de até algumas centenas de milhares de reais e não consegue acompanhar.

Não é para o investidor profissional, nem para quem gere dinheiro de terceiros, nem para carteiras
acima de meio milhão — não porque o sistema quebre, mas porque essas pessoas têm ferramenta e tempo,
que é exatamente o que o produto substitui.

**Premissa fechada hoje:** pessoa física brasileira, investindo na B3, declarando imposto no Brasil.
Sair disso é ideia sem data — ver [09-FUTURO](09-FUTURO.md).

## O que o produto entrega

Três coisas encadeadas, nesta ordem, que é também a ordem da navegação:

1. **Quanto sobra** — controle de gastos vivo, no celular, que termina num número utilizável
2. **Para onde vai** — a cascata: dívida cara antes de reserva, reserva antes de aporte
3. **O que comprar** — análise com preço justo, score por perfil, e o que derrubaria o veredito

O diferencial não é nenhum dos três isolados: é o encadeamento. Status Invest responde o terceiro e
ignora os dois primeiros; um app de finanças pessoais responde o primeiro e para ali.

## A postura editorial é o diferencial

Não é cuidado jurídico. É o produto:

- **Nada de número inventado.** Fonte externa fora do ar não vira estimativa silenciosa.
- **Faixa, nunca número único** em projeção. Cinco anos de premissas não merecem precisão de
  centavo.
- **Todo veredito vem com o que o derrubaria.** Um preço conferível, não uma opinião.
- **A idade do dado é informação de primeira linha.** Preço de anteontem muda a decisão.
- **Não se promete futuro.**

Isso está codificado, não é aspiração: `test/lint_ui_test.dart` reprova tela que exiba julgamento
sem explicabilidade ou projeção sem faixa.

## A tensão central

O produto é para quem não tem tempo, e pede lançamento de gastos, cadastro de posição, declaração de
meta e conferência de provento. **Quanto mais fundo ele vai, mais atenção cobra de quem não a tem.**

Não há solução elegante para isso — há decisões caso a caso, e cada uma deve ser tomada sabendo que
o custo é a atenção do usuário. Toda funcionalidade nova responde: *isto cobra mais tempo do que
devolve?*

## O que o produto não é

| Não é | Por quê |
|---|---|
| Home broker | Não executa ordem, não conecta com corretora |
| Ferramenta para profissional gerir carteira de terceiros | Uma conta, uma pessoa |
| Rede social de investidores | — |
| Ferramenta de trade, análise técnica, candles | Tendência e RSI aparecem só como contexto de preço: não decidem a etiqueta nem pontuam no score ([ADR-017](decisoes/ADR-017-o-score-nao-le-o-tecnico.md)) |
| Curso ou conteúdo educacional | Explica o que calcula, não ensina a investir |

**Sobre recomendação personalizada:** o produto quer indicar ativos com base no perfil, nas metas e
na carteira da pessoa, com o motivo junto. Essa é a direção declarada e decidida — com as
consequências registradas em [ADR-006](decisoes/ADR-006-recomendacao-personalizada.md).

## Modelo de negócio

| Item | Decisão |
|---|---|
| Modelo | Assinatura, sem versão gratuita permanente |
| Preço pretendido | Até R$ 9,90/mês |
| Gratuidade | **Nada de graça** — tudo atrás do trial |
| Trial | 14 dias, a partir da **primeira posição salva** |
| Cobrança | Compra dentro do aplicativo, via RevenueCat |
| Objetivo inicial | Cobrir o custo de operação |

Decisões em [ADR-008](decisoes/ADR-008-monetizacao-por-loja.md) e
[ADR-009](decisoes/ADR-009-trial-e-gratuidade.md).

**A hipótese de valor:** a pessoa paga quando percebe que o aplicativo indica ativos para *ela* —
comparando com o que ela já tem — e diz por quê.

**O risco que essa escolha carrega:** sem nada gratuito, sem landing page (removida em 2026-09-11) e
sem presença em loja, não existe hoje superfície de descoberta do produto. O risco declarado é de
aquisição, e a decisão de não ter gratuidade aponta na direção oposta a ele. Registrado, consciente,
revisável.

## Estado

Uma pessoa usa o sistema: o autor, com dados reais, diariamente. Nada publicado em loja, nenhuma
conta de desenvolvedor aberta, nenhuma receita. Ver [08-ESTADO](08-ESTADO.md).
