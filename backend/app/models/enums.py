from enum import StrEnum


class RiskProfile(StrEnum):
    conservative = "conservative"
    moderate = "moderate"
    aggressive = "aggressive"


class OptimizationStrategy(StrEnum):
    score_weighted = "score_weighted"
    max_sharpe = "max_sharpe"
    min_volatility = "min_volatility"
    hrp = "hrp"


class AssetType(StrEnum):
    br_stock = "br_stock"
    fii = "fii"
    us_stock = "us_stock"
    crypto = "crypto"


class AssetCategory(StrEnum):
    renda_fixa = "renda_fixa"
    acoes_br = "acoes_br"
    acoes_int = "acoes_int"
    fiis = "fiis"
    cripto = "cripto"


class RendaFixaType(StrEnum):
    cdb = "cdb"
    lci = "lci"
    lca = "lca"
    tesouro_selic = "tesouro_selic"
    tesouro_ipca = "tesouro_ipca"
    tesouro_pre = "tesouro_pre"
    lc = "lc"
    cri = "cri"
    cra = "cra"


class TaxType(StrEnum):
    pre_fixado = "pre_fixado"
    pos_fixado = "pos_fixado"
    hibrido = "hibrido"


class Liquidez(StrEnum):
    diaria = "diaria"
    no_vencimento = "no_vencimento"
