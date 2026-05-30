# flake8: noqa

# Enums
from .enums import (
    AssetCategory,
    AssetType,
    Liquidez,
    OptimizationStrategy,
    RendaFixaType,
    RiskProfile,
    TaxType,
)

# Company & Scoring
from .company import CompanyFundamentals, ScoredCompany

# Recommendation
from .recommendation import Allocation, RecommendRequest, RecommendResponse

# Analysis
from .analysis import (
    AssetAnalysis,
    DecisionBlock,
    FairPriceBlock,
    TechnicalBlock,
)

# Portfolio
from .portfolio import (
    PortfolioEvaluationRequest,
    PortfolioEvaluationResponse,
    PortfolioItem,
    PortfolioPosition,
    PortfolioSnapshot,
    PortfolioStateResponse,
    SavePortfolioRequest,
    StoredPortfolioItem,
)

# Watchlist
from .watchlist import WatchlistItem, WatchlistRequest

# Goals
from .goal import Goal, GoalsRequest

# Preferences
from .preferences import Preferences, PreferencesRequest

# Opportunities
from .opportunity import Opportunity, OpportunitiesResponse

# Dashboard
from .dashboard import (
    Alert,
    CategoryAllocation,
    DashboardResponse,
    DashboardSummary,
)

# Dip Analysis
from .dip import (
    DipAnalysisResponse,
    DipScanItem,
    DipScannerResponse,
    DipScoreBreakdownSchema,
    NewsItemSchema,
)

# Renda Fixa
from .renda_fixa import (
    RendaFixaAsset,
    RendaFixaAnalysisResult,
    RendaFixaCompareRequest,
    RendaFixaCompareResponse,
    ReferenceRates,
)

__all__ = [
    # Enums
    "AssetCategory",
    "AssetType",
    "Liquidez",
    "OptimizationStrategy",
    "RendaFixaType",
    "RiskProfile",
    "TaxType",
    # Company & Scoring
    "CompanyFundamentals",
    "ScoredCompany",
    # Recommendation
    "Allocation",
    "RecommendRequest",
    "RecommendResponse",
    # Analysis
    "AssetAnalysis",
    "DecisionBlock",
    "FairPriceBlock",
    "TechnicalBlock",
    # Portfolio
    "PortfolioEvaluationRequest",
    "PortfolioEvaluationResponse",
    "PortfolioItem",
    "PortfolioPosition",
    "PortfolioSnapshot",
    "PortfolioStateResponse",
    "SavePortfolioRequest",
    "StoredPortfolioItem",
    # Watchlist
    "WatchlistItem",
    "WatchlistRequest",
    # Goals
    "Goal",
    "GoalsRequest",
    # Preferences
    "Preferences",
    "PreferencesRequest",
    # Opportunities
    "Opportunity",
    "OpportunitiesResponse",
    # Dashboard
    "Alert",
    "CategoryAllocation",
    "DashboardResponse",
    "DashboardSummary",
    # Dip Analysis
    "DipAnalysisResponse",
    "DipScanItem",
    "DipScannerResponse",
    "DipScoreBreakdownSchema",
    "NewsItemSchema",
    # Renda Fixa
    "RendaFixaAsset",
    "RendaFixaAnalysisResult",
    "RendaFixaCompareRequest",
    "RendaFixaCompareResponse",
    "ReferenceRates",
]
