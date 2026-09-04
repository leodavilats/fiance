from __future__ import annotations

import io
import json
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

LARGURA = 1200
ALTURA = 630

_RAIZ = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_TOKENS = os.path.join(_RAIZ, "design-tokens", "tokens.json")


@lru_cache(maxsize=1)
def _paleta() -> dict[str, str]:
    with open(_TOKENS, encoding="utf-8") as arquivo:
        tokens = json.load(arquivo)

    escuro = tokens["color"]["dark"]
    return {
        "ground": escuro["ground-0"],
        "ground-1": escuro["ground-1"],
        "hairline": escuro["hairline"],
        "ink": escuro["ink-1"],
        "ink-2": escuro["ink-2"],
        "ink-3": escuro["ink-3"],
        "brand": escuro["brand"],
        "favorable": escuro["state-favorable"],
        "attention": escuro["state-attention"],
        "adverse": escuro["state-adverse"],
        "indeterminate": escuro["state-indeterminate"],
    }


_ESTADO_POR_VEREDITO = {
    "STRONG_BUY": "favorable",
    "BUY": "favorable",
    "HOLD": "attention",
    "SELL": "adverse",
    "STRONG_SELL": "adverse",
    "UNKNOWN": "indeterminate",
}


def _fonte(tamanho: int, negrito: bool = False) -> ImageFont.ImageFont:
    candidatas = (
        ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"]
        if negrito
        else ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf"]
    )
    for nome in candidatas:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def _brl(valor: float | None) -> str:
    if valor is None:
        return "—"
    inteiro, centavos = f"{valor:,.2f}".split(".")
    return "R$ " + inteiro.replace(",", ".") + "," + centavos


def render(
    symbol: str,
    name: str | None,
    verdict: str,
    verdict_label: str,
    price: float | None,
    fair_price: float | None,
) -> bytes:
    cores = _paleta()

    imagem = Image.new("RGB", (LARGURA, ALTURA), cores["ground"])
    pincel = ImageDraw.Draw(imagem)

    margem = 80
    estado = cores[_ESTADO_POR_VEREDITO.get(verdict, "indeterminate")]

    pincel.rectangle([0, 0, 16, ALTURA], fill=estado)

    pincel.text((margem, 72), "fiance", font=_fonte(28, negrito=True), fill=cores["brand"])

    pincel.text((margem, 150), symbol.upper(), font=_fonte(104, negrito=True), fill=cores["ink"])

    if name:
        recorte = name if len(name) <= 46 else name[:45] + "…"
        pincel.text((margem, 274), recorte, font=_fonte(34), fill=cores["ink-2"])

    pincel.text((margem, 356), verdict_label, font=_fonte(46, negrito=True), fill=estado)

    pincel.line([(margem, 436), (LARGURA - margem, 436)], fill=cores["hairline"], width=2)

    colunas = (
        ("Preço", _brl(price)),
        ("Preço justo estimado", _brl(fair_price)),
    )
    x = margem
    for rotulo, valor in colunas:
        pincel.text((x, 464), rotulo.upper(), font=_fonte(22), fill=cores["ink-3"])
        pincel.text((x, 498), valor, font=_fonte(46, negrito=True), fill=cores["ink"])
        x += 420

    pincel.text(
        (margem, ALTURA - 62),
        "Leitura do sistema, não recomendação de compra. Não há garantia de retorno.",
        font=_fonte(22),
        fill=cores["ink-3"],
    )

    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
