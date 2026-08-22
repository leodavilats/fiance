# Redesign de UX/UI do fiance

Reformulação completa da experiência — não um retrabalho visual. A ordem dos documentos é a ordem
do processo: **estrutura antes de pixel**.

## Os documentos

| Fase | Documento | O que responde |
|---|---|---|
| 1 | [00-DISCOVERY.md](00-DISCOVERY.md) | O que existe hoje, com evidência de arquivo e linha |
| 2 | [01-UX-AUDIT.md](01-UX-AUDIT.md) | O que está errado — 36 achados, P0 a P3 |
| 3 | [02-INFORMATION-ARCHITECTURE.md](02-INFORMATION-ARCHITECTURE.md) | Como a navegação passa a ser organizada, e o destino de cada tela antiga |
| 4 | [03-USER-JOURNEYS.md](03-USER-JOURNEYS.md) | Os 12 fluxos, para os três perfis de senioridade |
| 5 | [04-WIREFRAMES.md](04-WIREFRAMES.md) | A estrutura de cada tela, seus estados e a responsividade — sem visual |
| 6 | [05-VISUAL-LANGUAGE.md](05-VISUAL-LANGUAGE.md) | A identidade: "tinta e papel", paleta semântica, tipografia, a régua |
| 7 | [06-DESIGN-SYSTEM.md](06-DESIGN-SYSTEM.md) | Tokens e componentes, e o contrato de cada um |
| 8–9 | [07-IMPLEMENTATION.md](07-IMPLEMENTATION.md) | O que já está no ar, em ordem, e o que ainda não |

**Por onde começar:** para entender *por que* o produto mudou, leia 01 e 02. Para mexer numa tela,
leia 04 (a estrutura dela) e 06 (os componentes disponíveis). Para saber o que já existe em
código, leia 07.

## Os três achados que governam tudo

1. **`/strategy` não era rota.** 1092 linhas de template com Estratégia, Ajustes necessários,
   Alocação projetada e Quick Invest estavam em `components/index.ts` e em lugar nenhum da
   navegação. `GET /strategy` e `POST /quick-invest` rodavam para ninguém. **Corrigido.**
2. **8 destinos escondidos em tabs sem URL** dentro de `/market`. Sem deep link, sem voltar, sem
   restaurar estado. **Corrigido.**
3. **O backend é honesto e a UI não aproveitava.** `data_completeness`, `freshness`, proveniência,
   confiança e consenso de métodos já vinham da API, e a interface tratava a maior parte como
   número comum. O diferencial do produto estava calculado e invisível.

O redesign **não exigiu nenhum algoritmo novo**. Exigiu tornar alcançável e legível o que já era
calculado — e, no caminho, revelou três campos que a API calculava e descartava em silêncio
(`consensus_methods`, `trend_basis`, `allocation_gaps`).

## Tokens

Uma fonte, três alvos. Editar só `design-tokens/tokens.json`:

```bash
node design-tokens/build.mjs           # gera web/src/tokens.css,
                                       #      web/src/app/core/design-tokens.ts,
                                       #      mobile/lib/core/design_tokens.dart
node design-tokens/build.mjs --check   # falha se divergir (job `design-tokens` no CI)
```

## Regras que valem para todas as fases

- **Nada de dado inventado.** Métrica, endpoint ou indicador que não existe não entra em wireframe.
  Onde o dado falta, o entregável é um estado, não um número.
- **Regra de negócio fica no backend.** `analysis/` e `optimizer/` seguem a única fonte de verdade.
  A UI reflete e explica; não decide.
- **Três alvos, uma linguagem.** Todo token e toda régua semântica (score, veredito, estado) nasce
  numa fonte única e é gerada para CSS, TypeScript e Dart. A régua de score já divergiu entre web e
  mobile por ser mantida à mão em três arquivos.
- **Em conflito, clareza vence informação; decisão vence funcionalidade visível; facilidade vence
  sofisticação técnica.**
- Suíte verde é pré-requisito de merge:
  `cd backend && python -m pytest -q` · `flutter analyze && flutter test` ·
  `npm run format:check && npx ng build` · `node design-tokens/build.mjs --check`.
