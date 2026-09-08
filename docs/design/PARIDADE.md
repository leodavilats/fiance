# Contrato de paridade — web × mobile

> **Mesma intenção, não mesma implementação.**

Não há gerador de tokens visuais, e não deve haver. A camada visual é escrita à mão nas duas
plataformas — [`web/src/foundation.css`](../../web/src/foundation.css) e
[`mobile/lib/core/design_tokens.dart`](../../mobile/lib/core/design_tokens.dart) — e elas **podem
divergir**.

Este documento existe porque a pergunta "isso está igual?" é a pergunta errada. A certa é "isso
significa a mesma coisa?".

---

## Por que o gerador resolvia o problema errado

Quando a paridade era garantida por geração, ela garantia que **176 valores de cor** fossem
idênticos nos dois lados. E eram: uma varredura em 2026-09-08 não achou uma divergência.

No mesmo dia, o mobile não tinha `/mes` nem `/sobra` — as duas telas no topo da navegação do web.
Metade do produto (`cashflow/`, `cashflow_service`, a régua de dívida, a cascata) sem cliente
móvel, e `docs/ARCHITECTURE.md` afirmando que o shell do mobile "espelhava os destinos do web".

A camada acoplada era a que menos carregava significado. Cor não é onde a paridade quebra;
conceito é.

O mesmo padrão apareceu em tudo que o web cobra por máquina e o mobile não:

| Princípio | Web | Mobile, em 2026-09-08 | Depois |
|---|---:|---:|---|
| Explicabilidade em julgamento renderizado | 15 | **0** | cobrado por `test/lint_ui_test.dart` |
| Serifa carregando conclusão | 20 | 3 | cobrado: papel de veredito sem serifa reprova |
| Tamanho de tipo escrito solto | 0 | **49 linhas** | catraca em 49, e o teto só desce |

O web tinha zero tamanho solto porque uma regra reprova `text-sm`; o mobile tinha 49 porque
nenhuma regra rodava lá. **O defeito das máquinas deste produto era geográfico**, e a correção foi
levar cinco delas para o Dart — não escrever mais regras no web.

---

## Precisa ser igual

### Conceito

`mês` · `sobra` · `comprometido` · `livre agora` · `dívida` · `patrimônio` · `composição` ·
`concentração` · `veredito` · `saúde` · `score` · `preço justo` · `margem de segurança` ·
`falsificador` · `proveniência` · `projeção` · `faixa` · `alocação-alvo` · `desvio` · `reserva` ·
`apuração` · `isenção`

### Nome

O mesmo conceito tem o mesmo nome, na mesma língua e no mesmo tom. Um destino chamado
`Patrimônio` no web e `Carteira` no mobile é divergência, não sinônimo — foi como a diferença
passou meses sem ser vista.

### Hierarquia

`conclusão → evidência → explicação → detalhe`. A ordem sobrevive nas duas plataformas, mesmo
quando a forma muda.

### Regras de UX

- projeção sai como faixa, nunca número único;
- julgamento vem com como conferir a conta;
- ausência é um estado nomeado, nunca `0,00`;
- método não aplicável explica o motivo;
- nada de promessa sobre o futuro.

### Os números do domínio

Banda de régua, limiar e rótulo de veredito nascem em
[`product-rules.json`](../../design-tokens/product-rules.json) e são **gerados** para as duas
plataformas. Isto é número, não aparência — e a régua de score já divergiu quando era mantida à
mão em três arquivos.

---

## Pode ser diferente

- espaçamento, densidade e os **valores** da escala tipográfica;
- composição e ordem visual dentro da tela;
- navegação: subnav lateral no web, empilhamento e sheet no mobile;
- interação: hover e popover no web; toque, sheet e gesto no mobile;
- **valor de cor**, desde que cada plataforma passe o piso e declare o papel nos dois temas;
- profundidade: o web mostra quatro leituras lado a lado, o mobile revela progressivamente.

Um telefone sob sol pode precisar de mais contraste que um monitor. Exigir o mesmo hexadecimal
impediria a correção.

---

## Nunca deve ser copiado

| O quê | Por quê |
|---|---|
| Larguras de leitura — `readingMaxWidth`, `denseMaxWidth`, `subnavWidth`, `drawerWidth` | Um telefone não tem subnav. Estavam no Dart, sem um único leitor, porque um dia foram geradas |
| Subnav de seis pares | No telefone é segmento (2–3) ou rota empilhada (4+); barra rolável esconde as últimas |
| Tabela de colunas fixas em scroll horizontal | O mobile usa linha com disclosure progressivo |
| Afordância só de hover | No telefone não existe hover |
| `fi-money-xl` a 44px | Foi transliterado e ficou grande demais para caber — por isso nunca foi usado no mobile |
| Densidade como régua de espaçamento | No telefone a régua equivalente é a escala de texto do sistema |
| A gaveta `<details>` de proveniência | No mobile é sheet: o que se abre para conferir volta para onde estava |

---

## As duas máquinas

O resto é revisão humana. Estas duas existem porque cobrem modos de falha que a revisão humana
**já** falhou.

### `check-contrast.mjs`

Mede as duas plataformas, cada uma **contra o piso** — não uma contra a outra. Reprova papel
abaixo do piso, papel declarado só num tema, contorno de controle sob 3:1 e preenchimento que não
se distingue do próprio poço.

Confere também as **duas cópias do tema claro** do CSS. Eram 44 papéis sem guarda: quem editasse
só a consulta de mídia quebrava o contraste de quem está no padrão do sistema — a maioria, que
nunca tocou no seletor.

### `check-parity.mjs`

Responde se os cinco destinos existem nas duas plataformas. Não compara aparência, não compara
valor, não gera nada.

Ausência conhecida é **dívida registrada** em `DIVIDA_HOJE`, no mesmo padrão de
`SEM_MODELO_HOJE` nos testes do backend: não conserta hoje, não deixa crescer. E a lista **só
encolhe** — um item que passe a existir reprova, porque lista de dívida que não encolhe é a
documentação mentindo de novo.

**Hoje ela está vazia**, e foi ela quem cobrou a própria baixa: `mes` e `sobra` moraram em
`DIVIDA_HOJE` até as telas do mobile existirem (2026-09-08), e no instante em que passaram a
existir a verificação reprovou pedindo que as linhas saíssem.

---

## Revisão de PR

Só aparece quando o PR toca conceito.

```text
Conceito alterado, criado ou removido?
    │
    ├─ não ──→ segue: é implementação de uma plataforma
    │
    └─ sim ─→ Existe equivalente no web?      ─┐
              Existe equivalente no mobile?   ─┼→ se falta em um: é dívida
              A semântica continua igual?     ─┘  registrada, não silêncio
              A hierarquia continua igual?
                    │
                    └→ A implementação pode, e deve, ser diferente.
```

- [ ] O conceito existe nas duas plataformas — ou a ausência está registrada?
- [ ] O nome significa a mesma coisa nos dois lados?
- [ ] A ordem conclusão → evidência → explicação → detalhe se manteve?
- [ ] Os estados de ausência estão cobertos, ou algum cai em zero?
- [ ] O web usa o padrão natural do web?
- [ ] O mobile usa o padrão natural do mobile?
- [ ] Alguma igualdade visual artificial foi criada — um valor copiado só para "bater"?
