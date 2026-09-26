# ADR-018 — A queda é recorte de Descobrir, e não veredito

**Status:** ACEITO · estende a [ADR-013](ADR-013-o-tecnico-nao-decide.md) e a
[ADR-017](ADR-017-o-score-nao-le-o-tecnico.md) à varredura de quedas
**Data:** 2026-09-25
**Decidido por:** autor do projeto, que delegou a escolha depois da medição

## Contexto

O filtro "Em queda" de Descobrir mostrava a varredura de quedas (`/dip-scanner`). Cada ativo
recebia uma nota de 0 a 100 e uma etiqueta própria — "Oportunidade na baixa", "Aguardar" ou
"Armadilha" — calculadas por `analysis/dip_analysis.py`, fora das regras das ADRs 013 a 017.

## Problema

Medido em 2026-09-25 sobre 31 ativos reais:

- **26 saíam "Armadilha", 5 "Aguardar" e nenhum "Oportunidade na baixa".** A dimensão de valor foi
  calibrada para a margem antiga: dentro da faixa, a margem é zero e valia 6 de 30 pontos.
- **Contradizia a folha do ativo.** MXRF11 saía "Abaixo do preço justo" na folha e "Armadilha —
  cuidado com o value trap" na lista.
- **Ausência virava zero.** FII perdia os 25 pontos de qualidade por não ter ROE, margem nem D/E.
- **Sem faixa ainda havia leitura de valor**: 10,5 pontos "neutros".
- **O técnico decidia**: RSI, distância do topo e média de 200 dias somavam 25 pontos.
- A confiança era a nota ÷ 100, e não a qualidade da faixa.

A rota individual `/asset/{symbol}/dip-analysis` não tinha cliente, e dependia de notícias do
Google News — uma terceira fonte, que o invariante "só BRAPI e BCB SGS" proíbe.

## Alternativas

1. **Recalibrar cada dimensão** da nota. Mantém um segundo vocabulário de veredito nas duas
   plataformas, que precisa acompanhar toda mudança na leitura de valor.
2. **A queda vira recorte.** A varredura filtra pela queda desde a máxima de 52 semanas e mostra a
   leitura de valor que o resto do produto já mostra.

## Decisão

A alternativa 2. A queda é o que define "em queda": ela **filtra** (15% ou mais desde a máxima de 52
semanas, ajustável por `min_drop`), e a leitura de valor **ordena** (margem de segurança, com quem
não tem faixa no fim). Cada item traz a mesma etiqueta, faixa, qualidade e primeira razão da folha do
ativo.

Saem a nota, as três etiquetas próprias, `dip_analysis.py`, a rota individual, a regra de plano
`Feature.DIP_DIAGNOSIS`, o evento `dip_diagnosis_opened` e o coletor de notícias.

Sem app em loja, a mudança é feita de uma vez, sem migração em dois passos.

## Consequências

**Ganhos**

- Uma leitura só: a lista de quedas não contradiz mais a folha do ativo
- O técnico não decide em nenhuma tela
- A última fonte fora de BRAPI e BCB SGS sai do sistema

**Custos aceitos**

- Não há mais "diagnóstico de queda" que diga por que o ativo caiu. A queda é mostrada como fato, e
  o valor, pela leitura de sempre
- O plano perde uma regra de cerca (`DIP_DIAGNOSIS`); a cerca está desligada

## Referências

- `backend/app/services/dip_service.py` · `backend/app/models/dip.py` ·
  `backend/tests/test_varredura_de_quedas.py`
- `mobile/lib/features/market/opportunities_tab.dart` · `mobile/test/varredura_de_quedas_test.dart`
- [04-CALCULOS](../04-CALCULOS.md), seção *Varredura de quedas*
