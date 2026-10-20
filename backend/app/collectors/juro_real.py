from __future__ import annotations

import logging
import time

from app.core import cache

from . import circuit, mercado
from .plausibility import Range

logger = logging.getLogger(__name__)

PROVIDER = "mercado"
TITULO = "Tesouro IPCA+"

_CACHE_KEY = "juro_real:tesouro_ipca"
_TTL = 24 * 3600

FAIXA = Range(-5.0, 30.0, "Juro real fora de -5% a 30% ao ano não é taxa, é erro de leitura.")

SOURCE_BASE = "base"
SOURCE_CACHE_VENCIDO = "base_cache_vencido"


def mais_longo_a_venda(titulos: list[dict]) -> dict | None:
    a_venda = [
        t
        for t in titulos
        if t.get("titulo") == TITULO
        and t.get("taxa_compra") is not None
        and t.get("taxa_venda") is not None
    ]
    if not a_venda:
        return None
    return max(a_venda, key=lambda t: str(t["vencimento"]))


def _degradar(motivo: str) -> dict | None:
    vencido, _idade = cache.get_with_age(_CACHE_KEY)
    if vencido:
        logger.warning("Tesouro indisponível (%s); servindo cache vencido.", motivo)
        return {**vencido, "source": SOURCE_CACHE_VENCIDO}
    logger.warning("Tesouro indisponível (%s) e sem cache; ação fica sem taxa.", motivo)
    return None


def get_juro_real() -> dict | None:
    lido = cache.get(_CACHE_KEY)
    if lido:
        return lido
    if not circuit.allows(PROVIDER):
        return _degradar("circuito aberto")
    try:
        titulos = mercado._get("/v1/tesouro")["dados"]
    except Exception as exc:
        circuit.record_failure(PROVIDER, str(exc))
        return _degradar(str(exc))
    circuit.record_success(PROVIDER)

    titulo = mais_longo_a_venda(titulos)
    if titulo is None:
        logger.warning("Nenhum %s à venda no último dia da base; ação fica sem taxa.", TITULO)
        return None
    taxa = float(titulo["taxa_venda"])
    if not FAIXA.accepts(taxa):
        logger.warning("%s com taxa %s, fora da faixa: %s", TITULO, taxa, FAIXA.reason)
        return None

    juro = {
        "taxa": round(taxa, 2),
        "vencimento": str(titulo["vencimento"])[:10],
        "data": str(titulo.get("data"))[:10],
        "source": SOURCE_BASE,
        "fetched_at": time.time(),
    }
    cache.set(_CACHE_KEY, juro, _TTL)
    return juro
