# A visão nova: dois mundos, um perfil

> Decisão travada em **2026-09-04**. Este arquivo é o ponto de partida de toda a reconstrução —
> [MODELO_NEGOCIO.md](MODELO_NEGOCIO.md), [REGRAS_DE_DOMINIO.md](REGRAS_DE_DOMINIO.md),
> [../design/INFORMATION-ARCHITECTURE.md](../design/INFORMATION-ARCHITECTURE.md) e
> [ROADMAP.md](ROADMAP.md) partem do que está aqui. Se um deles
> contradisser este arquivo, este arquivo vence até ser atualizado — e a atualização é o primeiro
> passo, não um ajuste silencioso lá na frente.
>
> Contexto herdado de [DIRECAO.md](DIRECAO.md): aquele arquivo é a **análise** que
> levou a estas decisões — o que a proposta original acertava, subestimava, e por quê. Este arquivo
> é a **decisão**. As sete perguntas do §11 de lá estão respondidas abaixo; não precisam de nova
> leitura para começar a trabalhar.

---

## O conceito, numa frase

**Dois mundos que hoje vivem em apps diferentes — o que eu recebo e gasto, e o que sobra e viro
investimento — num produto só, e a ponte entre eles é sempre mediada pelo perfil da pessoa.**

Não é dois produtos colados. É um ciclo: renda → gasto → **sobra** → aporte → patrimônio → e o
patrimônio, ao render ou ao se desviar da meta, volta a informar a próxima decisão sobre a sobra.
Hoje o fiance só sabe fazer a metade de trás desse ciclo — e sabe fazer bem.

---

## O que foi decidido

### Nome e marca — mantidos

O produto continua **fiance**, com a logo atual. O que muda é a experiência por baixo — a IA
(arquitetura de informação), as telas, possivelmente até o gerador de tokens — não a fachada.
Isso significa: qualquer trabalho de marca fica restrito a como as telas usam a identidade
existente, não a criar uma nova. Ver [../design/INFORMATION-ARCHITECTURE.md](../design/INFORMATION-ARCHITECTURE.md)
para o que "repensar tudo" cobre de fato.

### Público — amplo, sem persona única

Não há um público-piloto escolhido. O produto atende de quem nunca investiu a quem já tem carteira
formada — a diferenciação acontece **dentro** do produto, pelo que o onboarding deriva, não por uma
versão diferente para cada segmento. Consequência prática: o onboarding não pode presumir nada sobre
renda, idade ou familiaridade com investimento — só pergunta fato (ver
[REGRAS_DE_DOMINIO.md](REGRAS_DE_DOMINIO.md#perfil-e-onboarding)) e deriva o resto.

### Base atual — não existe

**Ninguém usa o fiance em produção hoje.** Isso muda o cálculo de risco do resto deste documento e
do [PRE_PRODUCAO.md](PRE_PRODUCAO.md) de forma relevante:

- Não há migração de usuário, não há dado real em risco, não há trial rodando para gente de
  verdade — o item B4 do PRE_PRODUCAO ("todo usuário atual tem um trial vencido gravado") descreve
  um risco que **não se aplica** enquanto isso continuar verdadeiro. Confira antes de reabrir esse
  item: se algum dado de teste/demo estiver na base de produção, vale limpar antes, não migrar.
- Não há URL antiga para redirecionar por obrigação, não há tela madura "que as pessoas já usam" a
  respeitar. A reconstrução pode ser tão profunda quanto o produto pedir.
- Isso **não** dispensa nada do que já foi decidido por correção de engenharia — só remove a
  obrigação de compatibilidade retroativa. Ver a ressalva abaixo.

### Preservação de código — livre, com uma ressalva

A decisão foi **remodelar backend e frontend livremente** — nenhuma pasta, módulo ou fronteira
atual é sagrada só por já existir. `analysis/`, `optimizer/`, `ledger/`, a própria estrutura de
telas: tudo pode ser reorganizado se a nova arquitetura de informação pedir.

**A ressalva que precisa sobreviver à liberdade:** "remodelar livremente" é sobre **forma e
fronteira de módulo**, não sobre **correção**. `Decimal` para dinheiro fiscal, fuso BRT para mês
fiscal, uma porta única de escrita no razão, veredito com o que o derrubaria — essas não são
decisões de arquitetura de produto que a nova direção reabre; são o motivo de o IR estar errado
hoje ser bug (A4 do PRE_PRODUCAO) e não ser aceitável, e o motivo de o dinheiro nunca ter saído
errado de `ledger_service`. Uma reconstrução que jogasse isso fora reintroduziria, do zero, os
mesmos bugs que motivaram essas regras da primeira vez. Reorganizar o **onde** é livre; o **como**
de dinheiro e fisco continua sendo o que está em
[CLAUDE.md § Domínio e cálculo](../../CLAUDE.md#domínio-e-cálculo).

### Horizonte — meses, sem pressa

Não há data-alvo externa. A sequência de fases do
[ROADMAP.md](ROADMAP.md) valida cada etapa antes de avançar para a
próxima — o custo de descobrir cedo que uma aposta não segura é sempre menor que o custo de
construir em cima dela.

### As sete perguntas do DIRECAO_PRODUTO §11 — respondidas

| Pergunta | Resposta |
|---|---|
| Quem é a pessoa, exatamente? | Não há persona única; o produto atende amplo e deriva por dentro |
| O produto aceita dívida? | Orienta ativamente — ver [REGRAS_DE_DOMINIO.md](REGRAS_DE_DOMINIO.md#dívida) |
| Qual o preço-alvo, e cobre o Open Finance? | Ver [MODELO_NEGOCIO.md](MODELO_NEGOCIO.md) — a fronteira é manual/grátis vs. automático/pago |
| Renda líquida calculada ou só registrada? | Só registrada — ver [REGRAS_DE_DOMINIO.md](REGRAS_DE_DOMINIO.md#renda-líquida) |
| Educação própria ou curada? | Em aberto — não foi perguntado ainda; ver pendências no roadmap |
| Quem é dono do parecer CVM? | Em aberto — segue como ação a atribuir, não é decisão de produto |
| O investidor atual continua atendido? | Não há investidor atual a atender; a pergunta perde o objeto — o produto novo já nasce servindo a quem faz análise de ativo **e** a quem só quer ver a sobra do mês |

---

## O que isto não é

- Não é um app de orçamento com uma aba de investimento colada. Se a sobra não alimentar a decisão
  de investir automaticamente, a ponte não existe e o produto é dois apps num só instalador.
- Não é um relançamento de marca. Nome e logo ficam.
- Não é urgente. É profundo.
