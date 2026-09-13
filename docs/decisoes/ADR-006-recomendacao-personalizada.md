# ADR-006 — Recomendação personalizada como alvo de produto, sem parecer jurídico

**Status:** ACEITO
**Data:** 2026-09-13
**Decidido por:** autor do projeto

## Contexto

A hipótese de receita do produto, declarada pelo autor: a pessoa paga quando percebe que o aplicativo
**indica ativos para ela**, com base no perfil, nas metas e na carteira que já tem, e diz por quê.

A frase-alvo:

> *"PETR4 está 20% abaixo do preço justo e cabe na sua meta de renda, e você tem ITSA4 que está 20%
> acima — avalie se vale fazer o ajuste."*

O sistema já tem quase tudo o que isso exige: perfil de risco que muda os pesos do score, metas de
alocação, e `analysis/strategy.py:378` produzindo sugestões de compra por lacuna e de redução por
veredito, com razões escritas.

## Problema

No Brasil, recomendar valores mobiliários de forma personalizada, como atividade remunerada, é
atividade regulada — **Resolução CVM 19** (consultoria de valores mobiliários) e **Resolução CVM 20**
(analista), que alcançam também sistemas automatizados.

O sistema **já tem o interruptor dessa decisão**: `AFFIRMATION_LEVEL` (ver
[ADR-007](ADR-007-nivel-de-afirmacao.md)) opera em três níveis, e o nível 3 — prescritivo — está
desligado, com a nota de que aguarda parecer jurídico.

A pergunta não era técnica: era **qual nível de afirmação o produto quer entregar, e com que
respaldo**.

## Alternativas

1. **Manter o nível 2** — análise personalizada, sem prescrever valor por ativo
2. **Ligar o nível 3** com parecer jurídico prévio
3. **Ligar o nível 3** sem parecer
4. Abandonar a personalização e virar ferramenta descritiva

## Decisão

**Perseguir a recomendação personalizada como alvo de produto, operando no nível 2, sem buscar
parecer jurídico neste momento.**

Duas partes, e a distinção importa:

**A frase-alvo cabe no nível 2.** Comparar dois ativos da carteira da pessoa contra o preço justo e
sugerir que ela avalie um ajuste é análise personalizada com veredito explicado. O que o nível 3
acrescentaria é a **prescrição de valor por ativo** — *"aporte R$ 800 em PETR4"* —, e essa parte
permanece desligada.

**Não haverá parecer jurídico agora.** Decisão explícita do autor, tomada com conhecimento do
enquadramento regulatório descrito acima.

## Consequências

**Ganhos**

- A hipótese de receita pode ser construída sem mudança de arquitetura: o motor já personaliza
- O nível 2 mantém a postura editorial que é o diferencial declarado do produto — explicabilidade,
  falsificadores, faixa em vez de número único

**Riscos aceitos, declarados**

- O enquadramento regulatório não foi avaliado por advogado. A decisão de onde termina "análise
  explicada" e começa "recomendação personalizada" está sendo tomada por quem escreve o código
- A fronteira entre nível 2 e nível 3 é uma **constante em arquivo de configuração**, não uma trava.
  Alguém pode ligar o nível 3 sem que nada impeça
- O produto se destina a distribuição por loja, o que amplia a exposição em relação a uso pessoal
- Se um parecer futuro exigir recuo, o recuo é **configuração, não refactor** — e é exatamente para
  isso que a [ADR-007](ADR-007-nivel-de-afirmacao.md) existe

**Mitigação que já existe**

- O nível de afirmação é configuração, com efeito imediato e sem deploy de código
- `/aviso-cvm` lê `affirmation.current()` no servidor, então o texto jurídico **nunca** descreve um
  nível diferente do que o produto está entregando
- A explicabilidade obrigatória faz cada julgamento vir com o que o derrubaria, o que é o oposto de
  uma recomendação opaca

**Revisão:** esta decisão deve ser reexaminada antes da publicação em loja, e imediatamente se houver
intenção de ligar o nível 3.

## Referências

- [ADR-007](ADR-007-nivel-de-afirmacao.md)
- [01-PRODUTO](../01-PRODUTO.md), [09-FUTURO](../09-FUTURO.md)
- `backend/app/affirmation.py`, `backend/app/analysis/strategy.py`
- Resoluções CVM 19 e 20, de 2021
