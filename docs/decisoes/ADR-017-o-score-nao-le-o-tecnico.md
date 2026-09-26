# ADR-017 — O score de oportunidade não lê o técnico

**Status:** ACEITO · estende a [ADR-013](ADR-013-o-tecnico-nao-decide.md) ao score
**Data:** 2026-09-25
**Decidido por:** autor do projeto, que delegou a escolha do caminho depois da medição

## Contexto

A [ADR-013](ADR-013-o-tecnico-nao-decide.md) e a [ADR-014](ADR-014-um-modelo-por-classe.md) tiraram
tendência e RSI da leitura de valor: eles não mudam a etiqueta nem somam confiança. O score de
oportunidade ficou de fora dessa revisão. A
[auditoria de 2026-09-25](../historico/AUDITORIA-DO-PRECO-JUSTO-2026-09-25.md) o registrou como item
R-016.

## Problema

Em ação e BDR, o score tinha uma dimensão técnica, `50 + (60 − RSI) × 0,5` com ±10 por tendência,
pesando de 5% a 10% conforme o perfil. O score não é detalhe:

- ordena Descobrir por padrão;
- decide o destaque (`is_highlight`), que alimenta "O que há de novo";
- aparece na tela com as faixas Forte, Boa, Neutra e Fraca.

O glossário do aplicativo dizia que o score combina margem, dividendos, qualidade e endividamento.
O técnico pesava sem ser explicado.

Medido em 2026-09-25 sobre 31 ativos reais, com o histórico de preço de cada um:

- **Em BDR, o score era 100% técnico.** BDR não tem preço justo, e a BRAPI não entrega fundamento
  para ele. RSI e tendência eram a única dimensão que sobrava: MSFT34 tinha 57,8 pontos, e todos
  vinham do movimento do preço.
- Nas ações, o peso era pequeno. Sem o técnico, **o top 5 não muda em nenhum perfil, e nenhum
  destaque muda.** Uma ação por perfil troca de faixa (KLBN11 no moderado, VALE3 no arrojado), e os
  saltos maiores no ranking, de até 16 posições, são dos BDRs.

## Alternativas

1. **Tirar RSI e tendência do score** de ação e BDR. O score passa a ler só fundamento e margem.
2. **Manter** e declarar em ADR que o score é ranking, e não leitura de valor.
3. **Deixar o score nulo quando não há faixa.** Rejeitada: o aplicativo em loja lê `score` como
   número obrigatório num dos modelos, e nulo quebraria a tela de quem não atualizou. A completude
   já resolve isso: sem dimensão nenhuma, ela é zero, e a tela mostra "Sem dado".

## Decisão

A alternativa 1. `_score_technical` sai, a dimensão sai dos três perfis, e `score_opportunity`
deixa de receber RSI e tendência. Os outros pesos ficam como estão. O score divide pelo peso
disponível, então a parte que era do técnico se distribui na proporção dos outros.

Os rótulos "Excelente entrada", "Boa oportunidade", "Neutro" e "Evitar agora", em
`analysis/score_ruler.py`, saem também. Eles não tinham consumidor, e "Evitar agora" é uma ordem, e
não uma posição. Os limiares continuam no Python. Os rótulos que a tela mostra moram só no
aplicativo.

## Consequências

**Ganhos**

- O técnico não decide em lugar nenhum da leitura de valor nem do ranking
- BDR deixa de ter nota tirada do movimento do preço: com completude zero, sai como "Sem dado"
- O glossário diz o que entra no score, e que o movimento do preço não entra

**Custos aceitos**

- BDRs descem para o fim da ordenação por score, porque passam a ter nota zero
- Os pesos efetivos mudam um pouco: com todos os dados, os dividendos do conservador passam de 25%
  para 26%, e o crescimento do arrojado, de 40% para 44%

**Fora desta decisão:** a análise de quedas (`analysis/dip_analysis.py`) também usa RSI e
tendência, com 25 dos 100 pontos. Ela é outra funcionalidade, um diagnóstico de queda que declara
esse uso, e não entrou nesta revisão.

## Referências

- `backend/app/analysis/scoring.py` · `backend/app/analysis/score_ruler.py`
- `backend/tests/test_o_score_nao_le_o_tecnico.py`
- `mobile/lib/core/score_ruler.dart` · `mobile/lib/core/glossary.dart`
- [04-CALCULOS](../04-CALCULOS.md), seção *Score de oportunidade*
