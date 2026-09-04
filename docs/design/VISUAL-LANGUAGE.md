# Identidade visual

> A estrutura já está resolvida em [WIREFRAMES.md](WIREFRAMES.md). Aqui se decide como o
> fiance **parece** — e o critério é ter identidade própria, não parecer template de dashboard,
> clone de corretora ou protótipo gerado por IA.

## O conceito: **tinta e papel**

O fiance não é um painel de controle. É um **relatório de pesquisa que se atualiza** — a coisa
que um analista sênior te entregaria se ele lesse sua carteira todo dia.

Isso define tudo o que vem abaixo:

| | Painel de controle (o que evitamos) | Relatório de pesquisa (o que somos) |
|---|---|---|
| Estrutura | tudo é card com borda e sombra | fio de cabelo, espaço e um único chão |
| Hierarquia | cor e tamanho de card | tipografia e ritmo vertical |
| Cor | decorativa, onipresente | racionada, só para estado |
| Voz | rótulos de métrica | frases que concluem algo |
| Densidade | uniforme | respira onde se decide, fecha onde se inspeciona |

### As três decisões que criam a identidade

**1. Serifa decide, sans mede.**
Duas famílias com papéis inegociáveis. A **serifa** carrega toda voz conclusiva do produto — o
veredito de saúde ("Carteira saudável"), a frase de resumo do ativo, o diagnóstico de uma queda,
o texto de uma sugestão. A **sans** carrega tudo que é medida — números, tabelas, rótulos,
navegação. O usuário aprende sem ser ensinado: *quando o fiance muda de letra, ele está te
dizendo uma conclusão, não te mostrando um dado.* Nenhum dashboard SaaS faz isso; todo relatório
de research faz.

**2. Estrutura por fio e chão, não por card.**
Cada superfície tem **um** chão. Seções se separam por um fio de 1px e por espaço. O card fica
reservado a **objetos com os quais você pode agir** — uma oportunidade, uma posição, um insight
com botão. Card raro é card que significa algo; a parede de cards de peso igual é justamente o
que faz um produto parecer gerado automaticamente. Consequência direta: sombra sai da estrutura.
Existem exatamente duas sombras no sistema, e as duas são para coisas que flutuam (drawer,
popover).

**3. Cor é racionada para estado, e o julgamento é sempre mais cromático que a aritmética.**
Hoje o produto tem nove famílias de badge mapeando ao mesmo verde/amarelo/vermelho — quando tudo
grita, nada chama. A regra nova tem dois eixos separados:

- **Direção** — o sinal de um número (subiu/caiu). Tinta com **matiz de baixíssima saturação**.
  Legível numa coluna de 30 linhas, recessiva ao lado de qualquer coisa.
- **Estado** — o julgamento do sistema (favorável / atenção / adverso / indeterminado). Matiz de
  saturação média. É o que puxa o olho.

> **Regra de aceite:** em qualquer view, um selo de estado tem de ser mais cromático que
> qualquer número perto dele. Uma queda de 8,4% é aritmética; "queda saudável" é julgamento — e
> é o julgamento que o usuário precisa ver primeiro.

Isso resolve o problema semântico do briefing §21 na raiz: queda de preço deixa de ser pintada
como fracasso, porque a cor forte fica reservada para o que o sistema *concluiu* sobre ela.

**A marca sai do verde.** Verde hoje é simultaneamente cor de marca, de lucro, de botão primário
e de "boa oportunidade" — quatro trabalhos, nenhum bem feito. A marca passa a ser um **azul-
ardósia profundo, de baixa saturação**: credível em finanças, calmo, e deliberadamente longe do
índigo/violeta elétrico que marca produtos de IA. Verde volta a significar uma coisa só:
favorável.

## Chão e tinta

> **Trocado em 2026-09-04, por decisão de produto.** Os neutros eram mornos — papel impresso, o
> desvio deliberado descrito abaixo. Passaram a ser **frios**, derivados da marca: azul como
> identidade, neutros como estrutura. O que esta seção registra agora é a paleta em vigor, e o
> parágrafo final guarda o que a troca custou, porque isso já foi uma queixa de usuário.

**Escuro (padrão)** — grafite azul-ardósia, na mesma família fria da marca. Não é o `#0B0E14`
azul-preto onipresente: é dessaturado, e lê como tinta, não como tela.

**Claro** — near-white frio sobre superfície branca. Os neutros saem da mesma família azul da
marca, de modo que nenhum cinza da interface briga com `brand` por temperatura.

| Papel | Token |
|---|---|
| chão da página | `ground-0` |
| superfície | `ground-1` |
| superfície elevada / campo | `ground-2` |
| fio | `hairline` |
| fio forte | `hairline-strong` |
| tinta primária | `ink-1` |
| tinta secundária | `ink-2` |
| tinta terciária | `ink-3` |

**Os valores não estão escritos aqui de propósito.** Eles vivem em
`design-tokens/tokens.json`, e uma cópia neste arquivo seria uma segunda verdade que apodrece
calada — a tabela anterior listava `#7A847F` para a tinta terciária clara, um valor que o produto
nunca teve. O que este documento decide é o **papel**; o valor é do gerador.

**O custo conhecido da paleta fria.** O chão da página e a superfície voltaram a ficar perto:
`ground-0` e `ground-1` estão a 1,06:1 de contraste. Isso já aconteceu com `#FAF8F5` sob branco e
produziu uma queixa registrada — *"o plano de fundo se confunde com os componentes"*: um card
branco não tem de onde subir, e a página lê como uma superfície só. Duas coisas seguram a
hierarquia hoje, e é por isso que a troca não a derrubou: a estrutura da página nasce de **fio e
espaço** (`.fi-block`), não de card, e o card sobrevivente tem `hairline` desenhando a borda. Se a
separação voltar a incomodar, o conserto é uma linha — aprofundar `ground-0` em `tokens.json` —,
não um redesenho.

Já as **tintas** não são as do briefing: `#667085` como secundária dá 4,97:1 e `#98A2B3` como
legenda dá 2,58:1, contra pisos de 8:1 e 6:1. Foram derivadas na mesma família fria até cumprirem
o piso. Contraste é verificado, não recomendado, e afrouxar o limiar não estava em discussão.

Sem gradiente. Os dois `radial-gradient` do fundo atual saem — não carregam informação e são
metade do "AI dashboard aesthetic".

## Cor semântica

| Papel | Uso exclusivo | Token |
|---|---|---|
| **marca / interativo** | logo, ação primária, foco, nav ativa, linha de referência (CDI, meta, benchmark) | `brand` |
| **estado favorável** | veredito interessante, score forte, queda saudável, meta atingida | `state-favorable` |
| **estado atenção** | merece revisão, concentração alta, vencimento próximo | `state-attention` |
| **estado adverso** | evitar, queda estrutural, sinal de venda | `state-adverse` |
| **estado indeterminado** | Sem dado, método não aplicável, sem histórico | `state-indeterminate` |
| direção ↑ (aritmética) | número que subiu, **só em coluna de tabela** | `direction-up` |
| direção ↓ (aritmética) | número que caiu, **só em coluna de tabela** | `direction-down` |

Cada estado tem um **chão** correspondente — `state-*-surface` —, que é o fundo de um aviso ou de
um selo, nunca a tinta dele. A quantidade de pigmento de cada um sai de uma busca por contraste,
não do olho: é a maior que ainda deixa legíveis as duas coisas que ficam em cima, o rótulo na cor
do estado e o corpo em tinta primária.

### O piso de contraste

A AA é o chão legal, não o alvo. `design-tokens/check-contrast.mjs` cobra uma folga declarada
acima dela, e a escada de tinta é explícita — corpo, secundária e legenda precisam continuar
distinguíveis **entre si**, senão hierarquia vira uniformidade:

| Papel | Piso | Por quê |
|---|---|---|
| `ink-2` | 8:1 | texto secundário é lido, não olhado |
| `ink-3` | 6:1 | legenda é texto pequeno, e a regra para texto pequeno é mais rígida |
| `brand`, `state-*`, `direction-*` | 6:1 | carregam rótulo |
| `series-*` | 4,5:1 | forma no gráfico, **e texto no chip de categoria** |
| tinta sobre `*-surface` | 5,5:1 | o rótulo do selo |
| `ink-1` sobre `*-surface` | 6:1 | o corpo do aviso |

A linha das séries é a que menos parece óbvia e mais custou: enquanto série só desenhava barra e
linha, 3:1 bastava, porque forma não é texto. No dia em que a mesma cor passou a escrever o rótulo
do chip de categoria, o requisito mudou e nada percebeu — `series-other` escrevia a 3,1:1 sobre o
próprio chip. O verificador agora conhece esse par.

Duas coisas que essa tabela decide de propósito:

- **"Indeterminado" é um estado de primeira classe, com cor própria.** O backend já distingue
  `data_completeness` baixo de nota baixa; a paleta passa a distinguir também. Um score cinza
  quer dizer "não sei", nunca "ruim".
- **Marca e informação são a mesma cor.** Quando a interface desenha a linha do CDI, da meta ou
  do benchmark, é o sistema falando — e o sistema tem uma cor.

### Cor nunca é o único canal

Todo estado carrega **três** marcas: cor + forma/ícone + rótulo em texto. Um selo de estado sem
texto não passa na revisão de componente. Ninguém precisa distinguir verde de vermelho para usar
o fiance.

### Séries de gráfico

Seis categóricas + "Outros" cinza, no lugar das onze atuais. Papéis fixos em gráficos de
comparação: **carteira** = tinta primária (a linha do usuário é a mais forte), **benchmark** =
marca, **meta** = marca tracejada. Acima de seis categorias, agrupar em "Outros" — a sétima cor
distinguível não existe.

## Tipografia

| | Família | Papel |
|---|---|---|
| Sans | **Inter** (já carregada) | números, tabelas, rótulos, navegação, corpo |
| Serifa | **Source Serif 4** | veredito, diagnóstico, resumo de ativo, título de insight |

Source Serif 4 está no Google Fonts (web) e no `google_fonts` do Flutter — as duas plataformas
alcançam a mesma família, o que é pré-requisito de identidade compartilhada.

**Números têm tratamento próprio, e isso é obrigatório:**

```
font-variant-numeric: tabular-nums slashed-zero;
```

Zero ocorrência disso existe hoje no produto — é o defeito tipográfico mais visível de um app de
investimento, porque faz toda coluna de preço desalinhar. Passa a ser aplicado por token em
preço, percentual, patrimônio, score, taxa e data, nas três plataformas.

### Escala com papel semântico

Tamanho não se escolhe: se escolhe o papel.

| Token | px/lh | Peso | Família | Onde |
|---|---|---|---|---|
| `money-xl` | 44/48 | 600 | sans tab. | patrimônio em Hoje |
| `money-lg` | 32/36 | 600 | sans tab. | patrimônio em Carteira, preço em Ativo |
| `metric` | 22/28 | 600 | sans tab. | número de destaque de bloco |
| `metric-sm` | 16/22 | 600 | sans tab. | número em tabela e lista |
| `verdict` | 20/28 | 400 | **serifa** | veredito de saúde, resumo do ativo |
| `verdict-sm` | 16/24 | 400 | **serifa** | diagnóstico, texto de sugestão |
| `title` | 15/20 | 600 | sans | título de seção |
| `eyebrow` | 11/14 | 600 | sans, +8% tracking, caixa alta | rótulo de seção ("O QUE MUDOU") |
| `body` | 14/21 | 400 | sans | corpo |
| `label` | 13/18 | 500 | sans | rótulo de campo, cabeçalho de coluna |
| `caption` | 12/16 | 400 | sans | proveniência, nota, limitação |
| `ticker` | 14/18 | 600 | sans, +4% tracking | ticker |

Base do `body` vai de **15px para 16px**. Mínimo absoluto de texto: 12px — `text-[10px]` e
`text-[11px]` (hoje em rótulos e na bottom nav) saem, exceto em selo que já tem redundância
textual ao lado.

**Reconhecível em menos de um segundo:** só existe **um** `money-xl` por tela. Se dois números
disputam o mesmo tamanho, a tela não decidiu qual é a resposta.

## Forma, espaço e densidade

- **Raio:** 4 (selo, campo) · 8 (card, botão) · 12 (drawer, sheet) · pill. O raio único de 14px
  sai — raio grande e uniforme lê como app de consumo, não como instrumento.
- **Espaço:** escala de 4px. O ritmo vertical entre seções (24/32px) é o que substitui a borda
  de card como separador.
- **Densidade:** dois modos por atributo (`comfortable` 48px de linha / `compact` 36px),
  governados pela preferência `detail_level` e pelo controle local de tabela. É a alavanca que
  atende os três perfis de senioridade sem construir três produtos.
- **Sombra:** duas, e só para o que flutua — `drawer` e `popover`. Estrutura nunca usa sombra.

## Movimento

Movimento existe para explicar uma mudança de estado, nunca para decorar.

| Token | Duração | Onde |
|---|---|---|
| `fast` | 120ms | hover, foco, selo |
| `base` | 180ms | acordeão, troca de tab, troca de filtro |
| `slow` | 240ms | drawer, bottom sheet |

Entrada `cubic-bezier(0.2, 0, 0, 1)`, saída `cubic-bezier(0.4, 0, 1, 1)`.
Números **não** animam contagem — em produto financeiro, número que corre parece número
instável. `prefers-reduced-motion` desliga tudo menos opacidade.

## O elemento-assinatura: **a régua**

O score é a marca visual do fiance, e não pode ser "87/100" nem um gauge de dashboard.

É uma **régua** — um instrumento de medida, com zonas nomeadas e um valor marcado com precisão:

```
        evitar        neutro       boa        forte
  ├───────────┼────────────┼───────────┼──────────────┤
  0          40           60          75            100
                                          ▼
                                         87  Forte
```

- Zonas desenhadas com **peso de tinta diferente**, não com quatro cores berrantes — a cor
  entra só na zona onde o valor caiu.
- O valor é uma marca fina e precisa (não uma bolha), com o número em cifras tabulares acima e o
  rótulo da banda ao lado.
- Os limiares 40/60/75 são os do `score_ruler.py` — a régua é uma leitura da regra existente,
  não uma nova régua.
- **`data_completeness` baixo:** a régua fica tracejada e cinza, o número sai, e o rótulo é
  "sem dado". A ausência de dado deixa de ser codificada como número baixo.

Quatro tamanhos: `inline` (16px, dentro de texto) · `list` (24px, linha de tabela) ·
`card` (40px) · `page` (64px, cabeçalho do ativo).

**A mesma mecânica se reutiliza** em tudo que é "um valor numa escala com zonas nomeadas":
margem de segurança, gap de alocação, progresso de meta, saúde da carteira. Um instrumento,
quatro leituras — é isso que faz o produto parecer projetado em vez de montado.

## Ícones

Lucide (web) e Material Symbols Outlined (mobile), traço 1,5px, tamanho 16/18/20 apenas.
Regras: **nunca** ícone ao lado de todo rótulo; ícone só quando substitui palavra (ação em
barra de ferramentas) ou marca estado com redundância textual. Hoje quase todo `<h2>` do produto
carrega um ícone decorativo — isso sai, e é grande parte do que faz as telas parecerem
"template".

## Teste de identidade

O sistema passa se, num print sem logo:

1. dá para dizer o que é o produto pela **tipografia**, não pela cor;
2. existe **um** número claramente mais importante que os outros;
3. a cor forte aparece em **menos de 5%** da área da tela;
4. não há dois cards vizinhos de peso visual idêntico;
5. o veredito em serifa é a primeira frase que o olho lê;
6. em escala de cinza, todo estado continua legível.
