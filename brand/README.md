# Marca fiance

A marca das partes do fiance com cara pública: o app, a API de dados (`fiance-dados`) e o
laboratório (`fiance-trend`). Mora na raiz porque não é de nenhuma delas: um gerador só desenha as
três e escreve em cada uma o que ela consome.

Um eixo com dois traços de comprimentos diferentes (medir, comparar), a leitura solta à direita e um
chão que corre de borda a borda. O F é o que sobra de um instrumento de medição — não é um F metido
dentro de um quadrado, e é por isso que o desenho continua funcionando para quem não sabe o nome da
empresa.

**O chão fica descolado da haste de propósito.** Encostado, ele vira o terceiro braço e a marca lê
**E**. Se alguém "consertar" esse vão, quebrou a marca.

## A família

O F, a haste e os dois braços são os mesmos nas três partes. Muda o que está em volta, e a cor:

| Parte | Leitura (à direita) | Chão (embaixo) | Cor de destaque |
|---|---|---|---|
| **app** | um quadrado | uma barra | `brand` de `design_tokens.dart` |
| **dados** | grade 2 × 2 — registros | três linhas — uma tabela | `--destaque` do portal |
| **trend** | um quadrado | uma série que oscila e **termina nivelada** | `--destaque` do painel |

A série da trend não sobe de propósito: o laboratório mediu que tendência não antecipou retorno, e
uma marca subindo prometeria o que a pesquisa negou. Nas três, o chão fica descolado da haste.

Cada parte usa a sua cor de destaque e o seu neutro, lidos da folha de estilo dela: o gerador não
guarda paleta própria.

## Estes arquivos são gerados

```bash
python brand/build.py          # escreve; requer Pillow
python brand/build.py --check  # roda no CI, job `brand`
```

Não edite à mão nada do que ele escreve — o `--check` reprova, e com razão: o mesmo desenho vira ícone de
aplicativo Android/iOS e símbolo do produto. Duas cópias da geometria viram duas marcas em duas
semanas. Para mudar a marca, mexa em `GLYPH_EIXO` / `GLYPH_LEITURA` / `GLYPH_CHAO` no gerador.

O gerador escreve estes arquivos:

| Arquivo | O quê | Quem consome |
|---|---|---|
| `mobile/assets/brand/icon.png` | ícone do app | `mobile/pubspec.yaml` → `flutter_launcher_icons.image_path` |
| `mobile/assets/brand/icon_foreground.png` | camada de frente do adaptive icon Android | idem → `adaptive_icon_foreground` |
| `brand/kit/fiance-*.svg` | kit de referência (símbolo, assinatura, logotipo; `fiance-dados-*` e `fiance-trend-*` para as outras partes) | ninguém em runtime — é material de designer |
| `fiance-dados/dadosapi/paginas/portal.html` e `console.html`, entre `<!-- marca -->` e `<!-- favicon -->` | símbolo da dados e o logotipo no cabeçalho, que seguem o tema da página, e o favicon | a API de dados |
| `fiance-trend/frontend/src/Simbolo.tsx` (`Simbolo` e `Logotipo`) e `fiance-trend/frontend/public/favicon.svg` | símbolo da trend e o logotipo na barra lateral, e o favicon | o painel |

`icon.png`/`icon_foreground.png` não são asset empacotado no app: só o comando abaixo os lê, em
build-time. O launcher nativo é um **segundo passo**, e sem ele os ícones do app ficam com o
desenho antigo:

```bash
cd mobile && dart run flutter_launcher_icons
```

**O texto da marca é o logotipo, nas três partes.** As páginas web não escrevem "fiance" em fonte:
escrevem o mesmo logotipo geométrico do app (`AppWordmark`), em `currentColor`, ao lado do símbolo
de cada parte, e o nome da parte vem depois, em caixa alta pequena (`dados`, `console`, `trend`).

## O kit

Em `kit/`.

| Arquivo | Uso |
|---|---|
| `fiance-symbol.svg` · `-dark` · `-mono` | símbolo isolado |
| `fiance-dados-symbol.svg` · `-dark` · `-mono` | símbolo da API de dados |
| `fiance-trend-symbol.svg` · `-dark` · `-mono` | símbolo do laboratório |
| `fiance-lockup-h.svg` · `-dark` · `-mono` | assinatura horizontal (símbolo + logotipo) |
| `fiance-lockup-v.svg` · `-dark` | assinatura vertical |
| `fiance-wordmark.svg` · `-dark` | logotipo isolado |
| `fiance-compact.svg` | selo 120 para app bar, splash e avatar |

Os `-dark` são **transparentes**: trazem as tintas do tema escuro, não um fundo pintado. Os `-mono`
são `currentColor` — uma cor só, herdada de `color:` no elemento pai.

## Cor

Tudo sai de onde a paleta já existe — `mobile/lib/core/design_tokens.dart` para o app, a folha de
estilo de cada página para as outras partes —, e o gerador falha alto se um papel não estiver
declarado nos dois temas. Os valores não são repetidos aqui: o gerador os imprime ao rodar.

| Papel | App | Dados e trend |
|---|---|---|
| eixo e leitura | `brand`; `ink-on-brand` sobre a marca | `--destaque` |
| chão | `ink-3`; sobre a marca, `ink-on-brand` puxado na direção de `brand` | `--tinta-3` no portal, `--suave` no console e no painel |
| logotipo | `ink-1` | o texto da própria página |

O chão é **neutro**, não um azul mais claro: ele é referência, e referência não julga. O chão sobre a
marca é o único valor que não sai direto de um token — é `ink-on-brand` puxado 35% na direção de `brand`,
calculado pelo gerador, porque não existe papel "secundário sobre a marca" na fundação e
inventar um criaria uma cor que nenhuma tela conhece.

Nenhuma cor de **estado** (`favorable`, `attention`, `adverse`, `indeterminate`) nem de **direção**
(`up`/`down`) entra na marca. Elas significam julgamento e aritmética dentro do produto; se o
símbolo usasse uma delas, o verde passaria a querer dizer marca, lucro e veredito favorável ao mesmo
tempo — que é exatamente o defeito que derrubou as classes de direção usadas como estado.

O verde da dados não fere essa regra: é o destaque do portal, e não `favorable` do app, e o símbolo
da dados nunca aparece dentro do app.

## O logotipo

Contorno desenhado, não fonte instalada: os arquivos não dependem de webfont e não quebram em PDF,
e-mail ou slide de terceiro.

A personalidade vem de um detalhe só, repetido: **o braço médio do F, a travessa do A e o braço médio
do E ocupam exatamente a mesma faixa**. É o fio atravessando a palavra. O preço é que a travessa do A
fica um pouco alta e o braço do F um pouco baixo em relação à convenção — é desvio de propósito.

## Regras de aplicação

- **Área de respiro**: a altura da caixa alta do logotipo em volta de toda a assinatura.
- **Tamanho mínimo**: símbolo a 20 px, assinatura horizontal a 120 px de largura. Abaixo disso,
  símbolo sozinho.
- **Fundo escuro** usa os arquivos `-dark`, não o arquivo claro com filtro.
- Não recolorir, não inclinar, não sombrear, não aplicar gradiente, não mexer na entreletra do
  logotipo, não remontar a assinatura empilhando símbolo e palavra à mão.
