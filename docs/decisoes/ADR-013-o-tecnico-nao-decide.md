# ADR-013 — O técnico não decide, e a faixa carrega a própria incerteza

**Status:** SUBSTITUÍDO EM PARTE pela [ADR-014](ADR-014-um-modelo-por-classe.md) — seguem valendo
o técnico como contexto e o falsificador com `kind`; a qualidade, a taxa e o dividendo recorrente
foram refeitos
**Data:** 2026-09-20
**Decidido por:** autor do projeto, que delegou as escolhas desta auditoria

**Nota (2026-09-25):** os campos legados `consensus`, `consensus_methods`, `bazin` e `dcf` saíram da
resposta no commit `f8c2609`; a consequência que os mantinha não vale mais.

## Contexto

A [auditoria de 2026-09-20](../historico/AUDITORIA-DO-VEREDITO-2026-09-20.md) levantou 40 problemas no caminho
do preço ao veredito. Trinta deles eram defeito mecânico ou falta de fundamentação escrita. **Dez
eram decisões de produto** — e esta ADR as registra, porque mudam o que a tela diz sobre quase toda
a base.

## As decisões

### 1 · Tendência e RSI deixam de alterar o veredito

Até aqui, a tendência de baixa rebaixava `BUY` para `HOLD` e `HOLD` para `SELL`, e o RSI podia
promover de volta depois. Dois indicadores derivados **do mesmo preço** reescreviam uma conclusão de
valuation sem que nenhum fundamento tivesse mudado.

Medido em produção em 2026-09-20: **11 de 22 ações** saíam com sinal de venda, seis com margem zero
ou positiva. E havia um caminho em que a razão exibida contradizia a etiqueta na mesma folha —
*"a leitura cai de comprar para manter"* embaixo de **Comprar**.

**Decisão:** análise técnica é **contexto**. Aparece nas razões, nomeada como contexto de preço, e
não muda veredito nem soma confiança. A assimetria entre alta e baixa desaparece junto, porque
nenhuma das duas decide.

A exceção é o ativo **sem nenhum método aplicável**: ali a técnica decide porque não há alternativa,
sai marcada com `basis: trend` e com a confiança mais baixa do sistema.

### 2 · A confiança sai da evidência, não de somas de constantes

Era `0,4` inicial, `+0,2` por ter faixa, `−0,1` por dispersão, `+0,15` por existir técnico. Nenhuma
parcela tinha relação declarada com qualidade de dado.

**Decisão:** a confiança passa a sair de `band_quality`, do número de insumos independentes e dos
anos de histórico de dividendo. Tendência e RSI **não entram** — somar os dois seria contar a mesma
evidência duas vezes. E a interface mostra **a palavra**, não o decimal.

### 3 · A faixa passa a dizer com o que se apoia

Três métodos de ação não são três confirmações: Graham e lucros descontados vivem do mesmo LPA.

**Decisão:** o que conta como evidência é o **insumo econômico distinto** — dividendo, lucro,
patrimônio. `independent_inputs` viaja junto de `consensus_methods`, e `band_quality` resume:
`firme`, `ampla`, `fragil`, `sem_faixa`. Um método só, ou dois métodos lendo o mesmo insumo, saem
`fragil` — inclusive o BDR inteiro.

### 4 · Quem destoa é nomeado, não excluído

A primeira implementação excluía das bordas o método que se afastasse 2× da mediana. **Foi revertida
antes de existir**, porque um teste mostrou o efeito: com o usuário exigindo 12% de yield, o Bazin
cai de propósito, virava "outlier" e era descartado — e a preferência da pessoa sumia do resultado.

**Decisão:** o método que destoa é marcado `destoa_dos_demais`, continua definindo a borda, e derruba
a qualidade para `ampla`. Contra dado contaminado quem defende é a normalização, na origem.

### 5 · A posição dentro da faixa é preservada

Preço rente ao piso e rente ao teto recebiam margem 0 e viravam a mesma leitura.

**Decisão:** `band_position` (0 no piso, 1 no teto) sai na resposta e entra na razão.

### 6 · Falsificador passa a distinguir gatilho de premissa

O invariante do produto diz que *o veredito vem com o que o derrubaria*. O que ele entregava era o
preço em que a etiqueta muda — que reclassifica, não refuta.

**Decisão:** cada falsificador carrega `kind`. `gatilho` é o limiar de preço e a virada de
tendência; `premissa` é a condição econômica que sustenta o preço justo. Duas premissas passam a ser
calculadas:

- **dividendo:** o corte que leva o Bazin ao preço de hoje — `1 − preço ÷ Bazin`. Vale sempre que o
  método participa, e não apenas quando ele é o piso
- **crescimento:** o preço justo **sem crescimento**, quando ele fica abaixo do preço de hoje

### 7 · A taxa de desconto acompanha a Selic

13% fixo, com a Selic acima disso, é exigir da empresa menos do que o título do governo paga.

**Decisão:** `desconto = Selic do dia + 5 pontos de prêmio`, declarado em `EQUITY_RISK_PREMIUM`. Sem
juro conhecido, cai nos 13% de antes. O prêmio continua igual para toda empresa — sem beta nem
estrutura de capital, diferenciá-lo seria inventar.

Como `analysis/` não conhece fonte de dado, a taxa entra por parâmetro: quem a calcula é o serviço.

### 8 · O crescimento acima do teto é limitado, não substituído

Crescimento acima de 25% voltava ao padrão de 8% — uma empresa crescendo 30% era avaliada como se
crescesse 8%, menos que uma crescendo 24%.

**Decisão:** limitar ao teto. E `growth_source` passa a registrar `medido`, `estagnacao`,
`contracao` ou `ausente`, porque deterioração, estagnação e falta de informação não são a mesma
coisa.

### 9 · Dividendo extraordinário é definido pela própria série

A guarda anterior trocava média por mediana quando o *yield implícito* passava de 30%. Medida em
2026-09-20, deixava passar inflação de 2,8×, 4,4× e 5,6× no Bazin — e a entrada dela era um degrau.

**Decisão:** um ano que paga mais de **3× a mediana** dos outros não descreve capacidade recorrente,
e a série passa a ser lida pela mediana. Exige três anos: com menos, não há base para dizer o que é
recorrente.

### 10 · ETF não tem método de preço justo

Bazin estava declarado para ETF e nunca produziu número: ETF de índice não distribui o suficiente.

**Decisão:** ETF não tem método. A distribuição de um ETF é política do fundo, não capacidade de
gerar valor do que ele carrega. A leitura sai da tendência, marcada.

## Consequências

**Ganhos**

- O produto para de contradizer a própria razão na mesma tela
- Quem lê passa a saber **se pode confiar** na faixa, e não só onde ela está
- O que derruba a tese é separado do que troca a etiqueta
- Prejuízo, dado ausente e método inaplicável deixam de ser o mesmo silêncio

**Custos aceitos**

- **O veredito passa a mudar menos.** Ativo caro em tendência de alta continua caro, e ativo barato
  em queda continua barato. Quem lia a tendência como proteção perde essa proteção — ela está na
  tela, como contexto, e não na etiqueta
- **A taxa ligada à Selic derruba todo preço justo por lucros descontados** em juro alto. É o
  resultado correto de uma premissa que estava errada, e vai deixar mais ativo caro
- Mais campos na resposta e mais linhas na tela: `band_quality`, `independent_inputs`,
  `band_position`, `methods[]`, `confidence_label`, `kind`
- `consensus` continua na resposta, agora sem decidir nada

## Referências

- [AUDITORIA-DO-VEREDITO](../historico/AUDITORIA-DO-VEREDITO-2026-09-20.md) — os 40 itens e o que cada um virou
- `backend/app/analysis/fair_price.py` · `backend/app/analysis/decision.py` ·
  `backend/app/analysis/falsifiers.py`
- `test_faixa_carrega_a_incerteza.py`, removido pela ADR-014 · `mobile/test/a_tela_mostra_a_incerteza_test.dart`
- [ADR-011](ADR-011-preco-justo-e-faixa.md), que criou a faixa que esta ADR qualifica
