# Marca fiance

Pasta global na raiz do repositório: é aqui que web, mobile e o material de referência da marca se
encontram — um lugar só, não uma cópia por plataforma.

Um eixo com dois traços de comprimentos diferentes (medir, comparar), a leitura solta à direita e um
chão que corre de borda a borda. O F é o que sobra de um instrumento de medição — não é um F metido
dentro de um quadrado, e é por isso que o desenho continua funcionando para quem não sabe o nome da
empresa.

**O chão fica descolado da haste de propósito.** Encostado, ele vira o terceiro braço e a marca lê
**E**. Se alguém "consertar" esse vão, quebrou a marca.

## Estes arquivos são gerados

```bash
python design-tokens/build-icons.py          # escreve; requer Pillow
python design-tokens/build-icons.py --check  # roda no CI
```

Não edite nada aqui à mão — o `--check` reprova, e com razão: o mesmo desenho vira favicon, ícone de
aplicativo Android/iOS e símbolo do produto. Duas cópias da geometria viram duas marcas em duas
semanas. Para mudar a marca, mexa em `GLYPH_EIXO` / `GLYPH_LEITURA` / `GLYPH_CHAO` no gerador.

O gerador escreve estes arquivos:

| Arquivo | O quê | Quem consome |
|---|---|---|
| `favicon.svg` | favicon | tem **cópia idêntica** em `web/public/favicon.svg` |
| `favicon-512.png` | favicon grande | tem **cópia idêntica** em `web/public/favicon-512.png` |
| `apple-touch-icon.png` | iOS, web app | tem **cópia idêntica** em `web/public/apple-touch-icon.png` |
| `icon.png` | ícone do app | `mobile/pubspec.yaml` → `flutter_launcher_icons.image_path` lê direto daqui |
| `icon_foreground.png` | camada de frente do adaptive icon Android | idem → `adaptive_icon_foreground`, direto daqui |
| `fiance-*.svg` | kit de referência (símbolo, assinatura, logotipo) | ninguém em runtime — é material de designer |

**Por que o favicon tem cópia e o ícone do app não:** o Angular CLI recusa asset fora do workspace
do projeto (`"must be within the workspace root"`), então `web/angular.json` não pode apontar para
`../assets/brand`. A cópia em `web/public/` é escrita pelo mesmo gerador e conferida byte a byte pelo
`--check` — não é uma segunda fonte, é o mesmo arquivo em dois lugares porque o Angular exige. O
Dart do `flutter_launcher_icons` não tem essa restrição: lê `../assets/brand/icon.png` direto,
sem cópia.

`icon.png`/`icon_foreground.png` não são asset empacotado no app: só o comando abaixo os lê, em
build-time. O launcher nativo é um **segundo passo**, e sem ele os ícones do app ficam com o
desenho antigo:

```bash
cd mobile && dart run flutter_launcher_icons
```

## O kit

| Arquivo | Uso |
|---|---|
| `fiance-symbol.svg` · `-dark` · `-mono` | símbolo isolado |
| `fiance-lockup-h.svg` · `-dark` · `-mono` | assinatura horizontal (símbolo + logotipo) |
| `fiance-lockup-v.svg` · `-dark` | assinatura vertical |
| `fiance-wordmark.svg` · `-dark` | logotipo isolado |
| `fiance-compact.svg` | selo 120 para app bar, splash e avatar |

Os `-dark` são **transparentes**: trazem as tintas do tema escuro, não um fundo pintado. Os `-mono`
são `currentColor` — uma cor só, herdada de `color:` no elemento pai.

## Cor

Tudo sai de `design-tokens/tokens.json`.

| Papel | Claro | Escuro | Sobre a marca |
|---|---|---|---|
| eixo e leitura | `brand #295D7C` | `brand #74ACC9` | `ink-on-brand #FFFFFF` |
| chão | `ink-3 #525B6C` | `ink-3 #A0A6B1` | `#B4C6D1` |
| logotipo | `ink-1 #1F2933` | `ink-1 #E8EAEE` | — |

O chão é **neutro**, não um azul mais claro: ele é referência, e referência não julga. `#B4C6D1` é o
único valor que não sai direto de um token — é `ink-on-brand` puxado 35% na direção de `brand`,
calculado pelo gerador, porque não existe papel "secundário sobre a marca" no `tokens.json` e
inventar um criaria uma cor que nenhuma tela conhece.

Nenhuma cor de **estado** (`favorable`, `attention`, `adverse`, `indeterminate`) nem de **direção**
(`up`/`down`) entra na marca. Elas significam julgamento e aritmética dentro do produto; se o
símbolo usasse uma delas, o verde passaria a querer dizer marca, lucro e veredito favorável ao mesmo
tempo — que é exatamente o defeito que derrubou `.good`/`.warn`.

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
