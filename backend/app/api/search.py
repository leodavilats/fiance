"""Busca global.

Sem cerca de plano: procurar o que já é seu não é recurso premium, e uma caixa
de busca que responde 402 é pior que uma que não existe.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.services import search_service

router = APIRouter()


class SearchItem(BaseModel):
    kind: str = Field(..., description="position | fixed_income | asset")
    title: str
    subtitle: str
    ref: str = Field(
        ...,
        description=(
            "Ticker, ou id da posição de renda fixa. O cliente decide a rota: a árvore de "
            "navegação do web e a do app diferem, e um catálogo de rotas no servidor seria "
            "uma segunda verdade sobre a arquitetura de informação."
        ),
    )


class SearchGroup(BaseModel):
    label: str
    items: list[SearchItem]


class SearchResponse(BaseModel):
    query: str
    groups: list[SearchGroup] = Field(
        ...,
        description=(
            "Na ordem em que devem ser lidos: o que é da pessoa e, por último, o que "
            "existe no mercado. Destinos de tela ficam com o cliente."
        ),
    )
    total: int


@router.get("/search", response_model=SearchResponse)
async def global_search(
    q: str = Query("", max_length=64, description="O que a pessoa digitou"),
    user_id: str = Depends(get_current_user),
) -> SearchResponse:
    """Busca na carteira, na renda fixa e no universo."""
    return SearchResponse(**search_service.search(q, user_id))
