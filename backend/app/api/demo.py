from __future__ import annotations

import asyncio

from fastapi import APIRouter

from app.models import AssetType, PortfolioEvaluationRequest, PortfolioItem
from app.services import PortfolioService

router = APIRouter()

portfolio_service = PortfolioService()

DEMO_POSITIONS: list[dict] = [
    {"ticker": "PETR4", "quantity": 200, "avg_price": 32.00, "category": "acoes_br"},
    {"ticker": "ITUB4", "quantity": 300, "avg_price": 28.00, "category": "acoes_br"},
    {"ticker": "VALE3", "quantity": 100, "avg_price": 62.00, "category": "acoes_br"},
    {"ticker": "HGLG11", "quantity": 80, "avg_price": 155.00, "category": "fiis"},
    {"ticker": "BOVA11", "quantity": 50, "avg_price": 120.00, "category": "etfs"},
]

DISCLAIMER = (
    "Carteira de exemplo. Nenhum destes ativos está na sua conta, e nada aqui é "
    "recomendação — serve para você ver como a análise funciona antes de "
    "cadastrar a sua."
)


@router.get("/demo/portfolio")
async def demo_portfolio() -> dict:
    request = PortfolioEvaluationRequest(
        items=[
            PortfolioItem(
                ticker=p["ticker"],
                quantity=p["quantity"],
                avg_price=p["avg_price"],
                category=p["category"],
            )
            for p in DEMO_POSITIONS
        ]
    )

    evaluation = await portfolio_service.evaluate_portfolio(request)

    return {
        "is_demo": True,
        "disclaimer": DISCLAIMER,
        "evaluation": evaluation.model_dump(),
    }


@router.get("/demo/assets")
async def demo_assets() -> dict:
    await asyncio.sleep(0)
    return {
        "is_demo": True,
        "disclaimer": DISCLAIMER,
        "items": DEMO_POSITIONS,
        "asset_types": sorted({AssetType.br_stock.value, AssetType.fii.value, AssetType.etf.value}),
    }
