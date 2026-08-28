"""Carteira de demonstração para o estado vazio.

Tela vazia com um convite não ensina nada: a pessoa não sabe o que o produto faz
até ver o produto fazendo. A demonstração mostra a análise funcionando sobre uma
carteira plausível, com a faixa "isto é exemplo" **inescapável** — em todo item,
não só no topo, porque quem rola perde o aviso do topo.

Duas regras que o desenho garante:

* **Nunca é gravada.** A demonstração não toca a carteira do usuário nem cria
  posição nenhuma; é resposta de leitura. Semear dado de exemplo na conta de
  alguém é o tipo de coisa que depois aparece na declaração.
* **Os ativos são declarados aqui**, e não sorteados do universo. Uma seleção
  aleatória poderia montar uma carteira absurda — cinco bancos, ou tudo em
  micro cap — e o veredito de risco sobre ela ensinaria a coisa errada.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from app.models import AssetType, PortfolioEvaluationRequest, PortfolioItem
from app.services import PortfolioService

router = APIRouter()

portfolio_service = PortfolioService()

#: Carteira de exemplo: diversificada o bastante para o veredito de risco ser
#: emitido (quatro ativos é o mínimo) e para a composição ter mais de uma cor.
#: Os preços médios são redondos de propósito — número quebrado aqui sugere que
#: veio de algum lugar real.
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
    """A análise real rodando sobre uma carteira de exemplo.

    Usa exatamente o mesmo caminho de avaliação da carteira de verdade: uma
    demonstração que passasse por um cálculo simplificado mostraria uma tela que
    o produto não entrega.
    """
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
    """Só a lista, para telas que não precisam da avaliação inteira."""
    await asyncio.sleep(0)
    return {
        "is_demo": True,
        "disclaimer": DISCLAIMER,
        "items": DEMO_POSITIONS,
        "asset_types": sorted({AssetType.br_stock.value, AssetType.fii.value, AssetType.etf.value}),
    }
