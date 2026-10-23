import io
import os
import re
import sys
from urllib.parse import quote

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS = os.path.join(ROOT, "mobile", "lib", "core", "design_tokens.dart")

GLYPH_VIEWBOX = 100.0
GLYPH_EIXO = [
    (6, 6),
    (76, 6),
    (76, 19),
    (19, 19),
    (19, 41),
    (56, 41),
    (56, 54),
    (19, 54),
    (19, 79),
    (6, 79),
]
GLYPH_LEITURA = (83, 6, 96, 19, 3)
GLYPH_CHAO = (0, 87, 100, 95, 4)
GLYPH_GRADE = [
    (82, 6, 88, 12, 1.5),
    (90, 6, 96, 12, 1.5),
    (82, 14, 88, 20, 1.5),
    (90, 14, 96, 20, 1.5),
]
GLYPH_LINHAS = [
    (0, 86, 100, 89, 1.5),
    (0, 91.5, 100, 94.5, 1.5),
    (0, 97, 100, 100, 1.5),
]
GLYPH_SERIE = (
    "M2 91C7 91 9 88.5 14 88.5S21 93.5 26 93.5S33 88.5 38 88.5"
    "S45 93.5 50 93.5S57 88.5 62 88.5S69 91 74 91L98 91"
)
GLYPH_SERIE_TRACO = 3

VARIANTES = {
    "app": ([GLYPH_LEITURA], [GLYPH_CHAO], None),
    "dados": (GLYPH_GRADE, GLYPH_LINHAS, None),
    "trend": ([GLYPH_LEITURA], [], GLYPH_SERIE),
}

PORTAL = "fiance-dados/dadosapi/paginas/portal.html"
CONSOLE = "fiance-dados/dadosapi/paginas/console.html"
PAINEL_CSS = "fiance-trend/frontend/src/estilo.css"
PAINEL_FAVICON = "fiance-trend/frontend/public/favicon.svg"
PAINEL_SIMBOLO = "fiance-trend/frontend/src/Simbolo.tsx"

PAGINAS = {
    PORTAL: ("dados", "--destaque", "--tinta-3"),
    CONSOLE: ("dados", "--destaque", "--suave"),
}
PAINEL = ("trend", "--destaque", "--suave")

GROUND_MIX = 0.65

WORDMARK = [
    (62, "M0 0L62 0L62 13L13 13L13 49L50 49L50 62L13 62L13 100L0 100Z"),
    (13, "M0 0L13 0L13 100L0 100Z"),
    (
        74,
        "M29 0L45 0L74 100L59.5 100L37 22.4L14.5 100L0 100Z "
        "M29.29 49L44.71 49L48.48 62L25.52 62Z",
    ),
    (72, "M0 0L13 0L59 76L59 0L72 0L72 100L59 100L13 24L13 100L0 100Z"),
    (70, "M64.4 22.8A35 50 0 1 0 64.4 77.2L53.4 70.2A22 37 0 1 1 53.4 29.8Z"),
    (62, "M0 0L62 0L62 13L13 13L13 49L48 49L48 62L13 62L13 87L62 87L62 100L0 100Z"),
]
WORDMARK_TRACK = 13

RADIUS_RATIO = 0.22
GLYPH_RATIO = 0.58
ADAPTIVE_GLYPH_RATIO = 0.42

SS = 4


BRAND_DIR = "marca/kit"


_COR = re.compile(
    r"static const (dark|light)([A-Za-z0-9]+) = Color\(0x(?:FF)?([0-9A-Fa-f]{6})\);"
)

PAPEIS = {
    "Brand": "brand",
    "InkOnBrand": "ink-on-brand",
    "Ink1": "ink-1",
    "Ink3": "ink-3",
}


def tokens():
    with io.open(TOKENS, encoding="utf-8") as fh:
        dart = fh.read()

    palette = {"dark": {}, "light": {}}
    for tema, nome, valor in _COR.findall(dart):
        papel = PAPEIS.get(nome)
        if papel:
            palette[tema][papel] = "#" + valor.upper()

    faltando = [
        "%s%s" % (tema, nome)
        for tema in palette
        for nome, papel in PAPEIS.items()
        if papel not in palette[tema]
    ]
    if faltando:
        raise SystemExit(
            "design_tokens.dart nao declara: " + ", ".join(sorted(faltando))
        )

    return {"color": palette}


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def hexa(color):
    return "#%02X%02X%02X" % color


def mix(a, b, t):
    return tuple(int(round(a[i] * t + b[i] * (1.0 - t))) for i in range(3))


def place(size, ratio):
    span = size * ratio
    return span / GLYPH_VIEWBOX, (size - span) / 2.0


def draw_glyph(draw, size, ratio, fg, ground):
    scale, off = place(size, ratio)

    def pt(x, y):
        return (x * scale + off, y * scale + off)

    def rounded(spec, fill):
        x0, y0, x1, y1, r = spec
        draw.rounded_rectangle([pt(x0, y0), pt(x1, y1)], radius=r * scale, fill=fill)

    draw.polygon([pt(x, y) for x, y in GLYPH_EIXO], fill=fg)
    rounded(GLYPH_LEITURA, fg)
    rounded(GLYPH_CHAO, ground)


def render(size, bg, fg, ground, ratio=GLYPH_RATIO, rounded=True):
    big = size * SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if bg is not None:
        if rounded:
            draw.rounded_rectangle(
                [0, 0, big - 1, big - 1], radius=big * RADIUS_RATIO, fill=bg
            )
        else:
            draw.rectangle([0, 0, big - 1, big - 1], fill=bg)
    draw_glyph(draw, big, ratio, fg, ground)
    return img.resize((size, size), Image.LANCZOS)


def write_png(img, path, flatten=None):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if flatten is not None:
        base = Image.new("RGB", img.size, flatten)
        base.paste(img, mask=img.split()[3])
        img = base
    img.save(full)
    print("escrito %s (%dx%d)" % (path, img.size[0], img.size[1]))


def svg_doc(width, height, label, inner):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" '
        'width="%s" height="%s" role="img" aria-label="%s">\n'
        "<title>%s</title>\n%s\n</svg>\n"
    ) % (width, height, width, height, label, label, inner)


def _atributo(cor, prop):
    return '%s="%s"' % (prop, cor)


def _rect(spec, pintura):
    x0, y0, x1, y1, r = spec
    return '<rect x="%g" y="%g" width="%g" height="%g" rx="%g" %s/>' % (
        x0,
        y0,
        x1 - x0,
        y1 - y0,
        r,
        pintura,
    )


def symbol_markup(fg, ground, variante="app", pinta=_atributo):
    leituras, chaos, serie = VARIANTES[variante]
    partes = [
        '<path d="M%sZ" %s/>'
        % ("L".join("%g %g" % p for p in GLYPH_EIXO), pinta(fg, "fill"))
    ]
    partes += [_rect(spec, pinta(fg, "fill")) for spec in leituras]
    partes += [_rect(spec, pinta(ground, "fill")) for spec in chaos]
    if serie:
        partes.append(
            '<path d="%s" fill="none" stroke-width="%g" stroke-linecap="round" '
            'stroke-linejoin="round" %s/>'
            % (serie, GLYPH_SERIE_TRACO, pinta(ground, "stroke"))
        )
    return "".join(partes)


def cores_da_folha(rel, papel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        achados = re.findall(re.escape(papel) + r":\s*(#[0-9A-Fa-f]{6})", fh.read())
    if len(achados) < 2:
        raise SystemExit("%s nao declara %s nos dois temas" % (rel, papel))
    return achados[0].upper(), achados[1].upper()


def favicon(variante, folha, destaque, chao):
    (fg_c, fg_e), (chao_c, chao_e) = (
        cores_da_folha(folha, destaque),
        cores_da_folha(folha, chao),
    )
    classes = {("fg", "fill"): "f", ("chao", "fill"): "c", ("chao", "stroke"): "s"}
    corpo = symbol_markup(
        "fg", "chao", variante, lambda cor, prop: 'class="%s"' % classes[(cor, prop)]
    )
    estilo = (
        ".f{fill:%s}.c{fill:%s}.s{stroke:%s}"
        "@media (prefers-color-scheme:dark){.f{fill:%s}.c{fill:%s}.s{stroke:%s}}"
    ) % (fg_c, chao_c, chao_c, fg_e, chao_e, chao_e)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        "<style>%s</style>%s</svg>\n"
    ) % (estilo, corpo)


def simbolo_em_linha(variante, destaque, chao):
    corpo = symbol_markup(
        destaque,
        chao,
        variante,
        lambda var, prop: 'style="%s:var(%s)"' % (prop, var),
    )
    return (
        '<svg class="simbolo" viewBox="0 0 100 100" aria-hidden="true" '
        'focusable="false">%s</svg>'
    ) % corpo


def logotipo_em_linha():
    wm, wm_w = wordmark_markup()
    return (
        '<svg class="logotipo" viewBox="0 0 %g 100" role="img" aria-label="fiance" '
        'focusable="false"><g fill="currentColor">%s</g></svg>'
    ) % (wm_w, wm)


def _bloco(texto, nome, conteudo, rel):
    padrao = re.compile(r"(<!-- %s -->)(.*?)(<!-- /%s -->)" % (nome, nome), re.S)
    if not padrao.search(texto):
        raise SystemExit("%s nao tem o bloco <!-- %s -->" % (rel, nome))
    return padrao.sub(lambda m: m.group(1) + conteudo + m.group(3), texto)


def pagina(rel, variante, destaque, chao):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        texto = fh.read()
    icone = '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%s">' % (
        quote(favicon(variante, rel, destaque, chao).strip())
    )
    texto = _bloco(texto, "favicon", icone, rel)
    return _bloco(
        texto,
        "marca",
        simbolo_em_linha(variante, destaque, chao) + logotipo_em_linha(),
        rel,
    )


def _jsx(svg):
    svg = re.sub(
        r'style="(\w+):([^"]+)"', lambda m: 'style={{ %s: "%s" }}' % m.groups(), svg
    )
    svg = svg.replace('class="', 'className="')
    for attr in ("stroke-width", "stroke-linecap", "stroke-linejoin"):
        a, b = attr.split("-")
        svg = svg.replace(attr + "=", a + b.capitalize() + "=")
    return svg


def simbolo_tsx(variante, destaque, chao):
    return (
        "// Gerado por marca/build.py; não edite à mão.\n"
        "export default function Simbolo() {\n"
        "  return (\n    %s\n  );\n}\n\n"
        "export function Logotipo() {\n"
        "  return (\n    %s\n  );\n}\n"
    ) % (_jsx(simbolo_em_linha(variante, destaque, chao)), _jsx(logotipo_em_linha()))


def superficies():
    out = {}
    for rel, (variante, destaque, chao) in PAGINAS.items():
        out[rel] = pagina(rel, variante, destaque, chao)
    variante, destaque, chao = PAINEL
    out[PAINEL_FAVICON] = favicon(variante, PAINEL_CSS, destaque, chao)
    out[PAINEL_SIMBOLO] = simbolo_tsx(variante, destaque, chao)
    return out


def wordmark_markup():
    parts, x = [], 0
    for advance, d in WORDMARK:
        parts.append('<path d="%s" transform="translate(%g 0)"/>' % (d, x))
        x += advance + WORDMARK_TRACK
    return "".join(parts), x - WORDMARK_TRACK


def brand_files(light, dark, on_brand_hex, ground_hex):
    wm, wm_w = wordmark_markup()
    mono = ("currentColor", "currentColor")
    tints = {
        "light": (light["brand"], light["ink-3"]),
        "dark": (dark["brand"], dark["ink-3"]),
    }
    out = {}

    def add(name, width, height, what, inner):
        out["%s/fiance-%s.svg" % (BRAND_DIR, name)] = svg_doc(
            width, height, "Fiance, " + what, inner
        )

    add("symbol", 100, 100, "simbolo", symbol_markup(*tints["light"]))
    add(
        "symbol-dark",
        100,
        100,
        "simbolo em fundo escuro",
        symbol_markup(*tints["dark"]),
    )
    add("symbol-mono", 100, 100, "simbolo monocromatico", symbol_markup(*mono))

    for variante, folha, destaque, chao in (
        ("dados", PORTAL, "--destaque", "--tinta-3"),
        ("trend", PAINEL_CSS, "--destaque", "--suave"),
    ):
        (fg_c, fg_e), (chao_c, chao_e) = (
            cores_da_folha(folha, destaque),
            cores_da_folha(folha, chao),
        )
        add(
            "%s-symbol" % variante,
            100,
            100,
            "%s, simbolo" % variante,
            symbol_markup(fg_c, chao_c, variante),
        )
        add(
            "%s-symbol-dark" % variante,
            100,
            100,
            "%s, simbolo em fundo escuro" % variante,
            symbol_markup(fg_e, chao_e, variante),
        )
        add(
            "%s-symbol-mono" % variante,
            100,
            100,
            "%s, simbolo monocromatico" % variante,
            symbol_markup(*mono, variante=variante),
        )

    size, gap = 132, 46

    def lock_h(fg, ground, ink):
        return (
            '<g transform="scale(%g)">%s</g>\n'
            '<g fill="%s" transform="translate(%g 16)">%s</g>'
        ) % (size / 100.0, symbol_markup(fg, ground), ink, size + gap, wm)

    hw = size + gap + wm_w
    add(
        "lockup-h",
        hw,
        size,
        "assinatura horizontal",
        lock_h(tints["light"][0], tints["light"][1], light["ink-1"]),
    )
    add(
        "lockup-h-dark",
        hw,
        size,
        "assinatura horizontal em fundo escuro",
        lock_h(tints["dark"][0], tints["dark"][1], dark["ink-1"]),
    )
    add(
        "lockup-h-mono",
        hw,
        size,
        "assinatura horizontal monocromatica",
        lock_h(mono[0], mono[1], "currentColor"),
    )

    vs, vgap, vcap = 150, 42, 0.84
    vwm = wm_w * vcap
    vw, vh = round(max(vs, vwm), 2), round(vs + vgap + 100 * vcap, 2)

    def lock_v(fg, ground, ink):
        return (
            '<g transform="translate(%.2f 0) scale(%g)">%s</g>\n'
            '<g fill="%s" transform="translate(%.2f %g) scale(%g)">%s</g>'
        ) % (
            (vw - vs) / 2.0,
            vs / 100.0,
            symbol_markup(fg, ground),
            ink,
            (vw - vwm) / 2.0,
            vs + vgap,
            vcap,
            wm,
        )

    add(
        "lockup-v",
        vw,
        vh,
        "assinatura vertical",
        lock_v(tints["light"][0], tints["light"][1], light["ink-1"]),
    )
    add(
        "lockup-v-dark",
        vw,
        vh,
        "assinatura vertical em fundo escuro",
        lock_v(tints["dark"][0], tints["dark"][1], dark["ink-1"]),
    )

    add("wordmark", wm_w, 100, "logotipo", '<g fill="%s">%s</g>' % (light["ink-1"], wm))
    add(
        "wordmark-dark",
        wm_w,
        100,
        "logotipo em fundo escuro",
        '<g fill="%s">%s</g>' % (dark["ink-1"], wm),
    )

    add(
        "compact",
        120,
        120,
        "marca compacta",
        '<rect width="120" height="120" rx="28" fill="%s"/>\n'
        '<g transform="translate(27 27) scale(0.66)">%s</g>'
        % (light["brand"], symbol_markup(on_brand_hex, ground_hex)),
    )
    return out


def check_derived(brand_hex):
    targets = [
        ("mobile/pubspec.yaml", 'adaptive_icon_background: "%s"' % brand_hex),
        (
            "mobile/android/app/src/main/res/values/colors.xml",
            '<color name="ic_launcher_background">%s</color>' % brand_hex,
        ),
    ]
    bad = []
    for rel, needle in targets:
        with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            if needle not in fh.read():
                bad.append("%s nao contem %r" % (rel, needle))
    if bad:
        raise SystemExit("marca divergente:\n  " + "\n  ".join(bad))
    print(
        "conferido: adaptive_icon_background e ic_launcher_background em %s" % brand_hex
    )


def check(kit):
    bad = []
    for rel, want in sorted(kit.items()):
        full = os.path.join(ROOT, rel)
        if not os.path.exists(full):
            bad.append("%s nao existe" % rel)
            continue
        with io.open(full, encoding="utf-8") as fh:
            if fh.read() != want:
                bad.append("%s divergente" % rel)
    if bad:
        raise SystemExit(
            "marca fora do gerador:\n  "
            + "\n  ".join(bad)
            + "\nRode: python marca/build.py"
        )
    print("conferido: %d arquivos da marca" % len(kit))


def main():
    palette = tokens()["color"]
    color = palette["light"]
    brand_hex = color["brand"]
    on_brand_hex = color["ink-on-brand"]
    brand, on_brand = rgb(brand_hex), rgb(on_brand_hex)
    ground = mix(on_brand, brand, GROUND_MIX)
    ground_hex = hexa(ground)
    kit = brand_files(color, palette["dark"], on_brand_hex, ground_hex)
    kit.update(superficies())

    print("marca: brand=%s glifo=%s chao=%s" % (brand_hex, on_brand_hex, ground_hex))

    if "--check" in sys.argv:
        check(kit)
        check_derived(brand_hex)
        return

    for rel, body in sorted(kit.items()):
        full = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        io.open(full, "w", encoding="utf-8", newline="\n").write(body)
    print("escrito %d arquivos da marca" % len(kit))

    write_png(
        render(1024, brand, on_brand, ground, rounded=False),
        "mobile/assets/brand/icon.png",
        flatten=brand,
    )
    write_png(
        render(1024, None, on_brand, ground, ratio=ADAPTIVE_GLYPH_RATIO),
        "mobile/assets/brand/icon_foreground.png",
    )
    check_derived(brand_hex)


if __name__ == "__main__":
    main()
