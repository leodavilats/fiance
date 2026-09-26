from __future__ import annotations


def _virgula(texto: str) -> str:
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def reais(valor: float | None) -> str:
    return "R$ " + _virgula(f"{valor or 0:,.2f}")


def pct(fracao: float, casas: int = 1) -> str:
    return _virgula(f"{fracao * 100:,.{casas}f}") + "%"


def numero(valor: float, casas: int = 2) -> str:
    return _virgula(f"{valor:,.{casas}f}")
