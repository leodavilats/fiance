from enum import Enum


class RiskProfile(str, Enum):
    conservative = "conservative"
    moderate = "moderate"
    aggressive = "aggressive"


class OptimizationStrategy(str, Enum):
    score_weighted = "score_weighted"
    max_sharpe = "max_sharpe"
    min_volatility = "min_volatility"
    hrp = "hrp"


class AssetType(str, Enum):
    br_stock = "br_stock"
    fii = "fii"
    us_stock = "us_stock"
    crypto = "crypto"
