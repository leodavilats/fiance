
import io
import json
import os
import sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Marca fiance, direcao "Escala": um eixo com dois tracos de comprimentos
# diferentes (medir, comparar), a leitura solta a direita e um chao que corre
# de borda a borda. O chao fica DESCOLADO da haste de proposito -- encostado,
# ele vira o terceiro braco e a marca le "E".
#
# As coordenadas estao na mesma caixa de 100 de assets/brand/*.svg. Mexeu
# aqui, mexe la: o simbolo do produto e o icone do aplicativo sao o mesmo
# desenho, e e por isso que o --check existe.
GLYPH_VIEWBOX = 100.0
GLYPH_EIXO = [(6, 6), (76, 6), (76, 19), (19, 19), (19, 41),
              (56, 41), (56, 54), (19, 54), (19, 79), (6, 79)]
GLYPH_LEITURA = (83, 6, 96, 19, 3)   # x0, y0, x1, y1, raio
GLYPH_CHAO = (0, 87, 100, 95, 4)

# O chao e papel secundario: ink-on-brand puxado 35% na direcao de brand.
# Nao e cor nova, e mistura de dois tokens -- o tokens.json nao tem um papel
# "secundario sobre a marca", e inventar um so para o icone criaria uma cor
# que nenhuma tela conhece.
GROUND_MIX = 0.65

# Logotipo FIANCE: contorno proprio, caixa alta 100, linha de base y=100,
# haste 13. O detalhe de familia e que o braco medio do F, a travessa do A e o
# braco medio do E ocupam a MESMA faixa (y 49..62) -- o fio atravessando a
# palavra. Por isso a travessa do A fica um pouco alta e o braco do F um pouco
# baixo; e desvio de proposito, nao erro de desenho.
WORDMARK = [
    (62, 'M0 0L62 0L62 13L13 13L13 49L50 49L50 62L13 62L13 100L0 100Z'),
    (13, 'M0 0L13 0L13 100L0 100Z'),
    (74, 'M29 0L45 0L74 100L59.5 100L37 22.4L14.5 100L0 100Z '
         'M29.29 49L44.71 49L48.48 62L25.52 62Z'),
    (72, 'M0 0L13 0L59 76L59 0L72 0L72 100L59 100L13 24L13 100L0 100Z'),
    (70, 'M64.4 22.8A35 50 0 1 0 64.4 77.2L53.4 70.2A22 37 0 1 1 53.4 29.8Z'),
    (62, 'M0 0L62 0L62 13L13 13L13 49L48 49L48 62L13 62L13 87L62 87L62 100L0 100Z'),
]
WORDMARK_TRACK = 13

RADIUS_RATIO = 0.22
GLYPH_RATIO = 0.58
ADAPTIVE_GLYPH_RATIO = 0.42

SS = 4


# Pasta global na raiz do repo: e' aqui que o web (via assets do angular.json),
# o mobile (via image_path do flutter_launcher_icons) e o material de
# referencia da marca (fiance-*.svg, README) se encontram. Um so lugar, nao
# uma copia por plataforma.
BRAND_DIR = 'assets/brand'


def tokens():
    with io.open(os.path.join(ROOT, 'design-tokens', 'tokens.json'), encoding='utf-8') as fh:
        return json.load(fh)


def rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexa(color):
    return '#%02X%02X%02X' % color


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
    img = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if bg is not None:
        if rounded:
            draw.rounded_rectangle([0, 0, big - 1, big - 1],
                                   radius=big * RADIUS_RATIO, fill=bg)
        else:
            draw.rectangle([0, 0, big - 1, big - 1], fill=bg)
    draw_glyph(draw, big, ratio, fg, ground)
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


def favicon_svg(brand, on_brand, ground):
    side = 48.0
    scale, off = place(side, GLYPH_RATIO)
    eixo = 'L'.join('%g %g' % p for p in GLYPH_EIXO)
    leitura = GLYPH_LEITURA
    chao = GLYPH_CHAO
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" '
        'role="img" aria-label="fiance">\n'
        '  <rect width="48" height="48" rx="%g" fill="%s" />\n'
        '  <g transform="translate(%.4f,%.4f) scale(%.4f)">\n'
        '    <path d="M%sZ" fill="%s" />\n'
        '    <rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" />\n'
        '    <rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" />\n'
        '  </g>\n'
        '</svg>\n'
    ) % (
        side * RADIUS_RATIO, brand, off, off, scale,
        eixo, on_brand,
        leitura[0], leitura[1], leitura[2] - leitura[0], leitura[3] - leitura[1],
        leitura[4], on_brand,
        chao[0], chao[1], chao[2] - chao[0], chao[3] - chao[1], chao[4], ground,
    )


FAVICON = 'assets/brand/favicon.svg'

# O Angular CLI recusa asset fora do workspace do projeto ("must be within the
# workspace root"), entao o favicon.svg e os dois PNGs de web nao podem ser
# lidos direto de assets/brand por angular.json -- ganham copia idempotente
# em web/public/, escrita pelo mesmo gerador e conferida byte a byte pelo
# --check. O mobile nao tem essa restricao: flutter_launcher_icons le
# ../assets/brand/icon.png direto, sem copia.
FAVICON_WEB = 'web/public/favicon.svg'
FAVICON_512_WEB = 'web/public/favicon-512.png'
APPLE_TOUCH_ICON_WEB = 'web/public/apple-touch-icon.png'


def svg_doc(width, height, label, inner):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" '
        'width="%s" height="%s" role="img" aria-label="%s">\n'
        '<title>%s</title>\n%s\n</svg>\n'
    ) % (width, height, width, height, label, label, inner)


def symbol_markup(fg, ground):
    x0, y0, x1, y1, r = GLYPH_LEITURA
    cx0, cy0, cx1, cy1, cr = GLYPH_CHAO
    return (
        '<path d="M%sZ" fill="%s"/>'
        '<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s"/>'
        '<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s"/>'
    ) % (
        'L'.join('%g %g' % p for p in GLYPH_EIXO), fg,
        x0, y0, x1 - x0, y1 - y0, r, fg,
        cx0, cy0, cx1 - cx0, cy1 - cy0, cr, ground,
    )


def wordmark_markup():
    parts, x = [], 0
    for advance, d in WORDMARK:
        parts.append('<path d="%s" transform="translate(%g 0)"/>' % (d, x))
        x += advance + WORDMARK_TRACK
    return ''.join(parts), x - WORDMARK_TRACK


def brand_files(light, dark, on_brand_hex, ground_hex):
    """Kit da marca. Mesma geometria do icone -- e a razao de morar aqui."""
    wm, wm_w = wordmark_markup()
    mono = ('currentColor', 'currentColor')
    # O chao e neutro (ink-3), nao um azul mais claro: ele e referencia, e
    # referencia nao julga. ink-3 tambem e o unico neutro que passa de 3:1
    # como forma sobre o chao dos dois temas.
    tints = {
        'light': (light['brand'], light['ink-3']),
        'dark': (dark['brand'], dark['ink-3']),
    }
    out = {}

    def add(name, width, height, what, inner):
        out['%s/fiance-%s.svg' % (BRAND_DIR, name)] = svg_doc(
            width, height, 'Fiance, ' + what, inner)

    # simbolo
    add('symbol', 100, 100, 'simbolo', symbol_markup(*tints['light']))
    add('symbol-dark', 100, 100, 'simbolo em fundo escuro', symbol_markup(*tints['dark']))
    add('symbol-mono', 100, 100, 'simbolo monocromatico', symbol_markup(*mono))

    # assinatura horizontal: simbolo a 132, caixa alta da palavra centrada nele
    size, gap = 132, 46
    def lock_h(fg, ground, ink):
        return ('<g transform="scale(%g)">%s</g>\n'
                '<g fill="%s" transform="translate(%g 16)">%s</g>') % (
            size / 100.0, symbol_markup(fg, ground), ink, size + gap, wm)
    hw = size + gap + wm_w
    add('lockup-h', hw, size, 'assinatura horizontal',
        lock_h(tints['light'][0], tints['light'][1], light['ink-1']))
    add('lockup-h-dark', hw, size, 'assinatura horizontal em fundo escuro',
        lock_h(tints['dark'][0], tints['dark'][1], dark['ink-1']))
    add('lockup-h-mono', hw, size, 'assinatura horizontal monocromatica',
        lock_h(mono[0], mono[1], 'currentColor'))

    # assinatura vertical
    vs, vgap, vcap = 150, 42, 0.84
    vwm = wm_w * vcap
    vw, vh = round(max(vs, vwm), 2), round(vs + vgap + 100 * vcap, 2)
    def lock_v(fg, ground, ink):
        return ('<g transform="translate(%.2f 0) scale(%g)">%s</g>\n'
                '<g fill="%s" transform="translate(%.2f %g) scale(%g)">%s</g>') % (
            (vw - vs) / 2.0, vs / 100.0, symbol_markup(fg, ground),
            ink, (vw - vwm) / 2.0, vs + vgap, vcap, wm)
    add('lockup-v', vw, vh, 'assinatura vertical',
        lock_v(tints['light'][0], tints['light'][1], light['ink-1']))
    add('lockup-v-dark', vw, vh, 'assinatura vertical em fundo escuro',
        lock_v(tints['dark'][0], tints['dark'][1], dark['ink-1']))

    # logotipo isolado
    add('wordmark', wm_w, 100, 'logotipo', '<g fill="%s">%s</g>' % (light['ink-1'], wm))
    add('wordmark-dark', wm_w, 100, 'logotipo em fundo escuro',
        '<g fill="%s">%s</g>' % (dark['ink-1'], wm))

    # selo compacto: app bar, splash, avatar
    add('compact', 120, 120, 'marca compacta',
        '<rect width="120" height="120" rx="28" fill="%s"/>\n'
        '<g transform="translate(27 27) scale(0.66)">%s</g>' % (
            light['brand'], symbol_markup(on_brand_hex, ground_hex)))
    return out


def check_derived(brand_hex):
    targets = [
        ('web/src/index.html', '<meta name="theme-color" content="%s" />' % brand_hex),
        ('mobile/pubspec.yaml', 'adaptive_icon_background: "%s"' % brand_hex),
        ('mobile/android/app/src/main/res/values/colors.xml',
         '<color name="ic_launcher_background">%s</color>' % brand_hex),
    ]
    bad = []
    for rel, needle in targets:
        with io.open(os.path.join(ROOT, rel), encoding='utf-8') as fh:
            if needle not in fh.read():
                bad.append('%s nao contem %r' % (rel, needle))
    if bad:
        raise SystemExit('marca divergente:\n  ' + '\n  '.join(bad))
    print('conferido: theme-color, adaptive_icon_background e '
          'ic_launcher_background em %s' % brand_hex)


def check(brand_hex, on_brand_hex, ground_hex, kit):
    favicon = favicon_svg(brand_hex, on_brand_hex, ground_hex)
    esperado = {FAVICON: favicon, FAVICON_WEB: favicon}
    esperado.update(kit)
    bad = []
    for rel, want in sorted(esperado.items()):
        full = os.path.join(ROOT, rel)
        if not os.path.exists(full):
            bad.append('%s nao existe' % rel)
            continue
        with io.open(full, encoding='utf-8') as fh:
            if fh.read() != want:
                bad.append('%s divergente' % rel)
    if bad:
        raise SystemExit(
            'marca fora do gerador:\n  ' + '\n  '.join(bad) +
            '\nRode: python design-tokens/build-icons.py'
        )
    print('conferido: %s (+ copia em %s) e %d arquivos em %s' %
          (FAVICON, FAVICON_WEB, len(kit), BRAND_DIR))
    check_derived(brand_hex)


def main():
    palette = tokens()['color']
    color = palette['light']
    brand_hex = color['brand']
    on_brand_hex = color['ink-on-brand']
    brand, on_brand = rgb(brand_hex), rgb(on_brand_hex)
    ground = mix(on_brand, brand, GROUND_MIX)
    ground_hex = hexa(ground)
    kit = brand_files(color, palette['dark'], on_brand_hex, ground_hex)

    print('marca: brand=%s glifo=%s chao=%s' % (brand_hex, on_brand_hex, ground_hex))

    if '--check' in sys.argv:
        check(brand_hex, on_brand_hex, ground_hex, kit)
        return

    favicon = favicon_svg(brand_hex, on_brand_hex, ground_hex)
    for rel in (FAVICON, FAVICON_WEB):
        full = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        io.open(full, 'w', encoding='utf-8', newline='\n').write(favicon)
        print('escrito %s' % rel)
    for rel, body in sorted(kit.items()):
        full = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        io.open(full, 'w', encoding='utf-8', newline='\n').write(body)
    print('escrito %d arquivos em %s' % (len(kit), BRAND_DIR))

    favicon_512 = render(512, brand, on_brand, ground)
    apple_icon = render(180, brand, on_brand, ground, rounded=False)
    write_png(favicon_512, 'assets/brand/favicon-512.png')
    write_png(favicon_512, FAVICON_512_WEB)
    write_png(apple_icon, 'assets/brand/apple-touch-icon.png', flatten=brand)
    write_png(apple_icon, APPLE_TOUCH_ICON_WEB, flatten=brand)
    write_png(render(1024, brand, on_brand, ground, rounded=False),
              'assets/brand/icon.png', flatten=brand)
    write_png(render(1024, None, on_brand, ground, ratio=ADAPTIVE_GLYPH_RATIO),
              'assets/brand/icon_foreground.png')
    check_derived(brand_hex)


if __name__ == '__main__':
    main()
