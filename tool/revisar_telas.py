"""Gera o material para revisar as telas do aplicativo — por pessoa ou por IA.

Uso:
    python tool/revisar_telas.py             # catálogo + imagens
    python tool/revisar_telas.py --limpar    # apaga a revisão anterior antes
    python tool/revisar_telas.py --texto     # só o catálogo (instantâneo)
    python tool/revisar_telas.py --imagens   # só as capturas
    python tool/revisar_telas.py --check     # confere que nada saiu do radar

Produz duas leituras da mesma interface, porque nenhuma enxerga o que a outra vê:

- **O catálogo** lê `mobile/lib/` e extrai todo o texto e a estrutura. Enxerga até a frase que só
  aparece em situação rara, e não enxerga nada visual.
- **As imagens** renderizam cada tela nos quatro estados e nos dois temas. Enxergam espaçamento,
  cor e hierarquia, e só mostram o texto daquele estado.

Sai junto um COMO-AVALIAR.md com o contexto do produto: sem ele, quem avalia sugere o contrário do
que o produto ja decidiu.

Tudo vai para build/revisao/, que o git ignora — é material de revisão, não fonte.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MOBILE = RAIZ / "mobile"
LIB = MOBILE / "lib"
SAIDA = RAIZ / "build" / "revisao"
TELAS = SAIDA / "telas"
FONTES = SAIDA / ".fontes"

# Variáveis de peso, do repositório oficial do Google Fonts. Licença OFL.
_ARQUIVOS_DE_FONTE = {
    "IBMPlexSans-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/ibmplexsans/IBMPlexSans%5Bwdth%2Cwght%5D.ttf"
    ),
    "SourceSerif4-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/sourceserif4/"
        "SourceSerif4%5Bopsz%2Cwght%5D.ttf"
    ),
}

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


def _copiar_icones() -> None:
    destino = FONTES / "MaterialIcons-Regular.otf"
    if destino.exists():
        return

    flutter = shutil.which("flutter")
    if not flutter:
        print("  flutter nao encontrado no PATH; os icones sairao como quadrados vazios")
        return

    raiz = pathlib.Path(flutter).resolve().parent.parent
    for candidato in raiz.rglob("materialicons-regular.otf"):
        shutil.copy(candidato, destino)
        return
    for candidato in raiz.rglob("MaterialIcons-Regular.otf"):
        shutil.copy(candidato, destino)
        return

    print("  fonte de icones do Flutter nao localizada; eles sairao como quadrados vazios")


def _baixar_fontes() -> bool:
    FONTES.mkdir(parents=True, exist_ok=True)
    _copiar_icones()

    for nome, url in _ARQUIVOS_DE_FONTE.items():
        destino = FONTES / nome
        if destino.exists() and destino.stat().st_size > 10_000:
            continue

        print(f"baixando {nome}...")
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": "fiance-captura"})
            with urllib.request.urlopen(pedido, timeout=60) as resposta:
                destino.write_bytes(resposta.read())
        except Exception as erro:
            print(f"  nao foi possivel baixar {nome}: {erro}")
            print(
                "  Sem a fonte, a captura sai com caixas no lugar do texto. Baixe manualmente de "
                f"{url} e salve em {destino}."
            )
            return False

    return True


def _escrever_catalogo(catalogo: dict) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "catalogo.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (SAIDA / "CATALOGO.md").write_text(como_markdown(catalogo), encoding="utf-8")
    (SAIDA / "COMO-AVALIAR.md").write_text(_BRIEFING, encoding="utf-8")

    telas = len(catalogo["telas"])
    folhas = len(catalogo["folhas_e_formularios"])
    textos = sum(len(t.get("textos", [])) for t in catalogo["telas"])
    print(f"catalogo: {telas} telas, {folhas} folhas, {textos} textos")


def _capturar() -> int:
    if not _baixar_fontes():
        return 1

    print("capturando... (cerca de um minuto)")
    subprocess.run(
        ["flutter", "test", "captura/telas_test.dart"],
        cwd=MOBILE,
        shell=True,
        capture_output=True,
    )

    imagens = sorted(TELAS.rglob("*.png")) if TELAS.exists() else []
    if not imagens:
        print(
            "nenhuma imagem foi escrita. Rode `flutter test captura/telas_test.dart` em mobile/ "
            "para ver o erro."
        )
        return 1

    total = sum(i.stat().st_size for i in imagens)
    print(f"imagens: {len(imagens)} em {total / 1024 / 1024:.1f} MB")

    por_estado: dict[str, int] = {}
    for imagem in imagens:
        por_estado[imagem.parent.name] = por_estado.get(imagem.parent.name, 0) + 1
    for estado in sorted(por_estado):
        print(f"  telas/{estado}/  {por_estado[estado]}")

    return 0


def main() -> int:
    # O console do Windows nasce em cp1252 e engasga com acento e seta.
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limpar", action="store_true", help="apaga a revisao anterior antes")
    parser.add_argument("--texto", action="store_true", help="so o catalogo")
    parser.add_argument("--imagens", action="store_true", help="so as capturas")
    parser.add_argument("--stdout", action="store_true", help="imprime o catalogo, sem escrever")
    parser.add_argument(
        "--check",
        action="store_true",
        help="falha se o catalogo deixou de enxergar alguma tela; nao escreve nada",
    )
    args = parser.parse_args()

    if args.check:
        return _conferir(montar())

    if args.stdout:
        print(como_markdown(montar()))
        return 0

    if args.limpar and SAIDA.exists():
        # As fontes ficam de fora: baixa-las de novo custa rede e elas nao envelhecem.
        for item in SAIDA.iterdir():
            if item.name == FONTES.name:
                continue
            shutil.rmtree(item) if item.is_dir() else item.unlink()
        print("revisao anterior apagada")

    so_um = args.texto or args.imagens

    if args.texto or not so_um:
        _escrever_catalogo(montar())

    if args.imagens or not so_um:
        if _capturar() != 0:
            return 1

    print()
    print(f"-> {SAIDA.relative_to(RAIZ)}")
    print("Para avaliar, envie COMO-AVALIAR.md com o que interessa: CATALOGO.md para linguagem,")
    print("telas/conteudo/ para o visual, e as outras pastas para os estados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
