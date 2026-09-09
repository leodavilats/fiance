# Design do fiance — a especificação da interface

Esta pasta responde **como a interface deveria ser**, e só isso. Ela não diz o que está
construído: isso é o código, e o que falta é o [KNOWN_ISSUES](../KNOWN_ISSUES.md).

A separação é deliberada e custou um arquivo. Até 2026-08-28 havia aqui um `07-IMPLEMENTATION.md`
que registrava status — e ele apodreceu, como todo arquivo de status apodrece: dava como
inexistentes a busca global, o drawer de Atividade e a reestruturação das telas do mobile, todos
prontos. Foi removido junto com os três documentos de processo (`00-DISCOVERY`, `01-UX-AUDIT`,
`03-USER-JOURNEYS`), que auditavam um produto que em boa parte não existe mais. O porquê está no
[CHANGELOG](../CHANGELOG.md), na entrada de 2026-08-28, junto das decisões que só viviam neles.

Os arquivos perderam o prefixo numérico junto. O número indicava a fase do processo de redesign;
sem as fases, ele numerava uma sequência que ninguém segue — não se lê esta pasta em ordem, lê-se o
documento que corresponde ao que se está fazendo. O resto de `docs/` também não usa número.

## Os documentos

| Documento | O que responde | Quando ler |
|---|---|---|
| [INFORMATION-ARCHITECTURE.md](INFORMATION-ARCHITECTURE.md) | Como a navegação é organizada, e o destino de cada tela | **Antes de criar tela ou rota** |
| [WIREFRAMES.md](WIREFRAMES.md) | A estrutura de cada tela, seus estados e a responsividade — sem visual | Ao mexer numa tela |
| [VISUAL-LANGUAGE.md](VISUAL-LANGUAGE.md) | A identidade: "tinta e papel", paleta semântica, tipografia, a régua | Ao decidir aparência |
| [DESIGN-SYSTEM.md](DESIGN-SYSTEM.md) | Tokens e componentes, e o contrato de cada um | Antes de construir componente |
| [AI-TELLS.md](AI-TELLS.md) | O que faz uma tela parecer gerada por IA, e a regra contra cada coisa — texto, composição, dado de exemplo | Antes de aceitar qualquer tela como pronta |
| [PARIDADE.md](PARIDADE.md) | O que precisa ser igual entre web e mobile, o que pode divergir, e o que nunca se copia | **Antes de mexer num conceito** |

**INFORMATION-ARCHITECTURE é a autoridade da navegação.** Quando web e mobile divergem, é contra ele que se confere —
foi assim que a Estratégia apareceu: `strategy.component` tinha 1092 linhas de template e nenhuma
rota, e `GET /strategy` rodava para ninguém.

**PARIDADE é a autoridade sobre o que precisa ser igual.** A resposta curta é: conceito, nome e
hierarquia — não pixel, não hexadecimal. Nenhuma máquina o confere: a paridade é dirigida ao
longo do desenvolvimento das telas, e o documento é a autoridade.

## O que o redesign descobriu, e vale lembrar

O redesign **não exigiu nenhum algoritmo novo**. Exigiu tornar alcançável e legível o que já era
calculado — e, no caminho, revelou um padrão que voltou a aparecer sete vezes: **campo que o
backend calcula e o cliente descarta em silêncio**. `Modelo(**resultado.__dict__)` no Pydantic e
`fromJson` no Dart ignoram chave não declarada sem erro nenhum. Foi assim com `consensus_methods`,
`trend_basis`, `allocation_gaps`, `dcf`, `price_history`, `reason_groups` e
`pct_cdi_equivalente`.

O segundo padrão: **classe CSS que não existe não quebra o build, quebra a tela.** `.card`,
`.btn-primary`, `.tag`, `verdict-*` e `bg-success` eram usadas em dezenas de templates sem estar
definidas em CSS nenhum. Hoje o `npm run lint:ui` cobre isso, junto de ícone do Lucide não
registrado.

Os dois estão na lista de armadilhas do [CLAUDE.md](../../CLAUDE.md#armadilhas-que-não-quebram-o-build).

## Não há gerador de design

Cor, tipografia, espaço, raio, motion, densidade **e as réguas do produto** são escritos à mão:

| O quê | Onde |
|---|---|
| Fundação visual do web | [`web/src/foundation.css`](../../web/src/foundation.css) |
| Componentes do web | [`web/src/styles.css`](../../web/src/styles.css) |
| Fundação visual do mobile | [`mobile/lib/core/design_tokens.dart`](../../mobile/lib/core/design_tokens.dart) |
| Bandas de régua e vocabulário | `core/product-rules.ts` e `core/product_rules.dart` |
| Favicon e ícones do app | `python design-tokens/build-icons.py` (o único gerador que sobra) |

**A paridade entre web e mobile é dirigida no desenvolvimento das telas**, não por máquina. O que
precisa ser igual está em [PARIDADE.md](PARIDADE.md): conceito, nome e hierarquia. Espaçamento,
composição, navegação, gesto e cor são de cada plataforma.

Os limiares de score espelham `backend/app/analysis/score_ruler.py`, que é a fonte. Mudar um
limiar exige mudar o Python primeiro, e depois os dois clientes.

O mínimo da WCAG continua verificado, e não é design: `mobile/test/contraste_test.dart` cobra
4,5:1 para texto e 3:1 para limite de controle. Liberdade de UX/UI é escolher a cor, não publicar
o que não se lê.

## Regras que valem para toda a interface

- **Nada de dado inventado.** Métrica, endpoint ou indicador que não existe não entra em wireframe.
  Onde o dado falta, o entregável é um **estado**, não um número.
- **Regra de negócio fica no backend.** `analysis/` e `optimizer/` são a fonte única. A UI reflete
  e explica; não decide.
- **Mesma intenção, não mesma implementação.** Conceito, vocabulário e hierarquia são iguais nas
  plataformas; espaçamento, composição e navegação não precisam ser. O que é **número** — banda de
  régua, rótulo de veredito — nasce em `analysis/score_ruler.py` e é espelhado nos dois clientes
  no mesmo commit, porque a régua de score já divergiu entre web e mobile.
- **Em conflito:** clareza vence informação; decisão vence funcionalidade visível; facilidade vence
  sofisticação técnica.

Os comandos da suíte, com as contagens esperadas, estão em
[CLAUDE.md](../../CLAUDE.md#como-trabalhar-aqui).
