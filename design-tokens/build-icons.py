"""Gera a marca do fiance a partir de tokens.json.

Emite:
  web/public/favicon.svg              marca vetorial (aba do navegador)
  web/public/favicon-512.png          fallback raster
  web/public/apple-touch-icon.png     180x180, exigido por iOS
  mobile/assets/icon/icon.png         launcher iOS/Android legado
  mobile/assets/icon/icon_foreground.png   camada adaptativa Android

A marca é a mesma dos logos em app (LogoComponent no web, AppLogo no mobile):
quadrado arredondado com fundo `brand` e o glifo `trending-up` do Lucide em
`ink-on-brand`. Antes deste script os artefatos eram escritos a mão e ficaram
para tras quando a marca mudou: favicon e launcher ainda traziam o gradiente
verde-ciano abandonado, com glifo escuro sobre fundo que hoje pede glifo claro.

Uso: python design-tokens/build-icons.py [--check]
"""

import io
import json
import os
import sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Geometria do glifo `trending-up` do Lucide, no viewBox 24x24 de origem.
GLYPH = [
    [(22, 7), (13.5, 15.5), (8.5, 10.5), (2, 17)],
    [(16, 7), (22, 7), (22, 13)],
]
GLYPH_STROKE = 2.0
GLYPH_VIEWBOX = 24.0

# Proporcoes da marca, relativas ao lado do quadrado.
RADIUS_RATIO = 0.22
# O logo em app usa 0.56; o icone ganha um respiro a mais porque precisa ser
# legivel a 16px na aba e dentro da mascara do launcher.
GLYPH_RATIO = 0.58
# Android garante apenas os 66% centrais da camada adaptativa. O glifo entra
# menor para nao ser cortado por mascara circular.
ADAPTIVE_GLYPH_RATIO = 0.42

SS = 4  # supersampling


def tokens():
    with io.open(os.path.join(ROOT, 'design-tokens', 'tokens.json'), encoding='utf-8') as fh:
        return json.load(fh)


def rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def glyph_segments(size, ratio):
    """Pontos do glifo escalados e centralizados num quadrado de lado `size`."""
    span = size * ratio
    scale = span / GLYPH_VIEWBOX
    offset = (size - span) / 2.0
    out = []
    for poly in GLYPH:
        out.append([(x * scale + offset, y * scale + offset) for x, y in poly])
    return out, GLYPH_STROKE * scale


def draw_glyph(draw, size, ratio, color):
    polys, width = glyph_segments(size, ratio)
    r = width / 2.0
    for poly in polys:
        draw.line(poly, fill=color, width=int(round(width)), joint='curve')
        # `joint='curve'` arredonda as juncoes, mas nao as pontas.
        for x, y in (poly[0], poly[-1]):
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def render(size, bg, fg, ratio=GLYPH_RATIO, rounded=True):
    big = size * SS
    img = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if bg is not None:
        if rounded:
            draw.rounded_rectangle([0, 0, big - 1, big - 1],
                                   radius=big * RADIUS_RATIO, fill=bg)
        else:
            draw.rectangle([0, 0, big - 1, big - 1], fill=bg)
    draw_glyph(draw, big, ratio, fg)
    return img.resize((size, size), Image.LANCZOS)


def write_png(img, path, flatten=None):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if flatten is not None:
        base = Image.new('RGB', img.size, flatten)
        base.paste(img, mask=img.split()[3])
        img = base
    img.save(full)
    print('escrito %s (%dx%d)' % (path, img.size[0], img.size[1]))


def favicon_svg(brand, on_brand):
    polys = '\n'.join(
        '    <polyline points="%s" />' % ' '.join('%g %g' % p for p in poly)
        for poly in GLYPH
    )
    side = 48.0
    span = side * GLYPH_RATIO
    scale = span / GLYPH_VIEWBOX
    offset = (side - span) / 2.0
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" '
        'role="img" aria-label="fiance">\n'
        '  <rect width="48" height="48" rx="%g" fill="%s" />\n'
        '  <g transform="translate(%.4f,%.4f) scale(%.4f)" fill="none" stroke="%s"\n'
        '     stroke-width="%g" stroke-linecap="round" stroke-linejoin="round">\n'
        '%s\n'
        '  </g>\n'
        '</svg>\n'
    ) % (side * RADIUS_RATIO, brand, offset, offset, scale, on_brand, GLYPH_STROKE, polys)
    return svg


FAVICON = 'web/public/favicon.svg'


def check_derived(brand_hex):
    """Confere os dois hex que precisam existir fora do token.

    `theme-color` e um meta e `adaptive_icon_background` e YAML: nenhum dos dois
    aceita `var(--fi-brand)`. Como a marca ja mudou uma vez sem que estes
    acompanhassem, a divergencia falha aqui em vez de aparecer no launcher.
    """
    targets = [
        ('web/src/index.html', '<meta name="theme-color" content="%s" />' % brand_hex),
        ('mobile/pubspec.yaml', 'adaptive_icon_background: "%s"' % brand_hex),
    ]
    bad = []
    for rel, needle in targets:
        with io.open(os.path.join(ROOT, rel), encoding='utf-8') as fh:
            if needle not in fh.read():
                bad.append('%s nao contem %r' % (rel, needle))
    if bad:
        raise SystemExit('marca divergente:\n  ' + '\n  '.join(bad))
    print('conferido: theme-color e adaptive_icon_background em %s' % brand_hex)


def check(brand_hex, on_brand_hex):
    """Modo do CI.

    Confere o favicon (texto, deterministico) e os hex derivados. **Nao** compara
    os PNG byte a byte: a rasterizacao muda com a versao do Pillow e o check
    ficaria intermitente. O que precisa nao divergir e a cor da marca, e essa e
    verificavel de forma estavel.
    """
    want = favicon_svg(brand_hex, on_brand_hex)
    with io.open(os.path.join(ROOT, FAVICON), encoding='utf-8') as fh:
        got = fh.read()
    if got != want:
        raise SystemExit(
            '%s divergente do token. Rode: python design-tokens/build-icons.py' % FAVICON
        )
    print('conferido: %s' % FAVICON)
    check_derived(brand_hex)


def main():
    color = tokens()['color']['light']
    brand_hex = color['brand']
    on_brand_hex = color['ink-on-brand']
    brand, on_brand = rgb(brand_hex), rgb(on_brand_hex)

    print('marca: brand=%s glifo=%s' % (brand_hex, on_brand_hex))

    if '--check' in sys.argv:
        check(brand_hex, on_brand_hex)
        return

    io.open(os.path.join(ROOT, FAVICON), 'w', encoding='utf-8', newline='\n').write(
        favicon_svg(brand_hex, on_brand_hex)
    )
    print('escrito %s' % FAVICON)
    write_png(render(512, brand, on_brand), 'web/public/favicon-512.png')
    # iOS ignora transparencia e canto arredondado: aplica a propria mascara.
    write_png(render(180, brand, on_brand, rounded=False),
              'web/public/apple-touch-icon.png', flatten=brand)
    # Launcher aplica a propria mascara: o icone vai full-bleed e sem alfa,
    # como remove_alpha_ios no pubspec exige.
    write_png(render(1024, brand, on_brand, rounded=False),
              'mobile/assets/icon/icon.png', flatten=brand)
    write_png(render(1024, None, on_brand, ratio=ADAPTIVE_GLYPH_RATIO),
              'mobile/assets/icon/icon_foreground.png')
    check_derived(brand_hex)


if __name__ == '__main__':
    main()
