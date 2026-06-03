from .analysis import (
    AssetAnalysis,
    DecisionBlock,
    FairPriceBlock,
    TechnicalBlock,
)
from .company import CompanyFundamentals, ScoredCompany
from .dashboard import (
    Alert,
    CategoryAllocation,
    DashboardResponse,
    DashboardSummary,
)
from .dip import (
    DipAnalysisResponse,
    DipScanItem,
    DipScannerResponse,
    DipScoreBreakdownSchema,
    NewsItemSchema,
)
from .enums import (
    AssetCategory,
    AssetType,
    Liquidez,
    OptimizationStrategy,
    RendaFixaType,
    RiskProfile,
    TaxType,
)
from .goal import Goal, GoalsRequest, SectorGoal, SectorGoalsRequest
from .opportunity import OpportunitiesResponse, Opportunity
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
from .preferences import Preferences, PreferencesRequest
from .projection import (
    PassiveIncomeMonth,
    PassiveIncomeProjectionRequest,
    PassiveIncomeProjectionResponse,
    SectorAllocation,
    SectorAllocationResponse,
)
from .quick_invest import (
    QuickInvestAllocation,
    QuickInvestRequest,
    QuickInvestResponse,
)
from .recommendation import Allocation, RecommendRequest, RecommendResponse
from .renda_fixa import (
    ReferenceRates,
    RendaFixaAnalysisResult,
    RendaFixaAsset,
    RendaFixaCompareRequest,
    RendaFixaCompareResponse,
)

__all__ = [
    "AssetCategory",
    "AssetType",
    "Liquidez",
    "OptimizationStrategy",
    "RendaFixaType",
    "RiskProfile",
    "TaxType",
    "CompanyFundamentals",
    "ScoredCompany",
    "Allocation",
    "RecommendRequest",
    "RecommendResponse",
    "AssetAnalysis",
    "DecisionBlock",
    "FairPriceBlock",
    "TechnicalBlock",
    "PortfolioEvaluationRequest",
    "PortfolioEvaluationResponse",
    "PortfolioItem",
    "PortfolioPosition",
    "PortfolioSnapshot",
    "PortfolioStateResponse",
    "SavePortfolioRequest",
    "StoredPortfolioItem",
    "Goal",
    "GoalsRequest",
    "SectorGoal",
    "SectorGoalsRequest",
    "Preferences",
    "PreferencesRequest",
    "Opportunity",
    "OpportunitiesResponse",
    "Alert",
    "CategoryAllocation",
    "DashboardResponse",
    "DashboardSummary",
    "DipAnalysisResponse",
    "DipScanItem",
    "DipScannerResponse",
    "DipScoreBreakdownSchema",
    "NewsItemSchema",
    "RendaFixaAsset",
    "RendaFixaAnalysisResult",
    "RendaFixaCompareRequest",
    "RendaFixaCompareResponse",
    "ReferenceRates",
    "PassiveIncomeMonth",
    "PassiveIncomeProjectionRequest",
    "PassiveIncomeProjectionResponse",
    "SectorAllocation",
    "SectorAllocationResponse",
    "QuickInvestRequest",
    "QuickInvestResponse",
    "QuickInvestAllocation",
]
