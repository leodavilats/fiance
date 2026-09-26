# Interface

Por que a interface é assim, e o que uma tela nova precisa respeitar.
Fonte compartilhada com `mobile/lib/core/design_tokens.dart` e `mobile/test/lint_ui_test.dart`.
Última revisão: 2026-09-26

---

## Navegação — o ciclo do dinheiro

Cinco destinos de raiz, e `/ativo/:ticker` como camada:

```
/mes  →  /sobra  →  /patrimonio       /descobrir       /voce
```

URLs antigas seguem como redirect — `/hoje`, `/carteira/*`, `/estrategia/*`. **Link salvo é
contrato.**

**Deslizar na horizontal troca de destino de raiz**, e o gesto tem esse significado só ali. Dentro de
um card de ativo ele continua sendo vender e remover — o gesto interno vence a arena, e é por isso
que nenhuma seção tem pager próprio: dois pagers aninhados fazem o mesmo movimento significar coisas
diferentes sem aviso na tela.

`/voce` é índice de quatro eixos — `investir`, `avisos`, `aparencia`, `conta` —, e cada linha carrega
o estado atual em vez de só encaminhar.

Dois destinos deixaram de existir e não voltam:

- **`Hoje`** respondia "o que mudou", e isso é feed, não lugar. O feed vive no `Mês`.
- **`Estratégia`** se dissolveu: sem aporte, meta e projeção, sobrava o desvio de alocação, que é
  leitura de patrimônio e vive em `/sobra/desvio`.

`test/lint_ui_test.dart` reprova nome de destino aposentado e destino de navegação que o roteador não
declara.

---

## A camada visual é escrita à mão, inteira, num lugar só

**Não há gerador de design.** Cor (nos dois temas), tipografia, espaço, raio e motion
vivem em `mobile/lib/core/design_tokens.dart`. As bandas das réguas, o vocabulário de veredito e os
rótulos de categoria também são escritos — `core/product_rules.dart` e `core/vocabulary.dart`.

**Não escreva hexadecimal em `theme.dart`.** A paleta mora só na fundação, e há regra de lint para
isso.

---

## Cor

**Não existe alias.** Os papéis são:

| Grupo | Papéis |
|---|---|
| Chão | `ground-0`, `ground-1`, `ground-2` |
| Fio | `hairline` |
| Tinta | `ink-1`, `ink-2`, `ink-3` |
| Marca | `brand`, `ink-on-brand` |
| Estado | `favorable`, `attention`, `adverse`, `indeterminate` |
| Direção | `up`, `down` |
| Séries | por categoria |

**Papel de cor novo se declara nos dois temas.** Senão a cor não existe num deles, e a tela sai com
tinta de um tema no chão do outro.

### Estado ≠ direção

A distinção mais fácil de errar e a mais visível quando errada.

| | O que é | Croma | Função |
|---|---|---|---|
| **Estado** | Julgamento: veredito, saúde, severidade | Alto, prioridade cromática | `fiStateColor(FiState.x, brightness)` |
| **Direção** | Aritmética de um número: P&L, linha de gráfico | Baixo | `fiDirectionColor(delta, brightness)` |

Pintar direção com token de estado faz **uma perda aparecer como aviso** e o verde significar marca,
lucro e veredito favorável ao mesmo tempo.

### Contraste é verificado, não recomendado

`mobile/test/contraste_test.dart`, no CI, nos dois temas, contra o **mínimo da WCAG**: 4,5:1 para
texto e 3:1 para forma e limite de controle.

`ink-3` conta como texto, porque legenda é texto pequeno. Série de gráfico escreve o rótulo do
próprio chip, então também conta como texto. `hairline` fica de fora, é decoração.

Piso acima da norma é escolha de design, e escolha de design não tem máquina: **a paleta é livre, o
ilegível não é.**

---

## Tipografia

**Tipo é papel, não tamanho.** `FiType.body`, `.caption`, `.metric`, `.verdict`, `.axis`…

`fontSize:` solto tem catraca em `test/lint_ui_test.dart`, e **ela só desce**.

**Serifa decide, sans mede.** O papel de veredito sai na família serifada, e o teste reprova o
contrário: é o sinal de que aquela linha é conclusão, não mais um número.

---

## Composição

**Fio + chão, não card + card.** A hierarquia nasce de espaço, tipo e uma regra horizontal.

A caixa fica reservada ao que é **objeto**: uma posição, uma opção de renda fixa, uma sugestão. Ela
tem nome — **`FiObject`** — e só serve a isso. `Card`, `ListTile`, `SwitchListTile` e `CircleAvatar`
estão em **catraca zero**: o resto é `FiSection` + `FiRows`/`FiDataRow`.

Card dentro de card dentro de card é a forma mais reconhecível de o produto virar painel de BI.

**Grade de KPI é o cheiro de painel.** Três ou quatro caixas centralizadas com um número dentro não
são informação organizada, são widgets. A alternativa é uma linha de cifras sob um fio quando são
poucas, ou uma tabela quando o que importa é comparar.

---

## Componentes obrigatórios

| Ao colocar numa tela | Use | Senão |
|---|---|---|
| Bloco novo | `FiSection` | O lint reprova `Card`/`ListTile` |
| Objeto | `FiObject` | idem |
| Ação | `FiButton` (`primary`/`secondary`/`quiet`/`danger`), uma principal por contexto | Frase solta não parece ação |
| Número contra referência | `FiMeasure`, ou `ScoreRuler` para score | A régua é a assinatura do produto |
| Julgamento | `FiProvenance` — método, fonte, limitação | O lint reprova |
| Número projetado | `FiRange` — piso, teto, cenário base | O lint reprova |
| Espera | `FiSkeleton.screen(shape:, count:)`, ou `FiSkeleton.page()` quando a tela tem manchete e seções | Disco girando não diz o que vem, e a página salta |
| Revelar detalhe | `FiDisclosure` (item) ou `FiGroupDisclosure` (grupo) | `ExpansionTile` traz a moldura do Material de volta |
| Ficha de filtro | `FiChoiceChip` | `ChoiceChip` e `InputChip` têm estilo só no tema |
| Ligar e desligar | `FiSwitch`, com o rótulo da linha | O `Switch` solto era anunciado como "ligado", sem dizer o quê |
| Escolher um valor numa escala | `FiSlider`, com o formatador do produto | O `Slider` com `toStringAsFixed` mostrava 5.5% com ponto |
| Falha | `FiErrorState` + `fiErrorMessage` | Já houve oito grafias, e `Erro 500` chegou à tela |
| Ausência de dado | `FiEmptyState` | "Não conseguimos ler" ≠ "você não tem nada" |

---

## Estado de tela é contrato

Carregando, falha, vazio e conteúdo saem do par `FiSkeleton`/`FiErrorState` com `AsyncValue.when`.

**A falha guarda o erro, não um booleano.** Sem ele a tela só sabe dizer "algo deu errado" — uma
loja de carteira chegou a servir sete telas com um booleano que uma só lia.

**Bloco que carrega reserva o espaço.** `loading: () => SizedBox.shrink()` é reprovado por máquina:
a seção aparece depois e empurra a página para baixo, debaixo do dedo de quem estava lendo. Ou o
esqueleto tem a forma da seção, ou a seção não se desenha.

**Ausência de dado e falha de leitura nunca compartilham a mesma tela.**

---

## Explicabilidade

Score, veredito, preço justo e sugestão precisam de `FiProvenance`, `HelpTooltip` ou as funções de
proveniência de `core/score_ruler.dart`. **Mencionar em prosa não conta.**

O escape exige motivo escrito:

```dart
// design-exception: explicabilidade — …
```

**Há uma forma só de escapar, e ela nomeia a regra:** escapar de cabeçalho não escapa de contraste.

Regras específicas de conteúdo:

| Ao mostrar | Exigência |
|---|---|
| Cifra de preço justo | A base junto: o modelo principal, a qualidade e as premissas |
| Preço, ou lista de preços | `formatAge`. Em lista, o carimbo é o **mais antigo** (`oldestStamp`) |
| Projeção | Faixa, com piso, teto e cenário base |
| Julgamento | Proveniência e papel de veredito em serifa |

Dizer a idade do preço mais novo de uma lista promete frescor que a linha de baixo não tem.

**Momento é nível 1, não nota de rodapé.** Método e fonte moram na gaveta; **quando o dado foi lido,
não**. Um preço de anteontem muda a decisão.

**Evidência é o nível 2** (`FiEvidence`, em `mobile/lib/core/widgets/evidence.dart`): entre a
conclusão e o método, os três primeiros motivos da leitura, visíveis sem abrir nada, marcados por um
fio à esquerda e não por caixa. Na folha do ativo ela vem logo abaixo da margem de segurança, e o
resto das razões fica na seção do método, sem repetir as três.

**O nível de detalhe muda o que vem aberto, e nada é escondido** (`detail_level` em `/preferences`,
escolhido em Você → Como eu invisto, `/voce/investir`). Na folha do ativo: **Essencial** traz a etiqueta, o preço, a margem
em palavras e a evidência, com o método numa gaveta fechada, "Como chegamos nisso"; **Completo**, o
padrão, traz as seções de método abertas; **Avançado** acrescenta os métodos com o motivo de cada
silêncio e os insumos do cálculo — data de referência, Selic usada e sua origem, tipo do fundo. "O que
derrubaria esta leitura" fica visível em todos os níveis: veredito vem com o falsificador.

**A ordem das razões é hierarquia.** A evidência mostra as três primeiras que o backend manda, então
`decide()` as ordena para quem lê só elas: onde o preço está em relação à faixa, o valor numa frase,
a segunda conta. As premissas detalhadas ("Na conta, a taxa exigida…") são método, e vêm depois — no
Essencial, dentro da gaveta.

---

## As 17 regras de máquina

`mobile/test/lint_ui_test.dart` — roda em `flutter test`, que já é comando do CI. **Regra que exige
mudar a esteira para rodar é regra que não roda.**

| # | Regra |
|---|---|
| 1 | Nenhuma tela julga sem explicar |
| 2 | Nenhuma tela promete o futuro |
| 3 | Projeção só aparece como faixa |
| 4 | Todo botão de ícone tem nome acessível |
| 5 | O papel de veredito sai em serifa |
| 6 | Nenhuma tela fala como IA genérica |
| 7 | Nenhuma tela usa nome de destino que saiu |
| 8 | O tipo solto não cresce *(catraca)* |
| 9 | A caixa do Material não volta a crescer *(catraca)* |
| 10 | Nenhuma tela escreve cor à mão |
| 11 | Espera tem a forma do que vai chegar, não um disco girando |
| 12 | Todo destino navegado existe no roteador |
| 13 | A falha de leitura sai numa voz só |
| 14 | Bloco que carrega reserva o espaço em vez de sumir |
| 15 | Todo gráfico tem tabela equivalente (FiDisclosure com FiRows/FiDataRow), ou escape `grafico` |
| 16 | Controle de toque vem do sistema: `InkWell`/`GestureDetector` fora de `core/widgets/` *(catraca)* |
| 17 | Controle do Material só existe dentro do sistema: `Switch`, `Slider`, `ChoiceChip`, `InputChip`, `FilterChip`, `ExpansionTile` |

Mais o contraste, cobrado à parte em `contraste_test.dart`, nos dois temas, e o **alvo de toque de
44dp** dos componentes de toque do sistema, em `alvo_de_toque_test.dart`, pela diretriz
`iOSTapTargetGuideline` do Flutter. O teste exige antes que o componente tenha ação de toque na
semântica: sem ela, a diretriz nem o enxerga, e o leitor de tela não consegue apertá-lo.

Uma regra saiu em 2026-09-13: *"a busca global é alcançável de todo destino de raiz"*. A busca global
saiu do produto — não se busca tela, e o ativo se procura no campo de ticker do `/descobrir`, que é
filtro da lista —, e regra que exige o que o produto não quer mais é regra trabalhando contra ele.

⚠️ **A regra varre `lib/`.** O que estiver fora não é conferido. Ao escrever regra nova, confira
contra **o que o repositório tem**, não contra o que a extensão sugere: duas regras já varreram
`.html` num repositório que escrevia template dentro do `.ts`, e uma delas era a que protege a
explicabilidade.

---

## Linguagem

**Número em português é responsabilidade do formatador, não do template.** O locale é `pt_BR`:
`R$ 120.000` escrito como `R$ 120,000` se lê como cento e vinte reais. Vale também para a frase que
chega pronta do backend: razões, falsificadores e motivos de silêncio da análise saem por
`analysis/texto.py` (`reais`, `pct`, `numero`).

### A análise se lê sem glossário

Metade do público nunca investiu ([01-PRODUTO](01-PRODUTO.md)). Na folha do ativo, e nas frases que o
backend manda para ela:

- **Sigla nunca chega sozinha.** Ela pode ficar, mas com o nome por extenso ou a explicação ao lado,
  na mesma frase ou na mesma linha: "o retorno sobre o patrimônio (ROE)", "o índice de força
  relativa (RSI), de 0 a 100", "Fundo imobiliário (FII)". O nome do ativo que vem da fonte ("Maxi
  Renda FII") é nome próprio; quem diz o que o ativo é, por extenso, é o cabeçalho.
- **O método se chama pelo que mede.** "Pelo lucro distribuível", "Pelos dividendos", "Pelo valor
  patrimonial" — nunca DCF, Bazin ou Gordon. A confirmação é "uma segunda conta, com outro dado";
  "insumo" é vocabulário do código, não da tela.
- **Termo que fica tem verbete ao toque.** `FiDataRow` e `FiMeasure` aceitam `glossaryKey`: o rótulo
  ganha sublinhado pontilhado e o toque abre o verbete de `core/glossary.dart`. Chave sem verbete não
  vira toque, em silêncio — o teste confere que toda chave usada existe.
- **A margem sai em palavras e em reais** ("o preço está R$ 1,55 abaixo do piso do preço justo"). Um
  percentual negativo de margem não diz nada a quem começou agora.
- **Contexto de preço não prevê.** "Subiu rápido em pouco tempo", nunca "costuma vir correção".

`mobile/test/linguagem_da_folha_do_ativo_test.dart` monta a folha no Essencial, com a gaveta fechada
e aberta, e reprova sigla sem explicação ao lado e jargão de analista;
`backend/tests/test_linguagem_da_analise.py` faz o mesmo com as frases do backend, em todos os
cenários que elas cobrem. A lista de siglas vive nos dois testes.

**Nome de tela usa o nome do conceito, não um sinônimo.** A barra de `/voce` já dizia
"Configurações" e a de `/sobra/desvio` dizia "Estratégia".

**Vocabulário de IA genérica é reprovado por máquina.** A lista de frases já é código; composição e
hierarquia continuam sendo revisão humana.

⚠️ **Vocabulário sem consumidor é pior que vocabulário nenhum**, porque parece resolvido enquanto
quatro telas reescrevem o mapa à mão. Ao declarar um vocabulário novo, confira se ele chega a uma
tela. E ao acrescentar uma série, entre nos mapas de classe dos **três** blocos de categoria.

---

## Nível de detalhe e tema

**O nível de detalhe é preferência da conta** (`preferences.detail_level`, servidor), e substituiu a
antiga densidade em 2026-09-26; **tema é do aparelho** (armazenamento local).

**Filtro e recorte vivem na rota**, não em estado local — voltar não perde o recorte, e o mesmo
endereço leva ao mesmo lugar. Em `/patrimonio` o recorte é um só (`?por=valor|classe|setor`) e vale
para a tela inteira: dois controles de recorte a meia tela de distância obrigam a pessoa a decidir
duas vezes a mesma coisa.

---

## Marca

O ícone do aplicativo é **gerado** da cor `brand`, por `cd mobile && python tool/build_icons.py`
(requer Pillow). O CI confere com `--check`.

**O launcher nativo é um segundo passo:** `dart run flutter_launcher_icons`. Sem ele, os ícones ficam
com a cor antiga mesmo com a fundação correta.

---

## O que não é coberto por máquina

Composição, hierarquia e "cheiro de protótipo gerado" continuam sendo revisão humana. Antes de
aceitar uma tela nova como pronta, leia-a procurando sameness de template: blocos genéricos,
igualdade de peso entre coisas de importância diferente, e texto que poderia estar em qualquer
produto.
