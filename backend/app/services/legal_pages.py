from __future__ import annotations

from app import affirmation

VERSAO = "11 de setembro de 2026"

_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 17px;
  line-height: 1.65;
}
main { max-width: 70ch; margin: 0 auto; padding: 3rem 1.25rem 5rem; }
h1 { font-size: 1.9rem; line-height: 1.2; margin: 0 0 .5rem; letter-spacing: -.01em; }
h2 { font-size: 1.15rem; line-height: 1.3; margin: 0 0 .75rem; }
p, ul { margin: 0 0 1rem; }
ul { padding-left: 1.25rem; }
li { margin-bottom: .5rem; }
a { color: inherit; text-underline-offset: .2em; }
a:focus-visible { outline: 2px solid currentColor; outline-offset: 3px; border-radius: 2px; }
.pergunta { font-size: 1.05rem; opacity: .8; margin: 0 0 .25rem; }
.versao { font-size: .85rem; opacity: .65; margin: 0 0 2.5rem; }
section { padding-top: 1.75rem; margin-top: 1.75rem;
  border-top: 1px solid color-mix(in srgb, currentColor 15%, transparent); }
.aviso { padding: 1rem 1.1rem; margin: 2rem 0; border-radius: 4px;
  border-left: 3px solid currentColor;
  background: color-mix(in srgb, currentColor 6%, transparent); }
.aviso p:last-child { margin-bottom: 0; }
.rotulo { font-weight: 600; margin-bottom: .35rem; }
table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: .95rem; }
th, td { text-align: left; vertical-align: top; padding: .6rem .75rem .6rem 0;
  border-bottom: 1px solid color-mix(in srgb, currentColor 15%, transparent); }
th { font-weight: 600; }
.rodape { margin-top: 3rem; font-size: .95rem; opacity: .8; }
.tabela-rolavel { overflow-x: auto; }
@media (max-width: 460px) { body { font-size: 16px; } main { padding: 2rem 1rem 4rem; } }
"""

_MINUTA = """
<div class="aviso">
  <p class="rotulo">Minuta — ainda não revisada por advogado</p>
  <p>Este texto descreve com honestidade como o fiance funciona hoje, mas ainda não passou por
  revisão jurídica. Enquanto este aviso estiver aqui, ele vale como declaração de transparência,
  não como instrumento contratual definitivo.</p>
</div>
"""


def _pagina(titulo: str, pergunta: str, corpo: str, *, com_versao: bool = True) -> str:
    versao = f'<p class="versao">Versão de {VERSAO}.</p>' if com_versao else ""
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} — fiance</title>
<style>{_CSS}</style>
</head>
<body>
<main>
<h1>{titulo}</h1>
<p class="pergunta">{pergunta}</p>
{versao}
{_MINUTA}
{corpo}
</main>
</body>
</html>
"""


_TERMOS_CORPO = """
<section>
<h2>1. O que o fiance é</h2>
<p>O fiance é uma <strong>ferramenta de análise de investimentos</strong>. Ele lê dados públicos de
mercado, aplica critérios objetivos e mostra o resultado com a metodologia à vista: de onde veio
cada número, que premissa ele assume e o que o derrubaria.</p>
<p>O fiance <strong>não é</strong> consultoria de valores mobiliários, não é análise de valores
mobiliários prestada por analista credenciado, não é corretora, não é administrador de carteira e
não custodia dinheiro nem ativo de ninguém. Nada aqui é recomendação personalizada de compra ou
venda. O que está publicado sobre essa fronteira está em
<a href="/aviso-cvm">Aviso CVM</a>.</p>
</section>

<section>
<h2>2. Não há promessa de resultado</h2>
<p><strong>Não há garantia de retorno.</strong> Toda projeção que o fiance mostra é uma faixa de
cenários, não uma previsão, e rentabilidade passada não indica rentabilidade futura. As decisões de
investimento são suas, e o risco delas é seu.</p>
<p>Os cálculos podem conter erro. Quando encontramos um, ou consertamos ou escondemos o número com
um aviso — não deixamos número errado com cara de número certo.</p>
</section>

<section>
<h2>3. O dado que você lança é seu</h2>
<p>Você é responsável pelo que lança: posições, preços, datas, extratos importados. O fiance calcula
sobre o que recebe — carteira incompleta ou preço médio errado produz análise errada, e ele não tem
como saber disso sozinho.</p>
<p>A qualquer momento você pode <strong>exportar tudo</strong> ou <strong>apagar a conta
inteira</strong>, no aplicativo, em Você → Conta. Nenhuma das duas coisas fica atrás de plano pago,
e a exclusão remove o dado de fato — não o marca como oculto.</p>
</section>

<section>
<h2>4. Apuração de imposto</h2>
<p>O fiance apura ganho de capital em renda variável por mês e por categoria, a partir do que você
lançou no livro-razão, e mostra o cálculo. É uma <strong>estimativa de apoio</strong>: ela não
substitui a apuração oficial, não emite DARF, não cobre day trade e não considera a sua situação
fiscal completa. Confira com seu contador antes de declarar.</p>
</section>

<section>
<h2>5. Fontes de dado de mercado</h2>
<p>Cotação, indicador fundamentalista e provento vêm da BRAPI; CDI, Selic e IPCA vêm do Banco
Central (SGS). O fiance não controla essas fontes. Quando uma delas cai ou devolve número
implausível, o produto avisa a origem do dado que está mostrando — inclusive quando é cache vencido
ou estimativa.</p>
</section>

<section>
<h2>6. Uso aceitável</h2>
<p>A conta é pessoal e intransferível. Não é permitido raspar o serviço em escala, revender o
acesso, contornar limites de uso, nem apresentar a análise do fiance como recomendação profissional
sua a terceiros.</p>
</section>

<section>
<h2>7. Disponibilidade e mudanças</h2>
<p>O fiance é distribuído como aplicativo para celular. O serviço é oferecido no estado em que se
encontra, sem garantia de disponibilidade contínua. Podemos mudar, suspender ou encerrar
funcionalidades. Quando a mudança afetar o que você já lançou, avisamos antes e mantemos a
exportação funcionando.</p>
</section>

<section>
<h2>8. Lei aplicável e contato</h2>
<p>Estes termos são regidos pela lei brasileira. Dúvidas, pedidos de exclusão e exercício de
direitos previstos na LGPD: veja o canal indicado na
<a href="/privacidade">Política de Privacidade</a>.</p>
</section>
"""


_PRIVACIDADE_CORPO = """
<section>
<h2>O resumo, antes do detalhe</h2>
<p>Sua carteira não sai do produto. Nenhuma fonte externa recebe quanto você tem, quanto pagou ou
quanto ganhou — a BRAPI recebe apenas o código do papel, o mesmo que qualquer pessoa digita numa
busca. Você pode exportar tudo e apagar a conta quando quiser, sem precisar falar com ninguém e sem
plano pago.</p>
</section>

<section>
<h2>Que dado é coletado, e para quê</h2>
<div class="tabela-rolavel">
<table>
<thead><tr><th scope="col">Dado</th><th scope="col">Finalidade</th>
<th scope="col">Base legal (LGPD)</th></tr></thead>
<tbody>
<tr><td>Nome, e-mail e foto da conta Google</td><td>Identificar você e manter a sessão</td>
<td>Execução de contrato (art. 7º, V)</td></tr>
<tr><td>Posições, renda fixa, lançamentos, metas e preferências</td>
<td>Calcular a análise que você pediu</td><td>Execução de contrato (art. 7º, V)</td></tr>
<tr><td>Eventos de uso (vocabulário fechado, sem ticker e sem valor)</td>
<td>Entender que telas funcionam e onde o produto trava</td>
<td>Legítimo interesse (art. 7º, IX)</td></tr>
<tr><td>Token de notificação do aparelho</td><td>Enviar alerta que você configurou</td>
<td>Consentimento (art. 7º, I)</td></tr>
<tr><td>Log técnico com identificador de requisição e IP</td>
<td>Segurança, limite de uso e diagnóstico de erro</td>
<td>Legítimo interesse (art. 7º, IX)</td></tr>
</tbody>
</table>
</div>
<p>O dicionário de eventos é fechado no servidor: um evento que carregue ticker ou valor é
<strong>recusado</strong>, não filtrado depois. Isso é código, não promessa.</p>
</section>

<section>
<h2>Com quem o dado é compartilhado</h2>
<div class="tabela-rolavel">
<table>
<thead><tr><th scope="col">Terceiro</th><th scope="col">O que recebe</th>
<th scope="col">O que não recebe</th></tr></thead>
<tbody>
<tr><td>Google (entrar com Google)</td>
<td>A própria autenticação; nome, e-mail e foto voltam de lá</td><td>Nada da sua carteira</td></tr>
<tr><td>BRAPI (cotação e fundamento)</td><td>O código do papel consultado</td>
<td>Quem consultou, quanto tem, quanto pagou</td></tr>
<tr><td>Banco Central — SGS (CDI, Selic, IPCA)</td><td>Nada seu: a consulta é de série pública</td>
<td>Tudo</td></tr>
<tr><td>Firebase (notificação)</td><td>O token do aparelho e o texto do alerta</td>
<td>Sua carteira</td></tr>
<tr><td>Google Play e App Store</td>
<td>A distribuição do aplicativo e, quando houver cobrança, o pagamento</td>
<td>Sua carteira</td></tr>
<tr><td>Provedor de hospedagem e de banco</td>
<td>Armazena o dado em nosso nome, como operador</td>
<td>Não usa o dado para finalidade própria</td></tr>
</tbody>
</table>
</div>
<p>Quando a cobrança for ligada, o provedor de pagamento receberá identidade e dado de cobrança —
nunca dado de carteira. Esta seção será atualizada nomeando o provedor <em>antes</em> de qualquer
cobrança existir.</p>
<p><strong>Não vendemos dado pessoal</strong> e não o usamos para publicidade.</p>
</section>

<section>
<h2>Por quanto tempo o dado fica</h2>
<ul>
<li><strong>Enquanto a conta existir</strong>: carteira, lançamentos, metas e preferências.</li>
<li><strong>Ao apagar a conta</strong>: tudo isso é removido de imediato. Fica apenas um registro
anonimizado de que aquela conta existiu e foi apagada — sem nome, sem e-mail e sem foto —, para que
o mesmo identificador não seja reaproveitado.</li>
<li><strong>Log técnico</strong>: mantido pelo prazo necessário à segurança e diagnóstico.</li>
</ul>
</section>

<section>
<h2>Seus direitos, e como exercê-los</h2>
<p>A LGPD garante confirmação, acesso, correção, portabilidade, eliminação e revogação de
consentimento. Dois deles já estão implementados como botão dentro do aplicativo, sem
intermediário:</p>
<ul>
<li><strong>Exportar tudo</strong> — Você → Conta devolve um arquivo com todo o dado vinculado a
você.</li>
<li><strong>Apagar a conta</strong> — Você → Conta remove o dado, sem passar por atendimento e sem
cerca de plano. É o mesmo botão que atende a um pedido de exclusão feito por qualquer canal.</li>
</ul>
<p>Um canal de atendimento para os demais direitos, e para falar com o encarregado pelo tratamento
de dados, será publicado aqui antes de o aplicativo ser distribuído nas lojas. Enquanto isso, a
exclusão e a exportação já funcionam sem depender de atendimento.</p>
</section>

<section>
<h2>Segurança</h2>
<p>O acesso é isolado por conta na camada de dados: uma consulta sem dono não devolve carteira de
ninguém. A sessão tem prazo curto e a renovação é de uso único — reaproveitar uma renovação derruba
a sessão em todos os aparelhos. Segredos e dado sensível são removidos do log antes de ele ser
gravado.</p>
</section>

<section>
<h2>Mudanças nesta política</h2>
<p>Quando ela mudar de forma relevante, a data no topo muda e avisamos dentro do produto antes da
mudança valer. Veja também os <a href="/termos">Termos de Uso</a> e o
<a href="/aviso-cvm">Aviso CVM</a>.</p>
</section>
"""


_NOMES_DO_NIVEL = {1: "descritivo", 2: "analítico", 3: "prescritivo"}


def _cvm_corpo() -> str:
    modo = affirmation.current()
    nome = _NOMES_DO_NIVEL.get(int(modo.level), "—")

    return f"""
<section>
<h2>O que o fiance não faz</h2>
<p>As Resoluções CVM 19 e 20 tratam de <strong>análise</strong> e de <strong>consultoria</strong> de
valores mobiliários — atividades que exigem registro e que envolvem recomendação individualizada,
feita para a situação de uma pessoa específica.</p>
<p>O fiance não presta nenhuma das duas. Ele aplica critérios objetivos e públicos sobre dados
públicos e mostra o resultado com a conta à vista. Ninguém aqui olha a sua situação e diz o que você
deveria comprar.</p>
</section>

<section>
<h2>O quanto o produto afirma é configuração, não opinião</h2>
<p>O nível de afirmação do fiance é um ajuste explícito do sistema, com três posturas. Ele não varia
por tela nem por usuário:</p>
<div class="tabela-rolavel">
<table>
<thead><tr><th scope="col">Nível</th><th scope="col">O que o produto diz</th></tr></thead>
<tbody>
<tr><td>1 · Descritivo</td><td>Descreve a sua carteira. Não avalia ativo nem sugere operação.</td></tr>
<tr><td>2 · Analítico</td><td>Avalia ativo por critério objetivo, com a metodologia à vista, e não
diz quanto comprar de quê.</td></tr>
<tr><td>3 · Prescritivo</td><td>Acrescentaria valor por ativo — quanto aportar em qual papel.</td></tr>
</tbody>
</table>
</div>
<div class="aviso">
<p class="rotulo">Postura em vigor agora: nível {int(modo.level)} — {nome}</p>
<p>{modo.disclaimer}</p>
</div>
<p>O nível 3 existe no código e <strong>está desligado</strong> até haver parecer jurídico que o
autorize. Enquanto isso, o valor por ativo simplesmente não sai do servidor — não é escondido na
tela, é ausente da resposta.</p>
</section>

<section>
<h2>O que continua sendo seu</h2>
<p>A decisão de investir, e o risco dela. <strong>Não há garantia de retorno</strong>, e nada no
fiance considera a sua situação financeira, seus objetivos ou a sua tolerância a risco de forma
individualizada. Para recomendação personalizada, procure profissional habilitado e registrado na
CVM.</p>
</section>

<section>
<h2>Orientação sobre dívida é outra coisa</h2>
<p>Quando o fiance compara o custo de uma dívida com o que a sua carteira rende, ele está fazendo
aritmética de taxa de juros — dívida não é valor mobiliário, e essa comparação não é recomendação de
investimento. Ainda assim, a decisão é sua.</p>
</section>

<p class="rodape">Veja também os <a href="/termos">Termos de Uso</a> e a
<a href="/privacidade">Política de Privacidade</a>.</p>
"""


def termos() -> str:
    return _pagina(
        "Termos de Uso",
        "O que o fiance é, o que ele não é, e o que fica sendo seu.",
        _TERMOS_CORPO,
    )


def privacidade() -> str:
    return _pagina(
        "Política de Privacidade",
        "Que dado o fiance guarda, com quem compartilha e como você o leva embora.",
        _PRIVACIDADE_CORPO,
    )


def aviso_cvm() -> str:
    return _pagina(
        "Aviso CVM",
        "A fronteira entre analisar e recomendar, e de que lado o fiance está.",
        _cvm_corpo(),
        com_versao=False,
    )
