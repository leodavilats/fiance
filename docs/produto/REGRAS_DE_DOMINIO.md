# Regras de domínio da camada de caixa

> Parte de [VISAO.md](VISAO.md). Este arquivo é o equivalente, para o módulo de caixa
> ainda não construído, do que o [CLAUDE.md § Domínio e cálculo](../../CLAUDE.md#domínio-e-cálculo) é
> para o que já existe: a régua que a implementação segue. Quando o módulo nascer, o que estiver
> aqui migra para o CLAUDE.md como invariante — este arquivo é o rascunho antes de virar contrato.

---

## Dívida

**Decisão: o produto orienta ativamente, não só registra.**

### Por que isto não esbarra na fronteira CVM

O nível 3 de `affirmation.py` é sensível porque "compre X, venda Y" é recomendação individualizada
de **valor mobiliário** — Resolução CVM 19/20. Dívida não é valor mobiliário; "sua dívida custa mais
que qualquer investimento pode render, quite antes de aportar" é aritmética de taxa de juros, do
mesmo jeito que a orientação de reserva de emergência abaixo. Isso não muda a necessidade do parecer
jurídico já registrado no PRE_PRODUCAO (A3) para o que envolve ativo — só confirma que dívida fica
de fora daquele risco específico.

### A regra prática

1. **Classificar a dívida por custo**, não por tipo:
   - **Cara** (rotativo de cartão, cheque especial, a maioria do crédito pessoal sem garantia):
     taxa muito acima de qualquer retorno esperado de investimento de baixo risco. O produto
     prioriza quitação antes de qualquer sugestão de aporte.
   - **Administrável** (financiamento imobiliário, veicular com juros baixos, consignado): taxa
     comparável ou abaixo do que a carteira já rende. O produto não pede para quitar antecipado —
     isso é decisão de fluxo de caixa da pessoa, não uma régua financeira clara.
2. **A comparação é sempre contra o que a própria carteira da pessoa já rende** (ou, sem carteira,
   contra a Selic/CDI que o BCB já entrega) — nunca um número de mercado solto. É a mesma disciplina
   de "veredito vem com o que o derrubaria": aqui, o falsificador da sugestão de quitar é "sua
   dívida rende menos que X, então quitar não é a prioridade".
3. **A orientação nunca é silenciosa nem definitiva.** Aparece como um item no feed de "o que
   mudou", com o cálculo visível — não como um alerta que interrompe o fluxo de investir.

### O dado que isso exige

- **Free (manual):** a pessoa informa saldo devedor e taxa por dívida lançada. Sem isso, a régua
  simplesmente não aparece — o produto não estima taxa de rotativo de cartão sozinho, porque isso
  varia por banco e por dia, e errar aqui é pior que não mostrar nada.
- **Premium (automático):** saldo, fatura e taxa vêm da conexão Open Finance. Isto implica incluir
  o produto de crédito/empréstimo da Pluggy na integração — ele não estava na lista original de
  produtos a contratar (ver conversa sobre a Pluggy) porque, sem orientação de dívida, não havia uso
  para ele. Com esta decisão, ele volta a ser necessário para a versão automática funcionar por
  completo.

---

## Renda líquida

**Decisão: só registrar o valor que a pessoa diz que recebe. Nada de calcular a partir do bruto.**

### O que isso significa na prática

- O campo é "quanto cai na sua conta" — um número, declarado, sem tentar decompor em INSS, IRRF,
  FGTS, DAS ou pró-labore.
- **Nenhum rótulo pode sugerir cálculo que não existe.** Nunca "seu salário líquido calculado por
  nós"; sempre "o valor que você recebe", refletindo exatamente o que foi digitado. É a mesma
  disciplina que já existe em `affirmation.py` para não prometer precisão que o produto não tem.
- Regime de contratação (CLT, PJ, autônomo) continua sendo perguntado — não para calcular o líquido,
  mas porque ele muda **o formato do calendário de renda**: CLT tem 13º e férias como dois eventos
  de sobra maior por ano; PJ/autônomo tem renda mais variável e sem esses dois eventos. Isso é
  estrutura de calendário, não cálculo fiscal.

### Por que isto é a escolha certa para agora, não uma limitação permanente

Calcular o líquido a partir do bruto cria uma obrigação de estar sempre certo com tabelas de INSS e
IRRF que mudam por lei — exatamente o tipo de responsabilidade que hoje já dói em A4 do
PRE_PRODUCAO (IR de investimento calculado errado). Não empilhar um segundo número fiscal que pode
sair errado, numa fase em que o objetivo é validar se a ponte entre caixa e investimento retém
gente, é a decisão que evita repetir o mesmo erro numa frente nova. Se a validação confirmar a
tese, calcular o líquido a partir do regime pode voltar como melhoria — mas como projeto à parte,
com a mesma disciplina de faixa e fonte que `analysis/scenarios.py` já aplica a projeção.

---

## Perfil e onboarding

**Decisão herdada de [VISAO.md](VISAO.md): público amplo, sem persona única — o perfil se
deriva de dentro do produto, não se presume na entrada.**

### As perguntas de fato, no máximo cinco

| Pergunta | Por quê é perguntada, não derivada |
|---|---|
| Dia do salário | não há como medir sem já ter dado histórico |
| Valor recebido (líquido, ver acima) | idem |
| Regime de contratação | muda o formato do calendário de renda, não é opinião |
| Os 2-3 maiores gastos fixos | atalho para começar a ver algo útil já na primeira sessão |

**O que não se pergunta, porque se mede:**

- "Seus gastos variam muito?" — depois de 4-6 semanas de lançamento (manual ou automático), o
  produto já sabe a variância real. Perguntar isso na entrada coleta uma opinião pior que o dado.
- Perfil de risco para investimento — já existe em `preferences.risk_profile`; não duplicar com uma
  segunda pergunta parecida no onboarding de caixa.

### O limite que continua valendo

O CLAUDE.md registra que **onboarding é derivado, não guardado** — um contador de progresso criaria
segunda verdade. Isso continua verdadeiro para o **progresso** do onboarding (em que passo a pessoa
está). Não se aplica ao **fato declarado**: salário, dia de pagamento e regime são dado, do mesmo
jeito que uma meta de renda passiva já é dado guardado em `goals`. A distinção entre os dois é o que
precisa ficar escrita quando isto virar código, para que ninguém leia "onboarding não guarda nada" e
tente derivar salário de algum outro sinal.

---

## Pendências deste arquivo

Perguntas que ainda não foram feitas e vão precisar de resposta antes da fase 3 do
[ROADMAP.md](ROADMAP.md):

- Educação própria (redigida pelo time) ou curada (links/resumos de terceiro)?
- Quem assume o parecer jurídico sobre a fronteira CVM 19/20, incluindo a leitura do que a
  orientação de dívida não cobre?
