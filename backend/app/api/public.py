"""Superfície pública: o que o robô de busca lê, e mais nada.

O canal de aquisição do produto é a página de ativo indexável. Isso obriga a
existir uma leitura **sem titular**: mesma URL, mesmo HTML, para o robô e para
quem chega pelo link. Duas consequências que valem estar escritas:

* **Nada aqui toca dado de usuário.** A análise roda impessoal — sem o yield
  desejado de ninguém — e nenhuma rota deste módulo abre sessão. É por isso que
  ele fica fora do router protegido, e não por conveniência.
* **O teto de abuso é por IP.** Sem autenticação não há `user_id`, então o
  contador usa `ip:<endereço>` como chave. É a mesma tabela e o mesmo código do
  teto por usuário: a primitiva não precisou saber a diferença.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.core import usage
from app.core.brt import now_brt
from app.core.config import get_settings
from app.core.universe import get_universe
from app.models import AssetAnalysis
from app.services import AssetService

router = APIRouter()

asset_service = AssetService()

# Mais folgado que o teto por usuário porque um IP pode ser uma operadora
# inteira atrás de NAT — apertar aqui bloqueia gente legítima em bloco.
PUBLIC_PER_MINUTE = 60


async def _ip_rate_limit(request: Request, cost: int = 1) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return

    client = request.client.host if request.client else "desconhecido"
    count = usage.increment(
        f"ip:{client}",
        "public",
        usage.minute_window(),
        ttl_seconds=usage.MINUTE * 2,
        amount=cost,
    )
    if count > PUBLIC_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Muitas requisições. Aguarde um minuto.",
            headers={"Retry-After": "60"},
        )


@router.get("/public/asset/{symbol}", response_model=AssetAnalysis)
async def public_asset(symbol: str, request: Request) -> AssetAnalysis:
    """Análise impessoal de um ativo, para renderização no servidor."""
    await _ip_rate_limit(request)

    try:
        return await asset_service.analyze_asset(symbol, personalized=False)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/public/universe")
async def public_universe(request: Request) -> dict:
    """Os tickers que têm página — a fonte do sitemap."""
    await _ip_rate_limit(request, cost=2)

    tickers = await asyncio.to_thread(get_universe)
    return {
        "tickers": tickers,
        "count": len(tickers),
        # O robô usa isto para decidir se revisita. Dia brasileiro, como o
        # resto do produto.
        "lastmod": now_brt().strftime("%Y-%m-%d"),
    }
