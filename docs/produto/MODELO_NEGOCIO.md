# Modelo de negócio: manual é grátis, automático é pago

> Parte de [VISAO.md](VISAO.md). Decisão travada em 2026-09-04: **a fronteira de plano
> não é feature, é fonte do dado.** Tudo que a pessoa digita é grátis; tudo que o produto busca
> sozinho no banco é pago.

---

## A fronteira, por completo

| | **Free** — manual | **Premium** — automático |
|---|---|---|
| Gastos e receitas | a pessoa lança salário, contas fixas e gastos eventuais à mão | conectado ao banco via Open Finance: entra sozinho, categorizado |
| Dívida | a pessoa informa saldo devedor e taxa de cada dívida | saldo, fatura e taxa de rotativo vêm da conexão, sempre atualizados |
| Carteira de investimento | lançamento manual de posição, ou importação do extrato de Movimentação da B3 (XLSX) | conectado à corretora via Open Finance: posição **e** histórico de operações entram sozinhos |
| Sobra do mês, aporte sugerido, meta, preço justo, score, IR | **iguais nos dois planos** | **iguais nos dois planos** |

O que está de fora da tabela é deliberado: **nenhuma capacidade de análise fica atrás do plano.**
Score, preço justo, falsificadores, projeção em faixa, orientação sobre dívida — tudo isso roda
igual para quem digita e para quem conecta. O que se vende é **não precisar digitar**, não a
análise em si. Isso é uma continuidade direta do invariante já registrado no CLAUDE.md: *"nada é
cercado antes da primeira posição salva"* e *"a cerca de plano mora só em `entitlement/`, aplicar é
`Depends(requires(Feature.X))`"* — a peça nova é só um `Feature` a mais nesse arquivo, não uma
exceção à regra.

**Importação do extrato B3 (XLSX) fica no Free.** Não é Open Finance, é leitura de um arquivo que a
própria pessoa baixa — custo zero, e é o item de maior valor por esforço do
[ROADMAP.md](ROADMAP.md) — entra na Fase 3, no parser de importação.
Cercar isso atrás de plano pago seria cobrar pelo que já é de graça em outro lugar.

---

## Por que a fronteira é a fonte do dado, e não uma feature

Três motivos, nesta ordem de importância:

1. **É a única fronteira que se explica numa frase.** "Grátis, você digita; premium, a gente busca
   pra você" é compreensível sem gráfico. Cercar peças de análise cria a pergunta "por que isso é
   pago e aquilo não", que corrói a confiança na régua de score — o mesmo motivo que já levou o
   produto a nunca cercar cálculo.
2. **O custo real do produto está na automação, não na análise.** Rodar `analysis/` e `optimizer/`
   sobre um dado já digitado custa CPU; manter uma conexão Open Finance ativa custa dinheiro de
   verdade, todo mês, por pessoa. Cobrar exatamente onde o custo existe é a única fronteira que não
   subsidia usuário grátis com receita que ainda não existe.
3. **Preserva a promessa de explicabilidade.** Quem só digita continua vendo o veredito completo,
   com o que o derrubaria — a diferença nunca é "você paga, então agora eu te explico".

---

## O problema que isto não resolve sozinho: o custo fixo da Pluggy

Como levantado na conversa: o piso do plano de dados da Pluggy gira em torno de **R$ 2.500/mês**,
mais excedente por requisição acima disso — números que **não são públicos em detalhe** e que
mudam por negociação de volume (confirmar direto com o time comercial deles antes de qualquer
compromisso). Isso muda a pergunta de "quanto cobrar" para uma conta de unidade:

```
assinantes_premium × (preço_mensal − custo_de_cartão/banco) ≥ piso_da_pluggy + excedente
```

Com poucos assinantes, esse piso não se paga sozinho. Duas implicações práticas, já refletidas no
[ROADMAP.md](ROADMAP.md):

- **A fase manual (Free e Premium-sem-automação) precisa vir primeiro e provar retenção antes de a
  conexão Open Finance ser contratada.** Contratar o piso fixo sem ter para quem vender automação é
  pagar por uma capacidade vazia.
- **O preço da assinatura ainda não está definido**, e não deveria ser, antes de:
  1. saber quantos usuários o produto consegue reter na fase manual (fase de validação);
  2. ter uma cotação real da Pluggy (ou concorrente — Belvo, Klavi, Quanto) para o volume esperado
     desses usuários.

Esta seção fica **em aberto de propósito**: o número certo só existe depois desses dois dados, e
travar um preço antes disso seria decisão sem base.

---

## O que precisa existir em `entitlement/` quando a hora chegar

Sem implementar agora — só para não redescobrir a estrutura depois:

- Um novo `Feature` (ex.: `Feature.OPEN_FINANCE_SYNC`), com `min_plan = Plan.PREMIUM`, entrando em
  `RULES` de `entitlement/plans.py` do mesmo jeito que as regras de hoje.
- **Nenhuma condicional de plano fora de `entitlement/`** continua valendo — `cashflow/` e a
  expansão de `ledger/` para operação automática não podem saber quem paga, do mesmo jeito que
  `analysis/`, `optimizer/`, `collectors/` e `ledger/` não sabem hoje. O teste de arquitetura que já
  existe para isso cobre o módulo novo pelo mesmo mecanismo, sem trabalho extra.
- O gate de "conectar banco/corretora" na interface é um `<!-- ... -->` de UI que chama o mesmo
  padrão de 402 com corpo de gate que `gate.component.ts` já sabe renderizar — não é um componente
  novo de zero.

---

## O que fica para depois

- Preço exato da assinatura — depende da fase de validação e da cotação da Pluggy.
- Se existe um terceiro nível de plano (ex.: só conexão bancária, sem conexão de corretora, por um
  preço intermediário) — não decidido; a tabela acima assume dois planos.
- Nota fiscal, provedor de pagamento e tela de cobrança continuam na trilha B do
  [PRE_PRODUCAO.md](PRE_PRODUCAO.md) e não mudam com esta decisão.
