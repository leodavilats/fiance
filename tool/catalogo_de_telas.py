"""Monta o catálogo das telas do aplicativo, para revisão por pessoa ou por IA.

Uso:
    python tool/catalogo_de_telas.py            # escreve build/catalogo/
    python tool/catalogo_de_telas.py --stdout   # imprime o Markdown
    python tool/catalogo_de_telas.py --check    # confere que nada saiu do radar

Lê os fontes em mobile/lib/, não o aplicativo em execução: os textos de interface são literais no
código, e isso evita depender de emulador, de rede e da fonte que o ambiente de teste não carrega.
O que ele NÃO enxerga está declarado em "pontos cegos", no fim do relatório — nenhum leitor deve
supor que o silêncio aqui significa ausência na tela.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
LIB = RAIZ / "mobile" / "lib"
SAIDA = RAIZ / "build" / "catalogo"

_ROTA_PAI = re.compile(r"path:\s*'(/[\w/:-]*)'")
_ROTA_FILHA = re.compile(r"path:\s*'([\w:-]+)'")
_REDIRECT = re.compile(r"path:\s*'([^']+)',\s*redirect:\s*\(_,\s*_\)\s*=>\s*'([^']+)'")
_BUILDER = re.compile(r"builder:\s*\(context,\s*state\)\s*=>\s*(?:const\s+)?(\w+)")
_FERRAMENTA = re.compile(
    r"ToolScreen\((?:[^()]|\([^()]*\))*?child:\s*(?:const\s+)?(\w+)",
    re.DOTALL,
)
_FERRAMENTA_TITULO = re.compile(r"ToolScreen\((?:[^()]|\([^()]*\))*?title:\s*'([^']+)'", re.DOTALL)
_FERRAMENTA_PERGUNTA = re.compile(
    r"ToolScreen\((?:[^()]|\([^()]*\))*?question:\s*'([^']+)'", re.DOTALL
)

_TEXTO = re.compile(r"'((?:[^'\\]|\\.){2,}?)'")
_TITULO_APPBAR = re.compile(r"AppBar\(\s*title:\s*const\s+Text\('([^']+)'\)")
_SECAO = re.compile(r"FiSection\(\s*\n\s*title:\s*'([^']+)'")
_HINT = re.compile(r"hint:\s*'([^']+)'")
_BOTAO = re.compile(r"FiButton\.(\w+)\(\s*\n?\s*label:\s*(?:_?\w+\s*\?\s*)?'([^']+)'")
_ESQUELETO = re.compile(r"FiSkeleton\.tela\([^)]*label:\s*'([^']+)'", re.DOTALL)
_ERRO_TITULO = re.compile(r"FiErrorState\((?:[^()]|\([^()]*\))*?title:\s*'([^']+)'", re.DOTALL)
_ERRO_ACAO = re.compile(r"FiErrorState\((?:[^()]|\([^()]*\))*?action:\s*'([^']+)'", re.DOTALL)
_VAZIO = re.compile(r"FiEmptyState\((?:[^()]|\([^()]*\))*?title:\s*'([^']+)'", re.DOTALL)
_NAVEGA = re.compile(r"(?:context|GoRouter\.of\(context\))\.(?:go|push)\('([^']+)'")
_TIPO = re.compile(r"FiType\.(\w+)")

_COMPONENTES = (
    "FiSection",
    "FiObject",
    "FiRows",
    "FiDataRow",
    "FiButton",
    "FiMeasure",
    "FiRange",
    "FiProvenance",
    "HelpTooltip",
    "ScoreRuler",
    "FiHeadline",
    "FiFigures",
    "FiTag",
    "FiEmptyState",
    "FiErrorState",
    "FiSkeleton",
)

_MATERIAL_CRU = ("Card(", "ListTile(", "SwitchListTile(", "CircleAvatar(", "AlertDialog(")

_RUIDO = re.compile(
    r"^(?:[\w./:-]+\.dart|package:|https?://|[\d.,%$ RS-]+|[a-z_]+)$|^\s*$|^[A-Za-z_]+\(\)$"
)


_ADJACENTES = re.compile("'[ \t]*\r?\n[ \t]*'")


def _juntar_literais(fonte: str) -> str:
    anterior = None
    while anterior != fonte:
        anterior = fonte
        fonte = _ADJACENTES.sub("", fonte)
    return fonte


def _limpo(texto: str) -> bool:
    if len(texto) < 3 or _RUIDO.match(texto):
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]{3,}", texto)) and " " in texto


def _mapa_de_rotas() -> tuple[dict[str, dict], dict[str, str]]:
    fonte = (LIB / "core" / "router.dart").read_text(encoding="utf-8")

    redirects = {de: para for de, para in _REDIRECT.findall(fonte)}

    marcos = list(re.finditer(r"path:\s*'([\w:/-]+)'", fonte))
    rotas: dict[str, dict] = {}
    pai = ""

    for indice, achado in enumerate(marcos):
        caminho = achado.group(1)
        fim_do_bloco = marcos[indice + 1].start() if indice + 1 < len(marcos) else len(fonte)
        bloco = fonte[achado.end() : fim_do_bloco]

        if caminho.startswith("/"):
            pai = caminho
            rota = caminho
        elif pai:
            rota = f"{pai.rstrip('/')}/{caminho}"
        else:
            continue

        if rota in redirects:
            continue

        widget = _BUILDER.search(bloco)
        if not widget:
            continue

        detalhe = _FERRAMENTA.search(bloco)
        titulo = _FERRAMENTA_TITULO.search(bloco)
        pergunta = _FERRAMENTA_PERGUNTA.search(bloco)
        rotas[rota] = {
            "widget": widget.group(1),
            "ferramenta": (
                {
                    "titulo": titulo.group(1) if titulo else None,
                    "pergunta": pergunta.group(1) if pergunta else None,
                    "conteudo": detalhe.group(1),
                }
                if detalhe
                else None
            ),
        }

    return rotas, redirects


def _arquivo_do_widget(widget: str) -> pathlib.Path | None:
    for caminho in LIB.rglob("*.dart"):
        fonte = caminho.read_text(encoding="utf-8")
        if re.search(
            rf"class {re.escape(widget)} extends (?:Consumer)?(?:Stateful|Stateless)?Widget",
            fonte,
        ):
            return caminho
    return None


def _ler_tela(caminho: pathlib.Path) -> dict:
    bruto = caminho.read_text(encoding="utf-8")
    fonte = _juntar_literais(bruto)

    secoes = []
    for achado in re.finditer(r"FiSection\(", fonte):
        bloco = fonte[achado.start() : achado.start() + 600]
        titulo = re.search(r"title:\s*'([^']+)'", bloco)
        hint = _HINT.search(bloco)
        if titulo:
            secoes.append(
                {"titulo": titulo.group(1), "explicacao": hint.group(1) if hint else None}
            )

    textos = []
    for literal in _TEXTO.findall(fonte):
        texto = literal.replace("\\'", "'")
        if _limpo(texto) and texto not in textos:
            textos.append(texto)

    titulo = _TITULO_APPBAR.search(fonte)

    return {
        "arquivo": str(caminho.relative_to(RAIZ)).replace("\\", "/"),
        "titulo_da_barra": titulo.group(1) if titulo else None,
        "secoes": secoes,
        "acoes": _acoes(fonte),
        "estados": {
            "carregando": _ESQUELETO.findall(fonte),
            "falha": [
                {"titulo": t, "acao": a}
                for t, a in zip(_ERRO_TITULO.findall(fonte), _ERRO_ACAO.findall(fonte))
            ],
            "sem_dado": _VAZIO.findall(fonte),
        },
        "componentes": sorted({c for c in _COMPONENTES if c in fonte}),
        "explicabilidade": sorted(
            {c for c in ("FiProvenance", "HelpTooltip", "ScoreRuler") if c in fonte}
        ),
        "papeis_de_tipo": sorted(set(_TIPO.findall(fonte))),
        "navega_para": sorted(set(_NAVEGA.findall(fonte))),
        "material_cru": sorted({m.rstrip("(") for m in _MATERIAL_CRU if m in fonte}),
        "textos": textos,
        "linhas": len(bruto.splitlines()),
    }


def _acoes(fonte: str) -> list[dict]:
    vistas = []
    for peso, rotulo in _BOTAO.findall(fonte):
        item = {"peso": peso, "rotulo": rotulo}
        if item not in vistas:
            vistas.append(item)
    return vistas


_ABRE_FOLHA = re.compile(r"(?:Future<[\w?<>]+>|void)\s+(abrir\w+|show\w+)\s*\(")


def _folhas(arquivos_de_rota: set[str]) -> list[dict]:
    achadas = []
    for caminho in sorted(LIB.rglob("*.dart")):
        bruto = caminho.read_text(encoding="utf-8")
        if "showModalBottomSheet" not in bruto and "showDialog" not in bruto:
            continue

        aberturas = _ABRE_FOLHA.findall(bruto)
        if not aberturas:
            continue

        relativo = str(caminho.relative_to(RAIZ)).replace("\\", "/")
        dados = _ler_tela(caminho)
        achadas.append(
            {
                "abre_por": sorted(set(aberturas)),
                "dentro_de_tela_com_rota": relativo in arquivos_de_rota,
                **dados,
            }
        )
    return achadas


def montar() -> dict:
    rotas, redirects = _mapa_de_rotas()

    telas = []
    vistos: dict[str, dict] = {}

    for rota in sorted(rotas):
        widget = rotas[rota]["widget"]
        caminho = _arquivo_do_widget(widget)
        if caminho is None:
            telas.append({"rota": rota, "widget": widget, "erro": "fonte não localizado"})
            continue

        ferramenta = rotas[rota]["ferramenta"]
        if ferramenta:
            conteudo = _arquivo_do_widget(ferramenta["conteudo"])
            if conteudo is not None:
                caminho = conteudo

        chave = str(caminho)
        if chave not in vistos:
            vistos[chave] = _ler_tela(caminho)

        tela = {"rota": rota, "widget": widget, **vistos[chave]}
        if ferramenta:
            tela["widget"] = f"{widget} -> {ferramenta['conteudo']}"
            if ferramenta["titulo"]:
                tela["titulo_da_barra"] = ferramenta["titulo"]
            if ferramenta["pergunta"]:
                tela["pergunta_que_responde"] = ferramenta["pergunta"]
        telas.append(tela)

    return {
        "gerado_por": "tool/catalogo_de_telas.py",
        "fonte": "mobile/lib/ — análise dos fontes, não do aplicativo em execução",
        "destinos_de_raiz": ["/mes", "/sobra", "/patrimonio", "/descobrir", "/voce"],
        "redirects": redirects,
        "telas": telas,
        "folhas_e_formularios": _folhas({t.get("arquivo", "") for t in telas}),
        "pontos_cegos": [
            "Não renderiza: espaçamento, contraste, ordem visual e densidade não são vistos aqui.",
            "Texto montado em runtime (interpolação, plural, dado do servidor) aparece como o "
            "literal do código, não como a frase final.",
            "Folhas e diálogos que não são rota — o formulário de compra, o de lançamento — só "
            "entram pelo arquivo da tela que os abre.",
            "Widget usado condicionalmente aparece como presente, mesmo que a pessoa nunca o veja.",
            "Contraste é verificado por máquina em mobile/test/contraste_test.dart, não aqui.",
        ],
    }


def como_markdown(catalogo: dict) -> str:
    linhas = [
        "# Catálogo de telas do fiance",
        "",
        f"Gerado por `{catalogo['gerado_por']}` a partir de {catalogo['fonte']}.",
        "",
        "Destinos de raiz: " + " · ".join(catalogo["destinos_de_raiz"]),
        "",
        "---",
        "",
    ]

    detalhado: dict[str, str] = {}

    for tela in catalogo["telas"]:
        linhas.append(f"## `{tela['rota']}`")
        linhas.append("")
        if tela.get("erro"):
            linhas.append(f"⚠️ {tela['erro']} ({tela['widget']})")
            linhas.append("")
            continue

        ja_visto = detalhado.get(tela["arquivo"])
        if ja_visto:
            titulo = tela.get("titulo_da_barra")
            pergunta = tela.get("pergunta_que_responde")
            linhas.append(f"**Widget:** `{tela['widget']}` · `{tela['arquivo']}`")
            if titulo:
                linhas.append(f"**Título na barra:** {titulo}")
            if pergunta:
                linhas.append(f"**Pergunta que responde:** {pergunta}")
            linhas.append("")
            linhas.append(f"Mesmo conteúdo de `{ja_visto}` — o arquivo serve às duas rotas.")
            linhas.append("")
            linhas.append("---")
            linhas.append("")
            continue

        detalhado[tela["arquivo"]] = tela["rota"]

        linhas.append(f"**Widget:** `{tela['widget']}` · `{tela['arquivo']}` · {tela['linhas']} linhas")
        if tela["titulo_da_barra"]:
            linhas.append(f"**Título na barra:** {tela['titulo_da_barra']}")
        if tela.get("pergunta_que_responde"):
            linhas.append(f"**Pergunta que responde:** {tela['pergunta_que_responde']}")
        linhas.append("")

        if tela["secoes"]:
            linhas.append("**Seções, na ordem:**")
            linhas.append("")
            for s in tela["secoes"]:
                explicacao = f" — _{s['explicacao']}_" if s["explicacao"] else ""
                linhas.append(f"- {s['titulo']}{explicacao}")
            linhas.append("")

        if tela["acoes"]:
            linhas.append("**Ações:**")
            linhas.append("")
            for a in tela["acoes"]:
                linhas.append(f"- `{a['peso']}` — {a['rotulo']}")
            linhas.append("")

        estados = tela["estados"]
        if any(estados.values()):
            linhas.append("**Estados de tela:**")
            linhas.append("")
            for rotulo in estados["carregando"]:
                linhas.append(f"- carregando: {rotulo}")
            for f in estados["falha"]:
                linhas.append(f"- falha: {f['titulo']} (ação: {f['acao']})")
            for v in estados["sem_dado"]:
                linhas.append(f"- sem dado: {v}")
            linhas.append("")

        if tela["explicabilidade"]:
            linhas.append("**Explicabilidade:** " + ", ".join(tela["explicabilidade"]))
            linhas.append("")
        if tela["material_cru"]:
            linhas.append("⚠️ **Material cru:** " + ", ".join(tela["material_cru"]))
            linhas.append("")
        if tela["navega_para"]:
            linhas.append("**Leva a:** " + ", ".join(f"`{d}`" for d in tela["navega_para"]))
            linhas.append("")

        if tela["textos"]:
            linhas.append("**Textos da tela:**")
            linhas.append("")
            for texto in tela["textos"]:
                linhas.append(f"> {texto}")
                linhas.append("")

        linhas.append("---")
        linhas.append("")

    folhas = catalogo.get("folhas_e_formularios") or []
    if folhas:
        linhas.append("# Folhas e formulários")
        linhas.append("")
        linhas.append(
            "Não são rotas: abrem por cima de uma tela. É onde a pessoa escreve, e onde um texto "
            "ambíguo custa mais caro."
        )
        linhas.append("")
        for folha in folhas:
            linhas.append(f"## {', '.join(f'`{a}`' for a in folha['abre_por'])}")
            linhas.append("")
            linhas.append(f"**Arquivo:** `{folha['arquivo']}`")
            linhas.append("")
            if folha["arquivo"] in detalhado:
                linhas.append(
                    f"Vive dentro da tela `{detalhado[folha['arquivo']]}`, cujos textos já estão "
                    "acima."
                )
                linhas.append("")
                linhas.append("---")
                linhas.append("")
                continue
            if folha["acoes"]:
                linhas.append(
                    "**Ações:** " + ", ".join(f"{a['rotulo']} (`{a['peso']}`)" for a in folha["acoes"])
                )
                linhas.append("")
            if folha["material_cru"]:
                linhas.append("⚠️ **Material cru:** " + ", ".join(folha["material_cru"]))
                linhas.append("")
            if folha["textos"]:
                linhas.append("**Textos:**")
                linhas.append("")
                for texto in folha["textos"]:
                    linhas.append(f"> {texto}")
                    linhas.append("")
            linhas.append("---")
            linhas.append("")

    linhas.append("## O que este catálogo não enxerga")
    linhas.append("")
    for cego in catalogo["pontos_cegos"]:
        linhas.append(f"- {cego}")
    linhas.append("")

    return "\n".join(linhas)


_BRIEFING = """# Como avaliar este catálogo

Anexe este arquivo junto com `CATALOGO.md` ao pedir a avaliação.

## O produto

O fiance é para quem trabalha em outra coisa e tem pouco tempo para investir. Metade do público
nunca investiu. Ele encadeia três perguntas, nesta ordem, que é também a navegação:

1. `/mes` — quanto entrou e saiu
2. `/sobra` — quanto sobra, e para onde vai (dívida cara antes de reserva, reserva antes de aporte)
3. `/patrimonio` e `/descobrir` — onde está aplicado, e o que comprar

**A tensão central:** o produto é para quem não tem tempo, e pede lançamento de gasto, cadastro de
posição e conferência de provento. Toda tela cobra atenção de quem não a tem. Avalie cada uma
perguntando *isto cobra mais tempo do que devolve?*

## As regras que o produto já se impôs

Não sugira violar nenhuma delas — se achar que uma está errada, diga isso explicitamente.

- **Explicabilidade:** score, veredito, preço justo e sugestão saem com `FiProvenance` ou
  `HelpTooltip`. Mencionar em prosa não conta.
- **Faixa, nunca número único** em projeção.
- **Veredito vem com o que o derrubaria** — uma condição conferível, não uma opinião.
- **Fio e chão, não card sobre card.** A caixa (`FiObject`) é só para objeto: uma posição, uma
  opção, uma sugestão. `Card`, `ListTile` e `SwitchListTile` estão proibidos.
- **Grade de KPI é cheiro de painel.** Poucas cifras vão numa linha sob um fio; muitas viram tabela.
- **Estado de tela é contrato:** carregando, falha, vazio e conteúdo são quatro coisas distintas.
  Falha e vazio nunca compartilham a mesma tela.
- **O sistema não inventa dado.** Fonte fora do ar vira ausência declarada, com a idade do dado à
  vista.
- **Não se promete futuro**, e não se fala como IA genérica.

## O que queremos da avaliação

1. **Linguagem.** Há jargão que um iniciante não entenderia? Frase que promete mais do que o
   produto entrega? Texto que poderia estar em qualquer aplicativo?
2. **Hierarquia.** A tela responde a pergunta dela logo no alto, ou enterra a resposta?
3. **Excesso.** Que seção pode sair sem perda? Que número está ali só porque existe?
4. **Coerência.** O mesmo conceito tem o mesmo nome em todas as telas?
5. **Ação.** Cada tela tem uma ação principal clara, ou tem três de peso igual?

Aponte a tela e o texto exato. Prefira dez observações específicas a um ensaio.
"""


def _conferir(catalogo: dict) -> int:
    queixas = []

    rotas = {t["rota"] for t in catalogo["telas"]}
    for raiz in catalogo["destinos_de_raiz"]:
        if raiz not in rotas:
            queixas.append(f"destino de raiz fora do catálogo: {raiz}")

    mudas = [t["rota"] for t in catalogo["telas"] if not t.get("erro") and not t.get("textos")]
    if mudas:
        queixas.append(f"telas sem nenhum texto lido: {', '.join(mudas)}")

    perdidas = [t["rota"] for t in catalogo["telas"] if t.get("erro")]
    if perdidas:
        queixas.append(f"telas cujo fonte não foi localizado: {', '.join(perdidas)}")

    if not catalogo["folhas_e_formularios"]:
        queixas.append("nenhuma folha encontrada — o padrão de abertura mudou")

    if queixas:
        print("o catálogo deixou de enxergar parte do aplicativo:")
        for queixa in queixas:
            print(f"  - {queixa}")
        print(
            "\nIsto quase sempre significa que o router ou o padrão das telas mudou, e que o "
            "catálogo passou a descrever menos do que existe — em silêncio, que é o defeito que "
            "esta conferência evita."
        )
        return 1

    print(
        f"catálogo íntegro: {len(catalogo['telas'])} telas, "
        f"{len(catalogo['folhas_e_formularios'])} folhas"
    )
    return 0


def main() -> int:
    # O console do Windows nasce em cp1252 e engasga com acento e seta.
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdout", action="store_true", help="imprime em vez de escrever")
    parser.add_argument(
        "--check",
        action="store_true",
        help="falha se o catálogo deixou de enxergar alguma tela; não escreve nada",
    )
    args = parser.parse_args()

    catalogo = montar()

    if args.check:
        return _conferir(catalogo)

    markdown = como_markdown(catalogo)

    if args.stdout:
        print(markdown)
        return 0

    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "catalogo.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (SAIDA / "CATALOGO.md").write_text(markdown, encoding="utf-8")
    (SAIDA / "COMO-AVALIAR.md").write_text(_BRIEFING, encoding="utf-8")

    telas = len(catalogo["telas"])
    folhas = len(catalogo["folhas_e_formularios"])
    textos = sum(len(t.get("textos", [])) for t in catalogo["telas"])
    print(f"{telas} telas, {folhas} folhas, {textos} textos -> {SAIDA.relative_to(RAIZ)}")
    print("envie CATALOGO.md junto com COMO-AVALIAR.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
