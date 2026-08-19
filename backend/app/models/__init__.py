from .analysis import (
    AssetAnalysis,
    CompareResponse,
    DecisionBlock,
    FairPriceBlock,
    TechnicalBlock,
)
from .benchmark import BenchmarkPoint, BenchmarkResponse
from .company import CompanyFundamentals, ScoredCompany
from .dashboard import (
    Alert,
    CategoryAllocation,
    DashboardResponse,
    DashboardSummary,
    PortfolioHealth,
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
    ClosedTrade,
    ClosedTradesResponse,
    PortfolioEvaluationRequest,
    PortfolioEvaluationResponse,
    PortfolioItem,
    PortfolioPosition,
    PortfolioSnapshot,
    PortfolioStateResponse,
    SavePortfolioRequest,
    SellRequest,
    StoredPortfolioItem,
)
from .preferences import Preferences, PreferencesRequest
from .projection import (
    PassiveIncomeMonth,
    PassiveIncomeProjectionRequest,
    PassiveIncomeProjectionResponse,
)
from .quick_invest import (
    QuickInvestAllocation,
    QuickInvestRequest,
    QuickInvestResponse,
)
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
    "AssetAnalysis",
    "CompareResponse",
    "DecisionBlock",
    "FairPriceBlock",
    "TechnicalBlock",
    "BenchmarkPoint",
    "BenchmarkResponse",
    "PortfolioHealth",
    "PortfolioEvaluationRequest",
    "PortfolioEvaluationResponse",
    "PortfolioItem",
    "PortfolioPosition",
    "PortfolioSnapshot",
    "PortfolioStateResponse",
    "SavePortfolioRequest",
    "StoredPortfolioItem",
    "SellRequest",
    "ClosedTrade",
    "ClosedTradesResponse",
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
    "QuickInvestRequest",
    "QuickInvestResponse",
    "QuickInvestAllocation",
]
