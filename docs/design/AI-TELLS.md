# Não parecer gerado por IA

> [VISUAL-LANGUAGE.md](VISUAL-LANGUAGE.md) já assume isso como critério de aceite desde a primeira
> linha: "ter identidade própria, não parecer... protótipo gerado por IA". Aquele documento resolve
> a parte de **cor, forma e tipografia** — sem gradiente, sem parede de card, sem azul-índigo de
> produto de IA, sombra só para o que flutua. Isto aqui é o resto: **texto, composição e
> conteúdo de exemplo**, que uma paleta certa não corrige sozinha. Uma tela pode seguir cada token
> do sistema e ainda parecer gerada — porque "parece gerado" é, na maioria das vezes, um problema de
> **redação e composição**, não de estilo.
>
> Isto não é contra construir com IA — o projeto inteiro é. É contra o **subproduto** de gerar
> interface rápido sem o julgamento editorial de cortar o genérico. O sintoma mais comum não é
> "ficou feio", é "ficou plausível demais": nada está errado, e nada é **deste** produto.

---

## Voz e texto

**Sem emoji em rótulo, título ou corpo de texto.** Ícone é o Lucide já registrado, usado como
informação — não decoração de entusiasmo. 🎉 e ✨ ao lado de um número são o tell mais reconhecível
de texto gerado, e a régua de "serifa decide, sans mede" já não deixa espaço para eles: uma
conclusão do sistema é séria, nunca festiva.

**Sem ponto de exclamação, e sem comemorar o usuário.** "Parabéns, sua carteira está indo bem!" é
voz de app de gamification, não de relatório de research — e contradiz o próprio conceito de "tinta
e papel". A frase equivalente correta é descritiva: "Carteira saudável, sem desvio relevante da
meta."

**Banir o vocabulário de marketing genérico.** Nenhuma destas palavras entra em copy de produto:
*revolucionário, poderoso, simples e poderoso, leve seu dinheiro para o próximo nível,
transforme sua relação com o dinheiro, tudo em um só lugar* (a não ser que seja literalmente
verdade e específico). O produto já tem uma régua melhor para isto: se não existe nada que tornaria
a frase **errada**, ela é decoração, não informação. É a mesma exigência que
`analysis/falsifiers.py` aplica ao veredito de um ativo; vale para o texto da interface também.

**Banir a fala de assistente.** "Nós entendemos que organizar as finanças pode ser desafiador",
"É importante notar que", "Fico feliz em ajudar com isso", "Se você quiser, posso..." — nenhuma
frase da interface fala **sobre si mesma** ou hedgeia. Escreve-se a conclusão direto: "Sua sobra
este mês é R$ 640."

**O produto não é um chatbot, mesmo na parte educativa.** O papel de educador que a nova direção
assume (ver [DIRECAO_PRODUTO.md](../produto/DIRECAO.md)) não vira uma persona
conversacional com saudação ("Como posso te ajudar hoje?") e chips de sugestão. Educação é
explicação contextual no momento em que o número aparece — `<app-provenance>`,
`<app-help-tooltip>`, o texto de "Como calculamos" — nunca uma janela de chat com um avatar
simpático. Um app de dinheiro que parece estar **conversando com você** é o tell mais específico
deste produto, porque é exatamente o que um "assistente financeiro de IA" genérico faz.

---

## Composição

**Banir o hero de SaaS genérico.** Pill de badge + título gigante centralizado com gradiente +
dois botões de CTA + fileira de logos de "confiado por" é o template mais reconhecível de landing
page gerada — e a [Fase 1 do roadmap](../produto/ROADMAP.md#fase-1--validação-antes-de-qualquer-código-de-tela)
inclui construir uma. Regra: **um ponto de vista específico** substitui o template — a frase do
Hoje/mês-corrente que já existe no produto ("sua sobra este mês é R$ X") tem mais força que
qualquer headline genérica, e é verdadeira, o que uma headline de marketing raramente é.

**Banir a grade de três colunas ícone + título em negrito + parágrafo de uma frase.** É a mesma
doença da "grade de KPI" que o CLAUDE.md já reprova para número — aplicada a texto em vez de
métrica. Três blocos de peso igual, comprimento igual, tom igual, é o formato que se produz quando
não há hierarquia real entre os pontos. Se três coisas importam de verdade, elas quase nunca têm o
mesmo peso — deixe a mais importante ocupar mais espaço e vir primeiro.

**Desconfiar de simetria perfeita.** Conteúdo real é desigual: uma explicação precisa de três
linhas, outra de uma. Forçar todos os blocos a caber no mesmo espaço produz texto genérico
esticado até bater a margem, ou cortado até virar vago. Se o layout está pedindo texto do mesmo
tamanho em todo lugar, o layout é que está errado, não o conteúdo.

**Ilustração de estado vazio não é boneco genérico flutuando com notebook.** O contrato já manda:
*"onde o dado falta, o entregável é um estado, não um número"* — isso é sobre conteúdo. Sobre
forma: se o estado vazio leva ilustração, ela carrega significado específico do produto (o ícone
já registrado da categoria vazia, por exemplo), nunca um SVG de banco de imagem que poderia estar
em qualquer produto SaaS do mundo.

---

## Dado de exemplo

**Toda tela em revisão usa dado real ou realista, nunca com cara de placeholder.** "Ativo 1",
"Categoria A", "João da Silva", valores redondos demais (R$ 1.000,00, R$ 500,00 em toda linha) —
isso é o segundo tell mais rápido de reconhecer, porque ninguém revisa dado real e o vê assim.
Usar ticker de B3 de verdade, categoria do vocabulário gerado (nunca "Categoria X"), e valor com a
imprecisão de dinheiro de verdade (R$ 1.847,32, não R$ 1.850,00).

---

## Processo — o que isto muda ao pedir uma tela nova

- **Ancorar em algo que já existe antes de gerar.** Pedir "uma tela de X" sem referência gera a
  partir do genérico. Apontar a tela vizinha mais parecida (do [WIREFRAMES.md](WIREFRAMES.md) ou já
  construída) como ponto de partida produz uma tela que parece **deste** produto, não de um
  produto qualquer.
- **Cortar antes de aceitar.** Ao revisar uma tela gerada, o primeiro passe não é "está bonito?" —
  é "alguma frase daqui poderia estar em qualquer outro app financeiro sem mudar uma palavra?".
  Se sim, ela é decoração e sai.
- **Comparar com um concorrente real de vez em quando**, lado a lado (Status Invest, Investidor10,
  o próprio produto atual) — "sameness de template" é mais fácil de ver em comparação do que
  olhando uma tela sozinha.
- **A lista de frases proibidas é máquina; o resto não.** As frases nomeadas acima, a persona de
  assistente e emoji em texto de tela são cobrados por `test/lint_ui_test.dart` (regra
  *Vocabulário de IA*), varrendo só literal de string. Isso entrou depois de o
  documento existir por meses afirmando que nada aqui era checável — e enquanto ele afirmava, as
  duas primeiras telas do aplicativo abriam com "tudo em um só assistente", que são dois itens
  desta lista numa frase de dez palavras.
- **Composição, simetria e "plausível demais" continuam sendo revisão humana**, e é por isso que
  vale conferir **antes** de pedir a tela como pronta, não depois. Máquina não julga hierarquia.
