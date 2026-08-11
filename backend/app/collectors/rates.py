from __future__ import annotations

import logging

import httpx

from app.core import cache

logger = logging.getLogger(__name__)

_BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{sid}/dados/ultimos/1?formato=json"

_SERIES = {"cdi": 4389, "selic": 432, "ipca": 13522}

_CACHE_KEY = "reference_rates:bcb"
_TTL = 24 * 3600
_TIMEOUT = 6.0

DEFAULT_CDI_ANUAL = 14.40
DEFAULT_SELIC_ANUAL = 14.40
DEFAULT_IPCA_ANUAL = 5.0


def _fetch_series(client: httpx.Client, sid: int) -> float | None:
    resp = client.get(_BCB_URL.format(sid=sid))
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None
    return float(str(data[-1]["valor"]).replace(",", "."))


def get_rates() -> dict:
    cached = cache.get(_CACHE_KEY)
    if cached:
        return cached

    fallback = {
        "cdi_anual": DEFAULT_CDI_ANUAL,
        "selic_anual": DEFAULT_SELIC_ANUAL,
        "ipca_anual": DEFAULT_IPCA_ANUAL,
        "source": "estimativa",
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            cdi = _fetch_series(client, _SERIES["cdi"])
            selic = _fetch_series(client, _SERIES["selic"])
            ipca = _fetch_series(client, _SERIES["ipca"])
    except Exception as exc:
        logger.warning("Falha ao buscar taxas do BCB (%s); usando estimativas.", exc)
        return fallback

    if not cdi or not selic:
        logger.warning("BCB retornou dados incompletos; usando estimativas.")
        return fallback

    rates = {
        "cdi_anual": round(cdi, 2),
        "selic_anual": round(selic, 2),
        "ipca_anual": round(ipca, 2) if ipca is not None else DEFAULT_IPCA_ANUAL,
        "source": "bcb",
    }
    cache.set(_CACHE_KEY, rates, _TTL)
    return rates
