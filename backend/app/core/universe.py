from __future__ import annotations

CURATED_BR_STOCKS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "BBAS3.SA",
    "WEGE3.SA",
    "ITSA4.SA",
    "B3SA3.SA",
    "RENT3.SA",
    "EQTL3.SA",
    "TAEE11.SA",
    "CPLE6.SA",
    "SAPR11.SA",
    "VIVT3.SA",
    "EGIE3.SA",
    "KLBN11.SA",
    "SUZB3.SA",
    "TOTS3.SA",
    "RADL3.SA",
    "RAIL3.SA",
]

CURATED_FIIS = [
    "HGLG11.SA",
    "MXRF11.SA",
    "KNCR11.SA",
    "KNRI11.SA",
    "BCFF11.SA",
    "XPML11.SA",
    "VISC11.SA",
    "HGRE11.SA",
    "MALL11.SA",
    "BTLG11.SA",
    "VINO11.SA",
    "RBRR11.SA",
]

CURATED_US = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "BRK-B",
    "JNJ",
    "JPM",
    "V",
    "KO",
    "PEP",
    "SCHD",
    "VOO",
]

CURATED_CRYPTO = ["BTC", "ETH", "SOL"]


def curated_all() -> list[str]:

    return CURATED_BR_STOCKS + CURATED_FIIS + CURATED_US + CURATED_CRYPTO
