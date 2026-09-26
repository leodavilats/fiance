from __future__ import annotations

SEGMENT_PAPER = "papel"
SEGMENT_UNCLASSIFIED = "nao_classificado"

PAPER_REVIEWED_ON = "2026-09-25"

PAPER_FIIS = frozenset(
    {
        "AFHI11",
        "BCRI11",
        "BTCI11",
        "CPTS11",
        "CVBI11",
        "DEVA11",
        "HABT11",
        "HCTR11",
        "HGCR11",
        "IRDM11",
        "KNCR11",
        "KNHY11",
        "KNIP11",
        "KNSC11",
        "KNUQ11",
        "MCCI11",
        "MXRF11",
        "OUJP11",
        "PORD11",
        "RBRR11",
        "RBRY11",
        "RECR11",
        "RZAK11",
        "URPR11",
        "VCJR11",
        "VGHF11",
        "VGIP11",
        "VRTA11",
        "XPCI11",
    }
)


def fii_segment(symbol: str | None) -> str:
    base = (symbol or "").upper().removesuffix(".SA")
    return SEGMENT_PAPER if base in PAPER_FIIS else SEGMENT_UNCLASSIFIED
